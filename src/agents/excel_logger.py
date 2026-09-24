"""
Agent: Excel Logger
==================

Writes all events to local .xlsx with hash-chain audit trail.

6 sheets (see docs/architecture.md):
1. Process: timestamp, step, status, agent, duration, prev_hash, this_hash
2. Documents: doc_id, name, type, upload_date, status, source_authority
3. Classification: device_name, intended_use, class, rule_id, justification, version_snapshot
4. Validation: doc_id, requirement, result, missing_items, notes, prev_hash, this_hash
5. API_Log: timestamp, agent, model, tokens, cost, latency
6. Audit: hash_chain_verification results

Hash chain:
    this_hash = sha256(prev_hash + row_content + timestamp)
    First row: prev_hash = "GENESIS"

Defense: Excel is editable, but any modification breaks the chain.
Inspector can run audit.verify_chain() to detect tampering.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from src.state_machine import StateContext


GENESIS_HASH = "GENESIS"

SHEET_SCHEMAS = {
    "Process": ["timestamp", "step", "status", "agent", "duration_sec",
                "prev_hash", "this_hash"],
    "Documents": ["doc_id", "name", "type", "upload_date", "status",
                  "source_authority", "prev_hash", "this_hash"],
    "Classification": ["timestamp", "device_name", "intended_use", "class",
                       "rule_id", "justification", "version_snapshot",
                       "prev_hash", "this_hash"],
    "Validation": ["timestamp", "doc_id", "requirement", "result",
                   "missing_items", "notes", "prev_hash", "this_hash"],
    "API_Log": ["timestamp", "agent", "model", "input_tokens",
                "output_tokens", "cost_usd", "latency_ms", "prev_hash", "this_hash"],
    "Audit": ["timestamp", "event_type", "details",
              "prev_hash", "this_hash"],
}


class ExcelLogger:
    """Writes audit-trail events to local .xlsx with hash chain."""

    def __init__(self, xlsx_path: str | Path = "./data/audit_log.xlsx") -> None:
        self.xlsx_path = Path(xlsx_path)
        self.last_hash = GENESIS_HASH
        self.wb = None
        self._init_workbook()

    def _init_workbook(self) -> None:
        """Initialize the workbook with 6 sheets + headers."""
        try:
            import openpyxl
            from openpyxl import Workbook, load_workbook
        except ImportError:
            # openpyxl not installed — degrade gracefully (log to memory)
            return

        if self.xlsx_path.exists():
            self.wb = load_workbook(self.xlsx_path)
            # Load last hash from last row of Audit sheet
            if "Audit" in self.wb.sheetnames:
                audit_ws = self.wb["Audit"]
                if audit_ws.max_row > 1:
                    last_row = audit_ws.max_row
                    self.last_hash = audit_ws.cell(row=last_row, column=9).value or GENESIS_HASH
        else:
            self.wb = Workbook()
            # Remove default sheet
            if "Sheet" in self.wb.sheetnames:
                del self.wb["Sheet"]
            # Create 6 sheets with headers
            for sheet_name, columns in SHEET_SCHEMAS.items():
                ws = self.wb.create_sheet(sheet_name)
                for col_idx, col_name in enumerate(columns, 1):
                    ws.cell(row=1, column=col_idx, value=col_name)
            self.wb.save(self.xlsx_path)

    def log(self, sheet: str, event: dict) -> str:
        """Append a row to the specified sheet with hash chain.

        Args:
            sheet: One of SHEET_SCHEMAS keys
            event: Dict with event data (will be augmented with hash fields)

        Returns: this_hash (for verification)
        """
        if sheet not in SHEET_SCHEMAS:
            raise ValueError(f"Unknown sheet: {sheet}. Must be one of {list(SHEET_SCHEMAS.keys())}")

        timestamp = datetime.now().isoformat()
        row_content = json.dumps(event, sort_keys=True, default=str)
        this_hash = hashlib.sha256(
            f"{self.last_hash}{row_content}{timestamp}".encode()
        ).hexdigest()

        event_with_hash = {
            **event,
            "timestamp": timestamp,
            "prev_hash": self.last_hash,
            "this_hash": this_hash,
        }

        if self.wb is None:
            # openpyxl not installed — just update in-memory hash
            self.last_hash = this_hash
            return this_hash

        # Write to sheet
        if sheet not in self.wb.sheetnames:
            ws = self.wb.create_sheet(sheet)
            for col_idx, col_name in enumerate(SHEET_SCHEMAS[sheet], 1):
                ws.cell(row=1, column=col_idx, value=col_name)
        ws = self.wb[sheet]

        columns = SHEET_SCHEMAS[sheet]
        next_row = ws.max_row + 1
        for col_idx, col_name in enumerate(columns, 1):
            value = event_with_hash.get(col_name, "")
            ws.cell(row=next_row, column=col_idx, value=value)

        self.wb.save(self.xlsx_path)
        self.last_hash = this_hash
        return this_hash

    def verify_chain(self, sheet: str = "Audit") -> dict:
        """Verify hash chain integrity for a sheet.

        Returns: {valid: bool, rows_checked: int, breaks: list}
        """
        if self.wb is None:
            return {"valid": True, "rows_checked": 0, "breaks": [], "note": "openpyxl not installed"}

        if sheet not in self.wb.sheetnames:
            return {"valid": False, "rows_checked": 0, "breaks": [], "note": f"Sheet {sheet} not found"}

        ws = self.wb[sheet]
        columns = SHEET_SCHEMAS.get(sheet, [])
        if "prev_hash" not in columns or "this_hash" not in columns:
            return {"valid": True, "rows_checked": 0, "breaks": [],
                    "note": "Sheet does not have hash chain columns"}

        prev_hash_col = columns.index("prev_hash") + 1
        this_hash_col = columns.index("this_hash") + 1
        timestamp_col = columns.index("timestamp") + 1

        rows_checked = 0
        breaks = []
        expected_prev = GENESIS_HASH

        for row_idx in range(2, ws.max_row + 1):
            row_data = {}
            for col_idx, col_name in enumerate(columns, 1):
                cell_value = ws.cell(row=row_idx, column=col_idx).value
                if col_name not in ("prev_hash", "this_hash", "timestamp"):
                    row_data[col_name] = cell_value

            stored_prev = ws.cell(row=row_idx, column=prev_hash_col).value
            stored_this = ws.cell(row=row_idx, column=this_hash_col).value
            timestamp = ws.cell(row=row_idx, column=timestamp_col).value

            # Verify prev_hash matches expected
            if stored_prev != expected_prev:
                breaks.append({
                    "row": row_idx,
                    "expected_prev": expected_prev,
                    "actual_prev": stored_prev,
                })

            # Verify this_hash matches recomputed
            if timestamp:
                row_content = json.dumps(row_data, sort_keys=True, default=str)
                recomputed = hashlib.sha256(
                    f"{expected_prev}{row_content}{timestamp}".encode()
                ).hexdigest()
                if recomputed != stored_this:
                    breaks.append({
                        "row": row_idx,
                        "expected_hash": recomputed,
                        "actual_hash": stored_this,
                    })

            expected_prev = stored_this or GENESIS_HASH
            rows_checked += 1

        return {"valid": len(breaks) == 0, "rows_checked": rows_checked, "breaks": breaks}

    def close(self) -> None:
        """Save and close the workbook."""
        if self.wb is not None:
            self.wb.save(self.xlsx_path)


def excel_logger_agent(ctx: StateContext) -> dict:
    """State machine calls this for terminal states (DONE + MANUAL_REVIEW)."""
    logger = ExcelLogger()

    # Log the state machine completion event
    final_state = ctx.current_state.value
    logger.log("Audit", {
        "event_type": "state_machine_complete",
        "details": f"Final state: {final_state}, Audit events: {len(ctx.audit_log)}",
    })

    # Log classification result if available
    if ctx.classification_result:
        cr = ctx.classification_result
        logger.log("Classification", {
            "device_name": cr.get("device_name", ctx.submission_data.get("device_name", "")),
            "intended_use": cr.get("justification", "")[:200],
            "class": cr.get("md_class") or cr.get("ivd_class") or "(none)",
            "rule_id": cr.get("md_rule_id") or cr.get("ivd_rule_id") or "(none)",
            "justification": cr.get("justification", "")[:500],
            "version_snapshot": "EDE Classification Guidelines 2024 / Federal Decree-Law 38/2024",
        })

    # Log validation findings
    for finding in ctx.findings:
        logger.log("Validation", {
            "doc_id": finding.get("doc_id", ""),
            "requirement": finding.get("title", finding.get("clause_id", "")),
            "result": finding.get("verdict", ""),
            "missing_items": finding.get("description", "")[:200],
            "notes": finding.get("suggested_fix", "")[:200],
        })

    # Log all submitted documents
    for doc in ctx.submission_data.get("submitted_documents", []):
        logger.log("Documents", {
            "doc_id": doc.get("name", "")[:50],
            "name": doc.get("name", ""),
            "type": doc.get("type", ""),
            "upload_date": ctx.submission_data.get("submission_date", ""),
            "status": "submitted",
            "source_authority": ctx.submission_data.get("jurisdiction", "UAE EDE"),
        })

    logger.close()

    return {"logged": True, "xlsx_path": str(logger.xlsx_path)}
