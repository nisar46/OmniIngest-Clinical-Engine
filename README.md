# OmniIngest — ABDM 2.0 Clinical Data Ingestion Engine

**Role:** Business Analyst & Functional Architect | **Status:** Complete (Phase 0.3)  
**Author:** Nisar Ahmed — Healthcare BA | 13+ Years Hospital Floor Operations

---

## Why I Designed This

At RK Nursing Home in Bengaluru, patient admission clerks were manually copy-pasting data from paper OPD forms into different Excel sheets. This caused a lot of issues:
- Around 30% to 40% of records had spelling mistakes, incorrect phone numbers, or missing ABHA IDs during peak clinic hours.
- Billing departments ran into errors because their records didn't match the clinical logs.
- Patient consent under the DPDP Act 2023 wasn't documented consistently, which was a regulatory risk.
- There was no audit trail showing who edited what information.

I designed the functional requirements for OmniIngest to fix these daily hospital floor failures by catching errors before they reach the main database.

---

## BA Artifacts I Wrote

To guide the engineering team, I produced the following specifications:
- **PRD v1.0:** Mapped out a three-phase ingestion pipeline: Intake, Triage, and Dispatch.
- **12 Jira User Stories:** Detailed user stories with clear acceptance criteria for validating patient records.
- **Data Flow Diagram:** Mapped the journey of patient records from paper forms and local files into clean, relational database tables.
- **UAT Checklist:** Wrote test cases covering ABHA validation rules, consent check routing, and data purge behavior.
- **7-Pillar Database Schema:** Mapped out how to organize clinical data into clean tables conforming to healthcare interoperability standards.

---

## The 7-Pillar Relational Database Schema

I designed this schema around how hospital departments share patient data:

1. **Demographics:** Patient identity, ABHA ID, and contact details.
2. **Encounters:** Visit records (OPD/IPD, treating doctor, check-in times).
3. **Observations:** Patient vitals, lab results, and doctors' notes.
4. **Medications:** Prescriptions from the hospital pharmacy.
5. **Diagnostics:** Test reports and imaging details.
6. **Finance:** Invoices, payments, and billing details.
7. **Governance:** Consent logs, audit trails, and deletion records.

---

## Key Functional Requirements

### 1. Three-Phase Pipeline (Intake → Triage → Dispatch)
- **Intake:** Incoming files are loaded into temporary memory first. Nothing is written directly to the database on arrival.
- **Triage:** The system scans the data. If a record has a missing ABHA ID or billing error, it is flagged and routed to a dedicated triage screen for a clerk to fix.
- **Dispatch:** Only clean, verified records that pass all triage steps are written to the database.

### 2. ABHA Validation Rule
- **Rule:** Every patient record must have a valid 14-digit numeric ABHA ID. If a record fails this, it is blocked from the database and sent to the clerk's Identity Desk. All clinical fields are locked until the identity error is fixed.

### 3. DPDP Act Consent Purge
- **Rule:** If a patient revokes their consent, the compliance engine must isolate their records, hard-delete the corresponding rows from the database, and log the timestamped event in the Governance audit table.

---

**Nisar Ahmed** — Bengaluru, India  
[LinkedIn Profile](https://www.linkedin.com/in/nisar-ahmed-8440763a3) | [Portfolio Site](https://nisar46.github.io/portfolio/)
