"""
Tests for EDE Checklist Agent — multi-emirate + anti-monopoly + class-based.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.checklist import EDEChecklistAgent, MD_CLASS_CHECKLISTS, IVD_CLASS_CHECKLISTS


class TestEDEChecklistAgent:

    def setup_method(self):
        self.agent = EDEChecklistAgent()

    def test_md_class_i_checklist(self):
        """Class I should produce base checklist."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="I",
            target_emirates=["federal"],
            decision_date="2026-09-15",
            is_connected=False,
            is_ai_enabled=False,
        )
        # Should include basic items
        names = [item["name"] for item in checklist]
        assert any("Application Form" in n for n in names)
        assert any("ISO 13485" in n for n in names)
        # Should NOT include Class III/IV-only items
        assert not any("Penetration Test Report" in n for n in names)

    def test_md_class_iv_cumulative_checklist(self):
        """Class IV should include all lower classes' items + own."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="IV",
            target_emirates=["federal"],
            decision_date="2026-09-15",
            is_connected=True,
            is_ai_enabled=True,
        )
        names = [item["name"] for item in checklist]
        # Class I items
        assert any("Application Form" in n for n in names)
        # Class II items
        assert any("Technical File" in n for n in names)
        assert any("Risk Management File" in n for n in names)
        # Class III items
        assert any("Cybersecurity" in n for n in names)
        assert any("PMSP" in n for n in names)
        # Class IV items
        assert any("Penetration Test Report" in n for n in names)
        assert any("Human Factors" in n for n in names)

    def test_ivd_class_a_checklist(self):
        """IVD Class A should produce base IVD checklist."""
        checklist = self.agent.generate(
            device_type="IVD",
            risk_class="A",
            target_emirates=["federal"],
            decision_date="2026-09-15",
        )
        names = [item["name"] for item in checklist]
        assert any("Application Form" in n for n in names)
        assert any("ISO 13485" in n for n in names)

    def test_ivd_class_d_cumulative(self):
        """IVD Class D should include all lower."""
        checklist = self.agent.generate(
            device_type="IVD",
            risk_class="D",
            target_emirates=["federal"],
            decision_date="2026-09-15",
        )
        names = [item["name"] for item in checklist]
        assert any("Reference Measurement" in n for n in names)  # Class D
        assert any("Performance Evaluation" in n for n in names)  # Class B
        assert any("Clinical Performance Data" in n for n in names)  # Class C

    def test_anti_monopoly_post_feb_2026(self):
        """Post-Feb 2026 → multi-LAR requirement applies."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="III",
            target_emirates=["federal"],
            decision_date="2026-09-15",  # after Feb 2026
            is_connected=True,
            is_ai_enabled=True,
        )
        names = [item["name"] for item in checklist]
        assert any("Anti-monopoly" in n or "Multi-LAR" in n for n in names)

    def test_anti_monopoly_pre_feb_2026(self):
        """Pre-Feb 2026 → no anti-monopoly requirement."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="III",
            target_emirates=["federal"],
            decision_date="2025-12-01",  # before Feb 2026
            is_connected=True,
            is_ai_enabled=True,
        )
        names = [item["name"] for item in checklist]
        assert not any("Anti-monopoly" in n or "Multi-LAR" in n for n in names)

    def test_multi_emirate_dubai_addition(self):
        """Dubai emirate → DHA Digital Health Platform item added."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="III",
            target_emirates=["federal", "dubai"],
            decision_date="2026-09-15",
            is_connected=True,
            is_ai_enabled=True,
        )
        names = [item["name"] for item in checklist]
        assert any("DHA" in n for n in names)

    def test_multi_emirate_abu_dhabi_ai_addition(self):
        """Abu Dhabi + AI device → DOH Responsible AI item added."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="III",
            target_emirates=["federal", "abu_dhabi"],
            decision_date="2026-09-15",
            is_connected=True,
            is_ai_enabled=True,
        )
        names = [item["name"] for item in checklist]
        assert any("DOH Responsible AI" in n for n in names)

    def test_multi_emirate_abu_dhabi_no_ai_skipped(self):
        """Abu Dhabi without AI → DOH item not added."""
        checklist = self.agent.generate(
            device_type="MD",
            risk_class="III",
            target_emirates=["federal", "abu_dhabi"],
            decision_date="2026-09-15",
            is_connected=True,
            is_ai_enabled=False,  # no AI
        )
        names = [item["name"] for item in checklist]
        assert not any("DOH Responsible AI" in n for n in names)

    def test_data_localization_only_for_connected(self):
        """Data localization only for connected devices."""
        checklist_connected = self.agent.generate(
            device_type="MD", risk_class="III",
            target_emirates=["federal"],
            decision_date="2026-09-15",
            is_connected=True,
        )
        checklist_non_connected = self.agent.generate(
            device_type="MD", risk_class="III",
            target_emirates=["federal"],
            decision_date="2026-09-15",
            is_connected=False,
        )
        names_c = [item["name"] for item in checklist_connected]
        names_nc = [item["name"] for item in checklist_non_connected]
        assert any("Data Localization" in n for n in names_c)
        assert not any("Data Localization" in n for n in names_nc)

    def test_get_missing_documents(self):
        """Compare required vs submitted → return missing list."""
        submitted = ["Application Form (signed)", "ISO 13485:2016 Certificate"]
        missing = self.agent.get_missing_documents(
            device_type="MD",
            risk_class="I",
            submitted_documents=submitted,
            target_emirates=["federal"],
            decision_date="2026-09-15",
        )
        # Should have missing items (everything not in submitted list)
        assert len(missing) > 0
        missing_names = [m["name"] for m in missing]
        assert "Free Sale Certificate (UAE Embassy legalized)" in missing_names
        assert "Declaration of Conformity (EC-DoC)" in missing_names


class TestChecklistSchemas:

    def test_md_class_schemas_complete(self):
        """All 4 MD classes defined."""
        for cls in ["I", "II", "III", "IV"]:
            assert cls in MD_CLASS_CHECKLISTS, f"Missing MD class {cls}"
            assert len(MD_CLASS_CHECKLISTS[cls]) > 0

    def test_ivd_class_schemas_complete(self):
        """All 4 IVD classes defined."""
        for cls in ["A", "B", "C", "D"]:
            assert cls in IVD_CLASS_CHECKLISTS, f"Missing IVD class {cls}"
            assert len(IVD_CLASS_CHECKLISTS[cls]) > 0

    def test_all_items_have_required_fields(self):
        """Every checklist item should have name + source + mandatory."""
        for cls, items in MD_CLASS_CHECKLISTS.items():
            for item in items:
                assert "name" in item, f"MD class {cls}: item missing 'name'"
                assert "source" in item, f"MD class {cls}: item missing 'source'"
                assert "mandatory" in item, f"MD class {cls}: item missing 'mandatory'"
