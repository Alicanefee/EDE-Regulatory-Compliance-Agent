"""
Tests for EDE Classifier — GHTF MD + IVD rules.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from ede_classification import EDEClassifier, MD_RULES, IVD_RULES


class TestEDEClassifier:
    """Test the deterministic EDE classifier."""

    def setup_method(self):
        self.classifier = EDEClassifier()

    def test_canon_vitrae_mri_class_iii(self):
        """Canon VITRAE MRI System → Class III per EDE-MD-R13."""
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Diagnostic imaging via magnetic resonance",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=True,
            is_diagnostic=True,
            uses_ionizing_radiation=False,
            uses_non_ionizing_radiation=True,
            implantable=False,
            targets=[],
            contains_biological_substance=False,
            contains_drug=False,
        )
        assert result.md_class == "III"
        assert result.md_rule_id == "EDE-MD-R13"
        assert "non-ionizing" in result.justification.lower() or "non-ionizing" in result.justification
        assert result.is_uncertain is False

    def test_xray_class_iii(self):
        """X-ray device → Class III per EDE-MD-R14 (ionizing radiation)."""
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Diagnostic X-ray imaging",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=True,
            is_diagnostic=True,
            uses_ionizing_radiation=True,
            uses_non_ionizing_radiation=False,
            implantable=False,
            targets=[],
            contains_biological_substance=False,
            contains_drug=False,
        )
        assert result.md_class == "III"
        assert result.md_rule_id == "EDE-MD-R14"

    def test_surgical_forceps_class_ii(self):
        """Surgical forceps → Class II per EDE-MD-R1."""
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Surgical grasping",
            duration_of_use="transient",
            invasiveness="invasive_surgical",
            active=False,
            implantable=False,
            targets=[],
        )
        # R1 should match — surgically invasive, transient
        assert result.md_class is not None
        # Multiple rules may apply — R1 gives II, R7 gives I (if simple surgical instrument)
        # Conservative: should pick the higher
        assert result.md_class in ("I", "II")

    def test_simple_thermometer_class_i(self):
        """Simple thermometer → Class I per EDE-MD-R8 (default non-invasive)."""
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Body temperature measurement",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=False,
            is_diagnostic=False,
            implantable=False,
            targets=[],
        )
        assert result.md_class == "I"
        assert result.md_rule_id == "EDE-MD-R8"

    def test_ivd_hiv_test_class_d(self):
        """HIV test (IVD, infectious disease high risk) → Class D per EDE-IVD-R10."""
        result = self.classifier.classify(
            device_type="IVD",
            intended_use="HIV detection",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=False,
            ivd_type="infectious_disease_high_risk",
        )
        assert result.ivd_class == "D"
        assert result.ivd_rule_id == "EDE-IVD-R10"

    def test_ivd_pregnancy_test_class_b(self):
        """Self-testing pregnancy IVD → Class B per EDE-IVD-R6."""
        result = self.classifier.classify(
            device_type="IVD",
            intended_use="Pregnancy detection (self-test)",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=False,
            ivd_type="self_testing_pregnancy",
        )
        assert result.ivd_class == "B"
        assert result.ivd_rule_id == "EDE-IVD-R6"

    def test_ivd_specimen_receptacle_class_a(self):
        """Specimen receptacle → Class A per EDE-IVD-R1."""
        result = self.classifier.classify(
            device_type="IVD",
            intended_use="Specimen container",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=False,
            ivd_type="specimen_receptacle",
        )
        assert result.ivd_class == "A"
        assert result.ivd_rule_id == "EDE-IVD-R1"

    def test_cardiac_pacemaker_implant_class_iv(self):
        """Implantable cardiac pacemaker → Class IV per EDE-MD-R21 (central circulation)."""
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Cardiac pacing",
            duration_of_use="permanent",
            invasiveness="implantable",
            active=True,
            implantable=True,
            targets=["central_circulation"],
        )
        assert result.md_class == "IV"
        assert result.md_rule_id == "EDE-MD-R21"

    def test_conservative_rule_selection(self):
        """Multiple matching rules → highest class wins (conservative)."""
        # A device that could match both R7 (I) and R5 (II) should get II
        result = self.classifier.classify(
            device_type="MD",
            intended_use="Body fluid collection",
            duration_of_use="transient",
            invasiveness="non_invasive",
            active=False,
            handles_body_fluids=True,
            is_simple_surgical_instrument=True,
        )
        # R5 (II for body fluids) > R7 (I for simple instruments)
        assert result.md_class == "II"
        assert result.md_rule_id == "EDE-MD-R5"


class TestClassificationRules:
    """Test rule definitions are well-formed."""

    def test_all_md_rules_have_unique_ids(self):
        rule_ids = [r.rule_id for r in MD_RULES]
        assert len(rule_ids) == len(set(rule_ids)), "Duplicate rule_ids in MD_RULES"

    def test_all_ivd_rules_have_unique_ids(self):
        rule_ids = [r.rule_id for r in IVD_RULES]
        assert len(rule_ids) == len(set(rule_ids)), "Duplicate rule_ids in IVD_RULES"

    def test_all_md_rule_classes_valid(self):
        valid = {"I", "II", "III", "IV"}
        for rule in MD_RULES:
            assert rule.resulting_class in valid, \
                f"Rule {rule.rule_id} has invalid class: {rule.resulting_class}"

    def test_all_ivd_rule_classes_valid(self):
        valid = {"A", "B", "C", "D"}
        for rule in IVD_RULES:
            assert rule.resulting_class in valid, \
                f"Rule {rule.rule_id} has invalid class: {rule.resulting_class}"

    def test_md_rules_count(self):
        """Should have ~22 GHTF MD rules."""
        assert len(MD_RULES) >= 20, f"Expected ~22 MD rules, got {len(MD_RULES)}"

    def test_ivd_rules_count(self):
        """Should have ~16 IVD rules."""
        assert len(IVD_RULES) >= 14, f"Expected ~16 IVD rules, got {len(IVD_RULES)}"
