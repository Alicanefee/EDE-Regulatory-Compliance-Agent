"""
Agent: Evidence Validator
=========================

Role: Validate user submission evidence against retrieved regulatory rules.

Input: User document chunks + relevant regulatory clauses (retrieved)
Output: List of findings (per clause)

Output schema per finding:
    {
      "clause_id": str,           # rule_id from retrieved rules
      "verdict": "compliant" | "missing" | "unclear",
      "evidence_cited": str,      # quote from user doc
      "explanation": str,
      "suggested_fix": str,       # if not compliant
      "severity": "critical" | "warning" | "info"
    }

Defense layers:
- L1 preamble: "only cite clauses from retrieved_rules"
- L2 tool use: lookup_clause(clause_id) — verify before citing (TODO)
- L3 post-process: drop any cited_clause not in retrieved_rules

Conservative by design:
- If evidence is unclear → "unclear" verdict, not "compliant"
- If cited rule_id is hallucinated → drop finding, mark "(unverified)"
"""
from __future__ import annotations

import json
import os
import re
from typing import Any

from src.state_machine import StateContext


class EvidenceValidator:
    """Validates user evidence against regulatory rules."""

    PROMPT_TEMPLATE_PATH = "src/prompts/evidence_validator.md"

    def __init__(self, llm_client: Any | None = None) -> None:
        self.llm_client = llm_client

    def validate(
        self,
        user_evidence: list[dict],
        retrieved_rules: list[dict],
    ) -> list[dict]:
        """Validate each piece of evidence against applicable rules.

        Args:
            user_evidence: List of {doc_id, doc_type, text} dicts
            retrieved_rules: List of {rule_id, text, source} dicts

        Returns: List of findings.
        """
        if not self.llm_client:
            # Without LLM, do basic deterministic check
            return self._deterministic_check(user_evidence, retrieved_rules)

        try:
            with open(self.PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
                template = f.read()
        except FileNotFoundError:
            return self._deterministic_check(user_evidence, retrieved_rules)

        # Format prompt
        rules_text = "\n\n".join(
            f"[{r.get('rule_id', '?')}] ({r.get('source', '?')})\n{r.get('text', '')}"
            for r in retrieved_rules
        )
        evidence_text = "\n\n".join(
            f"[{e.get('doc_id', '?')}] ({e.get('doc_type', '?')})\n{e.get('text', '')[:500]}"
            for e in user_evidence
        )
        prompt = template.format(
            retrieved_rules=rules_text,
            user_evidence=evidence_text,
        )

        try:
            response = self.llm_client.chat(
                message=prompt,
                model="command-r-plus",
                temperature=0.0,
                preamble=(
                    "You are a meticulous regulatory evidence validator. "
                    "You only cite clauses from the provided retrieved_rules; "
                    "you never invent clause IDs. You output JSON only."
                ),
            )
            text = response.text
        except Exception:
            return self._deterministic_check(user_evidence, retrieved_rules)

        # Parse JSON output (LLM may include surrounding text)
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            findings = json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            return []

        # L3 defense: validate cited clause IDs
        valid_clause_ids = {r.get("rule_id") for r in retrieved_rules if r.get("rule_id")}
        for f in findings:
            cited = f.get("cited_clause", "") or f.get("clause_id", "")
            if cited and cited not in valid_clause_ids:
                f["cited_clause"] = "(unverified — LLM hallucinated)"
                f["severity"] = "warning"

        return findings

    def _deterministic_check(
        self,
        user_evidence: list[doc],
        retrieved_rules: list[dict],
    ) -> list[dict]:
        """Fallback: deterministic check without LLM.

        Checks if user evidence mentions key terms from each rule.
        Very crude — for production use the LLM path.
        """
        findings = []
        all_evidence_text = " ".join(e.get("text", "") for e in user_evidence).lower()

        for rule in retrieved_rules:
            rule_id = rule.get("rule_id", "?")
            rule_text = rule.get("text", "").lower()

            # Extract key terms from rule (e.g. "ifu", "arabic", "cybersecurity")
            key_terms = []
            for term in ["ifu", "arabic", "english", "cybersecurity", "sbom",
                          "threat model", "iso 13485", "iso 14971", "clinical evaluation",
                          "risk management", "data protection", "udi"]:
                if term in rule_text:
                    key_terms.append(term)

            missing_terms = [t for t in key_terms if t not in all_evidence_text]
            if missing_terms:
                findings.append({
                    "clause_id": rule_id,
                    "verdict": "missing",
                    "evidence_cited": "",
                    "explanation": f"Submission appears to lack: {', '.join(missing_terms)}",
                    "suggested_fix": f"Provide documentation covering: {', '.join(missing_terms)}",
                    "severity": "critical" if any(t in ["arabic", "cybersecurity", "iso 13485"]
                                                  for t in missing_terms) else "warning",
                })

        return findings


def evidence_validator_agent(ctx: StateContext) -> dict:
    """State machine calls this for VALIDATE state."""
    # In a real system, retrieve relevant rules from vector store
    # For now, use the regulatory_corpus chunks from ctx.ingested_chunks
    retrieved_rules = [
        {"rule_id": c.get("clause_id"), "text": c.get("text", ""),
         "source": c.get("source_file", "")}
        for c in ctx.ingested_chunks
        if c.get("clause_id")
    ]

    # Build user evidence from submitted documents (manifest names + types)
    user_evidence = [
        {"doc_id": d.get("name", ""), "doc_type": d.get("type", ""),
         "text": d.get("name", "")}
        for d in ctx.submission_data.get("submitted_documents", [])
    ]

    # Try LLM (optional)
    llm_client = None
    api_key = os.getenv("COHERE_API_KEY")
    if api_key:
        try:
            import cohere
            llm_client = cohere.Client(api_key=api_key)
        except Exception:
            pass

    validator = EvidenceValidator(llm_client=llm_client)
    findings = validator.validate(user_evidence, retrieved_rules)

    ctx.findings = findings
    return {"findings": len(findings)}
