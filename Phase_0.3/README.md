# 🏥 OmniIngest ABDM 2.0: The "Safety Rails" for Digital Health
> **Phase 2.0 | Production-Grade Interactive Governance Layer: June 2026**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)
![Standard](https://img.shields.io/badge/ABDM-NRCeS_Compliant-green.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/DPDP-Rule_8.3_Kill_Switch-red.svg?style=for-the-badge)
![Governance](https://img.shields.io/badge/Governance-Compliance_Engine_v0.3-purple.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Visitors](https://api.visitorbadge.io/api/visitors?path=nisar46%2FOmnigest_ABDM_2.0&label=Views&labelColor=%232c3e50&countColor=%23008080&style=flat)

## ⚡ Executive Summary
**OmniIngest ABDM 2.0** is an enterprise-grade clinical middleware pipeline engineered for modern clinical data ingestion in India's federated health ecosystem. 

**v2.0 Production Update (June 2026):** Upgraded from a passive chart-reporting dashboard into an **Interactive, Validation-First Clinical Data Workspace**. This version introduces bidirectional state reconciliation and absolute schema field locking to allow human-in-the-loop data repairs directly inside the processing pipeline without risk of database contamination.

### 📉 The 5-Year Practical Fieldwork Journey
This software is grounded in **5 years of clinical operations fieldwork** handling freelance/contract data streams at R K Nursing Home. Having managed thousands of production data entries, this pipeline solves the critical "Last Mile" problem of clinical interoperability. It extracts messy, unstructured legacy hospital datasets (CSV, PDF, HL7) and transforms them into clean, **HL7 FHIR R5** compliant bundles, while strictly enforcing India's **DPDP Act 2023** constraints.

👉 *Explore the full analysis of this journey in my detailed archive: [Clinical-Research-Archive](https://github.com/nisar46/Clinical-Research-Archive)*

---

## 💎 Critical Enterprise Features

### 1. Interactive Validation-First Workspace 
Moved completely away from static, passive graph-reporting to an active data remediation pipeline:
- **Executive Operations Matrix**: Basic bar charts are replaced by real-time metric cards tracking Pipeline Throughput Rate, Revenue Under Operational Hold, and Active Identity Firewall Blocks.
- **Validation-First Logic**: Harsh, definitive warnings are replaced by an auditing flag (**`PENDING_CLINICAL_AUDIT`**). High-value billing entries lacking explicit surgical confirmation are quietly routed for clinical correlation rather than triggering false-positive alerts.

### 2. Absolute Input Lockdown & Security 
Data correction is built to be secure and bulletproof against administrative error:
- **Cell-Level Freezing**: Inside the interactive editing tables (`st.data_editor`), all metadata, unique hashes, system timestamps, and calculated fields are frozen via explicit column configurations (`disabled=True`).
- **Targeted Operator Overrides**: Operators can only edit exactly four required operational target fields (`ABHA_ID`, `Patient_Name`, `Clinical_Payload`, and `Bill_Amount`).
- **High-Visibility Row Highlights**: An entire row lights up in a high-contrast amber tone if an active validation block is present, focusing operator attention precisely on what needs to be changed.

### 3. Silent Bidirectional Storage Sync
When data is corrected, the workspace acts completely frictionlessly like an automated sheet:
- **Silent SQL Persistence**: Saving a record bypasses slow text pop-ups and toasts, running a clean SQL `UPDATE` statement against the local SQLite instance using the uneditable `Notice_ID` as the immutable primary key.
- **Instant State Cleansing**: The memory cache is instantly dropped and refreshed via `st.rerun()`. Corrected rows quietly and seamlessly vanish from the Quarantine pool and reappear in the clean **FHIR R5 Validated Data Stream** instantly.

### 4. Overlapping Category Filters 
To support multi-department compliance tracking, data segregation logic relies on independent boolean vectors:
- **Shared Identity Risk Routing**: Missing or invalid 14-digit ABHA tokens are mapped across **both** the `PRIVACY_SHIELD` (as identity failure is a data privacy threat) and the `CLINICAL_VOID` tabs. If a record fails both clinical audit and identity checks, it dynamically scales into a combined hybrid label, keeping data fully visible to both clinical auditors and privacy officers simultaneously.

### 5. Guardrails: The Rule 8.3 Kill Switch
Compliance is not a checkbox; it is code.
- **Cryptographic Shredding**: Implements a dedicated "Kill Switch" that manages encryption key destruction within a decoupled PII Vault architecture, rendering encrypted database blocks mathematically unrecoverable noise upon data revocation.
- **Hard Database Purge**: SQLite rows flagged for destruction are physically expunged from the disk using targeted deletion execution scripts to strictly fulfill the Data Principal's right to erasure under the **India DPDP Act 2023**.

---

## 🏗️ Technical Stack


| Component | Technology | Role |
| :--- | :--- | :--- |
| **Ingestion Engine** | `Polars` (Rust-backed) | Vectorized string matching, high-performance regex sorting & normalization. |
| **Logic Layer** | Python 3.10 | Business logic, state allocation, Rule 8.3 enforcement. |
| **Database** | `SQLite` | Persistent storage matrix running parameterized transaction queries. |
| **Compliance** | `fhir.resources` | Strict HL7 FHIR R5 nested array name schema validation. |
| **Interface** | `Streamlit` | Rapid, reactive UI/UX displaying read-only styled layout maps. |

---

## 📜 Regulatory Alignment
This pipeline is engineered to align with:
- **ABDM Standards**: Maps records cleanly to the *Health Information Provider (HIP)* architecture milestones.
- **NRCeS**: Enforces recommendations from the National Resource Centre for EHR Standards.
- **DPDP Act 2023**: Incorporates strict, hard-coded adherence to user consent policies (Crypto-shredding + Hard Purges).

---

## 🚀 Installation & Launch

### Prerequisites
- Python 3.10+
- `pip`

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com/nisar46/OmniIngest-Clinical-Engine.git
   cd OmniIngest-Clinical-Engine/Phase_2.0
   pip install -r requirements.txt
   streamlit run app.py
   ```

---

## 👨‍💻 Developer & Data Specialist
**Nisar Ahmed**  
*Clinical Data Analyst*  
*Specialized Advanced Training: IIT Kanpur (Medical Gen AI) & IIT Guwahati*  

"Building the secure, interoperable data infrastructure for India's healthcare future."

---
*© 2026 Nisar Ahmed. Licensed under MIT.*
