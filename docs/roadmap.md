# Roadmap — EDE Regulatory Compliance Agent

> Updated as the project evolves. For demonstration and testing purposes only — see [DISCLAIMER.md](../DISCLAIMER.md).

## Current state (v0.2 — September 2026)

### Implemented
- ✅ EDE classification engine (`src/ede_classification.py`) — 22 GHTF MD rules + 16 IVD rules, conservative rule precedence
- ✅ Classifier agent — deterministic rules first, Cohere LLM fallback for uncertain cases
- ✅ YAML-driven state machine (`data/state_machine.yaml`) with MANUAL_REVIEW fallback and loop limits
- ✅ Checklist agent — per-class MD/IVD document lists + multi-emirate additions (DHA, DOH, DHCR)
- ✅ Excel audit log with SHA-256 hash chain + audit validator (`--verify-audit-only`)
- ✅ Multi-LAR verifier (anti-monopoly check, post-February 2026)
- ✅ Data localization checker (UAE storage, retention, consent, data flow)
- ✅ Arabic prominence checker (heuristic)
- ✅ Ingest agent (PDF, DOCX, JSON; OCR when Tesseract is installed)
- ✅ Evidence validator (LLM, L1 preamble + L3 post-process citation check)
- ✅ Regulatory watcher (document hash + diff)
- ✅ Vector store (ChromaDB when installed, in-memory fallback)
- ✅ CLI (`python -m src.main`) and Streamlit web UI
- ✅ 41 tests: classifier, checklist, audit chain, multi-LAR
- ✅ Synthetic sample corpus and a fictional sample submission

### Known limitations
- The regulatory corpus is synthetic, not official EDE text
- Evidence validation requires a Cohere API key; without one only deterministic checks run
- L2 hallucination defense (tool-based clause lookup) is not implemented
- No re-validation of past decisions when a regulation changes
- No Arabic NLP pipeline (RTL-aware tokenization, medical terminology)
- No UAE PASS integration
- The demo notebook is a placeholder

## v0.3 — Validation depth
**Target: +2 weeks**

- [ ] L2 tool-based clause lookup in the evidence validator
- [ ] Version snapshot capture at CLASSIFY (record EDE document versions used)
- [ ] Re-validation of past decisions when the regulatory watcher detects a change
- [ ] Pre-submission meeting recommendation (Class III/IV)
- [ ] PSUR reminders (every 2 years for high-risk devices)
- [ ] Adverse event 5-day reporting alarms
- [ ] Tests for the state machine, ingest agent and data localization checker
- [ ] End-to-end demo notebook

## v0.4 — Multi-jurisdiction
**Target: +2 weeks**

- [ ] Jurisdiction config switch (BEHAVIOR_AND_ATTENTION.md §D3) — share a core with the SFDA version
- [ ] Extract shared components (state machine, audit chain, retrieval) into a common package
- [ ] TITCK (Turkey) configuration

## v1.0 — Production
**Target: +4 weeks**

- [ ] Official regulatory corpus (licensed, versioned, with source references)
- [ ] Arabic NLP pipeline (CAMeL Tools for RTL + tokenization + medical terminology)
- [ ] LangGraph migration (custom state machine → LangGraph)
- [ ] UAE PASS SSO integration
- [ ] Rate limiting + DLP (data loss prevention)
- [ ] Monitoring (Grafana + alerting on agent failures)
- [ ] Documentation for regulator-facing audit

## Principles

- ❌ No production-grade claims before they are earned
- ❌ No untested features
- ❌ No real customer data without explicit consent
- ❌ No bypassing regulatory version locking (every decision must be version-stamped)
- ❌ No mixing of EDE regulations with legacy MOHAP regulations in the same retrieval pass

## Why this roadmap is public

1. **Credibility** — regulatory teams need to see exactly what the agent does and does not do
2. **Accountability** — public commitments are harder to break

## v1.0 success criteria

This project is "v1.0" when:
- [ ] A regulatory affairs team uses it on a real EDE submission, under their own professional responsibility
- [ ] The agent catches at least one issue the team missed (e.g. a missing secondary LAR after February 2026)
- [ ] The audit trail is verified by an independent party
- [ ] The team reports time savings compared with their previous manual workflow

Until those happen, it's pre-1.0.

## Relationship to the SFDA version

[SFDA-Regulatory-Compliance-Agent](https://github.com/Alicanefee/SFDA-Regulatory-Compliance-Agent) and this repository share:
- 4-layer architecture
- State machine YAML design
- Hash chain audit trail
- Hallucination defense (3-layer)
- Large document strategy (hierarchical summarization)
- BGE-M3 embedding schema

They differ in:
- Classification rules (SFDA A/B/C/D vs EDE I/II/III/IV + IVD A/B/C/D)
- Regulatory corpus (MDS-G5/G008/G010/G27 vs Federal Decree-Law 38 + EDE Guidelines)
- Multi-emirate layer (UAE only — DHA, DOH, DHCR additions)
- Anti-monopoly check (UAE only, post-February 2026)
- Arabic prominence rule (UAE-specific)
- Data localization (UAE Law 2/2019, 25-year retention)
- PSUR frequency (Saudi annual vs UAE biennial)
- Adverse event timeline (Saudi 10 days vs UAE 5 days)
