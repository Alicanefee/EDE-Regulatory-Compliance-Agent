"""
Agent: Orchestrator
==================

Role: Manages state machine transitions, generates user-facing messages.

Input: StateContext + agent output
Output: User message + next state decision

Pure Python — no LLM needed for basic orchestration. LLM only used for
rich user-facing messages (optional).

Behavior rules (BEHAVIOR_AND_ATTENTION.md §B1):
- LLM does NOT pick which agent to call (state machine does)
- Orchestrator's role: communication + transition logic only
- Knows when to say "I don't know" (uncertainty → MANUAL_REVIEW)
- Conservative by design (borderline → higher class)
- Disclaimer mandatory on every report
"""
from __future__ import annotations
from typing import Any

from src.state_machine import State, StateContext


class Orchestrator:
    """State machine dispatcher + user communication.

    The orchestrator does NOT pick which agent to call; the state machine does.
    The orchestrator's role is limited to communication + transition logic.
    """

    DISCLAIMER = (
        "⚠️ Demonstration only — based on a synthetic regulatory corpus. "
        "Not official EDE, legal or regulatory advice and not a regulatory clearance. "
        "Consult EDE (www.ede.gov.ae) for official approval. You are solely "
        "responsible for all legal obligations arising from your decisions. "
        "See DISCLAIMER.md."
    )

    def generate_user_message(
        self,
        state: State,
        ctx: StateContext,
        agent_output: dict | None = None,
    ) -> str:
        """Generate a user-facing message for the current state."""
        if state == State.UPLOAD:
            return (
                "[Step 1/9: UPLOAD]\n"
                "Please upload the submission package (PDF, DOCX, JSON manifest)."
            )
        elif state == State.INGEST:
            n = len(ctx.ingested_chunks)
            return f"[Step 2/9: INGEST]\n✓ {n} document chunks processed."
        elif state == State.CLASSIFY:
            if ctx.classification_result:
                cr = ctx.classification_result
                msg = "[Step 3/9: CLASSIFY]\n"
                msg += f"Device: {cr.get('device_name', '(unknown)')}\n"
                if cr.get("md_class"):
                    msg += f"MD Class: **{cr['md_class']}** (per {cr.get('md_rule_id', '?')})\n"
                if cr.get("ivd_class"):
                    msg += f"IVD Class: **{cr['ivd_class']}** (per {cr.get('ivd_rule_id', '?')})\n"
                msg += f"Justification: {cr.get('justification', '(none)')}\n"
                if cr.get("is_uncertain"):
                    msg += f"⚠️ Uncertain: {cr.get('uncertainty_reason', '')}\n"
                return msg
            return "[Step 3/9: CLASSIFY]\nClassifying..."
        elif state == State.CONFIRM_CLASS:
            cr = ctx.classification_result or {}
            return (
                "[Step 4/9: CONFIRM_CLASS]\n"
                f"Class: {cr.get('md_class') or cr.get('ivd_class')}\n"
                "Confirm class? [yes / no (re-classify) / manual]"
            )
        elif state == State.CHECKLIST:
            n = len(ctx.checklist)
            return f"[Step 5/9: CHECKLIST]\n✓ {n} required documents listed."
        elif state == State.COLLECT:
            submitted = len(ctx.submission_data.get("submitted_documents", []))
            required = len(ctx.checklist)
            return (
                f"[Step 6/9: COLLECT]\n"
                f"Submitted: {submitted} / Required: {required}"
            )
        elif state == State.VALIDATE:
            n = len(ctx.findings)
            critical = sum(1 for f in ctx.findings if f.get("severity") == "critical")
            return (
                f"[Step 7/9: VALIDATE]\n"
                f"✓ {n} findings ({critical} critical)."
            )
        elif state == State.REPORT:
            return self._format_report(ctx)
        elif state == State.DONE:
            return "[Step 9/9: DONE]\nProcess complete."
        elif state == State.MANUAL_REVIEW:
            return (
                "[⚠️ MANUAL REVIEW]\n"
                "Human review is required at this step. "
                "The agent could not decide — please consult your regulatory specialist.\n"
                + self.DISCLAIMER
            )
        return f"[{state.value}]"

    def _format_report(self, ctx: StateContext) -> str:
        """Format the final report (REPORT state)."""
        cr = ctx.classification_result or {}
        device_name = cr.get("device_name", ctx.submission_data.get("device_name", "Unknown"))

        lines = [
            "=" * 70,
            f"VALIDATION REPORT — {device_name}",
            "=" * 70,
            f"Jurisdiction: {ctx.submission_data.get('jurisdiction', 'UAE EDE')}",
            f"Target emirates: {', '.join(ctx.submission_data.get('target_emirates', ['federal']))}",
            "",
        ]

        # Classification
        if cr:
            lines.append("CLASSIFICATION")
            lines.append("-" * 70)
            if cr.get("md_class"):
                lines.append(f"  MD Class: {cr['md_class']} (per {cr.get('md_rule_id', '?')})")
            if cr.get("ivd_class"):
                lines.append(f"  IVD Class: {cr['ivd_class']} (per {cr.get('ivd_rule_id', '?')})")
            lines.append(f"  Justification: {cr.get('justification', '(none)')}")
            if cr.get("is_uncertain"):
                lines.append(f"  ⚠️ Uncertain: {cr.get('uncertainty_reason', '')}")
            lines.append("")

        # Findings
        if ctx.findings:
            critical = [f for f in ctx.findings if f.get("severity") == "critical"]
            warning = [f for f in ctx.findings if f.get("severity") == "warning"]
            info = [f for f in ctx.findings if f.get("severity") == "info"]

            for label, items, icon in [
                ("CRITICAL", critical, "🔴"),
                ("WARNING", warning, "🟡"),
                ("INFO", info, "🔵"),
            ]:
                if items:
                    lines.append(f"{icon} {label} ({len(items)})")
                    lines.append("-" * 70)
                    for i, f in enumerate(items, 1):
                        lines.append(f"  {i}. {f.get('title', '(no title)')}")
                        lines.append(f"     Cited clause: {f.get('cited_clause', '(none)')}")
                        lines.append(f"     Description: {f.get('description', '')}")
                        if f.get("suggested_fix"):
                            lines.append(f"     Fix: {f['suggested_fix']}")
                    lines.append("")
        else:
            lines.append("✅ No findings from the state-machine validation against the indexed sample corpus.")
            lines.append("")

        # Audit summary
        lines.append("AUDIT")
        lines.append("-" * 70)
        lines.append(f"  Events logged: {len(ctx.audit_log)}")
        lines.append(f"  State transitions: {sum(1 for e in ctx.audit_log if e.get('event') == 'agent_executed')}")
        lines.append("")

        # Disclaimer
        lines.append(self.DISCLAIMER)
        lines.append("=" * 70)

        return "\n".join(lines)

    def decide_next_state(
        self,
        current: State,
        agent_output: dict | None,
    ) -> str:
        """Decide next state based on agent output (used by state machine)."""
        if not agent_output:
            return State.UPLOAD.value  # initial

        if agent_output.get("error"):
            return State.MANUAL_REVIEW.value

        if agent_output.get("is_uncertain"):
            return State.MANUAL_REVIEW.value

        # CONFIRM_CLASS: handle user response
        if current == State.CONFIRM_CLASS:
            user_response = agent_output.get("user_response", "yes")
            if user_response == "yes":
                return State.CHECKLIST.value
            elif user_response == "no":
                return State.CLASSIFY.value  # re-classify (limited by max_loops)
            else:  # "manual"
                return State.MANUAL_REVIEW.value

        # Linear progression
        linear_order = [
            State.UPLOAD, State.INGEST, State.CLASSIFY, State.CONFIRM_CLASS,
            State.CHECKLIST, State.COLLECT, State.VALIDATE, State.REPORT, State.DONE,
        ]
        try:
            idx = linear_order.index(current)
            return linear_order[min(idx + 1, len(linear_order) - 1)].value
        except ValueError:
            return State.MANUAL_REVIEW.value


# Convenience function — used as agent in state machine dispatch
def orchestrator_agent(ctx: StateContext) -> dict:
    """State machine calls this for CONFIRM_CLASS + REPORT states."""
    orch = Orchestrator()
    message = orch.generate_user_message(ctx.current_state, ctx)
    return {"user_message": message, "next": "auto"}
