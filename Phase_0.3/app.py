
import streamlit as st
import pandas as pd
import polars as pl
import os
import time
from datetime import datetime
import uuid
import json

# Local Modules (Refactored Phase 0.2)
from src import ui
from src import ingress
from src import compliance_engine
from src import database # [Phase 0.3]
from src.utils import sample_generator

# 1. Setup & Config
ui.setup_page()
database.init_db() # [Phase 0.3] Initialize DB

# --- OMNI METRIC CARD RENDERER ---
# Single flat <div> only — Streamlit strips nested divs and renders </div> as raw text.
# Accent bar is achieved via border-top. All dynamic HTML injected via f-string inline.
def omni_metric(col, label, value, delta=None, delta_inverse=False,
                border="#10b981", glow="rgba(16,185,129,0.2)", value_color="#34d399"):
    if delta is not None:
        d_arrow = "↓" if delta_inverse else "↑"
        d_color = "#fca5a5" if delta_inverse else "#86efac"
        delta_part = f'<p style="margin:10px 0 0;font-size:0.90rem;color:{d_color};font-weight:600;letter-spacing:0.02em;">{d_arrow}&nbsp;{delta}</p>'
    else:
        delta_part = ""
    col.markdown(
        f'<div style="padding:18px 20px 18px 20px;border-radius:12px;background-color:#0f172a;'
        f'min-height:130px;border:1.5px solid {border};border-top:4px solid {border};'
        f'box-shadow:0 0 18px {glow},0 4px 16px rgba(0,0,0,0.5);margin-bottom:6px;">'
        f'<p style="margin:0;font-size:0.82rem;color:{border};text-transform:uppercase;'
        f'letter-spacing:0.08em;font-weight:700;opacity:0.9;">{label}</p>'
        f'<p style="margin:8px 0 0;font-size:2.3rem;font-weight:800;color:{value_color};'
        f'line-height:1.1;font-family:\'Segoe UI\',system-ui,sans-serif;">{value}</p>'
        f'{delta_part}'
        f'</div>',
        unsafe_allow_html=True
    )

# 2. Session State Initialization
if 'processed_df' not in st.session_state:
    # [Phase 0.3] Load from DB on startup
    db_data = database.get_all_records()
    if not db_data.is_empty():
        st.session_state.processed_df = db_data
        st.session_state.data_source = "DB_RECOVERY" # [FIX] Tell UI we have data
        st.session_state.detected_format = "Database Persistence"
    else:
        st.session_state.processed_df = None
        st.session_state.data_source = None

if 'data_source' not in st.session_state:
    st.session_state.data_source = None
if 'mapping_confirmed' not in st.session_state:
    st.session_state.mapping_confirmed = False
if 'revoked' not in st.session_state:
    st.session_state.revoked = False
if 'detected_format' not in st.session_state:
    st.session_state.detected_format = None
if 'governance_logs' not in st.session_state:
    st.session_state.governance_logs = []

# 3. Sidebar & Governance
if st.session_state.revoked:
    ui.render_governance_sidebar(st.session_state.governance_logs)
else:
    # Standard Sidebar
    ui.render_governance_sidebar(st.session_state.governance_logs)

st.sidebar.markdown("### 🛡️ System Status")

# Sandbox Toggle
col_sb, col_count = st.sidebar.columns([2, 1])
is_sandbox = col_sb.toggle("🛠️ Sandbox Mode", value=(st.session_state.data_source == "DUMMY"))
num_patients = col_count.number_input("Count", min_value=10, max_value=5000, value=1000, step=100)

if is_sandbox and st.session_state.data_source != "DUMMY":
    st.session_state.data_source = "DUMMY"
    with st.spinner(f"Generating {num_patients} test patients..."):
        # 1. Generate the raw files
        sample_generator.main(num_rows=num_patients) 
        
        # 2. Run the Engine (In-Memory like yesterday)
        new_df = ingress.run_ingress("raw_data.csv")
        
        # 3. Store directly in memory for instant display
        st.session_state.processed_df = new_df
        st.session_state.mapping_confirmed = True
        st.session_state.detected_format = "Sandbox Stream"
        
        # 4. Optional: Save to DB in background (won't block UI)
        try:
            database.save_records_bulk(new_df.to_dicts())
        except:
            pass
            
        st.rerun() 

# [Improvement] Visibility Toggle
show_pii = st.sidebar.checkbox("👁️ Reveal PII (Compliance Audit)", value=False)


if st.sidebar.button("Reset Session"):
    database.reset_database()
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()


# 4. Main Layout
ui.render_header()

if st.session_state.revoked:
    ui.render_revoked_warning()
    # Double-tap safety
    if st.session_state.processed_df is not None:
         # Use Compliance Engine for erasure
         pass 

# Input Section
col1, _ = st.columns([3, 1])
with col1:
    with st.expander("ℹ️ Ingestion Guidelines & Boundary Rules (Staff Instructions)", expanded=True):
        st.markdown("""
        **OmniIngest** is administrative/compliance middleware designed for **hospital operations staff**. 
        It validates and normalizes files before storing them in the central clinical database.
        
        *   **Acceptable Schema:** Files must map to Patient Name, ABHA ID, Notice ID, Consent Status, and Clinical Payload.
        *   **Identity Rule:** Patient records must contain a valid 14-digit numeric ABHA ID.
        *   **Content Filter:** Automatically scans the clinical payload for diagnostic keywords to reject administrative noise, empty rows, or canteen logs.
        *   **Consent Rule (India DPDP):** Revoked consent status is automatically hard-purged.
        
        *Note: This gateway is not for doctor diagnostic use. Natural language querying and intelligence are handled in the **Clinosyn OS** layer.*
        """)
        
    tab1, tab2 = st.tabs(["📂 File Upload (PDF/CSV)", "✍️ Manual Entry"])
    
    uploaded_file = None
    with tab1:
        uploaded_file = st.file_uploader("", type=['csv', 'json', 'xml', 'xlsx', 'pdf', 'txt'])
    
    with tab2:
        st.info("Enter data manually for demo purposes.")
        # (Manual entry logic preserved but simplified for brevity in this refactor step)
        if st.button("Generate Dummy Manual Data"):
             st.info("Manual Entry Module - Integrated via Clinical Gateway")

# File Processing Logic
if uploaded_file is not None:
    temp_path = os.path.join(os.getcwd(), uploaded_file.name)
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    st.markdown(f"<div style='background-color: #161b22; padding: 10px; border-radius: 8px; border-left: 4px solid #10a37f;'>📄 <b>Detected:</b> {uploaded_file.name}</div>", unsafe_allow_html=True)
    st.session_state.data_source = "REAL"
    
    # Auto-Ingest
    if not st.session_state.mapping_confirmed:
        with st.spinner("🕵️ OmniIngest Smart-Scan..."):
            # Using the new ingress that handles PDF
            new_df = ingress.run_ingress(temp_path, autofill=True) 
            
            # [Phase 0.3] Persistence Layer - Bulk Save
            database.save_records_bulk(new_df.to_dicts())
            
            st.session_state.processed_df = database.get_all_records() # Reload from Source of Truth
            st.session_state.detected_format = ingress.detect_format(temp_path)
            st.session_state.mapping_confirmed = True
        st.rerun()

# Dashboard & Analytics
if st.session_state.processed_df is not None:
    st.markdown("---")
    df = st.session_state.processed_df
    
    # Recalculate _ABHA_VALID dynamically for UI/filtering logic since it is not persisted in DB
    if "_ABHA_VALID" not in df.columns:
        df = df.with_columns(
            (
                (pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").str.len_chars() == 14) &
                (pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").str.contains(r"^\d{14}$"))
            ).alias("_ABHA_VALID")
        )
    
    # Audit Run
    results = ingress.run_audit(df, "Session", return_results=True)
    
    st.subheader(f"📊 Analytics Dashboard - {st.session_state.detected_format or 'N/A'}")

    m1, m2, m3, m4 = st.columns(4)
    omni_metric(m1, "🗂️ Total Ingested", results['total'],
                border="#10b981", glow="rgba(16,185,129,0.2)", value_color="#34d399")
    omni_metric(m2, "✅ Cleared Gate", results['processed'],
                border="#f59e0b", glow="rgba(245,158,11,0.2)", value_color="#fbbf24")
    omni_metric(m3, "🔥 Rule 8 Purged", results['purged'],
                border="#ef4444", glow="rgba(239,68,68,0.2)", value_color="#f87171")
    omni_metric(m4, "🔵 Quarantined", results['quarantined'],
                border="#2563eb", glow="rgba(37,99,235,0.2)", value_color="#60a5fa")

    # 5. Ingestion & Content Filter Gate (New Gatekeeper Stats)
    st.markdown("---")
    st.markdown("### 🧬 Ingestion & Clinical Filter Gate")
    g1, g2, g3 = st.columns(3)

    # Calculate Filter Stats
    total_clinical = len(df)
    truth_count = len(df.filter(pl.col("SURGICAL_TRUTH") == True)) if "SURGICAL_TRUTH" in df.columns else 0
    leak_count = len(df.filter(pl.col("Status_Reason") == "PENDING_CLINICAL_AUDIT")) if "Status_Reason" in df.columns else 0

    omni_metric(g1, "Clinical Content Filter Pass",
                f"{(truth_count/total_clinical*100):.1f}%" if total_clinical > 0 else "0.0%",
                border="#10b981", glow="rgba(16,185,129,0.2)", value_color="#34d399")
    omni_metric(g2, "Clinical Records Accepted", truth_count,
                border="#f59e0b", glow="rgba(245,158,11,0.2)", value_color="#fbbf24")
    omni_metric(g3, "Pending Clinical Audits", leak_count,
                border="#ef4444", glow="rgba(239,68,68,0.2)", value_color="#f87171")

    # --- OPERATIONAL KPI METRICS (Horizontal) ---
    st.markdown("### 📡 Operational Intelligence")
    kpi1, kpi2, kpi3 = st.columns(3)

    # KPI 1: Pipeline Throughput Rate
    total_rows = len(df)
    processed_rows = len(df.filter(pl.col("Ingest_Status") == "PROCESSED"))
    throughput_pct = f"{(processed_rows / total_rows * 100):.1f}%" if total_rows > 0 else "0.0%"
    omni_metric(kpi1, "⚡ Pipeline Throughput Rate", throughput_pct,
                delta=f"{processed_rows} of {total_rows} rows cleared",
                border="#10b981", glow="rgba(16,185,129,0.2)", value_color="#34d399")

    # KPI 2: Revenue Under Operational Hold
    if "Status_Reason" in df.columns and "Bill_Amount" in df.columns:
        hold_amount = df.filter(pl.col("Status_Reason") == "PENDING_CLINICAL_AUDIT")["Bill_Amount"].sum()
    else:
        hold_amount = 0.0
    omni_metric(kpi2, "💰 Revenue Under Operational Hold", f"₹{hold_amount:,.2f}",
                delta="Pending Clinical Audit", delta_inverse=True,
                border="#f59e0b", glow="rgba(245,158,11,0.2)", value_color="#fbbf24")

    # KPI 3: Identity Firewall Blocks
    if "Status_Reason" in df.columns:
        abha_block_count = len(df.filter(pl.col("Status_Reason") == "MISSING_ABHA"))
    else:
        abha_block_count = 0
    omni_metric(kpi3, "🛡️ Identity Firewall Blocks", abha_block_count,
                delta="MISSING_ABHA rows blocked", delta_inverse=True,
                border="#2563eb", glow="rgba(37,99,235,0.2)", value_color="#60a5fa")
    
    st.markdown("---")
    
    # 6. RESULTS HUB: Double-Lock Architecture
    st.markdown("---")
    res_tab1, res_tab2 = st.tabs(["✅ VALIDATED DATA STREAM", "🚨 DOUBLE-LOCK QUARANTINE"])
    
    with res_tab1:
        st.subheader("High-Integrity Clinical Records")
        success_df = df.filter(pl.col("Ingest_Status") == "PROCESSED")
        if not success_df.is_empty():
            clean_preview = compliance_engine.mask_pii_for_preview(success_df, is_revoked=st.session_state.revoked, reveal_pii=show_pii)
            
            # Format display status indicators
            if '_ABHA_VALID' in clean_preview.columns:
                clean_preview['_ABHA_VALID'] = clean_preview['_ABHA_VALID'].map({True: "✅ Valid", False: "⚠️ Edit Required"}).fillna("")
            if 'Status_Reason' in clean_preview.columns:
                clean_preview['Status_Reason'] = clean_preview['Status_Reason'].replace("N/A", "")
                
            st.dataframe(clean_preview, use_container_width=True, height=400, column_config={
                "_ABHA_VALID": "ABHA Status",
                "Status_Reason": "Validation Alert"
            })
            
            # Export Hub is now here
            st.markdown("#### 📥 Secure Export")
            e1, e2 = st.columns(2)
            with e1:
                 st.download_button("✅ FHIR Bundle (R5)", compliance_engine.get_fhir_bundle(success_df), "bundle.json", "application/json")
            with e2:
                 st.download_button("📜 Master CSV", success_df.write_csv(), "master.csv", "text/csv")
        else:
            st.info("No records have cleared the Truth Gate yet.")

    with res_tab2:
        st.subheader("Threat Command Center")
        
        # Interactive Threat Filters
        tf_col1, tf_col2 = st.columns(2)
        show_privacy = tf_col1.toggle("🛡️ Show Privacy Shields", value=True)
        show_clinical = tf_col2.toggle("🩺 Show Clinical Leaks", value=True)
        
        # Quarantine Logic & Categorization
        quar_df = df.filter(pl.col("Ingest_Status") != "PROCESSED")
        
        if not quar_df.is_empty():
            # Define overlapping category conditions
            is_privacy = (
                pl.col("Status_Reason").is_in(["CONSENT_REVOKED", "NOTICE_EXPIRED", "UNAUTHORIZED_PURPOSE", "MISSING_ABHA"]) |
                (~pl.col("_ABHA_VALID"))
            )
            is_clinical = (
                pl.col("Status_Reason").is_in(["PENDING_CLINICAL_AUDIT", "NONSENSE_DATA"]) |
                pl.col("Clinical_Payload").is_null() |
                (pl.col("Clinical_Payload").str.strip_chars() == "")
            )
            
            # Use Polars to dynamically construct Block_Category and Resolution_Fix
            quar_df = quar_df.with_columns([
                pl.when(is_privacy & is_clinical)
                .then(pl.lit("🔒 PRIVACY & 🏥 CLINICAL"))
                .when(is_privacy)
                .then(pl.lit("🔒 PRIVACY_SHIELD"))
                .otherwise(pl.lit("🏥 CLINICAL_VOID"))
                .alias("Block_Category"),
                
                pl.when(is_privacy & is_clinical)
                .then(pl.lit("Requires valid ABHA ID AND clinical mapping review."))
                .when(pl.col("Status_Reason") == "PENDING_CLINICAL_AUDIT")
                .then(pl.lit("Requires Valid ICD-10 mapping before billing release."))
                .when(pl.col("Status_Reason") == "CONSENT_REVOKED")
                .then(pl.lit("Patient Data Principal has exercised Right to Erasure."))
                .when(pl.col("Status_Reason") == "NONSENSE_DATA")
                .then(pl.lit("Payload contains non-medical or chaotic markers."))
                .when(pl.col("Status_Reason") == "MISSING_ABHA")
                .then(pl.lit("ABHA ID is missing or invalid."))
                .otherwise(pl.lit("Awaiting Clinical Verification."))
                .alias("Resolution_Fix")
            ])
            
            # Filter based on overlapping switch selections
            filter_expr = pl.lit(False)
            if show_privacy:
                filter_expr = filter_expr | is_privacy
            if show_clinical:
                filter_expr = filter_expr | is_clinical
            
            filtered_quar = quar_df.filter(filter_expr)
            
            if not filtered_quar.is_empty():
                # Convert to pandas to format and edit
                q_editor_df = filtered_quar.to_pandas()
                
                # Build a single clean "Fix Required" message per row
                def build_fix_alert(row):
                    abha_ok = bool(row.get('_ABHA_VALID', True))
                    reason = str(row.get('Status_Reason', ''))
                    issues = []
                    if not abha_ok or reason == "MISSING_ABHA":
                        issues.append("Fix ABHA ID")
                    if reason in ["PENDING_CLINICAL_AUDIT", "NONSENSE_DATA"]:
                        issues.append("Fix Clinical Data")
                    return " + ".join(issues) if issues else ""
                
                q_editor_df['Fix_Required'] = q_editor_df.apply(build_fix_alert, axis=1)
                
                # Drop internal helper columns — keep display clean
                display_cols = [c for c in q_editor_df.columns if c not in ['_ABHA_VALID', 'Status_Reason', 'Block_Category', 'Resolution_Fix', 'ingest_timestmp', 'Fix_Required']]
                q_editor_df = q_editor_df[display_cols + ['Fix_Required']]
                
                # Style Fix_Required column (disabled = Streamlit allows amber bg)
                def style_fix_col(row):
                    styles = [''] * len(row)
                    cols = list(row.index)
                    if row.get('Fix_Required', '') != '' and 'Fix_Required' in cols:
                        styles[cols.index('Fix_Required')] = 'background-color: #ffeedd; color: #cc3300; font-weight: bold;'
                    return styles
                
                # All columns that are NEVER editable regardless of fix type
                BASE_LOCKED = [
                    "Notice_ID", "Notice_Date", "Consent_Status", "Validated_ICD10",
                    "SURGICAL_TRUTH", "Ingest_Status", "Status_Reason", "ingest_timestmp",
                    "_ABHA_VALID", "Block_Category", "Resolution_Fix", "Fix_Required"
                ]
                FULL_METADATA_LOCK = [
                    "Notice_ID", "Notice_Date", "Consent_Status", "Validated_ICD10",
                    "SURGICAL_TRUTH", "Ingest_Status", "Status_Reason", "ingest_timestmp",
                    "_ABHA_VALID", "Block_Category", "Resolution_Fix"
                ]
                
                COL_CONFIG = {
                    "Fix_Required": st.column_config.TextColumn("⚠️ Fix Required", width="medium"),
                }
                
                # Split into fix-type groups so only the specific broken cell is editable per group
                grp_abha     = q_editor_df[q_editor_df['Fix_Required'] == "Fix ABHA ID"].copy()
                grp_clinical = q_editor_df[q_editor_df['Fix_Required'] == "Fix Clinical Data"].copy()
                grp_both     = q_editor_df[q_editor_df['Fix_Required'] == "Fix ABHA ID + Fix Clinical Data"].copy()
                grp_locked   = q_editor_df[~q_editor_df['Fix_Required'].isin(["Fix ABHA ID", "Fix Clinical Data", "Fix ABHA ID + Fix Clinical Data"])].copy()
                
                all_edited = []
                
                # Group 1: ABHA_ID ONLY editable — Patient_Name, Clinical_Payload, Bill_Amount all locked
                if not grp_abha.empty:
                    st.markdown("##### 🔴 Identity Fix — Correct ABHA ID Only")
                    edited = st.data_editor(
                        grp_abha.style.apply(style_fix_col, axis=1),
                        key="editor_abha", use_container_width=True,
                        disabled=[
                            "Notice_ID", "Notice_Date", "Patient_Name", "Consent_Status",
                            "Clinical_Payload", "Bill_Amount", "Validated_ICD10",
                            "SURGICAL_TRUTH", "Ingest_Status", "Status_Reason", "Fix_Required"
                        ],
                        column_config=COL_CONFIG, height=250
                    )
                    all_edited.append(edited)
                
                # Group 2: Clinical_Payload + Bill_Amount ONLY editable — ABHA_ID, Patient_Name locked
                if not grp_clinical.empty:
                    st.markdown("##### 🟠 Clinical Fix — Correct Clinical Payload & Bill Amount Only")
                    edited = st.data_editor(
                        grp_clinical.style.apply(style_fix_col, axis=1),
                        key="editor_clinical", use_container_width=True,
                        disabled=[
                            "Notice_ID", "Notice_Date", "ABHA_ID", "Patient_Name",
                            "Consent_Status", "Validated_ICD10", "SURGICAL_TRUTH",
                            "Ingest_Status", "Status_Reason", "Fix_Required"
                        ],
                        column_config=COL_CONFIG, height=250
                    )
                    all_edited.append(edited)
                
                # Group 3: ABHA_ID + Patient_Name + Clinical_Payload + Bill_Amount editable
                if not grp_both.empty:
                    st.markdown("##### 🔴🟠 Full Anomaly Fix — ABHA ID + Clinical Data")
                    locked_cols = list(set(
                        FULL_METADATA_LOCK +
                        [c for c in display_cols if c not in ["ABHA_ID", "Patient_Name", "Clinical_Payload", "Bill_Amount"]]
                    ))
                    edited = st.data_editor(
                        grp_both.style.apply(style_fix_col, axis=1),
                        key="editor_both", use_container_width=True,
                        disabled=locked_cols, column_config=COL_CONFIG, height=250
                    )
                    all_edited.append(edited)
                
                # Group 4: Read-only (e.g. CONSENT_REVOKED — nothing to edit)
                if not grp_locked.empty:
                    st.markdown("##### 🔒 Privacy Shield — Read Only")
                    edited = st.data_editor(
                        grp_locked.style.apply(style_fix_col, axis=1),
                        key="editor_locked", use_container_width=True,
                        disabled=list(set(FULL_METADATA_LOCK + display_cols)), column_config=COL_CONFIG, height=200
                    )
                    all_edited.append(edited)
                
                # Save & Re-Validate Action Button (Silent — no alerts)
                if st.button("💾 Save & Re-Validate"):
                    import pandas as _pd
                    combined = _pd.concat(all_edited, ignore_index=True) if all_edited else _pd.DataFrame()

                    for idx, row in combined.iterrows():
                        try:
                            raw_bill = float(str(row['Bill_Amount']).strip())
                        except (ValueError, TypeError):
                            raw_bill = 0.0
                        # Silent SQL UPDATE against SQLite 'patients' table using Notice_ID as key
                        database.update_patient_record(
                            notice_id=row['Notice_ID'],
                            abha_id=str(row['ABHA_ID']).strip(),
                            patient_name=str(row['Patient_Name']).strip(),
                            notice_date=row['Notice_Date'],
                            consent_status=row['Consent_Status'],
                            clinical_payload=str(row['Clinical_Payload']).strip(),
                            bill_amount=raw_bill,
                            validated_icd10=str(row.get('Validated_ICD10', '')).strip()
                        )

                    raw_df = database.get_all_records()
                    validated_df = ingress.validate_dataframe(raw_df)
                    database.save_records_bulk(validated_df.to_dicts())

                    # Silent state flush — corrected rows vanish immediately
                    del st.session_state['processed_df']
                    st.rerun()
            else:
                st.info("No threats detected in this filtering scenario.")
        else:
            st.success("Clean House: 0 Threats detected in current session.")
             
    # 7. System Governance
    if not st.session_state.revoked:
        st.markdown("---")
        if st.button("🔴 Purge Data (DPDP Rule 8)"):
             # Execute Kill Switch
             vault = compliance_engine.PIIVault()
             log = vault.shred_keys()
             
             # [Phase 0.3] DB Hard Delete
             database.hard_delete_all()
             
             st.session_state.governance_logs.append(f"{datetime.now().strftime('%H:%M:%S')} {log}")
             st.session_state.revoked = True
             st.session_state.processed_df = database.get_all_records() # Should be empty
             st.rerun()
    else:
        st.error("Exports & Operations Disabled: Data Purged.")
# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #444654;'>🛡️ <b>OmniIngest Phase 0.3:</b> The Master Build | Professional Clinical Data Ingestion</div>", unsafe_allow_html=True)
