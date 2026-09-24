"""
EDE Classification — GHTF-Aligned Medical Device Classification Engine
======================================================================

Python implementation of GHTF (Global Harmonization Task Force)
classification rules for the UAE Emirates Drug Establishment (EDE).

Two parallel systems:
  - MD (Medical Devices): Class I, II, III, IV (GHTF principles)
  - IVD (In Vitro Diagnostics): Class A, B, C, D

Source documents:
  - Federal Decree-Law No. 38 of 2024 (primary law)
  - EDE Classification Guidelines (2024 update)
  - GHTF/SG1/N77:2012 (general classification principles)

Important: the UAE uses I/II/III/IV instead of the Saudi SFDA A/B/C/D system.
This file is the UAE counterpart of the SFDA MDS-G008 rules.

The rules below are a simplified, synthetic model for demonstration and
testing purposes only — see DISCLAIMER.md.

Usage:
    from src.ede_classification import EDEClassifier

    classifier = EDEClassifier()
    result = classifier.classify(
        device_type="MD",
        intended_use="Diagnostic imaging via magnetic resonance",
        duration_of_use="short_term",
        invasiveness="non_invasive",
        active=True,
        uses_ionizing_radiation=False,
        targets_central_circulation=False,
        is_software=False,
        is_ivd=False,
    )
    # → {"class": "III", "rule_id": "EDE-MD-R13", "justification": "..."}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


# =========================================================================
# Constants & Enums
# =========================================================================


class DeviceType(str, Enum):
    """Device type — MD or IVD."""
    MD = "MD"       # Medical Device (Class I/II/III/IV)
    IVD = "IVD"     # In Vitro Diagnostic (Class A/B/C/D)
    SA_MD = "SaMD"  # Software as a Medical Device (separate classification)


class DurationOfUse(str, Enum):
    """Duration of contact with the body (GHTF definition)."""
    TRANSIENT = "transient"            # < 60 minutes
    SHORT_TERM = "short_term"          # 60 min - 30 days
    LONG_TERM = "long_term"            # > 30 days
    PERMANENT = "permanent"            # Implantable, indeterminate


class Invasiveness(str, Enum):
    """Degree of invasiveness."""
    NON_INVASIVE = "non_invasive"
    INVASIVE_BODY_ORIFICE = "invasive_body_orifice"  # Surgical invasiveness via orifice
    INVASIVE_SURGICAL = "invasive_surgical"           # Surgically invasive (cutting)
    IMPLANTABLE = "implantable"


class MDClass(str, Enum):
    """MD classes (GHTF)."""
    I = "I"
    II = "II"
    III = "III"
    IV = "IV"


class IVDClass(str, Enum):
    """IVD classes (GHTF)."""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


# =========================================================================
# MD Classification Rules (GHTF-aligned, 22 rules)
# =========================================================================
#
# The rules follow GHTF/SG1/N77:2012 principles, which the EDE
# Classification Guidelines adapt to UAE legislation.
#
# Rule precedence: the rule giving the higher risk class wins (conservative).
# E.g. if a device gets II from R5 and III from R13 → III.


@dataclass
class ClassificationRule:
    """A single classification rule."""
    rule_id: str          # e.g. "EDE-MD-R1"
    description: str      # What the rule says
    applies_to: dict     # Device characteristics that trigger the rule
    resulting_class: str  # Resulting class
    source_doc: str = "EDE Classification Guidelines"
    version: str = "2024"


# MD classification rules (22 rules)
MD_RULES: list[ClassificationRule] = [
    # --- Invasiveness-based rules (R1-R4) ---
    ClassificationRule(
        rule_id="EDE-MD-R1",
        description="Surgically invasive devices (typically short-term, non-implantable)",
        applies_to={"invasiveness": "invasive_surgical", "duration_of_use": ["transient", "short_term"], "implantable": False},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R2",
        description="Surgically invasive devices — long-term or implantable",
        applies_to={"invasiveness": "invasive_surgical", "duration_of_use": ["long_term", "permanent"], "implantable": True},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R3",
        description="Implantable devices — bone/tissue/blood contact",
        applies_to={"invasiveness": "implantable", "targets": ["bone", "tissue", "blood", "central_circulation", "central_nervous_system"]},
        resulting_class="II",  # Base — many implants escalate via other rules
    ),
    ClassificationRule(
        rule_id="EDE-MD-R4",
        description="Invasive via body orifice (non-surgical)",
        applies_to={"invasiveness": "invasive_body_orifice"},
        resulting_class="I",  # Base — short-term body orifice
    ),

    # --- Non-invasive rules (R5-R8) ---
    ClassificationRule(
        rule_id="EDE-MD-R5",
        description="Non-invasive, handling blood or body fluids",
        applies_to={"invasiveness": "non_invasive", "handles_body_fluids": True},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R6",
        description="Non-invasive, delivering fluids to wounds (wound dressing equipment)",
        applies_to={"invasiveness": "non_invasive", "delivers_to_wound": True},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R7",
        description="Non-invasive, simple surgical instruments (low risk)",
        applies_to={"invasiveness": "non_invasive", "is_simple_surgical_instrument": True},
        resulting_class="I",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R8",
        description="Non-invasive (default for other non-invasive devices)",
        applies_to={"invasiveness": "non_invasive"},
        resulting_class="I",
    ),

    # --- Active device rules (R9-R12) ---
    ClassificationRule(
        rule_id="EDE-MD-R9",
        description="Active therapeutic devices (transferring energy to the body)",
        applies_to={"active": True, "transfers_energy": True, "intended_use_contains": ["therapy", "treatment"]},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R10",
        description="Active diagnostic devices — low/moderate risk (e.g. ultrasound, ECG)",
        applies_to={"active": True, "is_diagnostic": True, "uses_ionizing_radiation": False},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R11",
        description="Active device — embedded software (not SaMD)",
        applies_to={"active": True, "is_embedded_software": True},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R12",
        description="Active device — monitoring vital functions (anesthesia, ICU monitors)",
        applies_to={"active": True, "monitors_vital_functions": True},
        resulting_class="III",
    ),

    # --- Special / high-risk rules (R13-R18) ---
    ClassificationRule(
        rule_id="EDE-MD-R13",
        description="Active diagnostic device — non-ionizing radiation (MRI, ultrasound)",
        applies_to={"active": True, "is_diagnostic": True, "uses_non_ionizing_radiation": True},
        resulting_class="III",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R14",
        description="Active diagnostic device — ionizing radiation (X-ray, CT, fluoroscopy)",
        applies_to={"active": True, "is_diagnostic": True, "uses_ionizing_radiation": True},
        resulting_class="III",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R15",
        description="Contraceptive devices (non-implantable)",
        applies_to={"intended_use_contains": ["contraception"], "implantable": False},
        resulting_class="III",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R16",
        description="Contraceptive devices (implantable) or prevention of sexually transmitted diseases",
        applies_to={"intended_use_contains": ["contraception", "std_prevention"], "implantable": True},
        resulting_class="IV",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R17",
        description="Disinfecting devices (cleaning/washing) — for invasive devices",
        applies_to={"intended_use_contains": ["disinfection", "sterilization"], "targets_invasive_devices": True},
        resulting_class="II",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R18",
        description="Non-active device — material change (wound closure, tissue regeneration)",
        applies_to={"intended_use_contains": ["tissue_healing", "wound_closure"], "active": False},
        resulting_class="III",
    ),

    # --- Devices containing drugs / biological substances (R19-R20) ---
    ClassificationRule(
        rule_id="EDE-MD-R19",
        description="Device containing a medicinal substance — animal/human derived (blood, plasma, derivatives)",
        applies_to={"contains_biological_substance": True, "intended_use_contains": ["drug_delivery", "blood_processing"]},
        resulting_class="IV",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R20",
        description="Device containing a medicinal substance — synthetic drug, drug-eluting (stent)",
        applies_to={"contains_drug": True, "is_drug_eluting": True},
        resulting_class="III",
    ),

    # --- Implants / surgical (R21-R22) ---
    ClassificationRule(
        rule_id="EDE-MD-R21",
        description="Implant — central nervous system, central circulation or vital function",
        applies_to={"implantable": True, "targets": ["central_nervous_system", "central_circulation"]},
        resulting_class="IV",
    ),
    ClassificationRule(
        rule_id="EDE-MD-R22",
        description="Implant — breast implant, eye implant or long-term invasive",
        applies_to={"implantable": True, "targets": ["breast", "eye", "long_term_invasive"]},
        resulting_class="III",
    ),
]


# =========================================================================
# IVD Classification Rules (GHTF A/B/C/D)
# =========================================================================

IVD_RULES: list[ClassificationRule] = [
    ClassificationRule(
        rule_id="EDE-IVD-R1",
        description="Specimen receptacles (sample containers)",
        applies_to={"ivd_type": "specimen_receptacle"},
        resulting_class="A",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R2",
        description="General labware — non-specific, low risk",
        applies_to={"ivd_type": "general_labware"},
        resulting_class="A",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R3",
        description="Self-testing IVDs (used by lay persons — pregnancy, glucose)",
        applies_to={"ivd_type": "self_testing"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R4",
        description="Complements (reagents, calibrators) — non-specialty",
        applies_to={"ivd_type": "general_complement"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R5",
        description="Self-testing — glucose meters (specifically)",
        applies_to={"ivd_type": "self_testing_glucose"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R6",
        description="Self-testing — pregnancy tests",
        applies_to={"ivd_type": "self_testing_pregnancy"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R7",
        description="Self-testing — fertility / ovulation",
        applies_to={"ivd_type": "self_testing_fertility"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R8",
        description="Genetic testing IVDs",
        applies_to={"ivd_type": "genetic_testing"},
        resulting_class="C",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R9",
        description="Blood banking — blood typing, cross-matching",
        applies_to={"ivd_type": "blood_banking"},
        resulting_class="C",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R10",
        description="Infectious disease — high public health risk (HIV, hepatitis)",
        applies_to={"ivd_type": "infectious_disease_high_risk"},
        resulting_class="D",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R11",
        description="Infectious disease — venereal disease (STD testing)",
        applies_to={"ivd_type": "std_testing"},
        resulting_class="D",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R12",
        description="Companion diagnostics (drug response, personalized medicine)",
        applies_to={"ivd_type": "companion_diagnostic"},
        resulting_class="C",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R13",
        description="Self-testing — cholesterol, drug of abuse",
        applies_to={"ivd_type": "self_testing_cholesterol_or_drug"},
        resulting_class="B",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R14",
        description="CD4+ monitoring (immune system assessment)",
        applies_to={"ivd_type": "cd4_monitoring"},
        resulting_class="C",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R15",
        description="Variant Creutzfeldt-Jakob disease (prion detection)",
        applies_to={"ivd_type": "prion_detection"},
        resulting_class="D",
    ),
    ClassificationRule(
        rule_id="EDE-IVD-R16",
        description="Blood screening for transfusion-transmissible infections",
        applies_to={"ivd_type": "blood_screening_transfusion"},
        resulting_class="D",
    ),
]


# =========================================================================
# Classifier
# =========================================================================


@dataclass
class ClassificationResult:
    """Classification result."""
    device_type: str            # "MD", "IVD", or both
    md_class: str | None        # Class I/II/III/IV
    md_rule_id: str | None
    ivd_class: str | None       # Class A/B/C/D
    ivd_rule_id: str | None
    justification: str
    is_uncertain: bool = False
    uncertainty_reason: str = ""


class EDEClassifier:
    """EDE classification engine.

    Deterministic rule-based classifier. No LLM is needed when the rules
    are clear; in uncertain cases the LLM is called (src/agents/classifier.py).

    Conservative by design (BEHAVIOR_AND_ATTENTION.md §B1):
    - When several rules match, the higher class wins
    - Borderline I/II → II, II/III → III, III/IV → IV
    """

    def __init__(self) -> None:
        self.md_rules = MD_RULES
        self.ivd_rules = IVD_RULES

    def classify(self, **device_chars: Any) -> ClassificationResult:
        """Derive the class from device characteristics.

        Args:
            device_type: "MD" | "IVD" | "both"
            intended_use: str (free text)
            duration_of_use: "transient" | "short_term" | "long_term" | "permanent"
            invasiveness: "non_invasive" | "invasive_body_orifice" | "invasive_surgical" | "implantable"
            active: bool
            is_diagnostic: bool
            uses_ionizing_radiation: bool
            uses_non_ionizing_radiation: bool
            transfers_energy: bool
            is_embedded_software: bool
            is_sa_md: bool
            monitors_vital_functions: bool
            implantable: bool
            targets: list[str]  # ["bone", "tissue", "blood", "central_circulation", ...]
            handles_body_fluids: bool
            delivers_to_wound: bool
            is_simple_surgical_instrument: bool
            contains_biological_substance: bool
            contains_drug: bool
            is_drug_eluting: bool
            ivd_type: str  # if IVD: "self_testing", "blood_banking", etc.

            (other ad-hoc characteristics are also evaluated by the rule matcher)

        Returns:
            ClassificationResult with md_class, ivd_class, justification, rule_ids
        """
        result = ClassificationResult(
            device_type=device_chars.get("device_type", "MD"),
            md_class=None,
            md_rule_id=None,
            ivd_class=None,
            ivd_rule_id=None,
            justification="",
        )

        # 1. Determine device type(s) to classify
        device_type = device_chars.get("device_type", "MD")

        # 2. Apply MD rules if applicable
        if device_type in ("MD", "both"):
            md_match = self._find_matching_rule(self.md_rules, device_chars)
            if md_match:
                result.md_class = md_match.resulting_class
                result.md_rule_id = md_match.rule_id
                result.justification = md_match.description

        # 3. Apply IVD rules if applicable
        if device_type in ("IVD", "both"):
            ivd_match = self._find_matching_rule(self.ivd_rules, device_chars)
            if ivd_match:
                result.ivd_class = ivd_match.resulting_class
                result.ivd_rule_id = ivd_match.rule_id
                if result.justification:
                    result.justification += f" | IVD: {ivd_match.description}"
                else:
                    result.justification = ivd_match.description

        # 4. Check for uncertainty
        if not result.md_class and not result.ivd_class:
            result.is_uncertain = True
            result.uncertainty_reason = (
                "No matching classification rule found. "
                "Manual review required — likely borderline case."
            )

        return result

    def _find_matching_rule(
        self, rules: list[ClassificationRule], device_chars: dict
    ) -> ClassificationRule | None:
        """Find the rule that gives the highest risk class for a device.

        Conservative by design: if several rules match, the one giving the
        highest risk class wins (I<II<III<IV, A<B<C<D).
        """
        matches = []
        for rule in rules:
            if self._rule_matches(rule, device_chars):
                matches.append(rule)

        if not matches:
            return None

        # Pick the highest risk class (conservative)
        return max(matches, key=lambda r: self._class_severity(r.resulting_class))

    def _rule_matches(self, rule: ClassificationRule, device_chars: dict) -> bool:
        """Does a rule match the device characteristics?

        ALL applies_to entries must be satisfied for a rule to match:
        - Missing field → rule does NOT match (the device lacks that characteristic)
        - Exception: 'intended_use_contains' → substring check against intended_use text
        """
        for key, expected in rule.applies_to.items():
            actual = device_chars.get(key)

            # Special case: intended_use_contains → check substrings in intended_use
            if key == "intended_use_contains":
                intended_use = (device_chars.get("intended_use") or "").lower()
                if isinstance(expected, list):
                    # ANY substring in list should be present (OR logic)
                    if not any(s.lower() in intended_use for s in expected):
                        return False
                else:
                    if expected.lower() not in intended_use:
                        return False
                continue

            # Missing field → rule does NOT match
            if actual is None:
                return False

            # Special case: both expected and actual are lists → check overlap
            # (e.g. targets: expected=["central_circulation", ...], actual=["central_circulation"])
            if isinstance(expected, list) and isinstance(actual, list):
                if not actual:  # empty list → device has no targets
                    return False
                # Match if ANY of device's actual items is in expected allowed list
                if not any(item in expected for item in actual):
                    return False
                continue

            # Standard checks
            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif isinstance(expected, bool):
                if actual != expected:
                    return False
            elif isinstance(expected, str):
                if actual != expected:
                    return False
        return True

    @staticmethod
    def _class_severity(class_str: str) -> int:
        """Class risk level — higher = riskier.

        A<B<C<D for IVD, I<II<III<IV for MD.
        Normalized for numeric comparison.
        """
        severity_map = {
            "I": 1, "II": 2, "III": 3, "IV": 4,
            "A": 1, "B": 2, "C": 3, "D": 4,
        }
        return severity_map.get(class_str, 0)


# =========================================================================
# Classifier Prompt Template (for ambiguous cases)
# =========================================================================

CLASSIFIER_PROMPT_TEMPLATE = """
[ROLE] You are the EDE Classifier Agent. You determine the risk class of a
medical device according to the UAE Emirates Drug Establishment (EDE)
Classification Guidelines.

[REGULATORY RULES] {retrieved_rules}

[DEVICE INFORMATION]
- Device type: {device_type} (MD or IVD or both)
- Intended use: {device_intended_use}
- Duration of use: {duration_of_use}
- Invasiveness: {invasiveness}
- Active: {active}
- Diagnostic: {is_diagnostic}
- Uses ionizing radiation: {uses_ionizing_radiation}
- Uses non-ionizing radiation: {uses_non_ionizing_radiation}
- Implantable: {implantable}
- Targets: {targets}
- Contains biological substance: {contains_biological_substance}
- Contains drug: {contains_drug}
- IVD type (if applicable): {ivd_type}

[PRE-QUESTION] Is this device an MD or an IVD? (It can be both — e.g. MRI + embedded AI = MD + SaMD)
[THEN] Apply the correct classification system:
  - MD: Class I, II, III, IV (GHTF principles)
  - IVD: Class A, B, C, D

[CONSTRAINTS]
- Only cite rule_ids present in REGULATORY RULES
- In borderline cases, choose the HIGHER class (I/II → II, II/III → III, III/IV → IV)
- If there is any uncertainty, set is_uncertain=true and route to MANUAL_REVIEW
- If dual classification (MD + SaMD) is required, give both

[OUTPUT] JSON format:
{{
  "device_type": "MD" | "IVD" | "both",
  "md_class": "I" | "II" | "III" | "IV" | null,
  "md_rule_id": "<EDE-MD-R##>" | null,
  "ivd_class": "A" | "B" | "C" | "D" | null,
  "ivd_rule_id": "<EDE-IVD-R##>" | null,
  "justification": "<2-3 sentences explaining how the rule applies>",
  "is_uncertain": <true|false>,
  "uncertainty_reason": "<if any>"
}}

Example output (Canon VITRAE MRI System — fictional sample):
{{
  "device_type": "MD",
  "md_class": "III",
  "md_rule_id": "EDE-MD-R13",
  "ivd_class": null,
  "ivd_rule_id": null,
  "justification": "Active diagnostic device using non-ionizing radiation (MR). Class III per EDE-MD-R13. The device also contains embedded AI, which may require a separate SaMD classification (this output covers the MD class).",
  "is_uncertain": false
}}
"""


# =========================================================================
# Sample EDE Regulatory Corpus Clauses (synthetic but realistic)
# =========================================================================
# Note: these clauses are synthetic, for demonstration only. They are not
# official regulatory text — use official documents from www.ede.gov.ae.

SAMPLE_EDE_CORPUS_CLAUSES = """
[FEDERAL-DECREE-LAW-38-2024-2.1]
UAE Federal Decree-Law No. 38 of 2024, Article 2.1
Application for medical device registration shall include: (a) device
description and intended purpose; (b) risk classification per EDE
Classification Guidelines; (c) Declaration of Conformity (DoC); (d)
technical file; (e) IFU in Arabic and English (Arabic prominence
required); (f) labelling in Arabic and English; (g) clinical
evaluation report for Class III/IV; (h) risk management file per
ISO 14971:2019.

---
[FEDERAL-DECREE-LAW-38-2024-2.2]
UAE Federal Decree-Law No. 38 of 2024, Article 2.2
Applicant must appoint a UAE-based Local Authorized Representative (LAR)
or Marketing Authorization Holder (MAH) holding a valid EDE Medical
Device Establishment License (MDEL). The LAR/MAH's appointment letter
must be legalized by UAE Ministry of Foreign Affairs (MoFA).

---
[FEDERAL-DECREE-LAW-38-2024-2.3]
UAE Federal Decree-Law No. 38 of 2024, Article 2.3
All patient-facing documentation (IFU, labelling, patient leaflets) must
be provided in both Arabic and English. The Arabic version must be at
least as prominent as the English version, with minimum text height of
1.6mm. The Arabic version must be reviewed by a certified Arabic medical
translator and stamped by the LAR/MAH.

---
[FEDERAL-DECREE-LAW-38-2024-2.4]
UAE Federal Decree-Law No. 38 of 2024, Article 2.4
Cybersecurity documentation is required for connected medical devices:
(a) cybersecurity risk assessment per IEC 81001-5-1; (b) software bill
of materials (SBOM); (c) threat model; (d) post-market cybersecurity
plan (PMCP). AI-enabled devices are subject to enhanced review per the
DOH Responsible AI Standard (October 2025).

---
[FEDERAL-DECREE-LAW-38-2024-2.5]
UAE Federal Decree-Law No. 38 of 2024, Article 2.5
Post-Market Surveillance System (PMSS) documentation must be submitted.
Must include: vigilance reporting procedure (adverse events within 5
days for death/serious injury), trend reporting (quarterly for Class
III/IV), periodic safety update reports (PSUR) — every 2 years for
high-risk devices.

---
[FEDERAL-DECREE-LAW-38-2024-2.6]
UAE Federal Decree-Law No. 38 of 2024, Article 2.6
Data protection compliance statement required for devices processing
personal health data. Must reference UAE Federal Decree-Law No. 45 of
2021 (PDPL) and Federal Law No. 2 of 2019 (ICT in Health): (a) data
flow diagram; (b) lawful basis for processing; (c) data retention
policy (minimum 25 years for medical records); (d) data localization
requirement — health data must be stored within UAE.

---
[EDE-CL-GHTF-R1]
EDE Classification Guidelines (2024 update), GHTF Rule 1
Surgically invasive medical devices intended for transient use (less
than 60 minutes) are classified as Class II. Examples: surgical
forceps, retractors, infusion sets.

---
[EDE-CL-GHTF-R13]
EDE Classification Guidelines (2024 update), GHTF Rule 13
Active diagnostic devices that emit non-ionizing radiation (such as
magnetic resonance, ultrasound) are classified as Class III. This
includes MRI systems, ultrasound scanners, and diagnostic lasers.

---
[EDE-CL-GHTF-R14]
EDE Classification Guidelines (2024 update), GHTF Rule 14
Active diagnostic devices that emit ionizing radiation (X-ray, CT,
fluoroscopy) are classified as Class III. Required radiation dose
documentation and ALARA (As Low As Reasonably Achievable) justification.

---
[EDE-CL-GHTF-R21]
EDE Classification Guidelines (2024 update), GHTF Rule 21
Implantable devices that come into contact with the central nervous
system, central circulation, or whose failure could lead to death or
serious deterioration of health, are classified as Class IV.

---
[EDE-CL-IVD-D1]
EDE Classification Guidelines — IVD classification
IVD devices for detecting transmissible agents in blood, blood
components, or tissues (e.g. HIV, HBV, HCV) are classified as Class D
due to high public health risk.

---
[EDE-CL-IVD-C1]
EDE Classification Guidelines — IVD classification
IVD devices for blood group typing, cross-matching, or blood banking
quality control are classified as Class C due to moderate-to-high
individual and public health risk.

---
[EDE-CL-IVD-B1]
EDE Classification Guidelines — IVD classification
Self-testing IVDs for general health screening (pregnancy, ovulation,
glucose monitoring) are classified as Class B due to moderate individual
risk but low public health risk.

---
[DOH-RAI-2025-1]
Abu Dhabi Department of Health — Responsible AI Standard (October 2025)
AI-enabled medical devices marketed in Abu Dhabi must additionally
comply with: (a) algorithm transparency documentation; (b) bias
assessment report; (c) ongoing performance monitoring plan; (d)
clinician feedback mechanism; (e) patient consent for AI-assisted
decisions. Failure to comply → registration rejection in Abu Dhabi
emirate (still acceptable federally via EDE).

---
[FEDERAL-LAW-2-2019-3.1]
UAE Federal Law No. 2 of 2019 — ICT in Health, Article 3.1
Health information generated or processed by medical devices must be
stored within UAE territory. Cross-border data transfer requires
explicit patient consent and EDE approval. Medical records must be
retained for minimum 25 years.
"""


# =========================================================================
# CLI (quick test)
# =========================================================================

def _demo_classify_canon_vitrae() -> ClassificationResult:
    """Demo: Canon VITRAE MRI System → EDE classification."""
    classifier = EDEClassifier()
    return classifier.classify(
        device_type="MD",
        intended_use="Diagnostic imaging via magnetic resonance",
        duration_of_use="transient",
        invasiveness="non_invasive",
        active=True,
        is_diagnostic=True,
        uses_ionizing_radiation=False,
        uses_non_ionizing_radiation=True,
        transfers_energy=False,
        is_embedded_software=False,
        is_sa_md=False,
        monitors_vital_functions=False,
        implantable=False,
        targets=[],
        handles_body_fluids=False,
        delivers_to_wound=False,
        is_simple_surgical_instrument=False,
        contains_biological_substance=False,
        contains_drug=False,
        is_drug_eluting=False,
    )


if __name__ == "__main__":
    # Demo run
    result = _demo_classify_canon_vitrae()
    print("=== Canon VITRAE MRI System — EDE Classification Demo ===\n")
    print(f"Device type: {result.device_type}")
    print(f"MD class: {result.md_class}")
    print(f"MD rule: {result.md_rule_id}")
    print(f"IVD class: {result.ivd_class}")
    print(f"IVD rule: {result.ivd_rule_id}")
    print(f"Justification: {result.justification}")
    print(f"Uncertain: {result.is_uncertain}")
    if result.uncertainty_reason:
        print(f"Uncertainty reason: {result.uncertainty_reason}")
    print()
    print("Sample EDE corpus clauses (first 500 chars):")
    print("-" * 60)
    print(SAMPLE_EDE_CORPUS_CLAUSES[:500] + "...")
