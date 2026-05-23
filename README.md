# ⚙️ OmniIngest: Clinical Data Ingestion & Quality Control Pipeline
> **Status: Phase 0.3 | Automated Data Cleansing & ABDM Ingestion Pipeline**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)
![Governance](https://img.shields.io/badge/Governance-ABDM_Native-0284C7.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/DPDP-Rule_8.3_Kill_Switch-red.svg?style=for-the-badge)

## ⚡ Executive Summary
**OmniIngest** is a high-performance clinical data pipeline designed to solve the "Dark Data" crisis in fragmented healthcare environments. It uses Python to extract, clean, and transform unstructured clinical records (PDF, CSV, HL7) into type-safe, **ABDM-compliant** database streams. 

Built with a **Privacy-by-Design** philosophy, OmniIngest delivers robust data normalization at scale, serving as the foundational ETL (Extract, Transform, Load) layer for high-integrity healthcare analytics.

---

### 🗄️ Core Database Schema: The 7-Pillar Relational Model
The pipeline ingests and cleans fragmented legacy records, mapping them into a structured relational database:
1. **Demographics:** PII-isolated identity management.
2. **Encounters:** Clinical visit metadata.
3. **Observations:** Vitals and diagnostic results.
4. **Medications:** FHIR-compliant pharmacy streams.
5. **Diagnostics:** Lab and imaging records.
6. **Finance:** Billing and insurance mapping.
7. **Governance:** Audit trails and DPDP-compliant logs.

---

### 🛡️ Privacy & Compliance (DPDP Act Rule 8.3)
Compliance is baked into the data pipeline:
- **Autonomous Shredding**: Python logic-based cryptographic erasure of PII.
- **Rule 8.3 Governance**: Real-time audit logs ensuring that Data Principal rights (Right to Erasure) are respected natively in the database.
- **Interoperability**: Designed for **HL7 FHIR R5** compliance to bridge the gap between rural clinics and global registries.

---

## 🚀 Get Started
1. **Clone & Setup**
   ```bash
   git clone https://github.com/nisar46/OmniIngest-Clinical-Engine.git
   pip install -r requirements.txt
streamlit run app.py
👨💻 Developer & Data Specialist
Nisar Ahmed
Clinical Data Specialist | 13+ Years Healthcare Expert
LinkedIn Profile

© 2026 Nisar Ahmed. Licensed under MIT.
