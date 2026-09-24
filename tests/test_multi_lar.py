"""
Tests for Multi-LAR Verifier — anti-monopoly mechanism.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils.multi_lar_verifier import (
    MultiLARVerifier, LARAssignment, AntiMonopolyFinding,
    ANTI_MONOPOLY_EFFECTIVE_DATE
)


class TestMultiLARVerifier:

    def setup_method(self):
        self.verifier = MultiLARVerifier()

    def test_pre_anti_monopoly_no_requirement(self):
        """Pre-Feb 2026 → no multi-LAR required."""
        findings = self.verifier.verify(
            decision_date="2025-12-01",  # before Feb 2026
            lar_assignments=[LARAssignment(
                lar_name="Single LAR",
                ede_license_id="LIC-001",
                ede_license_expiry="2027-12-31",
                geographic_coverage=["federal"],
                appointment_date="2025-01-01",
                is_primary=True,
            )],
        )
        # Should be info-level, not critical
        assert all(f.severity != "critical" for f in findings)
        assert any("not yet required" in f.title.lower() for f in findings)

    def test_post_anti_monopoly_single_lar_critical(self):
        """Post-Feb 2026 with single LAR → critical finding."""
        findings = self.verifier.verify(
            decision_date="2026-09-15",  # after Feb 2026
            lar_assignments=[LARAssignment(
                lar_name="Single LAR",
                ede_license_id="LIC-001",
                ede_license_expiry="2027-12-31",
                geographic_coverage=["federal"],
                appointment_date="2026-01-01",
                is_primary=True,
            )],
        )
        critical = [f for f in findings if f.severity == "critical"]
        assert len(critical) >= 1
        assert any("Single LAR" in f.title or "anti-monopoly" in f.title.lower() for f in critical)

    def test_post_anti_monopoly_dual_lar_ok(self):
        """Post-Feb 2026 with 2 LARs → no critical finding on count."""
        findings = self.verifier.verify(
            decision_date="2026-09-15",
            lar_assignments=[
                LARAssignment(
                    lar_name="Primary LAR",
                    ede_license_id="LIC-001",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["federal"],
                    appointment_date="2026-01-01",
                    is_primary=True,
                ),
                LARAssignment(
                    lar_name="Secondary LAR",
                    ede_license_id="LIC-002",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["federal"],
                    appointment_date="2026-02-01",
                    is_primary=False,
                ),
            ],
        )
        critical = [f for f in findings if f.severity == "critical"]
        assert len(critical) == 0

    def test_expired_license_critical(self):
        """LAR with expired license → critical."""
        findings = self.verifier.verify(
            decision_date="2026-09-15",
            lar_assignments=[
                LARAssignment(
                    lar_name="Primary LAR",
                    ede_license_id="LIC-001",
                    ede_license_expiry="2025-01-01",  # expired
                    geographic_coverage=["federal"],
                    appointment_date="2024-01-01",
                    is_primary=True,
                ),
                LARAssignment(
                    lar_name="Secondary LAR",
                    ede_license_id="LIC-002",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["federal"],
                    appointment_date="2026-02-01",
                    is_primary=False,
                ),
            ],
        )
        critical = [f for f in findings if f.severity == "critical"]
        assert any("expired" in f.title.lower() for f in critical)

    def test_no_primary_designated_warning(self):
        """No primary LAR → warning."""
        findings = self.verifier.verify(
            decision_date="2026-09-15",
            lar_assignments=[
                LARAssignment(
                    lar_name="LAR 1",
                    ede_license_id="LIC-001",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["federal"],
                    appointment_date="2026-01-01",
                    is_primary=False,  # none primary
                ),
                LARAssignment(
                    lar_name="LAR 2",
                    ede_license_id="LIC-002",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["federal"],
                    appointment_date="2026-02-01",
                    is_primary=False,
                ),
            ],
        )
        warnings = [f for f in findings if f.severity == "warning"]
        assert any("primary" in f.title.lower() for f in warnings)

    def test_geographic_coverage_gap(self):
        """LAR not covering required emirate → warning."""
        findings = self.verifier.verify(
            decision_date="2026-09-15",
            lar_assignments=[
                LARAssignment(
                    lar_name="Dubai-only LAR",
                    ede_license_id="LIC-001",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["dubai"],  # only Dubai
                    appointment_date="2026-01-01",
                    is_primary=True,
                ),
                LARAssignment(
                    lar_name="Secondary Dubai-only",
                    ede_license_id="LIC-002",
                    ede_license_expiry="2027-12-31",
                    geographic_coverage=["dubai"],
                    appointment_date="2026-02-01",
                    is_primary=False,
                ),
            ],
            target_emirates=["abu_dhabi"],  # need Abu Dhabi coverage
        )
        warnings = [f for f in findings if f.severity == "warning"]
        assert any("coverage gap" in f.title.lower() for f in warnings)
