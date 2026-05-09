# 🏥 OmniIngest ABDM 2.0: The "Safety Rails" for Digital Health
> **Phase 0.2 | Governance Layer (Budget 2026 Update): Feb 01, 2026**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)
![Standard](https://img.shields.io/badge/ABDM-NRCeS_Compliant-green.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/DPDP-Rule_8.3_Kill_Switch-red.svg?style=for-the-badge)
![Governance](https://img.shields.io/badge/Governance-Compliance_Engine_v0.2-purple.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Visitors](https://api.visitorbadge.io/api/visitors?path=nisar46%2FOmnigest_ABDM_2.0&label=Views&labelColor=%232c3e50&countColor=%23008080&style=flat)

## ⚡ Executive Summary
**OmniIngest ABDM 2.0** is the architectural backbone for modern clinical data ingestion in India's federated health ecosystem. 

**v0.2 Update (Feb 2026):** In response to the **Union Budget 2026 mandates** for "AI Public Infrastructure," this version introduces a dedicated **Compliance Engine** (`compliance_engine.py`) that enforces:
1.  **Pseudonymization by Design:** Cryptographic hashing of PII for population health analytics.
2.  **Auditability:** Immutable logging of data access/purges for government transparency requirements.

### 📉 The 5-Year Practical Journey
This software is grounded in **5 years of operational fieldwork**. Between 2020 and 2025, I handled thousands of data entry challenges in **rural Bangalore healthcare**. 

👉 *Explore the full analysis of those 5 years in my detailed portfolio: [Healthcare-Data-Analysis-Journey](https://github.com/nisar46/Healthcare-Data-Analysis-Journey)*

It solves the critical "Last Mile" problem of interoperability: taking messy, unstructured legacy hospital data (CSV, PDF, HL7) and transforming it into **FHIR R5** compliant bundles, while strictly adhering to India's **DPDP Act 2023** (Digital Personal Data Protection Act).

<!-- Video Removed to reduce repo size. See LinkedIn post for demo. -->

---

## 💎 Critical Features

### 1. The "ChatGPT Health" Experience
Phase 0.1 introduces a radical shift in clinical UX. We moved away from sterile, grey enterprise dashboards to a **"Vibe-Coded"** interface:
- **Teal & Dark Mode**: Reduced eye strain for 24/7 clinical operations, inspired by premium GenAI tools.
- **Glassmorphism Metrics**: Real-time floating compliance cards.
- **Interactive "Sandbox Mode"**: One-click generation of 1000+ synthetic patient records for stress-testing.

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

## 🏗️ Technical Architecture

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Ingestion Engine** | `Polars` (Rust-based) | High-performance data cleaning & normalization. |
| **Logic Layer** | Python 3.10 | Business logic, Rule 8 enforcement. |
| **Compliance** | `fhir.resources` | Strict FHIR R5 schema validation. |
| **Interface** | `Streamlit` | Rapid, reactive UI/UX. |

---

## 📜 Regulatory alignment
This project is engineered to align with:
- **ABDM Standards**: Specifically the *Health Information Provider (HIP)* guidelines.
- **NRCeS**: Adopts the latest National Resource Centre for EHR Standards recommendations.
- **DPDP Act 2023**: Hard-coded strict adherence to Data Principal rights (Right to Erasure).

👉 *See [docs/COMPLIANCE.md](docs/COMPLIANCE.md) for a deep dive.*  
👉 *See [docs/TECH_STACK.md](docs/TECH_STACK.md) for architecture details.*

---

## 🚀 Installation & Launch

### Prerequisites
- Python 3.10+
- `pip`

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/nisar46/OmniIngest-ABDM-2.0_Phase_0.1.git
   cd OmniIngest-ABDM-2.0_Phase_0.1
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Launch the Console**
   ```bash
   streamlit run app.py
   ```

---

## 👨‍💻 Author
**Nisar Ahmed**
*Senior Health-Tech Architect*

> "Building the digital nervous system for India's healthcare future."

---
*© 2026 Nisar Ahmed. Licensed under MIT.*
