# EDE Regulatory Compliance Agent

> **UAE Emirates Drug Establishment (EDE) regulatory pre-check AI agent** for medical device submissions.
> Detects missing documents, format issues and regulatory language gaps BEFORE submission.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Status: v0.2](https://img.shields.io/badge/status-v0.2-orange.svg)](docs/roadmap.md)
[![Tests: pytest](https://img.shields.io/badge/tests-pytest-green.svg)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Jurisdiction: UAE EDE](https://img.shields.io/badge/jurisdiction-UAE%20EDE-blue.svg)](docs/PLAN.md)

> ⚠️ **For demonstration and testing purposes only.** The regulatory corpus is synthetic and the sample submission is fictional. The output is not legal or regulatory advice and not a regulatory clearance. **All legal and regulatory obligations arising from use of this software remain solely with the user.** Read the full [Legal Disclaimer and Terms of Use](DISCLAIMER.md) before use.

**Author**: Ali Can Efe
**Sister repo**: [SFDA-Regulatory-Compliance-Agent](https://github.com/Alicanefee/SFDA-Regulatory-Compliance-Agent) (Saudi version)

---

## 🎯 What this is

A deterministic AI agent that scans medical device submission packages against a UAE EDE regulatory corpus and flags issues before submission. Designed for **medical device manufacturers** and **regulatory affairs teams** preparing UAE submissions.

**Regulatory context**: EDE (Emirates Drug Establishment) took over medical device regulation from MOHAP on **2 January 2025** under Federal Decree-Law No. 38 of 2024. All references in this repository are to EDE, not legacy MOHAP.

## 🏗️ Architecture (4-layer, mirrors the SFDA version)

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 4: UI + Excel Log                                        │  ← Streamlit + openpyxl (hash chain)
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Deterministic Agent Graph (state machine)             │  ← YAML-driven, LLM does not pick agents
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Fixed Vector Layer + Hybrid Retrieval                 │  ← BGE-M3 + BM25 + Cohere Rerank
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Document Ingest + Standardization                     │  ← pypdf + python-docx + Tesseract
└─────────────────────────────────────────────────────────────────┘
```

State machine (YAML-driven, `data/state_machine.yaml`):
```
UPLOAD → INGEST → CLASSIFY → CONFIRM_CLASS → CHECKLIST → COLLECT → VALIDATE → REPORT → DONE
                                   ↓ (error or uncertainty)
                             MANUAL_REVIEW
```

📖 **Research notes**: [`docs/PLAN.md`](docs/PLAN.md) (MOHAP → EDE transition, GHTF I/II/III/IV + IVD A/B/C/D classification, multi-emirate layer, anti-monopoly mechanism, EDE document list)

📖 **Behavior & Attention**: [`docs/BEHAVIOR_AND_ATTENTION.md`](docs/BEHAVIOR_AND_ATTENTION.md) (12 UAE-specific refinements, behavior rules, attention priority list)

📖 **Architecture**: [`docs/architecture.md`](docs/architecture.md) · **Roadmap**: [`docs/roadmap.md`](docs/roadmap.md)

## 🤖 EDE classification engine

**`src/ede_classification.py`** is the UAE-specific classification engine:

- **22 GHTF rules for MD devices** (Class I, II, III, IV) — `MD_RULES`
- **16 GHTF rules for IVD devices** (Class A, B, C, D) — `IVD_RULES`
- **Dual MD/IVD classification** support
- **Conservative by design** — when several rules match, the highest class wins
- **Classifier prompt template** for ambiguous cases (LLM fallback)
- **Sample EDE corpus clauses** (synthetic)

### Key UAE-specific differences from SFDA

| Feature | SFDA (Saudi Arabia) | EDE (UAE) |
|---|---|---|
| Classification system | A/B/C/D (22 SFDA rules) | **I/II/III/IV (GHTF) + A/B/C/D (IVD)** |
| Dual MD/IVD | No | ✅ Yes (separate parallel systems) |
| Anti-monopoly | No | ✅ Feb 2026+ (multi-LAR/MAH) |
| Arabic prominence rule | No | ✅ Min 1.6 mm, ≥ English |
| Data localization | NDMO (cross-border) | ✅ Law 2/2019, 25-year retention, UAE storage |
| Multi-emirate layer | No (single federal) | ✅ DHA + DOH + DHCR additions |
| DOH Responsible AI | No | ✅ Oct 2025 (Abu Dhabi AI devices) |
| PSUR frequency | Annual (C/D) | ✅ Biennial (high-risk) |
| Adverse event reporting | 10 days | ✅ 5 days |
| Fixed fee | No (variable) | ✅ AED 5,000 + 100 |
| Fixed timeline | No (variable) | ✅ 45 business days |

_Regulatory details are research notes and have not been verified against official sources._

## 🚀 Quick start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the tests
pytest

# 3. Try the EDE classification engine
python src/ede_classification.py
# → classifies the sample MRI system as Class III per EDE-MD-R13

# 4. Run the pre-check on the sample submission (from the repository root)
python -m src.main --submission data/sample_submission/sample_package.json

# 5. Optional: web UI
pip install -r web_ui/requirements.txt
streamlit run web_ui/app.py
```

The deterministic checks (classification, checklist, multi-LAR, data localization, audit chain) run without an API key. To enable LLM-based evidence validation, copy `.env.example` to `.env` and set `COHERE_API_KEY`.

## 📊 Current state

- **Status**: v0.2 — YAML-driven state machine, deterministic classification and checklists, hash-chain audit log, CLI and web UI
- **Implemented**: EDE classification engine, classifier / checklist / ingest / evidence validator / excel logger / regulatory watcher / orchestrator agents, multi-LAR verifier, data localization checker, Arabic prominence heuristic, 41 tests
- **Not yet implemented**: L2 tool-based clause lookup, re-validation after regulation changes, Arabic NLP pipeline, UAE PASS, official regulatory corpus — see [`docs/roadmap.md`](docs/roadmap.md)

## 🗂️ Repository layout

```
EDE-Regulatory-Compliance-Agent/
├── README.md
├── DISCLAIMER.md                              ← Demonstration-only terms and user responsibility
├── LICENSE                                    ← MIT
├── requirements.txt
├── .env.example
├── .gitignore
│
├── docs/
│   ├── PLAN.md                                ← UAE research notes (MOHAP → EDE, GHTF, multi-emirate)
│   ├── BEHAVIOR_AND_ATTENTION.md              ← 12 UAE refinements + behavior + attention
│   ├── architecture.md                        ← Detailed architecture
│   └── roadmap.md                             ← v0.2 → v1.0 roadmap
│
├── src/
│   ├── main.py                                ← CLI entry point (python -m src.main)
│   ├── ede_classification.py                  ← EDE classification rules (GHTF MD + IVD)
│   ├── state_machine.py                       ← YAML-driven state machine
│   ├── context_packet.py                      ← Context packet builder
│   ├── agents/
│   │   ├── orchestrator.py                    ← User messages + transition logic
│   │   ├── ingest.py                          ← PDF / DOCX / JSON / OCR ingest
│   │   ├── classifier.py                      ← Deterministic first, LLM fallback
│   │   ├── checklist.py                       ← MD + IVD + multi-emirate checklist
│   │   ├── evidence_validator.py              ← Clause-level validation (LLM)
│   │   ├── excel_logger.py                    ← Hash-chain audit log
│   │   └── regulatory_watcher.py              ← Document version tracking
│   ├── retrieval/                             ← BGE-M3 embeddings, ChromaDB store, Cohere Rerank
│   ├── prompts/                               ← Classifier, evidence validator, orchestrator templates
│   └── utils/
│       ├── audit.py                           ← Hash chain validator
│       ├── multi_lar_verifier.py              ← Anti-monopoly (multi-LAR) check
│       ├── data_localization_checker.py       ← Law 2/2019 data localization check
│       ├── arabic_prominence_checker.py       ← Arabic label prominence heuristic
│       ├── excel_writer.py
│       └── config.py
│
├── web_ui/
│   └── app.py                                 ← Streamlit UI
│
├── data/
│   ├── README.md                              ← Demonstration-only data notice
│   ├── regulatory_corpus/                     ← Synthetic EDE + IMDRF sample clauses
│   ├── sample_submission/
│   │   └── sample_package.json                ← Fictional test case (MRI system → UAE EDE)
│   └── state_machine.yaml
│
├── notebooks/
│   └── demo_walkthrough.ipynb                 ← Planned end-to-end demo
│
└── tests/                                     ← Classifier, checklist, audit chain, multi-LAR
```

## ⚠️ Disclaimers

- **This project is for demonstration and testing purposes only.** It must not be used for real medical device submissions or compliance decisions.
- Sample regulatory clauses in `data/regulatory_corpus/` are **synthetic** — written for demonstration only, they do NOT represent official EDE regulatory text
- The sample submission in `data/sample_submission/` is **fictional**; names are used for illustration only
- This agent does NOT provide legal or regulatory advice, and its output is not a regulatory clearance
- **The user is solely responsible** for verifying requirements with EDE and for **all legal and regulatory obligations** arising from use of this software or decisions based on its output
- The author accepts no liability for any loss, rejection, delay or other consequence arising from its use
- This is **independent R&D**, not affiliated with or endorsed by EDE, MOHAP, DHA, DOH, DHCR or any other authority
- For actual regulatory compliance work, always consult official EDE sources (www.ede.gov.ae) and a licensed regulatory affairs professional

Full terms: [DISCLAIMER.md](DISCLAIMER.md).

## 👤 Author

**Ali Can Efe** — Medical device industry expert and advisor with 13 years of experience across different departments: product management, regulatory compliance and AI-enabled imaging, with global expertise.

## License

MIT — see [LICENSE](LICENSE).
