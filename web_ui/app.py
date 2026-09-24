"""
EDE Regulatory Compliance Agent — Streamlit Web UI
==================================================

Basic UI: upload submission, multi-emirate selector, run agent, view report.

Run:
    cd web_ui
    streamlit run app.py

Or from repo root:
    streamlit run web_ui/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import streamlit as st

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.state_machine import State, StateContext, StateMachine
from src.agents.orchestrator import Orchestrator
from src.agents.classifier import EDEClassifierAgent
from src.agents.checklist import EDEChecklistAgent
from src.agents.evidence_validator import EvidenceValidator
from src.utils.multi_lar_verifier import MultiLARVerifier
from src.utils.arabic_prominence_checker import ArabicProminenceChecker
from src.utils.data_localization_checker import DataLocalizationChecker
from src.utils.audit import AuditValidator


# Page config
st.set_page_config(
    page_title="EDE Compliance Agent",
    page_icon="📋",
    layout="wide",
)

st.title("📋 EDE Regulatory Compliance Agent")
st.caption("UAE Emirates Drug Establishment — medical device submission pre-check")
st.warning(Orchestrator.DISCLAIMER)

# Sidebar — settings
with st.sidebar:
    st.header("⚙️ Settings")

    cohere_api_key = st.text_input(
        "Cohere API Key",
        value="",
        type="password",
        help="Required for LLM-based classification/validation. Leave empty for deterministic-only mode."
    )

    audit_xlsx_path = st.text_input(
        "Audit Log Path",
        value="./data/audit_log.xlsx",
        help="Excel file path for hash-chain audit trail."
    )

    st.divider()
    st.subheader("About")
    st.markdown("""
    **v0.2 — State Machine + Multi-Emirate + Anti-Monopoly**

    - 🇦🇪 UAE EDE (post-Jan 2025)
    - GHTF MD Class I/II/III/IV
    - GHTF IVD Class A/B/C/D
    - Multi-emirate support (DHA + DOH + DHCR)
    - Anti-monopoly (Feb 2026+)
    - Arabic prominence check
    - Data localization (Law 2/2019)
    - Hash chain audit trail

    ⚠️ This is independent R&D, not officially endorsed by EDE.
    """)


# Tab structure
tab_submit, tab_checklist, tab_classify, tab_report = st.tabs([
    "📤 Submit Package",
    "📋 Checklist Generator",
    "🎯 Classify Device",
    "📊 Audit Report",
])


# ============================================================
# Tab 1: Submit Package — full state machine run
# ============================================================
with tab_submit:
    st.header("Submit Package")

    col1, col2 = st.columns([2, 1])

    with col1:
        # File upload
        uploaded_file = st.file_uploader(
            "Upload submission package (JSON)",
            type=["json"],
            help="JSON manifest with device_name, jurisdiction, target_emirates, submitted_documents"
        )

        # OR paste JSON
        json_text = st.text_area(
            "Or paste JSON manifest",
            height=200,
            placeholder='{"device_name": "...", "jurisdiction": "UAE EDE", ...}'
        )

    with col2:
        # Multi-emirate selector
        st.subheader("Target Emirates")
        emirate_federal = st.checkbox("Federal (EDE)", value=True, disabled=True)
        emirate_dubai = st.checkbox("Dubai (DHA)")
        emirate_abudhabi = st.checkbox("Abu Dhabi (DOH)")
        emirate_dhcc = st.checkbox("Dubai Healthcare City (DHCR)")

        # Run button
        run_btn = st.button("🚀 Run Compliance Check", type="primary", use_container_width=True)

    if run_btn:
        # Load submission
        if uploaded_file:
            try:
                submission = json.loads(uploaded_file.getvalue().decode("utf-8"))
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                submission = None
        elif json_text.strip():
            try:
                submission = json.loads(json_text)
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON: {e}")
                submission = None
        else:
            st.warning("Please upload a file or paste JSON.")
            submission = None

        if submission:
            # Add selected emirates
            target_emirates = ["federal"]
            if emirate_dubai: target_emirates.append("dubai")
            if emirate_abudhabi: target_emirates.append("abu_dhabi")
            if emirate_dhcc: target_emirates.append("dhcc")
            submission["target_emirates"] = target_emirates

            with st.spinner("Running state machine..."):
                # Initialize state machine
                yaml_path = Path(__file__).parent.parent / "data" / "state_machine.yaml"
                try:
                    sm = StateMachine.from_yaml(yaml_path)
                except FileNotFoundError:
                    st.error(f"State machine YAML not found at {yaml_path}")
                    st.stop()

                # Build minimal agent registry (deterministic path, no LLM)
                from src.agents.checklist import EDEChecklistAgent

                def checklist_agent_fn(ctx):
                    agent = EDEChecklistAgent()
                    cr = ctx.classification_result or {}
                    risk_class = cr.get("md_class") or cr.get("ivd_class")
                    if not risk_class:
                        return {"error": "No class", "checklist": []}
                    device_type = "MD" if cr.get("md_class") else "IVD"
                    checklist = agent.generate(
                        device_type=device_type,
                        risk_class=risk_class,
                        target_emirates=ctx.submission_data.get("target_emirates", ["federal"]),
                        decision_date=ctx.submission_data.get("submission_date", ""),
                        is_connected=ctx.submission_data.get("is_connected", True),
                        is_ai_enabled=ctx.submission_data.get("is_ai_enabled", True),
                    )
                    ctx.checklist = checklist
                    return {"checklist": len(checklist)}

                # Simple agent registry (deterministic path)
                def classifier_fn(ctx):
                    from src.agents.classifier import EDEClassifierAgent
                    agent = EDEClassifierAgent(llm_client=None)
                    device_chars = {
                        "device_name": ctx.submission_data.get("device_name", ""),
                        "device_type": ctx.submission_data.get("device_type", "MD"),
                        "intended_use": ctx.submission_data.get("intended_use", "Diagnostic imaging"),
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
                    result = agent.classify(device_chars, retrieved_rules=[])
                    ctx.classification_result = result
                    return result

                def noop_fn(ctx):
                    return {}

                agent_registry = {
                    "orchestrator": noop_fn,
                    "ingest": noop_fn,
                    "classifier": classifier_fn,
                    "checklist": checklist_agent_fn,
                    "evidence_validator": noop_fn,
                    "excel_logger": noop_fn,
                }

                # Run state machine
                ctx = StateContext(
                    current_state=State.UPLOAD,
                    submission_data=submission,
                )
                ctx = sm.run(ctx, agent_registry, max_steps=15)

                # Run pre-checks
                multi_lar = MultiLARVerifier()
                lar_findings = multi_lar.verify_from_submission(submission)

                dl_checker = DataLocalizationChecker()
                dl_findings = dl_checker.check_from_submission(submission)

            # Display results
            st.subheader("Results")

            # State machine status
            if ctx.current_state == State.DONE:
                st.success(f"✅ State machine completed: {ctx.current_state.value}")
            elif ctx.current_state == State.MANUAL_REVIEW:
                st.error(f"⚠️ Routed to MANUAL_REVIEW")
            else:
                st.warning(f"State machine stopped at: {ctx.current_state.value}")

            # Classification result
            if ctx.classification_result:
                st.subheader("Classification")
                cr = ctx.classification_result
                col_a, col_b = st.columns(2)
                with col_a:
                    if cr.get("md_class"):
                        st.metric("MD Class", cr["md_class"])
                        st.caption(f"per {cr.get('md_rule_id', '?')}")
                    else:
                        st.metric("MD Class", "(none)")
                with col_b:
                    if cr.get("ivd_class"):
                        st.metric("IVD Class", cr["ivd_class"])
                        st.caption(f"per {cr.get('ivd_rule_id', '?')}")
                    else:
                        st.metric("IVD Class", "(none)")
                st.caption(cr.get("justification", ""))

            # Checklist
            if ctx.checklist:
                st.subheader(f"Checklist ({len(ctx.checklist)} items)")
                for i, item in enumerate(ctx.checklist, 1):
                    severity = "🔴" if item.get("mandatory") else "🟢"
                    emirate_tag = f" [{item.get('emirate', 'federal')}]" if "emirate" in item else ""
                    st.write(f"{severity} {i}. {item.get('name', '')} _({item.get('source', '?')}){emirate_tag}_")

            # Pre-check findings
            if lar_findings or dl_findings:
                st.subheader("Pre-check Findings")
                for f in lar_findings + dl_findings:
                    icon = {"critical": "🔴", "warning": "🟡", "info": "🔵", "ok": "✅"}.get(f.severity, "🔵")
                    st.write(f"{icon} **{f.title}** — {f.description}")
                    st.caption(f"Cited: {f.cited_clause}")


# ============================================================
# Tab 2: Checklist Generator (standalone)
# ============================================================
with tab_checklist:
    st.header("Checklist Generator")

    col1, col2 = st.columns(2)
    with col1:
        device_type = st.selectbox("Device Type", ["MD", "IVD"])
        risk_class = st.selectbox(
            "Risk Class",
            ["I", "II", "III", "IV"] if device_type == "MD" else ["A", "B", "C", "D"]
        )
    with col2:
        decision_date = st.date_input("Decision Date")
        is_connected = st.checkbox("Connected device", value=True)
        is_ai_enabled = st.checkbox("AI-enabled device", value=True)

    emirates = st.multiselect(
        "Target Emirates",
        ["federal", "dubai", "abu_dhabi", "dhcc"],
        default=["federal"]
    )

    if st.button("Generate Checklist"):
        agent = EDEChecklistAgent()
        checklist = agent.generate(
            device_type=device_type,
            risk_class=risk_class,
            target_emirates=emirates,
            decision_date=str(decision_date),
            is_connected=is_connected,
            is_ai_enabled=is_ai_enabled,
        )
        st.write(f"**{len(checklist)} required documents**")
        for i, item in enumerate(checklist, 1):
            severity = "🔴" if item.get("mandatory") else "🟢"
            emirate_tag = f" [{item.get('emirate', 'federal')}]" if "emirate" in item else ""
            st.write(f"{severity} {i}. {item.get('name', '')} _({item.get('source', '?')}){emirate_tag}_")


# ============================================================
# Tab 3: Classify Device (standalone)
# ============================================================
with tab_classify:
    st.header("Device Classification")

    intended_use = st.text_area(
        "Intended Use Statement",
        value="Diagnostic imaging via magnetic resonance",
        height=100,
    )

    col1, col2 = st.columns(2)
    with col1:
        device_type = st.selectbox("Device Type", ["MD", "IVD"])
        duration = st.selectbox("Duration of Use", ["transient", "short_term", "long_term", "permanent"])
        invasiveness = st.selectbox("Invasiveness", [
            "non_invasive", "invasive_body_orifice", "invasive_surgical", "implantable"
        ])
    with col2:
        active = st.checkbox("Active device", value=True)
        is_diagnostic = st.checkbox("Diagnostic", value=True)
        uses_ionizing = st.checkbox("Uses ionizing radiation", value=False)
        uses_non_ionizing = st.checkbox("Uses non-ionizing radiation", value=True)
        implantable = st.checkbox("Implantable", value=False)

    if st.button("Classify"):
        agent = EDEClassifierAgent(llm_client=None)
        device_chars = {
            "device_type": device_type,
            "intended_use": intended_use,
            "duration_of_use": duration,
            "invasiveness": invasiveness,
            "active": active,
            "is_diagnostic": is_diagnostic,
            "uses_ionizing_radiation": uses_ionizing,
            "uses_non_ionizing_radiation": uses_non_ionizing,
            "implantable": implantable,
            "targets": [],
            "contains_biological_substance": False,
            "contains_drug": False,
        }
        result = agent.classify(device_chars, retrieved_rules=[])

        st.subheader("Classification Result")
        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("MD Class", result.get("md_class") or "(none)")
            st.caption(f"per {result.get('md_rule_id', '?')}")
        with col_b:
            st.metric("IVD Class", result.get("ivd_class") or "(none)")
            st.caption(f"per {result.get('ivd_rule_id', '?')}")
        st.write(f"**Justification:** {result.get('justification', '')}")
        if result.get("is_uncertain"):
            st.warning(f"⚠️ Uncertain: {result.get('uncertainty_reason', '')}")


# ============================================================
# Tab 4: Audit Report
# ============================================================
with tab_report:
    st.header("Audit Trail Report")

    audit_path = st.text_input(
        "Audit Excel File Path",
        value=audit_xlsx_path
    )

    if st.button("Verify Audit Integrity"):
        try:
            validator = AuditValidator(audit_path)
            report = validator.generate_audit_report()
            st.code(report, language="text")
        except FileNotFoundError:
            st.error(f"Audit file not found: {audit_path}")
        except Exception as e:
            st.error(f"Error: {e}")
