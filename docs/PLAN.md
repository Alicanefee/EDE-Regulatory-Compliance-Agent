# UAE EDE Medical Device Regulation — Research Report

> Research notes on the UAE medical device regulatory landscape, written to be implementable at engineering level.
> Last updated: 2026-09-24
> Key finding: the MOHAP → EDE transition (Federal Decree-Law No. 38 of 2024, in force 2 January 2025)
>
> ⚠️ Research notes for a demonstration project. Not verified against official sources — see [DISCLAIMER.md](../DISCLAIMER.md).

---

## 1. Key Regulatory Change: MOHAP → EDE Transition

The most significant recent development in the UAE is the transfer of medical device regulatory authority from **MOHAP (Ministry of Health and Prevention) to EDE (Emirates Drug Establishment)**.

**Legal basis:** **Federal Decree-Law No. 38 of 2024**, in force since 2 January 2025, established EDE as the federal authority regulating all medical products, including medical devices and IVDs. It repealed the previous Federal Law No. 8 of 2019.

**Transferred services:** EDE took over 44 core regulatory services previously run by MOHAP, including product registration, renewals, variations, pharmacovigilance, import permits and post-market compliance.

**Application portal:** All applications are submitted through EDE's digital portal (www.ede.gov.ae).

> **⚠️ Critical for the AI agent:** The knowledge base must contain only current EDE documents. Legacy MOHAP documents may be kept for reference but must not be used in decision-making.

## 2. Classification System: GHTF-Aligned, 4 Classes

The UAE uses the **Global Harmonization Task Force (GHTF)** classification framework (unlike Saudi Arabia — Saudi A/B/C/D, UAE I/II/III/IV).

### Medical Devices (MD)
| Class | Risk | Examples | Route |
|---|---|---|---|
| **Class I** | Low | Surgical gloves, thermometer | Listing |
| **Class II** | Low-moderate | Blood pressure monitor, wheelchair | Full registration |
| **Class III** | Moderate-high | X-ray, dialysis, imaging | Comprehensive conformity evidence |
| **Class IV** | High | Heart valve, implantables | Most comprehensive + human approval |

### IVD Devices
| Class | Risk |
|---|---|
| **Class A** | Low |
| **Class B** | Low-moderate |
| **Class C** | Moderate-high |
| **Class D** | High |

### Classification Criteria
- Intended use
- Duration of use
- Degree of invasiveness
- Active functions

> **For the AI agent:** The classification engine must use the **EDE Classification Guidelines** (instead of SFDA MDS-G008).

## 3. Registration Process and Required Documents

### Registration Routes
| Route | Devices | Assessment |
|---|---|---|
| **Listing Route** | Class I | Simplified, Listing Certificate |
| **Registration Route** | Class II, III, IV | Comprehensive technical committee review |

### Registration Steps
1. Appoint a LAR/MAH (licensed company established in the UAE)
2. Manufacturer site registration (for first-time importers)
3. Product classification (official classification letter from EDE)
4. Prepare the registration dossier (technical file, safety, performance, clinical, CE/FDA)
5. Apply on the EDE portal (UAE PASS login, form, documents, fee)
6. Assessment and approval (45 business days)
7. Certificate issued (valid for 5 years)

### Required Documents
**Core:**
- Application form (signed and stamped)
- Copy of the manufacturer's factory registration certificate
- Free sale certificate from the country of origin (attested by the UAE embassy)
- Copy of the product agency agreement
- Quality conformity certificate / marketing authorization (CE, 510(k), PMA)
- Product information (description, formulation, types, sizes, models, accessories, uses, side effects, contraindications, warnings, precautions, instructions for use, packaging photos, brochures)
- Declaration of Conformity (EC Declaration of Conformity)
- Safety and effectiveness data (Class III and IV)

**Additional:**
- MDEL of the UAE representative/importer
- Letter of authorization from the manufacturer
- Passport copies of the applicant
- ISO 13485 certificate
- CE certificate or U.S. FDA approval

### Fees and Timelines
| Service | Fee | Timeline |
|---|---|---|
| Application | AED 100 | — |
| Device registration | AED 5,000 | 45 business days |
| Renewal | AED 250 | 15 business days |

### Critical Requirements
- The **MAH (Marketing Authorization Holder)** must be registered with EDE
- A **medical warehouse or marketing office** licensed by EDE
- **February 2026 anti-monopoly mechanism:** multiple agents are required for every medical product. The sole-distributorship model has ended.

## 4. AI/SaMD Regulation

### Legal Framework

**Federal level:**
- **Federal Decree-Law No. 38 of 2024** — Medical products, the pharmacy profession and pharmaceutical establishments. Covers SaMD.
- **Federal Law No. 2 of 2019** — Use of ICT in health fields. Requires local storage of health data (medical records retained for at least 25 years).
- **Federal Decree-Law No. 45 of 2021** — Personal Data Protection Law (PDPL). Health data is sensitive personal data.

**Emirate level:**
- **Dubai Health Authority (DHA)** — Dubai health services and digital health platforms
- **Abu Dhabi Department of Health (DOH)** — published the **Responsible AI Standard** in October 2025
- **Dubai Healthcare City Authority (DHCR)** — the only free zone with its own regulatory authority

### SaMD Classification
| Class | SaMD example |
|---|---|
| Class I | Basic administrative software |
| Class II | Vital sign monitors |
| Class III | Diagnostic imaging analysis |
| Class IV | Critical clinical decision support systems |

### AI-Specific Requirements
- Under the **National AI Strategy 2031**, EDE has established registration pathways for AI-enabled devices
- **Wearable and AI-based devices** are defined as "Medical Equipment" under Federal Decree-Law No. 38 of 2024
- **AI-enabled devices are subject to increasing scrutiny**
- **Cybersecurity documentation is mandatory** — gaps cause significant delays

## 5. Labeling and Language Requirements

- **Arabic labeling is mandatory** (on all medical device labels)
- **Arabic text must be at least as prominent as English text** (minimum 1.6 mm text height)
- **Both Arabic and English** for most product categories
- The **IFU** must be provided in Arabic and English; Arabic labeling may be applied as a sticker

> **For the AI agent:** Label and IFU checks must cover **language and format** requirements, not just content. This is a check dimension the SFDA version does not have.

## 6. Post-Market Surveillance

EDE is fully responsible for medical device post-market surveillance from 2026.

| Requirement | Detail |
|---|---|
| **PSUR** | **Every two years** for high-risk devices (annual in Saudi Arabia) |
| **Adverse event reporting** | **Within 5 days** for serious incidents (10 days in Saudi Arabia) |
| **Field Safety Corrective Action** | The manufacturer must provide a Field Safety Notice |
| **Federal Decree-Law 27/2026** | Good Pharmacovigilance Practice standard (July 2026) |

## 7. Free Zones and Emirate Differences

| Authority | Scope | Characteristics |
|---|---|---|
| **EDE** | Federal | The single federal authority valid across the UAE |
| **DHA** | Dubai | Dubai health services and digital health platforms |
| **DOH** | Abu Dhabi | Abu Dhabi health services + Responsible AI Standard |
| **DHCR** | Dubai Healthcare City | The only free zone with its own regulatory authority |

**Important:** Even where free zones have local regulations, **EDE approval is mandatory** for products to be sold on the UAE mainland.

## 8. SFDA vs EDE: Comparison

| Feature | SFDA (Saudi Arabia) | EDE (UAE) |
|---|---|---|
| Regulatory authority | SFDA | EDE (formerly MOHAP) |
| Primary law | MDS-G5, MDS-G008 | Federal Decree-Law No. 38 of 2024 |
| Classification | Class A, B, C, D | Class I, II, III, IV (MD); A, B, C, D (IVD) |
| Classification system | SFDA 22 rules | GHTF-aligned |
| Registration timeline | Variable | 45 business days |
| Registration fee | Variable | AED 5,000 + AED 100 |
| Validity | 5 years | 5 years |
| Local representative | AR | LAR/MAH |
| AI regulation | MDS-G010, MDS-G27 | Federal Decree-Law No. 38 + Responsible AI Standard |
| Language | Arabic + English | Arabic + English (Arabic ≥ English prominence) |
| Anti-monopoly | None | Multiple-agent requirement from February 2026 |
| PSUR frequency | Annual (C/D) | Every two years (high risk) |
| Adverse event | 10 days | 5 days |

## 9. Adaptation Plan for the UAE Agent

### What changes
| Component | SFDA | UAE EDE |
|---|---|---|
| Regulatory authority | SFDA | EDE |
| Primary law | MDS-G5, MDS-G008 | Federal Decree-Law No. 38 of 2024 |
| Classification document | MDS-G008 (22 rules) | EDE Classification Guidelines |
| AI guidance | MDS-G010, MDS-G27 | Federal Decree-Law No. 38 + Responsible AI Standard |
| Registration portal | SFDA MDMA | EDE Portal (www.ede.gov.ae) |
| Fee | Variable | AED 5,000 + AED 100 |
| Timeline | Variable | 45 business days |
| Local representative | AR | LAR/MAH |
| Anti-monopoly | None | Multiple-agent requirement |

### New checks to add
1. **Emirate-specific checks:** DHA, DOH and DHCR requirements
2. **Multiple-agent check:** more than one agent appointed as of February 2026
3. **Data localization check:** health data stored in the UAE (Federal Law No. 2 of 2019)
4. **Arabic label check:** prominence and size (min 1.6 mm)
5. **PSUR tracking:** two-year schedule for high-risk devices

### What stays the same
- Deterministic state machine
- Fixed vector schema (BGE-M3, 1024 dim)
- Excel-based logging
- Source separation (EDE documents vs user documents)
- Hallucination prevention (no output without a source)
- Human approval (Class III/IV)
- Large document strategy (hierarchical summarization)

## 10. Current EDE Document List

| Document | Description | Status |
|---|---|---|
| **Federal Decree-Law No. 38 of 2024** | Primary law | In force (2 January 2025) |
| **Classification of a Product Guidelines** | Classification guidance | 2024 update |
| **Registration of Medical Equipment** | Registration service | On the EDE portal |
| **Manufacturer Site Registration** | Manufacturer registration | Renewed every 5 years |
| **Standard on Medical Device Reporting (MDR)** | Reporting standard | July 2026 revision |
| **Federal Decree-Law 27/2026** | Pharmacovigilance standard | July 2026 |
| **Responsible AI Standard** | Abu Dhabi DOH | October 2025 |
