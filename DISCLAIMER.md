# Legal Disclaimer and Terms of Use

**EDE Regulatory Compliance Agent**
Last updated: 2026-09-24 · Version 1.0

> **Summary.** An AI pre-check agent for UAE medical device submissions. This project is provided for **demonstration and testing purposes only**. It is **not** legal, regulatory or medical advice, and its output is not a regulatory clearance or approval. All content is sample content. **All responsibility for any use of this software, and all legal and regulatory obligations arising from it, rests solely with the user.**

---

## 1. General Disclaimer

### 1.1 Not Professional Advice

This software — including its source code, command-line tools, APIs, user interfaces, documentation, rule files, data files, prompts, reports and any output it produces (together, the **"System"**) — is provided for general informational, educational and testing purposes only.

No content produced by or contained in the System:

- constitutes legal, regulatory or medical advice;
- creates a lawyer–client, consultant–client or any other professional relationship;
- replaces the opinion of a qualified lawyer or regulatory affairs professional;
- may be used as the basis for any regulatory submission, registration, labeling, market-access, clinical or legal decision, contract or declaration;
- constitutes evidence before any court, arbitral tribunal, mediator, regulator or administrative authority.

If you have a legal or regulatory question, consult a licensed and qualified lawyer or regulatory affairs professional in the relevant jurisdiction.

### 1.2 Sample Content

All content in the System is **sample content only**, including:

- the regulatory clauses in `data/regulatory_corpus/` and in `src/ede_classification.py` — **synthetic text** that does not reproduce official EDE, MOHAP, DHA, DOH, DHCR or IMDRF text;
- the classification rules — a **simplified model**, not the official EDE Classification Guidelines;
- the sample submission in `data/sample_submission/` — **fictional**, with placeholder names;
- regulation names, dates, fees, timelines, anti-monopoly, data localization and Arabic labeling requirements in the documentation — research notes **not verified** against official sources;
- checklists, classifications, findings and reports produced by the System.

None of it may be treated as definitive, current, complete or applicable to a specific situation, because:

- Medical device regulations differ between countries, emirates, free zones, authorities and sectors;
- they are amended, replaced and repealed over time, and new regulations, guidance documents and circulars are issued continuously;
- the facts of a specific case (product, parties, dates, location, sector) can fundamentally change the outcome;
- exceptions, exemptions and transitional provisions can override general rules.

### 1.3 Not a Regulatory Clearance

A result such as "no critical findings in this demo check" means only that the System found no issues against its sample corpus and simplified rules. It does **not** mean that a submission is complete, compliant or likely to be accepted, and it is not a regulatory clearance, approval, registration or certification of any kind. The System must not be used for clinical purposes or for any decision affecting patient safety.

The System is independent and is not affiliated with, endorsed by, sponsored by or connected to the Emirates Drug Establishment (EDE), the UAE Ministry of Health and Prevention (MOHAP), the Dubai Health Authority (DHA), the Abu Dhabi Department of Health (DOH), the Dubai Healthcare City Authority (DHCR), the International Medical Device Regulators Forum (IMDRF), or any other government authority, regulator, free zone, standards body or company. Names of authorities, laws and standards are used for identification and reference only.

### 1.4 The User Is Solely Responsible

Every natural or legal person who uses the System (the **"User"**):

- must independently verify the accuracy, currency, completeness and applicability of any information, finding, classification, checklist, document list or answer obtained from the System, directly with the relevant authority;
- is **solely, entirely and irrevocably responsible** for:
  - all decisions made with or without the System;
  - all legal, regulatory, administrative, criminal, financial and commercial consequences of those decisions;
  - all obligations towards regulators, patients, customers, distributors and any other third party;
  - all actions taken or omitted in reliance on the System's output.

### 1.5 Disclaimer of Liability

To the maximum extent permitted by applicable law, the authors, contributors, licensors and distributors of the System (the **"Developers"**) shall not be liable, under any legal theory (contract, tort, negligence, strict liability, product liability, statute or otherwise), for any loss or damage — direct, indirect, incidental, special, punitive or consequential — arising from:

- the use of, or inability to use, the System;
- errors, omissions, inaccuracies or outdated content in the System;
- any action taken or not taken in reliance on the System's output;
- the rejection, delay or withdrawal of any submission, registration or market authorization, and any penalty, recall or safety incident;
- the integration of third-party services (LLM APIs, vector databases, cloud providers);
- data loss, data breaches, unauthorized access or service interruption;
- the interpretation of the System's output by the User or by third parties.

---

## 2. Risks Specific to Artificial Intelligence

### 2.1 Large Language Models

When a Cohere API key is configured, the System uses a large language model for classifications that its rules cannot decide and for evidence validation. Large language models:

- can **hallucinate** — produce fabricated but persuasive content, including non-existent rules, clauses or citations;
- can reflect **biases** in their training data;
- can produce **outdated** information;
- can **guess** instead of expressing uncertainty;
- can perform **inconsistently** across languages, in particular with Arabic regulatory terminology;
- can cite sources **out of context** or **incorrectly**.

### 2.2 Safeguards and Their Limits

The System includes the following safeguards:

- **Deterministic classification first** — rule-based classification with conservative precedence (the highest matching class wins); the model is used only when no rule matches;
- **Retrieval-grounded prompts** and a **post-process citation check** for evidence validation;
- **YAML-driven state machine** — the model never decides which step runs next; errors and uncertainty route to MANUAL_REVIEW;
- **Hash-chain audit log** — changes to the Excel audit log can be detected.

**These safeguards reduce risk; they do not eliminate it:**

- the classification rules and checklists are simplified and written by humans; they can be wrong or incomplete;
- the citation check confirms that a clause was retrieved, not that a finding is correct;
- tool-based clause lookup is not implemented;
- the Arabic prominence and data localization checks are heuristics;
- the hash chain detects changes to the log; it does not make the logged decisions correct;
- the regulatory corpus is synthetic and incomplete.

**No output of the System may serve as the basis for any regulatory, legal or clinical decision without review by a qualified professional.**

### 2.3 Acceptance of AI-Related Risks

By using the System, the User acknowledges that AI-assisted and rule-based output is inherently uncertain and may contain errors, agrees not to rely on it as the sole basis for any decision, assumes all risk for decisions based on it, and — to the maximum extent permitted by law — waives any claim against the Developers arising from such errors.

---

## 3. Data, Third-Party Services and Privacy

### 3.1 Data Sources

The System does not download official regulatory texts. The regulatory corpus in `data/regulatory_corpus/` and the clauses in `src/ede_classification.py` were written for demonstration and testing; they are **synthetic**. The regulatory watcher can fetch documents from URLs configured by the User; the Developers do not guarantee the availability, accuracy or integrity of any fetched content.

The Developers do not guarantee that any data in the System is accurate, current or complete, or that it matches any official text.

### 3.2 Third-Party Services

When configured, the System uses the **Cohere API** (chat and rerank). Optional components may use **ChromaDB**, open-source embedding models, Tesseract OCR and Streamlit.

These services are subject to their own terms of use, privacy policies and data processing terms. The Developers are not responsible for the acts, omissions, outages or data breaches of any third-party service, and any data sent to them is sent at the User's own responsibility.

### 3.3 Privacy and Data Protection

When an API key is configured, the System sends submission data, document text and retrieved clauses to the third-party LLM provider.

The User:

- **must not** enter personal, sensitive or confidential data, including patient data, personal data of employees or customers, unpublished technical files, trade secrets or real submission documents;
- must anonymize any real data before using it with the System;
- is responsible for securing all files the System writes locally (the Excel audit log, the version registry and any reports);
- is solely responsible for compliance with applicable data protection laws, including UAE Federal Decree-Law No. 45 of 2021 (PDPL), the Saudi Personal Data Protection Law and the EU GDPR where applicable.

The Developers give **no warranty** of compliance with any data protection law.

---

## 4. Sample Scenarios and Test Cases

The sample submission and any test cases are **fictional**. All device, company and product names in them are placeholders; they do not describe any real product, company or submission, and they cannot be used to resolve any real case.

---

## 5. Intellectual Property and License

- The System's source code is distributed under the **MIT License** — see [LICENSE](LICENSE).
- Names of authorities, laws, standards, products and services mentioned in the System belong to their respective owners and are used for identification only.
- Official regulatory texts, their translations, compilations and commentaries may be subject to their own copyright and terms of use.
- Anyone who copies, modifies, redistributes or integrates the System, including for commercial purposes, must keep this disclaimer with it.

---

## 6. Warranty Disclaimer

The System is provided **"as is"** and **"as available"**, without warranty of any kind, express or implied, including warranties of merchantability, fitness for a particular purpose, accuracy, non-infringement, uninterrupted operation, or that errors will be corrected.

---

## 7. Limitation of Liability

To the maximum extent permitted by applicable law, the Developers' aggregate liability for all claims arising from or related to the System is limited to the amount the User paid for the System. The System is provided free of charge; where nothing was paid, the Developers' liability is **zero**.

---

## 8. User Undertakings

By using the System, the User undertakes:

1. not to use the System's output as legal, regulatory or medical advice;
2. not to prepare, file or withdraw any regulatory submission, or take any clinical or legal action, based on the System's output without review by a qualified professional;
3. to use the System for demonstration, education, research or testing only;
4. not to enter personal, sensitive or confidential data;
5. not to use the System for any unlawful purpose;
6. to accept the consequences of any errors in the System's output;
7. to keep this disclaimer with any copy or derivative of the System;
8. to have read, understood and accepted this disclaimer.

---

## 9. Governing Law and Jurisdiction

This disclaimer and any dispute arising from the use of the System are governed by the laws of the United Arab Emirates as applied in the Emirate of Dubai. The courts of Dubai have exclusive jurisdiction, unless mandatory law provides otherwise.

If any provision of this disclaimer is held invalid or unenforceable, it shall be limited to the minimum extent necessary, and the remaining provisions shall remain in full force and effect.

---

## 10. Changes

The Developers may amend this disclaimer at any time without notice. Changes take effect when published in this repository. Continued use of the System constitutes acceptance of the amended disclaimer.

---

## 11. Contact

Questions about this disclaimer can be raised through the repository's issue tracker: https://github.com/Alicanefee/EDE-Regulatory-Compliance-Agent/issues

---

## Final Word

This System is a **tool** for demonstration and testing. It is **not** a regulator, a conformity assessment body, a regulatory consultant, a law firm or a lawyer. It does **not** protect you from legal liability — **all responsibility arising from its use rests with you.**

*By using the System, you confirm that you have read, understood and accepted this disclaimer.*
