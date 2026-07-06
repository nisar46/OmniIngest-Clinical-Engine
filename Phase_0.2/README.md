# OmniIngest — Phase 0.2: Breaking the Monolith

**Role:** Business Analyst | **Status:** Complete

---

## What Changed from Phase 0.1

Phase 0.1 worked, but it was one big file doing everything at once. That's fine for testing, but it breaks the moment someone from pharmacy asks for something slightly different than what the hospital ward needs. So I stopped and redesigned it.

Phase 0.2 splits the pipeline into specialist modules — each one does one job well. This came directly from watching how hospital departments actually hand off data. The ward nurse doesn't care about insurance billing fields. The billing clerk doesn't care about vitals. So why should a single script try to handle both at once?

---

## What Each Module Does

**universal_adapter.py — The Translator**

This handles the messy part: different departments send data in different formats. CSV from the OPD counter. PDF from the radiology lab. HL7 from the pharmacy. JSON from the billing system. This module reads all of them and brings them into one consistent structure before anything else touches the data.

**ingress.py — The Intake Nurse**

Once data is in a consistent structure, this module runs the quality checks. It looks for missing ABHA IDs, incomplete consent records, and fields that don't match the expected clinical formats. If something is wrong, it doesn't just crash — it flags the record and routes it to the right triage desk so a clerk can fix it manually.

**compliance_engine.py — The Governance Layer**

This is where the DPDP Act rules actually get enforced. Every record that comes through here gets checked against Rule 8 — does this patient have active consent? If not, the record is quarantined. If consent is later revoked, the engine handles the cryptographic purge. Nothing gets written to the database until this module signs off.

---

## Why I Designed It This Way

The biggest problem in hospital data work is that errors in one department's data corrupt records for everyone else. By separating each function into its own module, a failure in the pharmacy feed doesn't touch the ward records. Each module can be tested, fixed, or upgraded without breaking the rest.

This is the architecture that eventually became the foundation for Phase 0.3 and the full OmniIngest engine.

---

## Key Acceptance Criteria Written (Jira Stories)

- Incoming records from any format must produce identical output structure before the ingress module runs
- Records with missing or malformed ABHA IDs must be routed to the Identity Desk — no direct database writes allowed
- The compliance engine must log every purge event with a timestamp before the delete executes

---

**Nisar Ahmed** — Healthcare Business Analyst | [LinkedIn](https://www.linkedin.com/in/nisar-ahmed-8440763a3) | [Portfolio](https://nisar46.github.io/portfolio/)
