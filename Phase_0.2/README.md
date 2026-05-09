# 🏗️ Phase 0.2: The Orchestration Layer (Specialized Engineering)
> **Status: Modular Refactor | Governance & Departmental Logic**

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=for-the-badge&logo=python)
![Standard](https://img.shields.io/badge/ABDM-NRCeS_Compliant-green.svg?style=for-the-badge)
![Security](https://img.shields.io/badge/DPDP-Rule_8.3_Kill_Switch-red.svg?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Active-brightgreen)


## ⚡ Executive Summary
In Phase 0.2, I refactored the initial "Monolith" into a modular **Orchestration Layer**. This version introduces a dedicated **Compliance Engine** (`compliance_engine.py`) and a specialized **Ingress Department** to handle complex clinical data streams.

### 📉 The 6-Year Practical Journey
This software is grounded in **6 years of clinical data operations (2020–2026)**. Having handled thousands of real-world records at **Rural Healthcare Setups**, I designed this layer to solve the "Last Mile" problem: transforming messy, unstructured hospital data into **FHIR R5** compliant bundles.

👉 *Explore my full 6-year professional evolution: https://github.com/nisar46/Clinical-Research-Archive*

---

## 💎 Critical Features

### 1. Departmental Architecture (The Specialist Model)
We moved away from a single-file system to a modular "Department" structure:
- **The Translator (`universal_adapter.py`)**: Handles 10+ clinical formats.
- **The Nurse (`ingress.py`)**: Performs data hygiene and "Smart-Scan" field recovery.
- **The Security Guard (`compliance_engine.py`)**: Enforces DPDP rules and FHIR nesting.

### 2. Guardrails: The Rule 8.3 Kill Switch
- **Cryptographic Masking**: Implements a dedicated "Kill Switch" for immediate PII isolation in the session state.
- **Audit Lineage**: Every purge is tracked in a governance log, ensuring regulatory transparency as per the **DPDP Act 2023**.

### 3. Zero-Failure Smart Ingress
The `ingress.py` engine is built for the "Ground Truth" of hospital data:
- **Heuristic Recovery**: If standard headers fail, the engine uses regex patterns to "rescue" critical identifiers like ABHA IDs.
- **Format Agnostic**: Seamlessly handles JSON, XML, HL7, FHIR, and Clinical PDFs.

---

## 🏗️ Technical Architecture


| Component | Technology | Role |
| :--- | :--- | :--- |
| **Ingestion Engine** | `Polars` | High-performance data cleaning & normalization. |
| **Logic Layer** | Python 3.10 | Business logic & Rule 8.3 enforcement. |
| **Compliance** | `fhir.resources` | Strict FHIR R5 schema validation. |
| **Interface** | `Streamlit` | Modern, reactive Clinical UI. |

---

## 🚀 Installation & Launch

### Setup
1. **Clone the repository**
   ```bash
   git clone https://github.com
   cd OmniIngest-Clinical-Engine/Phase_0.2
   ```

2. **Install & Run**
   ```bash
   pip install -r requirements.txt
   streamlit run app.py
   ```

---

## 👨‍💻 Author
**Nisar Ahmed**  
*Clinical Subject Matter Expert (SME)*

---
*© 2026 Nisar Ahmed. Licensed under MIT.*
