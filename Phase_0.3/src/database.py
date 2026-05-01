def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Pillar 1: Demographics (PII Isolation)
    # We use ABHA_ID or Notice_ID as the anchor
    c.execute('''CREATE TABLE IF NOT EXISTS demographics (
        abha_id TEXT PRIMARY KEY,
        patient_name TEXT,
        notice_date TEXT,
        consent_status TEXT
    )''')
    
    # Pillar 3: Observations (Clinical Data - No Names here!)
    c.execute('''CREATE TABLE IF NOT EXISTS observations (
        obs_id INTEGER PRIMARY KEY AUTOINCREMENT,
        abha_id TEXT, 
        clinical_payload TEXT,
        ingest_timestamp TEXT,
        FOREIGN KEY (abha_id) REFERENCES demographics (abha_id)
    )''')
    
    # Pillar 7: Governance (Rule 8.3 Audit Log)
    c.execute('''CREATE TABLE IF NOT EXISTS governance_audit (
        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT, 
        target_abha_id TEXT,
        timestamp TEXT
    )''')
    
    conn.commit()
    conn.close()

def rule_8_3_incinerator(abha_id):
    """Rule 8.3: Hard SQL Delete across all pillars."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Log the destruction (Compliance requirement)
    c.execute("INSERT INTO governance_audit (action, target_abha_id, timestamp) VALUES (?, ?, ?)",
              ("HARD_DELETE_PURGE", abha_id, datetime.now().isoformat()))
    
    # 2. Delete clinical data first
    c.execute("DELETE FROM observations WHERE abha_id = ?", (abha_id,))
    
    # 3. Delete PII last
    c.execute("DELETE FROM demographics WHERE abha_id = ?", (abha_id,))
    
    conn.commit()
    conn.close()
    print(f"🔥 Rule 8.3: Patient {abha_id} completely incinerated from the vault.")
