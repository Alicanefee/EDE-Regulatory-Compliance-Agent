"""
Agent: Classifier (UAE EDE version)
====================================

Pipeline:
1. Run deterministic EDEClassifier (src/ede_classification.py)
2. If is_uncertain → call LLM with classifier prompt template
3. Validate LLM output against retrieved rules (L3 hallucination defense)
4. Return ClassificationResult

Conservative by design:
- Borderline I/II → II, II/III → III, III/IV → IV
- Uncertain → MANUAL_REVIEW
- Dual MD/IVD/SaMD classification when applicable
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from src.ede_classification import EDEClassifier, ClassificationResult
from src.state_machine import StateContext


class EDEClassifierAgent:
    """UAE EDE Classifier Agent — deterministic first, LLM fallback."""

    PROMPT_TEMPLATE_PATH = "src/prompts/classifier.md"

    def __init__(self, llm_client: Any | None = None) -> None:
        self.deterministic_classifier = EDEClassifier()
        self.llm_client = llm_client  # Cohere client for ambiguous cases

    def classify(
        self,
        device_chars: dict,
        retrieved_rules: list[dict] | None = None,
    ) -> dict:
        """Classify device per EDE Classification Guidelines.

        Returns: dict with md_class, md_rule_id, ivd_class, ivd_rule_id,
                 justification, is_uncertain, uncertainty_reason.
        """
        # Step 1: Deterministic classifier
        det_result = self.deterministic_classifier.classify(**device_chars)

        # Step 2: If uncertain and LLM available → call LLM
        if det_result.is_uncertain and self.llm_client and retrieved_rules:
            llm_result = self._classify_with_llm(device_chars, retrieved_rules)
            if llm_result:
                return llm_result

        # Step 3: Return deterministic result (or uncertain flag if no LLM)
        return {
            "device_type": det_result.device_type,
            "md_class": det_result.md_class,
            "md_rule_id": det_result.md_rule_id,
            "ivd_class": det_result.ivd_class,
            "ivd_rule_id": det_result.ivd_rule_id,
            "justification": det_result.justification,
            "is_uncertain": det_result.is_uncertain,
            "uncertainty_reason": det_result.uncertainty_reason,
            "device_name": device_chars.get("device_name", ""),
        }

    def _classify_with_llm(
        self,
        device_chars: dict,
        retrieved_rules: list[dict],
    ) -> dict | None:
        """LLM fallback for ambiguous cases.

        Reads prompt template from src/prompts/classifier.md,
        fills placeholders, calls LLM, parses JSON output,
        validates cited rule_id exists in retrieved_rules (L3 defense).
        """
        try:
            with open(self.PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            return None

        # Format retrieved rules as text
        rules_text = "\n\n".join(
            f"[{r.get('rule_id', '?')}] ({r.get('source', '?')})\n{r.get('text', '')}"
            for r in retrieved_rules
        )

        # Fill template
        prompt = template.format(
            retrieved_rules=rules_text,
            device_type=device_chars.get("device_type", "MD"),
            device_intended_use=device_chars.get("intended_use", ""),
            duration_of_use=device_chars.get("duration_of_use", ""),
            invasiveness=device_chars.get("invasiveness", ""),
            active=device_chars.get("active", False),
            is_diagnostic=device_chars.get("is_diagnostic", False),
            uses_ionizing_radiation=device_chars.get("uses_ionizing_radiation", False),
            uses_non_ionizing_radiation=device_chars.get("uses_non_ionizing_radiation", False),
            implantable=device_chars.get("implantable", False),
            targets=device_chars.get("targets", []),
            contains_biological_substance=device_chars.get("contains_biological_substance", False),
            contains_drug=device_chars.get("contains_drug", False),
            ivd_type=device_chars.get("ivd_type", ""),
        )

        try:
            response = self.llm_client.chat(
                message=prompt,
                model="command-r-plus",
                temperature=0.0,
                preamble=(
                    "You are a meticulous EDE classifier. "
                    "You only cite clauses from the provided rules; you never invent clause IDs."
                ),
            )
            text = response.text
        except Exception:
            return None

        # Parse JSON output
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            result = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return None

        # L3 defense: validate cited rule_ids exist in retrieved_rules
        valid_rule_ids = {r.get("rule_id") for r in retrieved_rules if r.get("rule_id")}
        if result.get("md_rule_id") and result["md_rule_id"] not in valid_rule_ids:
            result["md_rule_id"] = "(unverified — LLM hallucinated)"
        if result.get("ivd_rule_id") and result["ivd_rule_id"] not in valid_rule_ids:
            result["ivd_rule_id"] = "(unverified — LLM hallucinated)"

        return result


def classifier_agent(ctx: StateContext) -> dict:
    """State machine calls this for CLASSIFY state.

    Reads submission data from ctx, calls EDEClassifierAgent.classify().
    """
    # Build device_chars from submission data + classification result
    submission = ctx.submission_data

    # In a real system, this would extract device characteristics from the
    # ingested documents (technical file). For now, use submission metadata.
    device_chars = {
        "device_name": submission.get("device_name", ""),
        "device_type": submission.get("device_type", "MD"),
        "intended_use": submission.get("intended_use", "Diagnostic imaging"),
        "duration_of_use": "transient",
        "invasiveness": "non_invasive",
        "active": True,
        "is_diagnostic": True,
        "uses_ionizing_radiation": False,
        "uses_non_ionizing_radiation": True,
        "implantable": False,
        "targets": [],
        "contains_biological_substance": False,
        "contains_drug": False,
    }

    # Try to initialize LLM client (optional — may not have API key in tests)
    llm_client = None
    api_key = os.getenv("COHERE_API_KEY")
    if api_key:
        try:
            import cohere
            llm_client = cohere.Client(api_key=api_key)
        except Exception:
            pass  # LLM optional

    agent = EDEClassifierAgent(llm_client=llm_client)
    result = agent.classify(device_chars, retrieved_rules=[])

    ctx.classification_result = result
    return result
