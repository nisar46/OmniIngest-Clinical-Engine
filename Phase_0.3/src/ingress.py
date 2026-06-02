import polars as pl
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from .compliance_engine import ComplianceEngine

# Configuration: Mapping synonyms for messy columns to Canonical ABDM schema
COLUMN_MAPPING = {
    "patient_name": "Patient_Name",
    "abha_id": "ABHA_ID",
    "notice_id": "Notice_ID",
    "notice_date": "Notice_Date",
    "consent_status": "Consent_Status",
    "clinical_payload": "Clinical_Payload",
    "bill_amount": "Bill_Amount",
    "data_purpose": "Data_Purpose"
}

def detect_format(file_path: str) -> str:
    """Detects the file format based on the extension."""
    ext = os.path.splitext(file_path)[1].lower()
    format_map = {
        '.csv': 'CSV (Polars)',
        '.json': 'JSON (Universal)',
        '.xml': 'XML (Universal)',
        '.xlsx': 'Excel (Universal)',
        '.xls': 'Excel (Universal)',
        '.dcm': 'DICOM (Imaging)',
        '.hl7': 'HL7 V2 (Clinical)',
        '.fhir': 'FHIR R5 (Standard)',
        '.pdf': 'PDF (Clinical Report)',
        '.txt': 'Text (Clinical Report)'
    }
    return format_map.get(ext, f"Unknown ({ext.upper()})")

def validate_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Runs the Clinical Truth Gate & Compliance validation on a Polars DataFrame."""
    # FIX 1: Strict ABHA ID Validation (must be exactly 14 digits, no letters)
    df = df.with_columns(
        pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").alias("ABHA_ID")
    )
    df = df.with_columns(
        (
            (pl.col("ABHA_ID").str.len_chars() == 14) &
            (pl.col("ABHA_ID").str.contains(r"^\d{14}$"))
        ).alias("_ABHA_VALID")
    )

    # FIX 2: Expanded Clinical Keyword List (more specific medical terms)
    patterns = r"(?i)(hypertension|diabetes|asthma|fever|cough|prescribed|fracture|migraine|diagnosed|surgery|infection|cardiac|renal|pulmonary|administered|ibuprofen|metformin|insulin|amlodipine|paracetamol|losartan|salbutamol|sumatriptan|telmisartan)"

    # FIX 3: Negative Keyword Block (overrides positive match if negation present)
    negative_patterns = r"(?i)(no\s+(treatment|diagnosis|notes|clinical|records|history)|unknown condition|not available|nil|n\/a|no clinical|without (any )?(diagnosis|notes|records)|patient discharged without)"

    # FIX 4: Minimum Payload Length (< 20 chars = junk, force False)
    df = df.with_columns(
        pl.when(pl.col("Clinical_Payload").str.len_chars() < 20)
        .then(pl.lit(False))
        .when(pl.col("Clinical_Payload").str.contains(negative_patterns))
        .then(pl.lit(False))   # Negative override: 'No treatment notes' = False
        .otherwise(pl.col("Clinical_Payload").str.contains(patterns))
        .fill_null(False)
        .alias("SURGICAL_TRUTH")
    )

    df = df.with_columns([
        # Audit Statuses — now uses strict ABHA validation
        pl.when(~pl.col("_ABHA_VALID"))
        .then(pl.lit("QUARANTINED"))
        .when(pl.col("Consent_Status") == "REVOKED")
        .then(pl.lit("PURGED"))
        .otherwise(pl.lit("PROCESSED"))
        .alias("Ingest_Status"),
    ])
    
    # Logic for Revenue Leak: High Bill but no Clinical Truth
    df = df.with_columns([
        pl.when((pl.col("Bill_Amount") > 5000) & (pl.col("SURGICAL_TRUTH") == False))
        .then(pl.lit("PENDING_CLINICAL_AUDIT"))
        .when(pl.col("Consent_Status") == "REVOKED")
        .then(pl.lit("CONSENT_REVOKED"))
        .when(~pl.col("_ABHA_VALID"))
        .then(pl.lit("MISSING_ABHA"))
        .otherwise(pl.lit("N/A"))
        .alias("Status_Reason")
    ])

    # Final Override: If it's a Revenue Leak, it's Quarantined
    df = df.with_columns([
        pl.when(pl.col("Status_Reason") == "PENDING_CLINICAL_AUDIT")
        .then(pl.lit("QUARANTINED"))
        .otherwise(pl.col("Ingest_Status"))
        .alias("Ingest_Status")
    ])

    return df

def run_ingress(file_path: str, autofill: bool = False):
    """
    Phase 0.3 Ingress: Integrated with Clinical Truth Gate & SQL Persistence.
    """
    ext = os.path.splitext(file_path)[1].lower()
    
    # 1. Loading
    try:
        if ext == '.csv':
            df = pl.read_csv(file_path)
        elif ext == '.json':
            df = pl.read_json(file_path)
        elif ext == '.xml':
            # XML Parser: Reads each child element as a row
            tree = ET.parse(file_path)
            root = tree.getroot()
            records = []
            for child in root:
                record = {sub.tag: (sub.text.strip() if sub.text else "") for sub in child}
                records.append(record)
            df = pl.DataFrame(records) if records else pl.DataFrame()
        else:
            # Fallback for other unsupported formats
            df = pl.read_csv(file_path)
    except Exception as e:
        # Emergency fallback to empty DF if file is locked or missing
        return pl.DataFrame()

    # 2. Canonical Mapping
    # Ensure all columns are renamed to uppercase canonical versions for DB compatibility
    rename_dict = {}
    for col in df.columns:
        if col.lower() in COLUMN_MAPPING:
            rename_dict[col] = COLUMN_MAPPING[col.lower()]
    
    df = df.rename(rename_dict)
    
    # Ensure critical columns exist
    for canonical in COLUMN_MAPPING.values():
        if canonical not in df.columns:
            df = df.with_columns(pl.lit(None).alias(canonical))

    # Type Normalization: XML parses everything as strings, cast numeric columns
    if "Bill_Amount" in df.columns:
        df = df.with_columns(
            pl.col("Bill_Amount").cast(pl.Float64, strict=False).fill_null(0.0).alias("Bill_Amount")
        )

    # 3. Clinical Truth Logic & Validation
    df = validate_dataframe(df)

    return df

def run_audit(df, label, return_results=False):
    """Generates execution dashboard stats."""
    if df is None or df.is_empty():
        return {"total": 0, "processed": 0, "purged": 0, "quarantined": 0} if return_results else None

    res = {
        "format": label, 
        "total": len(df),
        "processed": len(df.filter(pl.col("Ingest_Status") == "PROCESSED")),
        "purged": len(df.filter(pl.col("Ingest_Status") == "PURGED")),
        "quarantined": len(df.filter(pl.col("Ingest_Status") == "QUARANTINED")),
        "purge_reasons": {},
        "quarantine_reasons": {}
    }
    
    # Calculate reasons safely
    if res["purged"] > 0:
        p_reasons = df.filter(pl.col("Ingest_Status") == "PURGED").group_by("Status_Reason").count().to_dicts()
        res["purge_reasons"] = {r["Status_Reason"]: r["count"] for r in p_reasons}
        
    if res["quarantined"] > 0:
        q_reasons = df.filter(pl.col("Ingest_Status") == "QUARANTINED").group_by("Status_Reason").count().to_dicts()
        res["quarantine_reasons"] = {r["Status_Reason"]: r["count"] for r in q_reasons}
    
    return res if return_results else None

def erase_pii_for_revocation(df):
    """Rule 8: Erasure on Revocation."""
    return df.with_columns([
        pl.when(pl.col("Consent_Status") == "REVOKED")
        .then(pl.lit("[DATA PURGED]"))
        .otherwise(pl.col("Patient_Name"))
        .alias("Patient_Name"),
        pl.when(pl.col("Consent_Status") == "REVOKED")
        .then(pl.lit("[DATA PURGED]"))
        .otherwise(pl.col("ABHA_ID"))
        .alias("ABHA_ID")
    ])
