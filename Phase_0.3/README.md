# OmniIngest — Phase 0.3: The Complete Engine

**Role:** Business Analyst & Functional Architect | **Status:** Complete  
**Author:** Nisar Ahmed — 13+ years clinical operations, Bengaluru

---

## The Problem This Solves

I spent five years managing data at RK Nursing Home. Every single day, admission clerks were manually copying patient information from paper OPD forms into Excel sheets. Around 30 to 40 percent of those records came in with errors during peak hours — wrong ABHA IDs, missing consent entries, billing fields that didn't match the clinical record. Nobody noticed until billing ran end-of-month reconciliation and suddenly 200 records were in dispute.

This isn't a technology problem. It's a workflow problem. The data entry happens under pressure, between patients, with no validation happening in real time. OmniIngest Phase 0.3 was built to fix that — not by replacing the clerk, but by giving the system a way to catch and fix errors before they reach the database.

---

## How the Pipeline Works

The entire flow is: **Intake → Triage → Dispatch**. Nothing skips a step.

**Intake (the airlock)**

When a file arrives — whether it's a CSV from the OPD counter, a PDF from radiology, a JSON from the pharmacy system — it goes into temporary memory first. It never touches the database at this stage. This is by design. We needed a quarantine zone where data could be inspected before it became permanent.

**Triage (the specialist desks)**

Once in memory, the ingress engine scans every record. Two types of problems get flagged:

- Records with missing or broken ABHA IDs go to the Identity Desk. The clerk sees only the identity fields — everything else is locked. The only job is to fix the ABHA number. This prevents well-meaning clerks from accidentally editing clinical data while trying to fix an ID problem.

- Records with incomplete clinical payloads or billing flags go to the Clinical Audit Desk. The clerk sees the financial risk indicators and can edit the clinical payload and bill amount. That's it.

**Dispatch (the safe write)**

Only records that clear both triage desks get written to the database. At this point, the compliance engine runs one final check — consent status, DPDP Rule 8 validation — before the record is committed. If consent is flagged as revoked, the record never makes it to production storage.

---

## Database Structure (7-Pillar Schema)

I designed this schema based on how clinical data actually flows through a hospital, not how database textbooks say it should. Each pillar maps to a real department handoff:

| Pillar | What It Holds |
|---|---|
| Demographics | Patient identity, ABHA ID, contact details |
| Encounters | Visit records — OPD/IPD, treating doctor, dates |
| Observations | Vitals, diagnostic readings, clinical notes |
| Medications | Pharmacy prescriptions, drug codes |
| Diagnostics | Lab results, imaging records |
| Finance | Billing, insurance claims, revenue flags |
| Governance | Consent logs, DPDP audit trail, purge records |

The schema uses a hybrid relational and JSON structure so that variable fields from different departments don't crash the schema when a new data type shows up.

---

## DPDP Compliance Specs Written

**ABHA Validation Rule:** Every record must contain a 14-digit continuous numeric ABHA ID. Records failing this check are blocked from the database entirely and routed to the Identity Desk.

**Rule 8 Purge Logic:** When a patient's consent status changes to revoked, the compliance engine isolates those records, hard-deletes the rows, and logs the deletion event with a timestamp. The data is gone and cannot be recovered — which is exactly what the DPDP Act requires.

**PII Masking:** Patient names and ABHA IDs are masked before they appear on any screen unless an authorized user explicitly toggles the reveal switch. The actual database values stay intact — only the display layer is redacted.

---

## BA Artifacts Produced

- PRD v1.0 covering all three pipeline phases
- 12 Jira user stories with acceptance criteria
- Data flow diagram: OPD → Intake → Triage → Dispatch → Database
- UAT checklist covering identity validation, consent routing, and purge behavior
- 7-pillar relational database schema documentation

---

**Nisar Ahmed** — Healthcare Business Analyst | [LinkedIn](https://www.linkedin.com/in/nisar-ahmed-8440763a3) | [Portfolio](https://nisar46.github.io/portfolio/)
