# UAE EDE Medical Device Agent — Behavior, Attention and Refinements

> This document complements [`PLAN.md`](PLAN.md). Its structure mirrors the Saudi (SFDA) version, with UAE-specific differences highlighted.
> Last updated: 2026-09-24
>
> ⚠️ Design notes for a demonstration project. Regulatory details are not verified against official sources — see [DISCLAIMER.md](../DISCLAIMER.md).

---

## PART A — 12 UAE-Specific Refinements to the Plan

Several of the 15 Saudi refinements also apply to the UAE (hash chain audit, hallucination defense, version lock). The UAE-specific additions are below.

### A1. MOHAP → EDE Transition — Critical Date Semantics

EDE came into force on 2 January 2025. Applications filed BEFORE that date follow the MOHAP process; applications filed AFTER it follow the EDE process.

**Add to the agent's version snapshot:**
```
regulator_at_decision: "MOHAP" | "EDE"
regulator_transition_date: "2025-01-02"
```

**Rule:** If `decision_date >= 2025-01-02` → EDE rules apply. Earlier decisions rest on MOHAP and **do not require re-assessment** (backward compatibility).

### A2. Dual Classification System — MD vs IVD

The UAE has two parallel classification systems:
- **MD (Medical Devices):** Class I, II, III, IV
- **IVD (In Vitro Diagnostics):** Class A, B, C, D

Saudi Arabia has a single A/B/C/D system. In the UAE the agent must first answer "Is this device an MD or an IVD?". If it is an IVD, it must use the A/B/C/D letters.

**Classifier prompt update:**
```
[PRE-QUESTION] Is this device an MD or an IVD? (based on intended use + technology)
[THEN] Apply the correct classification system:
  - MD: Class I, II, III, IV (GHTF)
  - IVD: Class A, B, C, D
```

### A3. Multi-Emirate Check — Federal + 3 Emirate Authorities

EDE is the federal authority, but three emirate-level authorities may add requirements:

| Emirate | Authority | Additional requirement |
|---|---|---|
| Dubai | DHA | Additional registration for digital health platforms |
| Abu Dhabi | DOH | **Responsible AI Standard (October 2025)** — for AI devices |
| Dubai Healthcare City | DHCR | Free zone — own regulatory authority |

**The agent's multi-emirate mode:**
```python
class Emirate(str, Enum):
    FEDERAL = "EDE"    # default — valid across the UAE
    DUBAI = "DHA"      # additional, for sales in Dubai
    ABU_DHABI = "DOH"  # additional, for sales in Abu Dhabi (Responsible AI)
    DHCC = "DHCR"      # Dubai Healthcare City free zone
```

In the CHECKLIST state, the state machine must add an **additional item list** for each target emirate.

### A4. Anti-Monopoly Mechanism Check (February 2026)

From February 2026, **multiple agents** are required for every medical product. The sole-distributorship model has ended.

**Add to the checklist:**
- Have at least 2 LARs/MAHs been appointed?
- Are the LARs' EDE licenses valid?
- Is each LAR's geographic scope (which emirate) specified?

**Agent attention point:** If `decision_date >= 2026-02-01`, the anti-monopoly check is mandatory; before that date it is optional.

### A5. Arabic Label Prominence Check (stricter than Saudi Arabia)

Saudi Arabia requires Arabic + English but has no prominence rule. In the UAE:
- Arabic text must be at least as prominent as English text
- Minimum text height of 1.6 mm
- The label may be applied as a sticker

**The agent's visual check:**
```python
def verify_arabic_label_prominence(label_image_path):
    # OCR both languages
    ar_text = ocr_arabic(label_image_path)
    en_text = ocr_english(label_image_path)

    # Prominence check (font size approximation)
    ar_size = estimate_text_height(ar_text)
    en_size = estimate_text_height(en_text)

    if ar_size < en_size:
        return Finding(severity='critical',
                       msg=f'Arabic text ({ar_size}mm) smaller than English ({en_size}mm)')
    if ar_size < 1.6:
        return Finding(severity='critical',
                       msg=f'Arabic text height {ar_size}mm < 1.6mm minimum')
```

### A6. Data Localization Check (Federal Law No. 2 of 2019)

Health data must be stored in the UAE. Medical records must be retained for at least 25 years.

**Add to the checklist (connected devices):**
- Has a data flow diagram been provided?
- Is the data stored in the UAE? (e.g. a Bahrain cloud region is OUT, a UAE region is IN)
- Is a 25-year retention policy defined?
- Is there a patient consent mechanism?

**This differs from Saudi NDMO:** the UAE has a **specific** 25-year retention + local storage requirement for health data.

### A7. PDPL + Federal Law 2/2019 + SaMD Triple Compliance

Connected AI devices need three layers of compliance:

| Layer | Law | Requirement |
|---|---|---|
| Data protection | Federal Decree-Law No. 45 of 2021 (PDPL) | Consent for sensitive data processing |
| Health data retention | Federal Law No. 2 of 2019 | Local storage + 25-year retention |
| SaMD registration | Federal Decree-Law No. 38 of 2024 | EDE portal registration |

**The agent's triple check:** for connected AI devices, the checklist must include a requirement item for each of the three laws.

### A8. SaMD Classification Independent of MD Classification

A device can contain both an MD and SaMD (for example an MRI system + AI image analysis). Each requires a **separate classification**.

**The agent's dual classification mode:**
```python
@dataclass
class DualClassification:
    md_class: str  # "I" | "II" | "III" | "IV"
    samd_class: str | None  # "I" | "II" | "III" | "IV" or None if no SaMD
    md_rule_id: str
    samd_rule_id: str | None
```

### A9. 45 Business Day SLA Tracking (fixed, unlike Saudi Arabia)

The UAE registration timeline is a **fixed 45 business days**; in Saudi Arabia it is variable.

**The agent's SLA monitor:**
- 30 business days after submission → reminder: "Awaiting EDE response, 15 days remaining"
- At 45 business days → warning: "SLA exceeded — ask EDE for a status update"
- At 60 business days → automatic escalation: "Regulator SLA breach — recommend legal review"

### A10. Fixed Fee Structure (AED 5,000 + 100)

UAE fees are fixed:
- Application: AED 100
- Registration: AED 5,000
- Renewal: AED 250

**Add to the checklist:**
- Has AED 5,100 been paid? (receipt)
- Has the AED 100 application fee been paid?
- Renewal after 5 years → AED 250 reminder

### A11. UAE PASS Authentication Requirement

The EDE portal is accessed with UAE PASS, so **the MAH must have a UAE PASS account** as part of the application process.

**Add to the agent's preparation checklist:**
- Is the MAH registered with UAE PASS?
- Is the UAE PASS account active? (test login)
- Has the applicant's passport copy been attached?

### A12. PSUR + Adverse Event Timeline Differences (shorter than Saudi Arabia)

| Event | Saudi Arabia | UAE | Agent alert |
|---|---|---|---|
| Adverse event (death/serious injury) | 10 days | **5 days** | Reminder at T+3 days, alarm at T+5 days |
| FSCA | 5 days | (reported to EDE, different format from SFDA) | Reminder at T+2 days |
| PSUR (high risk) | Annual | **Every two years** | Reminder for the first PSUR at month 24 |

**The agent's jurisdiction-specific timeline matrix:**
```python
TIMELINES = {
    "SFDA": {"adverse_event": 10, "fsca": 5, "psur_high_risk": 12},
    "EDE":  {"adverse_event": 5,  "fsca": "format_diff", "psur_high_risk": 24},
}
```

---

## PART B — UAE Agent Behavior and Identity

The 10 Saudi behavior rules adapted for the UAE — most are unchanged; the UAE-specific differences are:

### B1. UAE-Specific Behavior Rules

| # | Rule | UAE-specific rationale |
|---|---|---|
| 1 | **Dual classification** — give separate classes for MD and SaMD | The IVD and MD systems are separate in the UAE |
| 2 | **Multi-emirate mode** — show the additional requirements of target emirates | EDE is federal, but DHA/DOH/DHCR add requirements |
| 3 | **MOHAP → EDE date awareness** — state which regulator's rules apply based on the decision date | Before 2 January 2025 MOHAP, after it EDE |
| 4 | **Arabic ≥ English prominence** — check font size | Explicit rule in the UAE (none in Saudi Arabia) |
| 5 | **Data localization** — UAE storage + 25-year retention | Specific to Federal Law 2/2019 |
| 6 | **Anti-monopoly check** — more than one LAR after February 2026 | New mechanism, none in Saudi Arabia |
| 7 | **45 business day SLA** — fixed timeline tracking | Fixed in the UAE (variable in Saudi Arabia) |
| 8 | **Three overlapping laws** — PDPL + Law 2/2019 + Decree 38/2024 | For connected AI devices |
| 9 | **UAE-specific disclaimer** — "This is not official EDE advice" | Reference to UAE legislation |
| 10 | **Emirate guidance** — state emirate requirements based on the target sales region | Dubai / Abu Dhabi / DHCC differences |

### B2. Communication Template — UAE version

```
[EDE Classification Result]
Device: Canon VITRAE MRI System (1.5T)   (fictional sample submission)
Intended use: Diagnostic imaging via magnetic resonance
MD class: **III** (per EDE Classification Guidelines, Rule 13 — diagnostic imaging)
SaMD class: **III** (per Federal Decree-Law No. 38/2024 — AI image analysis)

Cited MD clause: EDE-CL-R13.2
Cited SaMD clause: Federal Decree-Law 38/2024 §4.3

Justification: "Active diagnostic devices using non-ionizing radiation for diagnosis
fall under Class III. AI image analysis software embedded in MD falls under SaMD
Class III per Federal Decree-Law No. 38/2024."

Target emirate: Dubai + Abu Dhabi
  → Federal EDE requirements: ✓
  → DHA additional requirements: pending (digital health platform)
  → DOH Responsible AI Standard: pending (Oct 2025)

Confirm class? [Yes / No (re-classify) / Manual review]
```

### B3. UAE-Specific Silent Failure Modes

| Bad behavior | Why it is bad in the UAE | Correct behavior |
|---|---|---|
| Using the Saudi classification (A/B/C/D) | The UAE uses I/II/III/IV — wrong class = submission rejected | Use the correct system; separate MD from IVD |
| Using legacy MOHAP documents as a rule source | Legacy rules are invalid after the EDE transition | If `decision_date >= 2025-01-02`, EDE only |
| Accepting a single LAR (after February 2026) | Anti-monopoly violation — submission rejected | Require at least 2 LARs |
| Allowing Arabic < English prominence | Violates a UAE legal requirement | Arabic ≥ English, min 1.6 mm |
| Allowing health data storage in a non-UAE cloud region | Violates Federal Law 2/2019 data localization | Storage in the UAE (UAE cloud region or on-premises) |
| Checking only federal EDE requirements | DHA/DOH/DHCR additions are missed | Generate additional checklists per target emirate |

---

## PART C — UAE Attention Priority List

UAE-specific additions and differences to the 30-item Saudi list:

### C1. UAE-Specific P0 (Critical) — differs from Saudi Arabia

| # | Item | UAE detail | Saudi equivalent |
|---|---|---|---|
| 1 | **MD/IVD distinction** | Determine the device type first, then the correct classification system | Single A/B/C/D |
| 2 | **GHTF classification** | Class I/II/III/IV (MD), A/B/C/D (IVD) | SFDA 22 rules |
| 3 | **LAR/MAH license** | Registered and licensed with EDE | AR (Saudi-resident) |
| 4 | **Anti-monopoly** (February 2026+) | Multiple agents required | None |
| 5 | **Arabic ≥ English prominence** | Min 1.6 mm font | Arabic + English (no prominence rule) |
| 6 | **Data localization** | UAE storage + 25-year retention | NDMO (cross-border) |
| 7 | **Three overlapping laws** (connected AI) | PDPL + Law 2/2019 + Decree 38/2024 | NDMO + MDS-G27 |
| 8 | **Separate SaMD classification** | Class I/II/III/IV SaMD | MDS-G010 |
| 9 | **Cybersecurity** | Mandatory for EDE (SBOM + threat model + PMCP) | MDS-G27 |
| 10 | **UAE PASS** | MAH UAE PASS account required | SFDA portal |

### C2. UAE-Specific P1 (High) — differs from Saudi Arabia

| # | Item | UAE | Saudi Arabia |
|---|---|---|---|
| 11 | **Multi-emirate additions** | DHA + DOH (Responsible AI) + DHCR | None (single federal) |
| 12 | **Responsible AI Standard** (DOH, October 2025) | Additional Abu Dhabi requirement for AI devices | MDS-G010 |
| 13 | **MDEL** (Medical Device Establishment License) | UAE representative/importer | AR license |
| 14 | **Free sale certificate** (attested by the UAE embassy) | From the country of origin | SFDA's own process |
| 15 | **45 business day SLA** | Fixed | Variable |
| 16 | **AED 5,000 + 100 fee** | Fixed structure | Variable |
| 17 | **MAH registration** | On the EDE portal | AR appointment |
| 18 | **Passport copies** | For the applicant | None |

### C3. UAE-Specific P2 (Medium) — differs from Saudi Arabia

| # | Item | UAE | Saudi Arabia |
|---|---|---|---|
| 19 | **PSUR frequency** | **Every two years** for high risk | Annual for C/D |
| 20 | **Adverse event timeline** | **5 days** (death/serious injury) | 10 days |
| 21 | **Federal Decree-Law 27/2026** | Good Pharmacovigilance Practice (July 2026) | SFDA's own process |
| 22 | **Federal Law 2/2019** | 25-year health data retention | NDMO (no period specified) |
| 23 | **DOH Responsible AI Standard** (October 2025) | For Abu Dhabi AI devices | MDS-G27 |
| 24 | **DHCR free zone** | Dubai Healthcare City has a separate regulator | None |
| 25 | **National AI Strategy 2031** | EDE's AI registration pathways | Saudi Vision 2030 |

### C4. State × Priority Level Matrix

| State | UAE attention levels |
|---|---|
| INGEST | P3 + P1 (#15 font size, #16 UAE PASS verification) |
| CLASSIFY | P0 (#1 MD/IVD distinction, #2 GHTF classification, #8 SaMD) |
| CONFIRM_CLASS | P0 (#1, #2) + dual class display |
| CHECKLIST | P0 (1-10) + P1 (11-18) + multi-emirate additions |
| COLLECT | P1 (#11 multi-emirate, #13 MDEL, #14 free sale certificate) |
| VALIDATE | P0 (4-10) + P1 (11-18) + P2 (19-25) |
| REPORT | All levels + per-emirate breakdown |
| Post-market | P2 (#19 PSUR, #20 adverse event, #21 pharmacovigilance) |

---

## PART D — Multi-Jurisdiction Core for the UAE

The A15 refinement (multi-jurisdiction flag) becomes even more important in the UAE version:

### D1. Shared Core (common to Saudi Arabia, the UAE and Turkey)

| Component | Mechanism |
|---|---|
| Deterministic state machine | Same YAML structure, jurisdiction-specific collections |
| Fixed vector schema | BGE-M3, 1024 dim, L2 normalized |
| Hybrid retrieval | BM25 + vector + Cohere Rerank |
| Hallucination defense | 3 layers (preamble + tool + post-process) |
| Hash chain audit | Excel + SHA-256 chain |
| Context packet | Same schema, jurisdiction-specific content |
| Large document strategy | Hierarchical summarization |

### D2. Jurisdiction-Specific Modules

| Module | Saudi Arabia | UAE | Turkey (planned) |
|---|---|---|---|
| Regulator | SFDA | EDE | TITCK |
| Primary law | MDS-G5, MDS-G008 | Federal Decree-Law No. 38/2024 | Ministry of Health regulations |
| Classification | A/B/C/D (22 rules) | I/II/III/IV (GHTF) + A/B/C/D (IVD) | A/B/C/D (EU-aligned) |
| Local representative | AR | LAR/MAH (multiple after Feb 2026) | Authorized Representative |
| Main portal | SFDA MDMA | EDE Portal (UAE PASS) | TITCK UTS |
| Language | Arabic + English | Arabic ≥ English (prominence) | Turkish (mandatory) |
| Data localization | NDMO | Law 2/2019 (25 years) | KVKK |
| PSUR frequency | Annual (C/D) | Every two years (high risk) | Annual (Class IIb/III) |
| Adverse event | 10 days | 5 days | 15 days |
| Anti-monopoly | — | Yes (Feb 2026) | — |
| Separate SaMD classification | MDS-G010 | Decree 38/2024 | TITCK SaMD guidance |

### D3. Config-Based Jurisdiction Switching (v1.0 design)

```python
# Multi-jurisdiction config switch
JURISDICTION_CONFIGS = {
    "SFDA": {
        "regulator": "SFDA",
        "classification_system": "MD_A_B_C_D",
        "primary_law": "MDS-G5",
        "classification_doc": "MDS-G008",
        "ai_guidance": ["MDS-G010", "MDS-G27"],
        "local_rep_type": "AR",
        "portal": "SFDA MDMA",
        "language_rule": "arabic_english_required",
        "psur_frequency_months": 12,
        "adverse_event_days": 10,
        "anti_monopoly_required": False,
    },
    "EDE": {
        "regulator": "EDE",
        "classification_system": "MD_I_II_III_IV_PLUS_IVD_A_B_C_D",
        "primary_law": "Federal Decree-Law No. 38/2024",
        "classification_doc": "EDE Classification Guidelines",
        "ai_guidance": ["Decree 38/2024", "Responsible AI Standard (DOH)"],
        "local_rep_type": "LAR_MAH_MULTI",  # post-Feb 2026
        "portal": "EDE Portal (UAE PASS)",
        "language_rule": "arabic_greater_equal_english_1_6mm",
        "psur_frequency_months": 24,
        "adverse_event_days": 5,
        "anti_monopoly_required": True,
        "multi_emirate_mode": ["DHA", "DOH", "DHCR"],
    },
    # Planned: TITCK config (Turkey)
}

# The state machine uses the jurisdiction to pick the right config
class JurisdictionConfig:
    def __init__(self, jurisdiction: str):
        if jurisdiction not in JURISDICTION_CONFIGS:
            raise ValueError(f"Unknown jurisdiction: {jurisdiction}")
        self.config = JURISDICTION_CONFIGS[jurisdiction]

    @property
    def classification_system(self) -> str:
        return self.config["classification_system"]

    # ... other accessors
```

---

## PART E — Implementation Order

1. **EDE classification rules first.** Classification is the agent's most critical decision point; the other modules depend on how the EDE Classification Guidelines are modeled (the UAE counterpart of SFDA MDS-G008).
2. **Multi-emirate module second.** Emirate-level additions only make sense after classification, because DHA/DOH requirements depend on the device type.
3. **Jurisdiction config last.** The config file captures the classification rules and the multi-emirate module once both exist — concrete code first, then the config abstraction.
