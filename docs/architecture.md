# Architecture — EDE Regulatory Compliance Agent

> Detailed technical architecture. UAE EDE version of the SFDA architecture.
> Mirrors the SFDA architecture with UAE-specific differences highlighted.

## System diagram (4-layer)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 4: UI + Excel Log                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐             │
│  │  Streamlit Web UI         │  │  Excel Logger (hash chain)│             │
│  │  - Upload + UAE PASS auth │  │  - 6 sheets              │             │
│  │  - Multi-emirate selector │  │  - Audit trail            │             │
│  │  - Dual MD/IVD classify   │  │  - Hash chain integrity   │             │
│  └──────────────────────────┘  └──────────────────────────┘             │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3: Deterministic Agent Graph (state machine)                     │
│  ┌──────────────────────────────────────────────────────────┐             │
│  │  State machine (YAML-driven) — LLM does not pick agents  │             │
│  │  UPLOAD→INGEST→CLASSIFY→CONFIRM→CHECKLIST→COLLECT         │             │
│  │  →VALIDATE→REPORT→DONE                                   │             │
│  └──┬──────────────────────────────────────────────────────┘             │
│     │ dispatches to                                                       │
│     ▼                                                                     │
│  7 agent roles: Orchestrator | Ingest | Classifier (EDE) | Evidence      │
│                 Validator | Checklist (EDE) | Excel Logger | Reg Watcher │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Fixed Vector Layer + Hybrid Retrieval                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐       │
│  │  BGE-M3 (fixed)  │  │  BM25 (keyword)  │  │  Cohere Rerank   │       │
│  │  1024 dim, L2    │  │  Arabic-aware    │  │  v3 (precision)  │       │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘       │
│       │                       │                       │                  │
│       └───────────────────────┴───────────────────────┘                  │
│                              ▼                                            │
│  Collections: ede_regulations | user_documents | templates | faq       │
│  (CRITICAL: ede_regulations and user_documents MUST NOT mix)            │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Document Ingest + Standardization                            │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐     │
│  │  pypdf           │  │  python-docx     │  │  Tesseract OCR    │     │
│  │  (PDF parsing)   │  │  (DOCX parsing)  │  │  (image OCR)      │     │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘     │
│       → Standard JSON chunks with metadata                              │
└─────────────────────────────────────────────────────────────────────────┘
```

## UAE-specific differences from SFDA architecture

### Difference 1: Dual MD/IVD classification

SFDA uses a single A/B/C/D system. EDE has **two parallel systems**:
- MD: Class I, II, III, IV (GHTF principles, 22 rules)
- IVD: Class A, B, C, D (GHTF principles, 16 rules)

A device can be both (e.g. MRI hardware + embedded AI image analysis software). The classifier agent produces dual output (`md_class` + optional `samd_class`).

See `src/ede_classification.py` for the rule-based implementation.

### Difference 2: Multi-emirate regulatory layer

SFDA is single-federal. UAE has federal EDE + 3 emirate additions:
- **DHA** (Dubai) — digital health platforms
- **DOH** (Abu Dhabi) — Responsible AI Standard (Oct 2025)
- **DHCR** (Dubai Healthcare City) — free zone with separate authority

Checklist agent generates emirate-specific additions based on `target_emirates` parameter. See `src/agents/checklist.py`.

### Difference 3: Anti-monopoly mechanism (Feb 2026+)

UAE introduced multi-LAR/MAH requirement. Checklist agent flags missing secondary LAR if `decision_date >= 2026-02-01`.

### Difference 4: Arabic text prominence check

UAE requires Arabic text ≥ English prominence (min 1.6mm font). This is a **visual/OCR check**, not just text presence. Ingest agent needs Arabic OCR + font size estimation.

### Difference 5: Data localization

UAE Federal Law No. 2 of 2019 requires health data stored in UAE + 25-year retention. Checklist agent flags connected devices that use AWS Bahrain (outside UAE).

## Defense layers (same as SFDA + UAE additions)

| Layer | What it does | UAE addition |
|---|---|---|
| L1 Preamble constraint | LLM told "only cite clauses from retrieved_rules" | — |
| L2 Tool use for lookup | LLM must call `lookup_clause(clause_id)` before citing | — |
| L3 Post-process validator | Drops any cited_clause not in retrieved_rules | — |
| L4 Hash chain audit | Every decision logged with prev_hash | — |
| L5 Version snapshot | Every decision records which EDE doc version was used | MOHAP→EDE transition date check |
| L6 UAE-specific | Anti-monopoly (multi-LAR), Arabic prominence, data localization | **UAE-only** |

## State machine (same as SFDA, YAML-driven)

```
UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE
                                                                                         ↓
                                                                               MANUAL_REVIEW (fallback)
```

Each state:
- entry_condition: what triggers it
- agent: which agent to call
- output: what data the agent produces
- next: success transition
- on_error: failure transition (typically MANUAL_REVIEW)

Loops (CONFIRM_CLASS, COLLECT) have max_loops to prevent infinite cycling.

## Big document strategy (same as SFDA)

For documents > 1024k tokens (technical files, clinical evaluation reports):
1. Structural split by heading + clause + appendix
2. Per-section summary (map step)
3. Document map (reduce step)
4. Query-driven retrieval (only relevant sections + summaries)
5. Never send full document to LLM

## Anticipated UAE-specific failure modes

| Failure | Mitigation |
|---|---|
| LLM classifies using Saudi A/B/C/D instead of EDE I/II/III/IV | Preamble explicitly forbids; validator checks resulting_class format |
| Arabic OCR fails on RTL text | Use CAMeL Tools + Tesseract Arabic model; flag for manual review if confidence < 0.7 |
| Old MOHAP document referenced as rule source | Validator rejects any source != "EDE"; post-Jan 2025 only |
| Single LAR accepted after Feb 2026 | Checklist agent counts LARs; if < 2, flag critical |
| Arabic font < 1.6mm not detected | Ingest agent estimates text height via OCR bbox analysis |
| Cross-border cloud (AWS Bahrain) accepted | Checklist agent rejects with data localization note |
| Emirate addition missed (e.g. DOH Responsible AI for Abu Dhabi) | Checklist generates per-emirate additions; missing → critical |

## Production upgrade path

| Current (v0.2) | Production (v1.0) |
|---|---|
| Single jurisdiction (UAE EDE) | Multi-jurisdiction (Saudi + UAE + Turkey) via jurisdiction config switch |
| Cohere Command R+ only | UnifiedLLMClient (Cohere + OpenAI + Anthropic + Gemini + local) |
| Synthetic sample corpus | Official, licensed, versioned regulatory corpus |
| ChromaDB optional, in-memory fallback | ChromaDB persistent by default |
| Streamlit web UI, no auth | Streamlit web UI + UAE PASS SSO + Keycloak for multi-user |
| Regulatory watcher (hash + diff, on demand) | Scheduled EDE site scanning + re-validation of affected decisions |
| Heuristic Arabic prominence check | CAMeL Tools + RTL detection + font size estimation |
| No monitoring | Grafana + alerting |

> For demonstration and testing purposes only — see [DISCLAIMER.md](../DISCLAIMER.md).
