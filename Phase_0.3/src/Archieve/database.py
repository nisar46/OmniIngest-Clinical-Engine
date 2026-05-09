import sqlite3
import os
from datetime import datetime

DB_NAME = "omnigest_vault.db"

def init_db():
    """Initializes the 7-Pillar Vault Architecture with PII Isolation."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Pillar 1: Demographics (PII Isolation - Identifiable Data)
    c.execute('''CREATE TABLE IF NOT EXISTS demographics (
        abha_id TEXT PRIMARY KEY,
        patient_name TEXT,
        notice_date TEXT,
        consent_status TEXT
    )''')
    
    # Pillar 3: Observations (Clinical Data - De-identified logic)
    c.execute('''CREATE TABLE IF NOT EXISTS observations (
        obs_id INTEGER PRIMARY KEY AUTOINCREMENT,
        abha_id TEXT, 
        clinical_payload TEXT,
        ingest_timestamp TEXT,
        FOREIGN KEY (abha_id) REFERENCES demographics (abha_id)
    )''')
    
    # Pillar 7: Governance (Rule 8.3 Audit Log - Records Actions, not Data)
    c.execute('''CREATE TABLE IF NOT EXISTS governance_audit (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT, 
        target_abha_id TEXT,
        timestamp TEXT
    )''')
    
    conn.commit()
    conn.close()

def save_record(data: dict):
    """SME Logic: Atomically splits data into Demographics and Observations."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # Update Pillar 1: Demographics
        c.execute('''INSERT OR REPLACE INTO demographics 
                  (abha_id, patient_name, notice_date, consent_status)
                  VALUES (?, ?, ?, ?)''',
                  (data.get('ABHA_ID'), data.get('Patient_Name'), 
                   data.get('Notice_Date'), data.get('Consent_Status')))
        
        # Update Pillar 3: Observations
        c.execute('''INSERT INTO observations 
                  (abha_id, clinical_payload, ingest_timestamp)
                  VALUES (?, ?, ?)''',
                  (data.get('ABHA_ID'), data.get('Clinical_Payload'), 
                   datetime.now().isoformat()))
        
        conn.commit()
    except Exception as e:
        print(f"❌ Vault Error during split-save: {e}")
    finally:
        conn.close()

def get_all_records():
    """SME Logic: Re-joins the pillars for the SME UI using Polars."""
    import polars as pl
    import pandas as pd
    conn = sqlite3.connect(DB_NAME)
    try:
        # SQL JOIN to reconstruct the view for the SME Dashboard
        query = '''
            SELECT d.abha_id as ABHA_ID, d.patient_name as Patient_Name, 
                   d.notice_date as Notice_Date, d.consent_status as Consent_Status,
                   o.clinical_payload as Clinical_Payload, o.ingest_timestamp as Ingest_Timestamp
            FROM demographics d
            JOIN observations o ON d.abha_id = o.abha_id
        '''
        df = pd.read_sql(query, conn)
        return pl.from_pandas(df)
    except Exception as e:
        print(f"❌ Vault Read Error: {e}")
        return pl.DataFrame()
    finally:
        conn.close()

def rule_8_3_incinerator(abha_id):
    """Rule 8.3: Targeted Hard SQL Delete across all clinical pillars."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        # 1. Log the destruction (Compliance requirement)
        c.execute("INSERT INTO governance_audit (action, target_abha_id, timestamp) VALUES (?, ?, ?)",
                  ("HARD_DELETE_PURGE", abha_id, datetime.now().isoformat()))
        
        # 2. Delete clinical data first (Observations)
        c.execute("DELETE FROM observations WHERE abha_id = ?", (abha_id,))
        
        # 3. Delete PII last (Demographics)
        c.execute("DELETE FROM demographics WHERE abha_id = ?", (abha_id,))
        
        conn.commit()
        print(f"🔥 Rule 8.3: Patient {abha_id} completely incinerated from the vault.")
    except Exception as e:
        print(f"❌ Incinerator Failure: {e}")
    finally:
        conn.close()
