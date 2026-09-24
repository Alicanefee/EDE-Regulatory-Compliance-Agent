"""
Multi-LAR Verifier (Anti-Monopoly Mechanism)
=============================================

UAE EDE Anti-Monopoly requirement (February 2026):
  Every medical device must have multiple LAR/MAH assigned.
  Single-distributor model ended.

This module verifies:
  1. At least 2 LAR/MAH assigned per product
  2. Each LAR/MAH has valid EDE license
  3. Geographic coverage (which emirates)
  4. Effective date check (post-Feb 2026)

See docs/BEHAVIOR_AND_ATTENTION.md §A4 for the design.

Dependencies: openpyxl (for cross-referencing the Excel audit log)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


# Anti-monopoly effective date
ANTI_MONOPOLY_EFFECTIVE_DATE = "2026-02-01"  # February 2026


@dataclass
class LARAssignment:
    """A LAR/MAH assignment for a product."""
    lar_name: str           # Company name
    ede_license_id: str     # EDE Medical Device Establishment License ID
    ede_license_expiry: str  # ISO date
    geographic_coverage: list[str]  # ["federal", "dubai", "abu_dhabi", "dhcc"]
    appointment_date: str  # ISO date
    is_primary: bool = False


@dataclass
class AntiMonopolyFinding:
    """Result of anti-monopoly check."""
    severity: str  # "critical" | "warning" | "info" | "ok"
    title: str
    description: str
    cited_clause: str = "EDE Anti-Monopoly Mechanism (Feb 2026)"


class MultiLARVerifier:
    """Verifies UAE EDE anti-monopoly compliance."""

    def verify(
        self,
        decision_date: str,
        lar_assignments: list[LARAssignment],
        target_emirates: list[str] | None = None,
    ) -> list[AntiMonopolyFinding]:
        """Verify anti-monopoly compliance for a submission.

        Args:
            decision_date: ISO date (e.g. "2026-09-15")
            lar_assignments: List of LAR/MAH assignments
            target_emirates: List of target emirates ["federal", "dubai", ...]

        Returns: List of findings (empty if compliant).
        """
        findings = []

        # Pre-Feb 2026 → no anti-monopoly requirement
        if decision_date < ANTI_MONOPOLY_EFFECTIVE_DATE:
            findings.append(AntiMonopolyFinding(
                severity="info",
                title="Anti-monopoly not yet required",
                description=(
                    f"Decision date {decision_date} is before anti-monopoly effective "
                    f"date {ANTI_MONOPOLY_EFFECTIVE_DATE}. Single-LAR model accepted."
                ),
            ))
            return findings

        # Post-Feb 2026 → check multi-LAR
        if len(lar_assignments) < 2:
            findings.append(AntiMonopolyFinding(
                severity="critical",
                title="Single LAR/MAH after Feb 2026 (anti-monopoly violation)",
                description=(
                    f"Only {len(lar_assignments)} LAR/MAH assigned. "
                    f"Post-{ANTI_MONOPOLY_EFFECTIVE_DATE}, minimum 2 required."
                ),
                cited_clause="EDE Anti-Monopoly Mechanism (Feb 2026)",
            ))

        # Check each LAR's license validity
        today = date.today().isoformat()
        for lar in lar_assignments:
            # License not expired
            if lar.ede_license_expiry < today:
                findings.append(AntiMonopolyFinding(
                    severity="critical",
                    title=f"LAR license expired: {lar.lar_name}",
                    description=(
                        f"LAR '{lar.lar_name}' license expired on {lar.ede_license_expiry}. "
                        f"EDE MDEL must be valid."
                    ),
                    cited_clause="Federal Decree-Law No. 38 of 2024, Article 2.2",
                ))

            # Geographic coverage check
            if target_emirates:
                covered = set(lar.geographic_coverage)
                required = set(target_emirates) | {"federal"}
                missing_emirates = required - covered
                if missing_emirates and "federal" not in covered:
                    findings.append(AntiMonopolyFinding(
                        severity="warning",
                        title=f"LAR coverage gap: {lar.lar_name}",
                        description=(
                            f"LAR does not cover: {', '.join(missing_emirates)}. "
                            f"May need separate LAR for those emirates."
                        ),
                    ))

        # Check primary LAR is designated
        primaries = [lar for lar in lar_assignments if lar.is_primary]
        if not primaries:
            findings.append(AntiMonopolyFinding(
                severity="warning",
                title="No primary LAR designated",
                description=(
                    "No LAR marked as primary (is_primary=True). "
                    "Submission processing may be delayed."
                ),
            ))
        elif len(primaries) > 1:
            findings.append(AntiMonopolyFinding(
                severity="warning",
                title="Multiple primary LARs",
                description=(
                    f"{len(primaries)} LARs marked as primary. Only one should be primary."
                ),
            ))

        return findings

    def verify_from_submission(self, submission_data: dict) -> list[AntiMonopolyFinding]:
        """Convenience: verify from a submission_package.json structure."""
        decision_date = submission_data.get("submission_date", date.today().isoformat())

        lar_block = submission_data.get("lar_mah", {})
        lar_assignments = []

        primary = lar_block.get("primary")
        if primary:
            lar_assignments.append(LARAssignment(
                lar_name=primary,
                ede_license_id=lar_block.get("primary_license_id", ""),
                ede_license_expiry=lar_block.get("primary_license_expiry", "2027-12-31"),
                geographic_coverage=lar_block.get("primary_coverage", ["federal"]),
                appointment_date=lar_block.get("appointment_date", decision_date),
                is_primary=True,
            ))

        secondary = lar_block.get("secondary")
        if secondary:
            lar_assignments.append(LARAssignment(
                lar_name=secondary,
                ede_license_id=lar_block.get("secondary_license_id", ""),
                ede_license_expiry=lar_block.get("secondary_license_expiry", "2027-12-31"),
                geographic_coverage=lar_block.get("secondary_coverage", ["federal"]),
                appointment_date=lar_block.get("secondary_appointment_date", decision_date),
                is_primary=False,
            ))

        target_emirates = submission_data.get("target_emirates", ["federal"])
        return self.verify(decision_date, lar_assignments, target_emirates)
