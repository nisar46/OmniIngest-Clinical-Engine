import polars as pl
import os
import re
from datetime import datetime, timedelta
from .compliance_engine import ComplianceEngine
from .database import save_record

# Configuration: Mapping synonyms for messy hospital headers to Canonical schema
COLUMN_MAPPING = {
    "ID_ABHA": "ABHA_ID", "abha_id": "ABHA_ID", "Health_ID": "ABHA_ID",
    "ABHA": "ABHA_ID", "ABHA_No": "ABHA_ID", "ABHA Number": "ABHA_ID",
    "Patient_Name": "Patient_Name", "patient_name": "Patient_Name",
    "Full_Name": "Patient_Name", "Patient": "Patient_Name",
    "Consent_ID": "Notice_ID", "Notice_ID": "Notice_ID",
    "Consent": "Consent_Status", "Status": "Consent_Status",
    "Date": "Notice_Date", "Notice_Date": "Notice_Date",
    "Data": "Clinical_Payload", "Summary": "Clinical_Payload"
}

def run_ingress(file_path: str, autofill: bool = False):
    """
    Phase 0.3 Hardened Ingress.
    Orchestrates: Load -> Recover -> Compliance Check -> Vault Commit.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. Loading Phase
    try:
        if ext == '.csv':
            lf = pl.scan_csv(file_path)
        elif ext == '.json':
            lf = pl.read_json(file_path).lazy()
        elif ext == '.pdf':
            from . import ingress_pdf
            lf = ingress_pdf.extract_from_pdf(file_path).lazy()
        else:
            from .universal_adapter import parse_data_file
            df_pd = parse_data_file(file_path)
            lf = pl.from_pandas(df_pd).lazy()
    except Exception as e:
        print(f"Ingress Error: {e}")
        return pl.DataFrame()

    # 2. Canonical Normalization
    existing_cols = lf.collect_schema().names()
    cols_lower = {c.lower(): c for c in existing_cols}
    actual_mapping = {}
    for k, v in COLUMN_MAPPING.items():
        if k.lower() in cols_lower:
            actual_mapping[cols_lower[k.lower()]] = v
    
    q = lf.rename(actual_mapping)
    target_fields = ["ABHA_ID", "Patient_Name", "Clinical_Payload", "Consent_Status", "Notice_ID", "Notice_Date"]
    
    current_cols = q.collect_schema().names()
    for f in target_fields:
        if f not in current_cols:
            fill_val = "2026-01-01" if f == "Notice_Date" else f"AUTO_{f}"
            q = q.with_columns(pl.lit(fill_val).alias(f))

    # 3. Compliance & Status Logic
    engine = ComplianceEngine()
    df = q.collect()
    
    # Audit statuses (DPDP Rule 3 & 8)
    df = df.with_columns([
        pl.when(pl.col("Consent_Status") == "REVOKED")
        .then(pl.lit("PURGED"))
        .when(pl.col("Notice_Date").cast(pl.Utf8).str.to_date("%Y-%m-%d", strict=False) < engine.threshold_date)
        .then(pl.lit("PURGED"))
        .otherwise(pl.lit("PROCESSED"))
        .alias("Ingest_Status")
    ])

    # 4. THE VAULT COMMIT (Phase 0.3 SME Signature)
    records = df.to_dicts()
    for row in records:
        # Only commit compliant data to the 7-Pillar Vault
        if row.get('Ingest_Status') == 'PROCESSED':
            save_record(row)
            
    return df

def run_audit(df, label):
    """Generates execution stats for the SME Dashboard."""
    res = {
        "format": label, 
        "total": len(df),
        "processed": len(df.filter(pl.col("Ingest_Status") == "PROCESSED")),
        "purged": len(df.filter(pl.col("Ingest_Status") == "PURGED"))
    }
    return res
