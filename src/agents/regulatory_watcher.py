"""
Agent: Regulatory Watcher
=========================

Periodically scans EDE official documents page for new versions.

Input: URL list (EDE official document URLs)
Output: New version notifications + diff analysis

Pipeline:
1. Poll EDE document URLs on schedule (weekly)
2. Download each document
3. Compute version hash (sha256 of text)
4. Compare with last-seen hash (from version_registry.json)
5. If changed → fetch both versions, run diff
6. Notify user: "Federal Decree-Law No. 38/2024 updated — 14 clauses changed"
7. Trigger re-validation of past decisions that depended on the old version

EDE-specific URLs:
  - https://www.ede.gov.ae (main portal)
  - Federal Decree-Law No. 38 of 2024
  - EDE Classification Guidelines
  - DOH Responsible AI Standard (Abu Dhabi)

Dependencies: requests (or httpx for async)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any


# EDE official document URLs to watch
EDE_DOCUMENT_URLS = {
    "Federal Decree-Law No. 38 of 2024": "https://www.ede.gov.ae/en/legislation/federal-decree-law-38-2024",
    "EDE Classification Guidelines": "https://www.ede.gov.ae/en/guidelines/classification",
    "EDE Manufacturer Site Registration": "https://www.ede.gov.ae/en/services/manufacturer-registration",
    "DOH Responsible AI Standard (Abu Dhabi)": "https://doh.gov.ae/en/standards/responsible-ai",
    "Standard on Medical Device Reporting (MDR)": "https://www.ede.gov.ae/en/standards/mdr",
}


class RegulatoryWatcher:
    """Watches EDE regulatory documents for new versions.

    Maintains a version registry:
        {
          "Federal Decree-Law No. 38 of 2024": {
            "current_version": "1.0",
            "current_hash": "sha256:abc...",
            "last_checked": "2026-09-24T11:30:00",
            "last_changed": "2025-01-02",
            "url": "https://..."
          },
          ...
        }
    """

    def __init__(self, registry_path: str | Path = "./data/version_registry.json") -> None:
        self.registry_path = Path(registry_path)
        self.registry = self._load_registry()

    def _load_registry(self) -> dict:
        """Load existing registry from JSON file."""
        if self.registry_path.exists():
            try:
                return json.loads(self.registry_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return {}
        return {}

    def _save_registry(self) -> None:
        """Save registry to JSON file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        self.registry_path.write_text(
            json.dumps(self.registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def scan_all(self) -> list[dict]:
        """Scan all EDE documents for new versions.

        Returns: list of changes detected.
        """
        changes = []
        for doc_name, url in EDE_DOCUMENT_URLS.items():
            change = self._scan_one(doc_name, url)
            if change:
                changes.append(change)
        self._save_registry()
        return changes

    def _scan_one(self, doc_name: str, url: str) -> dict | None:
        """Scan a single document for changes."""
        try:
            import requests
            response = requests.get(url, timeout=30, headers={
                "User-Agent": "EDE-Regulatory-Watcher/0.1"
            })
            response.raise_for_status()
            content = response.text
        except ImportError:
            return None  # requests not installed
        except Exception as e:
            return {
                "doc_name": doc_name,
                "url": url,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

        content_hash = hashlib.sha256(content.encode()).hexdigest()
        existing = self.registry.get(doc_name, {})

        if existing.get("current_hash") == content_hash:
            # No change
            existing["last_checked"] = datetime.now().isoformat()
            self.registry[doc_name] = existing
            return None

        # Change detected
        old_hash = existing.get("current_hash")
        old_version = existing.get("current_version", "unknown")
        new_version = self._extract_version(content) or "unknown"

        change = {
            "doc_name": doc_name,
            "url": url,
            "old_version": old_version,
            "new_version": new_version,
            "old_hash": old_hash,
            "new_hash": content_hash,
            "timestamp": datetime.now().isoformat(),
            "diff_summary": self._compute_diff_summary(existing.get("content"), content),
        }

        # Update registry
        self.registry[doc_name] = {
            "current_version": new_version,
            "current_hash": content_hash,
            "current_content": content[:5000],  # store first 5KB for diff
            "last_checked": datetime.now().isoformat(),
            "last_changed": datetime.now().isoformat(),
            "url": url,
        }

        return change

    def _extract_version(self, content: str) -> str | None:
        """Try to extract version string from document content."""
        import re
        # Look for patterns like "Version 5.0", "v3.1", "1.0", etc.
        match = re.search(r"(?:Version|Ver\.?|v)\s*(\d+\.\d+)", content, re.IGNORECASE)
        if match:
            return match.group(1)
        # Look for date pattern
        match = re.search(r"(\d{1,2}/\d{1,2}/\d{4})", content)
        if match:
            return match.group(1)
        return None

    def _compute_diff_summary(self, old_content: str | None, new_content: str) -> str:
        """Compute a simple diff summary (line count delta + first changed lines)."""
        if not old_content:
            return f"New document detected ({len(new_content)} chars)"
        old_lines = old_content.split("\n")
        new_lines = new_content.split("\n")
        added = max(0, len(new_lines) - len(old_lines))
        removed = max(0, len(old_lines) - len(new_lines))
        return f"+{added} lines, -{removed} lines (total: {len(new_lines)} vs {len(old_lines)})"

    def notify_change(self, change: dict) -> str:
        """Generate a user notification for a regulatory version change."""
        msg = (
            f"⚠️ REGULATORY UPDATE DETECTED\n"
            f"Document: {change['doc_name']}\n"
            f"Old version: {change.get('old_version', 'unknown')}\n"
            f"New version: {change.get('new_version', 'unknown')}\n"
            f"URL: {change['url']}\n"
            f"Diff: {change.get('diff_summary', '(no summary)')}\n"
            f"Timestamp: {change['timestamp']}\n\n"
            f"⚠️ Past decisions that depended on the old version may need re-validation. "
            f"Run audit.verify_chain() + re-run classifier + evidence validator."
        )
        return msg

    def trigger_revalidation(self, doc_name: str, old_version: str) -> list[str]:
        """Find past decisions that depended on the old version.

        TODO (v0.3): Query Excel audit trail for decisions citing old_version.
        Returns: list of decision_ids to re-validate.
        """
        # Placeholder — in v0.3 this would query the Excel audit log
        return []


def regulatory_watcher_agent(ctx) -> dict:
    """State machine calls this for periodic checks (not part of main flow)."""
    watcher = RegulatoryWatcher()
    changes = watcher.scan_all()
    notifications = [watcher.notify_change(c) for c in changes]
    return {
        "changes_detected": len(changes),
        "notifications": notifications,
    }
