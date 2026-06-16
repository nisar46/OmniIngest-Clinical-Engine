
import sqlite3
import json
import os
from datetime import datetime

# [MASTER RESET] Using a brand new name to force Streamlit to clear its cache
DB_NAME = r"D:\Omnigest_ABDM_2.0\Phase_0.3\omniingest_FINAL.db"

def init_db():
    # Force close any existing connections by creating a fresh one
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Patients Table (The "Filing Cabinet")
    c.execute('''CREATE TABLE IF NOT EXISTS patients (
        notice_id TEXT PRIMARY KEY,
        abha_id TEXT,
        patient_name TEXT,
        notice_date TEXT,
        consent_status TEXT,
        clinical_payload TEXT,
        bill_amount REAL,
        validated_icd10 TEXT,
        surgical_truth BOOLEAN,
        ingest_status TEXT,
        status_reason TEXT,
        ingest_timestmp TEXT
    )''')
    
    # Audit Table (Immutable Log)
    c.execute('''CREATE TABLE IF NOT EXISTS audit_log (
        log_id TEXT PRIMARY KEY,
        timestamp TEXT,
        action TEXT,
        details TEXT
    )''')
    
    # REGENERATE SECURE COMPLIANCE SQL VIEW
    c.execute("CREATE VIEW IF NOT EXISTS final_validated AS SELECT * FROM patients WHERE status_reason != 'CONSENT_REVOKED';")

    # ESTABLISH PERSISTENT AUDIT LOG STORAGE
    c.execute('''CREATE TABLE IF NOT EXISTS audit_events (
        timestamp TEXT,
        event_type TEXT,
        target_token TEXT,
        compliance_rule TEXT,
        operator_action TEXT
    )''')
    
    conn.commit()
    conn.close()

def log_audit_event(event_type: str, target_token: str, compliance_rule: str, operator_action: str):
    """Logs a compliance action into the persistent audit_events table."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''INSERT INTO audit_events (timestamp, event_type, target_token, compliance_rule, operator_action)
                 VALUES (?, ?, ?, ?, ?)''', 
              (datetime.now().isoformat(), event_type, target_token, compliance_rule, operator_action))
    conn.commit()
    conn.close()

def save_records_bulk(records_list: list):
    """Phase 0.3 Performance Optimization: High-speed bulk insertion."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Prepare the list of tuples for sqlite executemany
        data_tuples = [
            (
                r.get('Notice_ID'), r.get('ABHA_ID'), r.get('Patient_Name'), 
                r.get('Notice_Date'), r.get('Consent_Status'), r.get('Clinical_Payload'),
                r.get('Bill_Amount', 0.0), r.get('Validated_ICD10'), r.get('SURGICAL_TRUTH'),
                r.get('Ingest_Status', 'PROCESSED'), r.get('Status_Reason', 'N/A'), 
                datetime.now().isoformat()
            ) for r in records_list
        ]
        
        c.executemany('''INSERT OR REPLACE INTO patients 
                      (notice_id, abha_id, patient_name, notice_date, consent_status, clinical_payload, 
                       bill_amount, validated_icd10, surgical_truth, ingest_status, status_reason, ingest_timestmp)
                      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', data_tuples)
        conn.commit()
    except Exception as e:
        print(f"Bulk DB Error: {e}")
    finally:
        conn.close()

def get_all_records():
    conn = sqlite3.connect(DB_NAME)
    import polars as pl
    try:
        # Use pandas for easy sql read then to polars
        import pandas as pd
        df = pd.read_sql("SELECT * FROM patients", conn)
        
        # [Fix] Remap lowercase DB columns back to Canonical Schema for App compatibility
        rename_map = {
            "notice_id": "Notice_ID",
            "abha_id": "ABHA_ID",
            "patient_name": "Patient_Name",
            "notice_date": "Notice_Date",
            "consent_status": "Consent_Status",
            "clinical_payload": "Clinical_Payload",
            "bill_amount": "Bill_Amount",
            "validated_icd10": "Validated_ICD10",
            "surgical_truth": "SURGICAL_TRUTH",
            "ingest_status": "Ingest_Status",
            "status_reason": "Status_Reason"
        }
        df = df.rename(columns=rename_map)
        
        return pl.from_pandas(df)
    except Exception as e:
        return pl.DataFrame()
    finally:
        conn.close()

def hard_delete_all():
    """Rule 8.3: Targeted True SQL Delete for Revoked/Expired Records only."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM patients WHERE ingest_status = 'PURGED'")
    conn.commit()
    conn.close()

def update_patient_record(notice_id: str, abha_id: str, patient_name: str, notice_date: str, consent_status: str, clinical_payload: str, bill_amount: float, validated_icd10: str = None):
    """Updates an existing patient record in the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute('''UPDATE patients SET 
                     abha_id = ?, 
                     patient_name = ?, 
                     notice_date = ?, 
                     consent_status = ?, 
                     clinical_payload = ?, 
                     bill_amount = ?, 
                     validated_icd10 = ?
                     WHERE notice_id = ?''', 
                  (abha_id, patient_name, notice_date, consent_status, clinical_payload, bill_amount, validated_icd10, notice_id))
        conn.commit()
    except Exception as e:
        print(f"Update DB Error: {e}")
    finally:
        conn.close()

def reset_database():
    """Completely wipe the database for sandbox resets."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM patients")
    c.execute("DELETE FROM audit_log")
    conn.commit()
    conn.close()

# Start Fresh
if __name__ == "__main__":
    init_db()
else:
    init_db()
