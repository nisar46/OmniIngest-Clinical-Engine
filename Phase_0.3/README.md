# 🏥 OmniIngest ABDM 2.0: The "Safety Rails" for Digital Health
> **Phase 0.3 | Governance Layer (Budget 2026 Update): Feb 01, 2026**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)
![Standard](https://img.shields.io/badge/ABDM-NRCeS_Compliant-green.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/DPDP-Rule_8.3_Kill_Switch-red.svg?style=for-the-badge)
![Governance](https://img.shields.io/badge/Governance-Compliance_Engine_v0.3-purple.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Visitors](https://api.visitorbadge.io/api/visitors?path=nisar46%2FOmnigest_ABDM_2.0&label=Views&labelColor=%232c3e50&countColor=%23008080&style=flat)

## ⚡ Executive Summary
**OmniIngest ABDM 2.0** is the core data pipeline for modern clinical data ingestion in India's federated health ecosystem. 

**v0.3 Update (Feb 2026):** In response to the **Union Budget 2026 mandates** for "AI Public Infrastructure," this version introduces a dedicated **Compliance Engine** (`compliance_engine.py`) that enforces:
1.  **Pseudonymization by Design:** Cryptographic hashing of PII for population health analytics.
2.  **Auditability:** Immutable logging of data access/purges for government transparency requirements.

### 📉 The 13-Year Practical Journey
This software is grounded in **13+ years of clinical operations fieldwork**. Having handled thousands of data entry challenges and managed facility workflows, this pipeline solves the critical "Last Mile" problem of interoperability. It takes messy, unstructured legacy hospital data (CSV, PDF, HL7) and transforms it into clean, **FHIR R5** compliant bundles, while strictly adhering to India's **DPDP Act 2023**.

👉 *Explore the full analysis of this journey in my detailed archive: [Clinical-Research-Archive](https://github.com/nisar46/Clinical-Research-Archive)*

---

## 💎 Critical Features

### 1. Modern Data UX
We moved away from sterile, grey enterprise dashboards to a modern interface designed for fast clinical operations:
- **Teal & Dark Mode**: Reduced eye strain for 24/7 clinical operations.
- **Glassmorphism Metrics**: Real-time floating compliance cards.
- **Interactive "Sandbox Mode"**: One-click generation of 1000+ synthetic patient records for stress-testing data pipelines.

![Clinical Dashboard](docs/assets/clinical_dashboard.png)

### 2. Guardrails: The Rule 8.3 Kill Switch
Compliance is not a checkbox; it is code.
- **Cryptographic Shredding**: Implements a dedicated "Kill Switch" that overrides retention policies for immediate PII erasure.
- **Audit Lineage**: Even when data is purged, the *fact* of the purge is cryptographically logged in `audit_2026.json` with a unique Audit ID, ensuring regulatory transparency without retaining the sensitive data itself.
- **Visual Feedback**: The UI actively demonstrates the shredding process with a 3-step visible governance log.

![Rule 8.3 Kill Switch](docs/assets/rule_8_3_log.png)

### 3. Zero-Failure Smart Ingress
The `ingress.py` engine is built to never crash:
- **Universal Field Recovery**: If standard column mapping fails, the engine scans the entire file content using regex patterns to "rescue" critical identifiers like ABHA IDs.
- **Format Agnostic**: Seamlessly handles JSON, XML, XL7, FHIR, PDF, and deeply nested CSVs.

---

## 🏗️ Technical Stack

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Ingestion Engine** | `Polars` (Rust-based) | High-performance data cleaning & normalization. |
| **Logic Layer** | Python 3.10 | Business logic, Rule 8 enforcement. |
| **Compliance** | `fhir.resources` | Strict FHIR R5 schema validation. |
| **Interface** | `Streamlit` | Rapid, reactive UI/UX. |

---

## 📜 Regulatory alignment
This pipeline is engineered to align with:
- **ABDM Standards**: Specifically the *Health Information Provider (HIP)* guidelines.
- **NRCeS**: Adopts the latest National Resource Centre for EHR Standards recommendations.
- **DPDP Act 2023**: Hard-coded strict adherence to Data Principal rights (Right to Erasure).

---

## 🚀 Installation & Launch

### Prerequisites
- Python 3.10+
- `pip`

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/nisar46/OmniIngest-Clinical-Engine.git
   cd OmniIngest-Clinical-Engine/Phase_0.3
   pip install -r requirements.txt
   streamlit run app.py
   

## 👨💻 Developer & Data Specialist
**Nisar Ahmed**  
*Clinical Data Specialist 
"Building the data pipelines for India's healthcare future."

---
*© 2026 Nisar Ahmed. Licensed under MIT.*

