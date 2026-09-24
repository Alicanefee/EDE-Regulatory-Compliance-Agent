"""
EDE Regulatory Compliance Agent — Context Packet Builder
========================================================

Builds the Context Packet — a fixed JSON structure passed to each agent
call. Prevents "lost-in-the-middle" by limiting context to only relevant
rules + user evidence for the current step.

See docs/architecture.md for the Context Packet design.

Schema:
    {
      "step": "CLASSIFY" | "VALIDATE" | ...,
      "device_intended_use": str,
      "retrieved_rules": [
        {"rule_id": "MDS-G008-R1", "text": "...", "source": "MDS-G008", "version": "2023"}
      ],
      "user_evidence": [
        {"doc_id": "IFU-001", "page": 4, "text": "..."}
      ],
      "previous_state": "INGEST"
    }
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedRule:
    """A regulatory clause retrieved from the vector store."""
    rule_id: str       # e.g. "MDS-G008-R1"
    text: str          # The clause text
    source: str        # e.g. "MDS-G008"
    version: str       # e.g. "v1.0, 2023"
    jurisdiction: str  # e.g. "Saudi FDA"


@dataclass
class UserEvidence:
    """A piece of evidence from the user's submission."""
    doc_id: str    # e.g. "IFU-001"
    doc_type: str  # e.g. "ifu", "technical_file"
    page: int = 0
    text: str = ""


@dataclass
class ContextPacket:
    """Fixed JSON structure passed to each agent call."""
    step: str                       # Current state name
    device_intended_use: str = ""
    retrieved_rules: list[RetrievedRule] = field(default_factory=list)
    user_evidence: list[UserEvidence] = field(default_factory=list)
    previous_state: str = ""

    def to_prompt_context(self) -> str:
        """Render as a prompt-ready text block."""
        rules_text = "\n\n".join(
            f"[{r.rule_id}] ({r.jurisdiction})\n{r.text}"
            for r in self.retrieved_rules
        )
        evidence_text = "\n\n".join(
            f"[{e.doc_id} page {e.page}] ({e.doc_type})\n{e.text[:300]}..."
            for e in self.user_evidence
        )
        return f"""# Context Packet
## Step: {self.step}
## Previous state: {self.previous_state or '(initial)'}

## Device intended use
{self.device_intended_use or '(not provided)'}

## Retrieved regulatory rules
{rules_text or '(no rules retrieved)'}

## User evidence (from submission)
{evidence_text or '(no evidence provided)'}
"""


def build_context_packet(
    step: str,
    device_intended_use: str = "",
    retrieved_rules: list[RetrievedRule] | None = None,
    user_evidence: list[UserEvidence] | None = None,
    previous_state: str = "",
) -> ContextPacket:
    """Build a ContextPacket for an agent call."""
    return ContextPacket(
        step=step,
        device_intended_use=device_intended_use,
        retrieved_rules=retrieved_rules or [],
        user_evidence=user_evidence or [],
        previous_state=previous_state,
    )
