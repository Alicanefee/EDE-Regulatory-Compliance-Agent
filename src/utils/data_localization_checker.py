"""
Data Localization Checker
=========================

UAE Federal Law No. 2 of 2019 requires:
  - Health data must be stored within UAE territory
  - Cross-border transfer requires explicit patient consent + EDE approval
  - Medical records must be retained for minimum 25 years

This module checks:
  1. Cloud provider/region used by the device
  2. Whether region is within UAE
  3. Data retention policy statement
  4. Patient consent mechanism

Dependencies: requests (for cloud region verification)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


# Cloud regions classified by jurisdiction
CLOUD_REGIONS_UAE = {
    # Microsoft Azure — UAE regions
    "uaenorth": "Microsoft Azure — UAE North (Dubai)",
    "uaecentral": "Microsoft Azure — UAE Central (Abu Dhabi)",
    # AWS — Bahrain is closest but NOT UAE
    # Google Cloud — no UAE region
    # Oracle Cloud — Dubai region
    "me-dubai-1": "Oracle Cloud — Dubai",
    # AliCloud — Dubai region
    "me-east-1": "AliCloud — UAE (Dubai)",
}

CLOUD_REGIONS_OUTSIDE_UAE = {
    # AWS Bahrain (close but cross-border)
    "me-south-1": "AWS Middle East (Bahrain) — cross-border, requires consent",
    # AWS UAE region (announced 2025)
    "me-central-1": "AWS Middle East (UAE) — UAE-based",
    # Other common regions
    "us-east-1": "AWS US East — non-UAE",
    "us-west-2": "AWS US West — non-UAE",
    "eu-west-1": "AWS EU Ireland — non-UAE",
    "europe-west1": "GCP Europe West — non-UAE",
}

MIN_RETENTION_YEARS = 25


@dataclass
class DataLocalizationFinding:
    """Result of data localization check."""
    severity: str  # "critical" | "warning" | "info" | "ok"
    title: str
    description: str
    cited_clause: str = "UAE Federal Law No. 2 of 2019"


class DataLocalizationChecker:
    """Verifies UAE data localization compliance for connected medical devices."""

    def check(
        self,
        device_chars: dict,
        submitted_documents: list[dict],
    ) -> list[DataLocalizationFinding]:
        """Check data localization compliance.

        Args:
            device_chars: {is_connected, cloud_provider, cloud_region, data_types}
            submitted_documents: List of submitted documents

        Returns: List of findings.
        """
        findings = []

        is_connected = device_chars.get("is_connected", False)
        if not is_connected:
            findings.append(DataLocalizationFinding(
                severity="info",
                title="Not a connected device (data localization not applicable)",
                description="Device does not transmit data — Law 2/2019 storage rules not triggered.",
            ))
            return findings

        cloud_provider = device_chars.get("cloud_provider", "").lower()
        cloud_region = device_chars.get("cloud_region", "").lower()

        # Check 1: Cloud region is within UAE
        if cloud_region:
            if cloud_region in CLOUD_REGIONS_UAE:
                findings.append(DataLocalizationFinding(
                    severity="ok",
                    title="Cloud region within UAE",
                    description=f"Region: {CLOUD_REGIONS_UAE[cloud_region]}",
                ))
            elif cloud_region in CLOUD_REGIONS_OUTSIDE_UAE:
                # Cross-border — requires explicit consent
                if cloud_region == "me-central-1":
                    # AWS UAE region (post-2025)
                    findings.append(DataLocalizationFinding(
                        severity="ok",
                        title="AWS UAE region",
                        description="AWS Middle East (UAE) — UAE-based, compliant.",
                    ))
                else:
                    findings.append(DataLocalizationFinding(
                        severity="critical",
                        title=f"Cross-border cloud region: {cloud_region}",
                        description=(
                            f"Region: {CLOUD_REGIONS_OUTSIDE_UAE[cloud_region]}. "
                            f"Federal Law 2/2019 requires health data stored within UAE. "
                            f"Cross-border requires explicit patient consent + EDE approval."
                        ),
                    ))
            else:
                findings.append(DataLocalizationFinding(
                    severity="warning",
                    title=f"Unknown cloud region: {cloud_region}",
                    description=(
                        f"Region not in known UAE-approved list. "
                        f"Verify with cloud provider documentation."
                    ),
                ))

        # Check 2: Data retention policy documented
        has_retention_policy = any(
            "retention" in d.get("name", "").lower()
            or "data_localization" in d.get("type", "").lower()
            or "policy" in d.get("name", "").lower()
            for d in submitted_documents
        )
        if not has_retention_policy:
            findings.append(DataLocalizationFinding(
                severity="critical",
                title="Data retention policy missing",
                description=(
                    f"Federal Law 2/2019 requires minimum {MIN_RETENTION_YEARS} years "
                    f"retention for medical records. No policy document found in submission."
                ),
            ))
        else:
            findings.append(DataLocalizationFinding(
                severity="ok",
                title="Data retention policy document present",
                description=f"Verify minimum {MIN_RETENTION_YEARS}-year retention is specified.",
            ))

        # Check 3: Patient consent mechanism (for processing health data)
        has_consent_doc = any(
            "consent" in d.get("name", "").lower()
            or "pdpl" in d.get("name", "").lower()
            for d in submitted_documents
        )
        if not has_consent_doc:
            findings.append(DataLocalizationFinding(
                severity="critical",
                title="Patient consent documentation missing",
                description=(
                    "PDPL (Federal Decree-Law 45/2021) requires patient consent for "
                    "processing health data. No consent documentation found."
                ),
                cited_clause="Federal Decree-Law No. 45 of 2021 (PDPL)",
            ))

        # Check 4: Data flow diagram
        has_data_flow = any(
            "data flow" in d.get("name", "").lower()
            or "data_flow" in d.get("type", "").lower()
            for d in submitted_documents
        )
        if not has_data_flow:
            findings.append(DataLocalizationFinding(
                severity="warning",
                title="Data flow diagram missing",
                description=(
                    "Required by Law 2/2019 for connected devices. "
                    "Shows: where data is collected, processed, stored."
                ),
            ))

        return findings

    def check_from_submission(self, submission_data: dict) -> list[DataLocalizationFinding]:
        """Convenience: check from submission_package.json structure."""
        submitted_docs = submission_data.get("submitted_documents", [])

        # In real system, device_chars would come from the technical file
        # For demo, assume connected MRI with default cloud
        device_chars = {
            "is_connected": True,  # the sample MRI system is connected
            "cloud_provider": submission_data.get("cloud_provider", "azure"),
            "cloud_region": submission_data.get("cloud_region", "uaenorth"),
            "data_types": ["imaging_data", "patient_metadata"],
        }

        return self.check(device_chars, submitted_docs)
