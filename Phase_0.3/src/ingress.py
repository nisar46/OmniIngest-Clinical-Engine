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

def apply_canonical_mapping(df: pl.DataFrame) -> pl.DataFrame:
    rename_dict = {}
    for col in df.columns:
        if col.lower() in COLUMN_MAPPING:
            rename_dict[col] = COLUMN_MAPPING[col.lower()]
    
    df = df.rename(rename_dict)
    
    for canonical in COLUMN_MAPPING.values():
        if canonical not in df.columns:
            df = df.with_columns(pl.lit(None).alias(canonical))

    if "Bill_Amount" in df.columns:
        df = df.with_columns(
            pl.col("Bill_Amount").cast(pl.Float64, strict=False).fill_null(0.0).alias("Bill_Amount")
        )
    return df

def validate_dataframe(df: pl.DataFrame) -> pl.DataFrame:
    """Runs the Clinical Truth Gate & Compliance validation on a Polars DataFrame."""
    # FIX 1: Official NHA ABHA Validation Framework
    df = df.with_columns(
        pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").alias("ABHA_ID")
    )
    
    abha_stripped = pl.col("ABHA_ID").str.replace_all("-", "")
    is_14_digits = (abha_stripped.str.len_chars() == 14) & (abha_stripped.str.contains(r"^\d{14}$"))
    is_proper_format = pl.col("ABHA_ID").str.contains(r"^[0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4}$")
    
    abha_formatted = pl.when(~is_proper_format & is_14_digits).then(
        abha_stripped.str.slice(0, 2) + "-" + abha_stripped.str.slice(2, 4) + "-" + abha_stripped.str.slice(6, 4) + "-" + abha_stripped.str.slice(10, 4)
    ).otherwise(pl.col("ABHA_ID"))
    
    df = df.with_columns(abha_formatted.alias("ABHA_ID"))
    
    df = df.with_columns(
        pl.col("ABHA_ID").str.contains(r"^[0-9]{2}-[0-9]{4}-[0-9]{4}-[0-9]{4}$").fill_null(False).alias("_ABHA_VALID")
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
        import streamlit as st
        if ext == '.csv':
            df = pl.scan_csv(file_path).collect()
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
        elif ext in ['.xlsx', '.xls']:
            try:
                df = pl.read_excel(file_path)
            except (ImportError, ModuleNotFoundError):
                import streamlit as st
                st.warning('⚠️ System Dependency Missing: Please run "pip install calamine xlsx2csv openpyxl" in your terminal to enable Excel data parsing.')
                st.stop()
        elif ext in ['.txt', '.pdf']:
            import re
            text = ""
            if ext == '.pdf':
                try:
                    import PyPDF2
                    with open(file_path, 'rb') as f:
                        reader = PyPDF2.PdfReader(f)
                        text = "\n".join([page.extract_text() for page in reader.pages])
                except Exception as pdf_e:
                    st.toast(f"Parsing Exception: {str(pdf_e)}")
                    return pl.DataFrame()
            else:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            # Split these unstructured payloads by explicit record delimiter anchors
            blocks = re.split(r'\n={3,}\n?|\n-{3,}\n?|={10,}|-{10,}', text)
            records = []
            for block in blocks:
                if not block.strip(): continue
                record = {}
                name_match = re.search(r'Patient Name:\s*(.+)', block, re.IGNORECASE)
                abha_match = re.search(r'ABHA ID:\s*(.+)', block, re.IGNORECASE)
                payload_match = re.search(r'Clinical Payload:\s*(.+)', block, re.IGNORECASE)
                bill_match = re.search(r'Bill Amount:\s*([0-9.]+)', block, re.IGNORECASE)
                consent_match = re.search(r'Consent Status:\s*(.+)', block, re.IGNORECASE)
                notice_match = re.search(r'Notice ID:\s*(.+)', block, re.IGNORECASE)
                
                if name_match: record['patient_name'] = name_match.group(1).strip()
                if abha_match: record['abha_id'] = abha_match.group(1).strip()
                if payload_match: record['clinical_payload'] = payload_match.group(1).strip()
                if bill_match: record['bill_amount'] = float(bill_match.group(1).strip())
                if consent_match: record['consent_status'] = consent_match.group(1).strip()
                if notice_match: record['notice_id'] = notice_match.group(1).strip()
                if record: records.append(record)
                
            df = pl.DataFrame(records) if records else pl.DataFrame()
        else:
            # Fallback for other unsupported formats
            df = pl.read_csv(file_path)
    except Exception as e:
        import streamlit as st
        st.toast(f"Parsing Exception: {str(e)}")
        # Emergency fallback to empty DF if file is locked or missing
        return pl.DataFrame()

    # 2. Canonical Mapping
    df = apply_canonical_mapping(df)

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
