"""
EDE Regulatory Compliance Agent — Main Entry Point
====================================================

v0.2: State machine-driven flow (replaces inline v0.1 logic).

Usage (from the repository root):
    python -m src.main --submission data/sample_submission/sample_package.json
    python -m src.main --submission <path> --audit /path/to/audit_log.xlsx
    python -m src.main --submission <path> --verify-audit-only

For demonstration and testing purposes only — see DISCLAIMER.md.

Pipeline:
    UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT
    → VALIDATE → REPORT → DONE
                       ↓ (on_error)
                   MANUAL_REVIEW
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

import click
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel

from src.state_machine import State, StateContext, StateMachine
from src.agents.orchestrator import Orchestrator, orchestrator_agent
from src.agents.ingest import ingest_agent, IngestAgent
from src.agents.classifier import classifier_agent, EDEClassifierAgent
from src.agents.checklist import EDEChecklistAgent
from src.agents.evidence_validator import evidence_validator_agent, EvidenceValidator
from src.agents.excel_logger import excel_logger_agent, ExcelLogger
from src.agents.regulatory_watcher import regulatory_watcher_agent, RegulatoryWatcher
from src.utils.audit import AuditValidator
from src.utils.multi_lar_verifier import MultiLARVerifier
from src.utils.arabic_prominence_checker import ArabicProminenceChecker
from src.utils.data_localization_checker import DataLocalizationChecker

load_dotenv()
console = Console()


# Agent registry — map agent name to callable
def build_agent_registry() -> dict[str, Any]:
    """Build the agent registry for the state machine."""
    return {
        "orchestrator": orchestrator_agent,
        "ingest": ingest_agent,
        "classifier": classifier_agent,
        "checklist": lambda ctx: _checklist_agent(ctx),
        "evidence_validator": evidence_validator_agent,
        "excel_logger": excel_logger_agent,
        "regulatory_watcher": regulatory_watcher_agent,
    }


def _checklist_agent(ctx: StateContext) -> dict:
    """State machine calls this for CHECKLIST state."""
    agent = EDEChecklistAgent()
    cr = ctx.classification_result or {}

    # Determine class from classification result
    if cr.get("md_class"):
        device_type = "MD"
        risk_class = cr["md_class"]
    elif cr.get("ivd_class"):
        device_type = "IVD"
        risk_class = cr["ivd_class"]
    else:
        return {"error": "No classification result", "checklist": []}

    target_emirates = ctx.submission_data.get("target_emirates", ["federal"])
    decision_date = ctx.submission_data.get("submission_date", "")
    is_connected = ctx.submission_data.get("is_connected", True)  # default for MRI
    is_ai_enabled = ctx.submission_data.get("is_ai_enabled", True)

    checklist = agent.generate(
        device_type=device_type,
        risk_class=risk_class,
        target_emirates=target_emirates,
        decision_date=decision_date,
        is_connected=is_connected,
        is_ai_enabled=is_ai_enabled,
    )
    ctx.checklist = checklist
    return {"checklist": len(checklist)}


@click.command()
@click.option(
    "--submission",
    "submission_path",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Path to submission package JSON.",
)
@click.option(
    "--audit",
    "audit_xlsx",
    type=click.Path(path_type=Path),
    default=Path("./data/audit_log.xlsx"),
    help="Path to audit log Excel file (created if missing).",
)
@click.option("--verify-audit-only", is_flag=True, help="Just verify audit chain, don't run agent.")
@click.option("--show-agent-trace", is_flag=True, help="Show each agent execution in console.")
def main(
    submission_path: Path,
    audit_xlsx: Path,
    verify_audit_only: bool,
    show_agent_trace: bool,
) -> None:
    """Run the EDE regulatory compliance agent on a submission package."""

    console.print(Panel.fit(
        "[bold]EDE Regulatory Compliance Agent v0.2[/bold]\n"
        "[dim]State machine-driven · Hash chain audit · Multi-emirate aware[/dim]",
        border_style="purple",
    ))

    # Verify audit only mode
    if verify_audit_only:
        if not audit_xlsx.exists():
            console.print(f"[red]✗ Audit file not found: {audit_xlsx}[/red]")
            sys.exit(1)
        validator = AuditValidator(audit_xlsx)
        report = validator.generate_audit_report()
        console.print(report)
        sys.exit(0 if "✅" in report else 1)

    # 1. Load submission
    submission = json.loads(submission_path.read_text(encoding="utf-8"))
    console.print(f"[bold]Submission loaded:[/bold] {submission.get('device_name')}")
    console.print(f"[dim]Jurisdiction: {submission.get('jurisdiction')}")
    console.print(f"[dim]Target emirates: {submission.get('target_emirates')}")
    console.print(f"[dim]Documents: {len(submission.get('submitted_documents', []))}[/dim]\n")

    # 2. Initialize state machine from YAML
    yaml_path = Path(__file__).parent.parent / "data" / "state_machine.yaml"
    sm = StateMachine.from_yaml(yaml_path)

    # 3. Build agent registry
    agent_registry = build_agent_registry()

    # 4. Run multi-LAR verification (anti-monopoly)
    console.print("[bold]Step 0: Multi-LAR verification (anti-monopoly)...[/bold]")
    multi_lar = MultiLARVerifier()
    lar_findings = multi_lar.verify_from_submission(submission)
    for f in lar_findings:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵", "ok": "✅"}.get(f.severity, "🔵")
        console.print(f"  {icon} {f.title}: {f.description[:80]}")
    console.print()

    # 5. Run Arabic prominence check (if labeling docs available)
    console.print("[bold]Step 0b: Arabic prominence check (heuristic)...[/bold]")
    ar_checker = ArabicProminenceChecker()
    # (For demo — actual labeling docs would be in submission)
    console.print("  [dim](skipped — no labeling docs to check in demo submission)[/dim]\n")

    # 6. Run data localization check
    console.print("[bold]Step 0c: Data localization check...[/bold]")
    dl_checker = DataLocalizationChecker()
    dl_findings = dl_checker.check_from_submission(submission)
    for f in dl_findings:
        icon = {"critical": "🔴", "warning": "🟡", "info": "🔵", "ok": "✅"}.get(f.severity, "🔵")
        console.print(f"  {icon} {f.title}: {f.description[:80]}")
    console.print()

    # 7. Run the state machine
    console.print("[bold]Running state machine...[/bold]")
    ctx = StateContext(
        current_state=State.UPLOAD,
        submission_data=submission,
    )
    ctx = sm.run(ctx, agent_registry, max_steps=20)

    # 8. Show user-facing messages from each state
    if show_agent_trace:
        console.print("\n[bold]Agent execution trace:[/bold]")
        orch = Orchestrator()
        for event in ctx.audit_log:
            if event.get("event") == "agent_executed":
                console.print(f"  [dim]→ {event.get('state')}: {event.get('agent')}[/dim]")

    # 9. Show final report
    console.print("\n[bold]Final report:[/bold]\n")
    orch = Orchestrator()
    report = orch.generate_user_message(State.REPORT, ctx)
    console.print(report)

    # 10. Add pre-state-machine findings (multi-LAR + data localization) to the report
    if lar_findings or dl_findings:
        console.print("\n[bold]Additional pre-check findings:[/bold]")
        for f in lar_findings + dl_findings:
            icon = {"critical": "🔴", "warning": "🟡", "info": "🔵", "ok": "✅"}.get(f.severity, "🔵")
            console.print(f"  {icon} {f.title}")
            console.print(f"     [dim]{f.description}[/dim]")
            console.print(f"     [dim]Cited: {f.cited_clause}[/dim]")

    # 11. Exit code — critical findings from the pre-checks count too
    precheck_critical = sum(1 for f in lar_findings + dl_findings if f.severity == "critical")
    if ctx.current_state == State.MANUAL_REVIEW:
        console.print("\n[red]⚠️ Submission routed to MANUAL_REVIEW[/red]")
        console.print(f"[yellow]{Orchestrator.DISCLAIMER}[/yellow]")
        sys.exit(1)
    elif ctx.current_state == State.DONE:
        critical = precheck_critical + sum(
            1 for f in ctx.findings if f.get("severity") == "critical"
        )
        if critical > 0:
            console.print(f"\n[red]✗ {critical} critical finding(s) in this demo check[/red]")
        else:
            console.print("\n[green]✓ No critical findings in this demo check[/green]")
        console.print(f"[yellow]{Orchestrator.DISCLAIMER}[/yellow]")
        sys.exit(1 if critical > 0 else 0)


if __name__ == "__main__":
    main()
