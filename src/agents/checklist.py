"""
Agent: Checklist (UAE EDE version)
==================================

Per-class document checklist for UAE EDE submissions.

Two parallel checklists:
  - MD (Class I, II, III, IV) — different document sets per class
  - IVD (Class A, B, C, D) — different document sets

Plus UAE-specific additions vs SFDA:
  - Multi-emirate extensions (DHA, DOH Responsible AI, DHCR)
  - Anti-monopoly requirement (Feb 2026+) — multiple LAR/MAH
  - Arabic prominence check (min 1.6mm font)
  - Data localization statement (Law 2/2019, 25-year retention)
  - 45 business day SLA tracking
  - Fixed fee structure (AED 5,000 + 100)

See docs/PLAN.md §3 (Required Documents) for the full document list.
"""
from __future__ import annotations
from typing import Any


# MD class-based checklist (UAE EDE)
# Cumulative: Class IV includes all of Class III, which includes Class II, etc.

MD_CLASS_CHECKLISTS: dict[str, list[dict]] = {
    "I": [
        {"name": "Application Form (signed, stamped)", "source": "EDE", "mandatory": True},
        {"name": "Manufacturer Factory Registration Certificate", "source": "EDE", "mandatory": True},
        {"name": "Product Description (intended use, models, dimensions)", "source": "EDE", "mandatory": True},
        {"name": "Free Sale Certificate (UAE Embassy legalized)", "source": "Origin country", "mandatory": True},
        {"name": "Declaration of Conformity (EC-DoC)", "source": "EDE", "mandatory": True},
        {"name": "IFU (Arabic + English, Arabic prominence)", "source": "EDE", "mandatory": True},
        {"name": "Labelling (Arabic + English)", "source": "EDE", "mandatory": True},
        {"name": "ISO 13485:2016 Certificate", "source": "ISO", "mandatory": True},
        {"name": "LAR/MAH Appointment Letter (MoFA legalized)", "source": "EDE", "mandatory": True},
    ],
    "II": [
        # All of Class I, plus:
        {"name": "Technical File (full)", "source": "EDE", "mandatory": True},
        {"name": "Risk Management File (ISO 14971:2019)", "source": "ISO", "mandatory": True},
        {"name": "Clinical Evaluation Report (equivalence-based, MEDDEV 2.7/1 rev.4)", "source": "EDE", "mandatory": True},
        {"name": "EDE Classification Letter", "source": "EDE", "mandatory": True},
        {"name": "MDEL (Medical Device Establishment License) of LAR/MAH", "source": "EDE", "mandatory": True},
    ],
    "III": [
        # All of Class II, plus:
        {"name": "Clinical Evaluation Report (with clinical data + literature review)", "source": "EDE", "mandatory": True},
        {"name": "Cybersecurity Documentation (IEC 81001-5-1 + SBOM + Threat Model) [if connected]", "source": "IEC", "mandatory": True},
        {"name": "Post-Market Surveillance Plan (PMSP)", "source": "EDE", "mandatory": True},
        {"name": "PSUR Plan (every 2 years)", "source": "EDE", "mandatory": True},
        {"name": "UDI DI + PI labeling verified", "source": "GUDID", "mandatory": True},
    ],
    "IV": [
        # All of Class III, plus:
        {"name": "Clinical Evaluation Report (with clinical investigation + PMCF)", "source": "EDE", "mandatory": True},
        {"name": "Penetration Test Report [if connected]", "source": "IEC 62443", "mandatory": True},
        {"name": "Full Cybersecurity Documentation (with PMCP)", "source": "IEC 81001-5-1", "mandatory": True},
        {"name": "Human Factors Engineering File (IEC 62366-1)", "source": "IEC", "mandatory": True},
    ],
}

# IVD class-based checklist (separate from MD)
IVD_CLASS_CHECKLISTS: dict[str, list[dict]] = {
    "A": [
        {"name": "Application Form (signed, stamped)", "source": "EDE", "mandatory": True},
        {"name": "Manufacturer Factory Registration Certificate", "source": "EDE", "mandatory": True},
        {"name": "Product Description", "source": "EDE", "mandatory": True},
        {"name": "Free Sale Certificate (UAE Embassy legalized)", "source": "Origin country", "mandatory": True},
        {"name": "Declaration of Conformity", "source": "EDE", "mandatory": True},
        {"name": "IFU + Labelling (Arabic + English)", "source": "EDE", "mandatory": True},
        {"name": "ISO 13485:2016 Certificate", "source": "ISO", "mandatory": True},
        {"name": "LAR/MAH Appointment (MoFA legalized)", "source": "EDE", "mandatory": True},
    ],
    "B": [
        # All of A, plus:
        {"name": "Technical File", "source": "EDE", "mandatory": True},
        {"name": "Performance Evaluation Report", "source": "EDE", "mandatory": True},
        {"name": "Risk Management File (ISO 14971:2019)", "source": "ISO", "mandatory": True},
    ],
    "C": [
        # All of B, plus:
        {"name": "Clinical Performance Data", "source": "EDE", "mandatory": True},
        {"name": "Post-Market Surveillance Plan", "source": "EDE", "mandatory": True},
        {"name": "UDI DI + PI labeling verified", "source": "GUDID", "mandatory": True},
    ],
    "D": [
        # All of C, plus:
        {"name": "Full Clinical Evaluation (incl. clinical utility)", "source": "EDE", "mandatory": True},
        {"name": "Reference Measurement Procedure", "source": "EDE", "mandatory": True},
    ],
}

# UAE-specific additional requirements (across all classes)
UAE_SPECIFIC_ADDITIONS = [
    {
        "name": "Multi-LAR/MAH assignment (Anti-monopoly, Feb 2026+)",
        "source": "EDE",
        "mandatory": True,
        "applies_after": "2026-02-01",
        "check": "At least 2 LAR/MAH appointed with valid EDE licenses",
    },
    {
        "name": "Arabic text prominence verification (min 1.6mm)",
        "source": "EDE",
        "mandatory": True,
        "applies_to": ["ifu", "labelling"],
        "check": "Arabic text >= English prominence, min 1.6mm font height",
    },
    {
        "name": "Data Localization Statement (Federal Law 2/2019)",
        "source": "Federal Law 2/2019",
        "mandatory": True,
        "applies_to": ["connected_devices"],
        "check": "Health data stored in UAE; 25-year retention policy",
    },
    {
        "name": "PDPL Compliance Statement (Federal Decree-Law 45/2021)",
        "source": "PDPL",
        "mandatory": True,
        "applies_to": ["devices_processing_health_data"],
        "check": "Lawful basis for processing; patient consent mechanism",
    },
    {
        "name": "UAE PASS Authentication for MAH",
        "source": "EDE",
        "mandatory": True,
        "check": "MAH has active UAE PASS account",
    },
]

# Multi-emirate additional requirements (above federal EDE)
EMIRATE_ADDITIONS = {
    "dubai": [
        {
            "name": "DHA Digital Health Platform Registration",
            "source": "DHA",
            "mandatory": True,
            "applies_to": ["digital_health_devices"],
        },
    ],
    "abu_dhabi": [
        {
            "name": "DOH Responsible AI Standard Compliance (Oct 2025)",
            "source": "DOH",
            "mandatory": True,
            "applies_to": ["ai_enabled_devices"],
            "check": "Algorithm transparency, bias assessment, monitoring plan",
        },
    ],
    "dhcc": [
        {
            "name": "DHCR Free Zone Application",
            "source": "DHCR",
            "mandatory": True,
            "check": "Separate application for Dubai Healthcare City Authority",
        },
    ],
}


class EDEChecklistAgent:
    """Generates per-class checklist for UAE EDE submissions.

    Pure rule-based — no LLM needed. Checklists are deterministic.

    Pipeline:
    1. Get base checklist by class (MD or IVD)
    2. Add UAE-specific additions (anti-monopoly, Arabic prominence, data loc)
    3. Add emirate-specific additions (DHA, DOH, DHCR)
    """

    def generate(
        self,
        device_type: str,  # "MD" or "IVD"
        risk_class: str,
        target_emirates: list[str] | None = None,
        decision_date: str = "",
        is_connected: bool = False,
        is_ai_enabled: bool = False,
    ) -> list[dict]:
        """Generate full checklist.

        Args:
            device_type: "MD" or "IVD"
            risk_class: "I", "II", "III", "IV" (MD) or "A", "B", "C", "D" (IVD)
            target_emirates: ["federal", "dubai", "abu_dhabi", "dhcc"]
            decision_date: ISO date for anti-monopoly check
            is_connected: True for cybersecurity/data loc requirements
            is_ai_enabled: True for DOH Responsible AI requirements

        Returns: List of required documents with source + emirate tag.
        """
        # Step 1: Base checklist by class
        if device_type == "MD":
            base = self._get_cumulative(MD_CLASS_CHECKLISTS, risk_class)
        elif device_type == "IVD":
            base = self._get_cumulative(IVD_CLASS_CHECKLISTS, risk_class)
        else:
            raise ValueError(f"Unknown device type: {device_type}")

        # Step 2: Add UAE-specific additions
        additions = []
        for item in UAE_SPECIFIC_ADDITIONS:
            # Apply anti-monopoly only after Feb 2026
            if item.get("applies_after"):
                if decision_date >= item["applies_after"]:
                    additions.append({**item, "category": "uae_specific"})
            else:
                # Apply to specific doc types or connected/AI devices
                if item.get("applies_to"):
                    applies = item["applies_to"]
                    if "connected_devices" in applies and not is_connected:
                        continue
                    if "ai_enabled_devices" in applies and not is_ai_enabled:
                        continue
                additions.append({**item, "category": "uae_specific"})

        # Step 3: Add emirate-specific additions
        emirate_adds = []
        if target_emirates:
            for emirate in target_emirates:
                if emirate in EMIRATE_ADDITIONS:
                    for item in EMIRATE_ADDITIONS[emirate]:
                        # Skip AI items for non-AI devices
                        if "ai_enabled_devices" in item.get("applies_to", []):
                            if not is_ai_enabled:
                                continue
                        if "digital_health_devices" in item.get("applies_to", []):
                            if not is_connected:
                                continue
                        emirate_adds.append({**item, "emirate": emirate})

        return base + additions + emirate_adds

    def get_missing_documents(
        self,
        device_type: str,
        risk_class: str,
        submitted_documents: list[str],
        target_emirates: list[str] | None = None,
        decision_date: str = "",
        is_connected: bool = False,
        is_ai_enabled: bool = False,
    ) -> list[dict]:
        """Compare required vs submitted, return missing list."""
        required = self.generate(
            device_type, risk_class, target_emirates, decision_date, is_connected, is_ai_enabled
        )
        submitted_lower = [d.lower() for d in submitted_documents]
        missing = []
        for r in required:
            name_lower = r["name"].lower()
            # Check if any submitted doc contains the required name (substring)
            if not any(name_lower in s for s in submitted_lower):
                missing.append(r)
        return missing

    @staticmethod
    def _get_cumulative(checklists: dict, target_class: str) -> list[dict]:
        """Get cumulative checklist — class IV includes all lower classes."""
        order = list(checklists.keys())
        if target_class not in order:
            raise ValueError(f"Unknown class: {target_class}. Must be one of {order}")
        idx = order.index(target_class)
        result = []
        for cls in order[: idx + 1]:
            result.extend(checklists[cls])
        return result
