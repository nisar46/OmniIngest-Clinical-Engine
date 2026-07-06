# ⚙️ OmniIngest — ABDM 2.0 Clinical Data Ingestion Engine

> **Role:** Business Analyst & Functional Architect | **Status:** Completed (Phase 0.3)
> **Author:** Nisar Ahmed — Healthcare BA | 13+ Years Clinical Operations

---

## 📌 The Clinical Problem (What This Solves)

At RK Nursing Home, patient admission clerks manually re-entered data from paper OPD forms into disconnected Excel sheets. This created:
- ABHA ID mismatches and missing entries on 30–40% of records during peak hours
- Billing discrepancies due to misaligned clinical and finance data
- DPDP Act 2023 consent documentation gaps — creating regulatory liability
- Zero audit trail for data corrections made by clerks

This repository documents the **functional specifications, user stories, database schema design, and compliance logic** I defined as Business Analyst to solve these floor-level failures.

---

## 📋 BA Artifacts Produced

| Artifact | Description |
|---|---|
| **PRD v1.0** | Product Requirements Document — defines the 3-phase pipeline: Intake → Triage → Dispatch |
| **12 Jira User Stories** | Full backlog with acceptance criteria for each ingestion rule |
| **Data Flow Diagram** | Maps clinical floor data sources → ingestion pipeline → relational database |
| **UAT Checklist** | Acceptance testing criteria for ABHA validation, consent routing, and purge logic |
| **7-Pillar Database Schema** | Relational model translating clinical workflows into FHIR R5-compliant tables |

---

## 🗄️ Core Database Schema: The 7-Pillar Relational Model

Designed to map messy clinical floor data into a structured, queryable system:

| Pillar | Clinical Purpose |
|---|---|
| **1. Demographics** | PII-isolated patient identity management (ABHA-linked) |
| **2. Encounters** | Clinical visit metadata — OPD/IPD, treating doctor, timestamps |
| **3. Observations** | Vitals, diagnostic results, clinical notes |
| **4. Medications** | FHIR-compliant pharmacy prescription streams |
| **5. Diagnostics** | Lab and imaging record mapping |
| **6. Finance** | Billing, insurance mapping, revenue-under-hold flags |
| **7. Governance** | Audit trails, DPDP consent logs, Rule 8 purge records |

---

## 🛡️ Key Functional Specifications Written

### ABHA Identity Validation Rule
- **Acceptance Criteria:** Every patient record MUST contain a valid 14-digit continuous numeric ABHA ID. Any record failing this check is routed to the Identity Desk — all other fields are locked until the ABHA anomaly is resolved by the clerk.

### DPDP Act Rule 8 — Consent-Based Purge Logic
- **Acceptance Criteria:** Records tagged `CONSENT_REVOKED` must be isolated and hard-deleted from the database. The purge mechanism must render the data unrecoverable and log the deletion event in the Governance audit table.

### 3-Phase Ingestion Pipeline (Intake → Triage → Dispatch)
1. **Intake (Memory Airlock):** Incoming files are loaded into temporary memory — data is NEVER written to the database on receipt.
2. **Triage (Segmented Workflow):** In-memory data is scanned and split — invalid records go to the Identity Desk or Clinical Audit Desk for manual correction.
3. **Dispatch (Secure Filing):** Only records clearing Triage are written to the secure relational backend.

---

## 👨‍💼 About the Author

**Nisar Ahmed**
*Healthcare Business Analyst | Clinical Product Owner | 13+ Years Hospital Floor Experience*

[LinkedIn](https://www.linkedin.com/in/nisar-ahmed-8440763a3) | [Portfolio](https://nisar46.github.io/portfolio/)

---
*© 2026 Nisar Ahmed. Licensed under MIT.*
