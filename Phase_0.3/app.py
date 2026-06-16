import streamlit as st
import pandas as pd
import polars as pl
import os
import time
from datetime import datetime
import uuid
import json
import sqlite3

# Local Modules (Refactored Phase 0.3 - Airlock Architecture)
from src import ui
from src import ingress
from src import compliance_engine
from src import database
from src.utils import sample_generator

# 1. Zero-Baseline Startup Initialization & Session Persistence Fix
if 'APP_INITIALIZED' not in st.session_state:
    st.session_state.clear()
    st.cache_data.clear()
    # Programmatically clear lingering states and zero-baseline telemetry
    database.reset_database()
    st.session_state['APP_INITIALIZED'] = True
    st.session_state.processed_df = None
    st.session_state.data_source = None
    st.session_state.detected_format = None
    st.session_state.governance_logs = []

# Setup & Config
ui.setup_page()
database.init_db()

# --- OMNI METRIC CARD RENDERER ---
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
    db_data = database.get_all_records()
    if not db_data.is_empty():
        st.session_state.processed_df = db_data
        st.session_state.data_source = "DB_RECOVERY"
        st.session_state.detected_format = "Database Persistence"
    else:
        st.session_state.processed_df = None
        st.session_state.data_source = None

if 'governance_logs' not in st.session_state:
    st.session_state.governance_logs = []

# 3. Sidebar & Governance
ui.render_governance_sidebar(st.session_state.governance_logs)

st.sidebar.markdown("### 🛡️ System Status")
is_sandbox = st.sidebar.toggle("🛠️ Sandbox Mode", value=(st.session_state.data_source == "DUMMY"))
num_patients = st.sidebar.number_input("Count", min_value=10, max_value=5000, value=1000, step=100)
sandbox_formats = []
if is_sandbox:
    selected_format = st.sidebar.selectbox("Testing File Format", ["Choose Format...", "CSV", "JSON", "XML", "XLSX", "PDF", "TXT"])
    sandbox_formats = [selected_format]

show_pii = st.sidebar.checkbox("👁️ Reveal PII", value=False)

if is_sandbox:
    if selected_format == "Choose Format...":
        st.info("ℹ️ Awaiting Configuration: Please select a target testing format and click 'Regenerate Synthetic Data' to initialize the data gateway.")
    elif st.sidebar.button("Regenerate Synthetic Data"):
        st.session_state.data_source = "DUMMY"
        with st.spinner(f"Generating {num_patients} test patients..."):
            try:
                # STEP 1: INTAKE (Memory only first)
                sample_generator.main(num_rows=num_patients, formats=sandbox_formats) 
                
                # Read the generated file based on the first selected format or default to CSV
                target_file = "raw_data.csv"
                if "CSV" in sandbox_formats: target_file = "raw_data.csv"
                elif "JSON" in sandbox_formats: target_file = "raw_data.json"
                elif "XML" in sandbox_formats: target_file = "raw_data.xml"
                elif "XLSX" in sandbox_formats: target_file = "raw_data.xlsx"
                elif "PDF" in sandbox_formats: target_file = "raw_data.pdf"
                elif "TXT" in sandbox_formats: target_file = "raw_data.txt"
                
                memory_df = ingress.run_ingress(target_file)
                
                # Airlock Isolation - Save fully processed triage to DB
                database.reset_database()
                if not memory_df.is_empty():
                    database.save_records_bulk(memory_df.to_dicts())
                
                st.session_state.processed_df = database.get_all_records()
                st.session_state.detected_format = f"Sandbox Stream ({target_file.split('.')[-1].upper()})"
                st.cache_data.clear()
                st.rerun()
            except (ImportError, ModuleNotFoundError):
                st.warning('⚠️ System Dependency Missing: Please run "pip install calamine xlsx2csv openpyxl" in your terminal to enable Excel data parsing.')
                st.stop()

if st.sidebar.button("Reset Session"):
    database.reset_database()
    st.session_state.clear()
    st.cache_data.clear()
    st.rerun()

# Global Purge in sidebar (Sidebar Interlock)
with st.sidebar.expander("🚨 Global Admin Actions"):
    st.markdown("### Emergency System Purge")
    purge_confirm = st.checkbox("I understand the consequences")
    purge_text = st.text_input("Type 'CONFIRM PURGE' to proceed")
    if st.button("Purge All Data", disabled=not (purge_confirm and purge_text == "CONFIRM PURGE")):
        vault = compliance_engine.PIIVault()
        log = vault.shred_keys()
        database.hard_delete_all()
        database.log_audit_event("SYSTEM_PURGE", "GLOBAL", "Emergency Action", "Global Purge Executed")
        st.session_state.governance_logs.append(f"{datetime.now().strftime('%H:%M:%S')} Global Purge Executed: {log}")
        st.session_state.processed_df = None
        st.cache_data.clear()
        st.rerun()

# 4. Main Layout
ui.render_header()

# --- STEP 1: INTAKE PIPELINE ---
st.markdown("### 📥 STEP 1: Intake")
tab1, tab2 = st.tabs(["📂 File Upload", "✍️ Manual Entry"])
uploaded_file = None
with tab1:
    uploaded_file = st.file_uploader("", type=['csv', 'json', 'xml', 'xlsx', 'pdf', 'txt'])

    if uploaded_file is not None:
        temp_path = os.path.join(os.getcwd(), uploaded_file.name)
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        st.success(f"Detected: {uploaded_file.name}")
        st.session_state.data_source = "REAL"
        
        with st.spinner("🕵️ OmniIngest Smart-Scan..."):
            try:
                # Airlock Isolation
                memory_df = ingress.run_ingress(temp_path, autofill=True) 
                if not memory_df.is_empty():
                    database.save_records_bulk(memory_df.to_dicts())
                st.session_state.processed_df = database.get_all_records()
                st.session_state.detected_format = ingress.detect_format(temp_path)
                st.cache_data.clear()
                st.rerun()
            except (ImportError, ModuleNotFoundError):
                st.warning('⚠️ System Dependency Missing: Please run "pip install calamine xlsx2csv openpyxl" in your terminal to enable Excel data parsing.')
                st.stop()

with tab2:
    with st.form("manual_entry_form"):
        col1, col2 = st.columns(2)
        man_name = col1.text_input("Patient Full Name")
        man_abha = col2.text_input("14-Digit ABHA ID")
        man_payload = st.text_area("Clinical Summary/Payload Text")
        man_bill = st.number_input("Billing Amount (INR)", min_value=0.0)
        submitted = st.form_submit_button("Submit Manual Entry")
        
        if submitted:
            record = {
                "Patient_Name": man_name,
                "ABHA_ID": man_abha,
                "Clinical_Payload": man_payload,
                "Bill_Amount": man_bill,
                "Notice_ID": str(uuid.uuid4()),
                "Notice_Date": datetime.now().strftime("%Y-%m-%d"),
                "Consent_Status": "ACTIVE",
                "Data_Purpose": "Manual Entry"
            }
            man_df = pl.DataFrame([record])
            # Pass through central validation engine
            man_df = ingress.validate_dataframe(ingress.apply_canonical_mapping(man_df))
            database.save_records_bulk(man_df.to_dicts())
            st.session_state.processed_df = database.get_all_records()
            st.session_state.data_source = "MANUAL"
            st.cache_data.clear()
            st.rerun()

if st.session_state.processed_df is not None:
    df = st.session_state.processed_df
    
    # Validation helpers
    if "_ABHA_VALID" not in df.columns:
        df = df.with_columns(
            (
                (pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").str.len_chars() == 14) &
                (pl.col("ABHA_ID").cast(pl.Utf8).fill_null("").str.contains(r"^\d{14}$"))
            ).alias("_ABHA_VALID")
        )
    
    # --- STEP 2: TRIAGE DASHBOARD ---
    st.markdown("---")
    st.markdown("### 🔬 STEP 2: Triage & Operational Telemetry")
    
    # Top Level Telemetry (Non-Financial)
    m1, m2, m3 = st.columns(3)
    total_intake = len(df)
    cleared_flow = len(df.filter(pl.col("Ingest_Status") == "PROCESSED"))
    quarantined_flow = len(df.filter(pl.col("Ingest_Status") != "PROCESSED"))
    
    omni_metric(m1, "📥 Intake Batch Count", total_intake, border="#3b82f6", glow="rgba(59,130,246,0.2)", value_color="#60a5fa")
    omni_metric(m2, "✅ Cleared Flow Volume", cleared_flow, border="#10b981", glow="rgba(16,185,129,0.2)", value_color="#34d399")
    omni_metric(m3, "🚨 Total Active Triage Errors", quarantined_flow, border="#f59e0b", glow="rgba(245,158,11,0.2)", value_color="#fbbf24")

    st.markdown("---")
    st.markdown("### 🚀 STEP 3: Dispatch (Double-Lock Architecture)")
    res_tab1, res_tab2 = st.tabs(["✅ VALIDATED DATA STREAM", "🚨 DOUBLE-LOCK QUARANTINE"])
    
    with res_tab1:
        st.subheader("High-Integrity Clinical Records")
        success_df = df.filter(pl.col("Ingest_Status") == "PROCESSED")
        if not success_df.is_empty():
            clean_preview = compliance_engine.mask_pii_for_preview(success_df, is_revoked=False, reveal_pii=show_pii)
            st.dataframe(clean_preview, use_container_width=True, height=400)
            
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
        
        # Granular Purge for CONSENT_REVOKED
        revoked_df = df.filter(pl.col("Status_Reason") == "CONSENT_REVOKED")
        if not revoked_df.is_empty():
            revoked_warning = st.empty()
            revoked_warning.error(f"⚠️ {len(revoked_df)} Records flagged with CONSENT_REVOKED. DPDP Rule 8 compliance required.")
            if st.button("🔥 Execute Targeted Purge (Rule 8)"):
                with st.spinner("Executing Cryptographic Purge..."):
                    conn = sqlite3.connect(database.DB_NAME)
                    c = conn.cursor()
                    c.execute("DELETE FROM patients WHERE status_reason = 'CONSENT_REVOKED'")
                    conn.commit()
                    conn.close()
                    
                    database.log_audit_event("RULE_8_PURGE", f"{len(revoked_df)} Records", "DPDP Rule 8", "Targeted Purge of Revoked Records")
                    revoked_warning.empty()
                    st.session_state.processed_df = database.get_all_records()
                    st.session_state.governance_logs.append(f"{datetime.now().strftime('%H:%M:%S')} Targeted Purge Executed for {len(revoked_df)} revoked records.")
                    st.cache_data.clear()
                    st.rerun()

        # Triage Desks
        st.markdown("#### 🛡️ Segmented Triage Desks")
        
        # 1. Identity Desk
        missing_abha_df = df.filter(pl.col("Status_Reason") == "MISSING_ABHA")
        if not missing_abha_df.is_empty():
            st.markdown("##### 🔴 Identity Desk (Fix ABHA ID)")
            # Apply front-end masking but restore the editable target column
            id_editor_df = compliance_engine.mask_pii_for_preview(missing_abha_df, is_revoked=False, reveal_pii=show_pii)
            id_editor_df['ABHA_ID'] = missing_abha_df.to_pandas()['ABHA_ID']
            
            # UI only shows these columns via column_config, hide the rest
            all_cols = list(id_editor_df.columns)
            col_config = {col: None for col in all_cols if col not in ['Patient_Name', 'ABHA_ID']}
            
            edited_id = st.data_editor(
                id_editor_df,
                key="identity_desk_editor",
                column_config=col_config,
                disabled=["Patient_Name"],
                use_container_width=True
            )
            if st.button("💾 Save & Re-Validate Identity Data"):
                orig_pd = missing_abha_df.to_pandas()
                for idx, row in edited_id.iterrows():
                    orig_row = orig_pd[orig_pd['Notice_ID'] == row['Notice_ID']].iloc[0]
                    # Only process if changed
                    if str(row['ABHA_ID']) != str(orig_row['ABHA_ID']):
                        database.update_patient_record(
                            notice_id=row['Notice_ID'],
                            abha_id=str(row['ABHA_ID']).strip(),
                            patient_name=str(orig_row['Patient_Name']).strip(),
                            notice_date=orig_row['Notice_Date'],
                            consent_status=orig_row['Consent_Status'],
                            clinical_payload=str(orig_row['Clinical_Payload']).strip(),
                            bill_amount=float(orig_row['Bill_Amount']) if pd.notna(orig_row['Bill_Amount']) else 0.0,
                            validated_icd10=str(orig_row.get('Validated_ICD10', '')).strip()
                        )
                        database.log_audit_event("ABHA_OVERRIDE", str(row['Notice_ID']), "Identity Desk", f"Corrected ABHA from {orig_row['ABHA_ID']} to {row['ABHA_ID']}")
                raw_df = database.get_all_records()
                validated_df = ingress.validate_dataframe(raw_df)
                database.save_records_bulk(validated_df.to_dicts())
                st.session_state.processed_df = database.get_all_records()
                st.cache_data.clear()
                st.rerun()

        # 2. Clinical Desk
        clinical_audit_df = df.filter(pl.col("Status_Reason") == "PENDING_CLINICAL_AUDIT")
        if not clinical_audit_df.is_empty():
            st.markdown("##### 🟠 Clinical Audit Desk")
            
            # Show Financial Risk Badge here
            hold_amount = clinical_audit_df["Bill_Amount"].sum()
            st.warning(f"💰 Revenue Under Operational Hold: ₹{hold_amount:,.2f}")
            
            # Render Clinical_Payload for audit operational capabilities
            clin_editor_df = compliance_engine.mask_pii_for_preview(clinical_audit_df, is_revoked=False, reveal_pii=show_pii)
            clin_editor_df['Clinical_Payload'] = clinical_audit_df.to_pandas()['Clinical_Payload']
            
            all_cols = list(clin_editor_df.columns)
            col_config = {col: None for col in all_cols if col not in ['Clinical_Payload', 'Bill_Amount', 'Patient_Name']}
            col_config['Clinical_Payload'] = st.column_config.TextColumn("Clinical Payload (Editable)")
            col_config['Bill_Amount'] = st.column_config.NumberColumn(format="₹%.2f")
            
            edited_clin = st.data_editor(
                clin_editor_df,
                key="editor_clin_desk",
                column_config=col_config,
                disabled=["Patient_Name"],
                use_container_width=True
            )
            if st.button("💾 Save & Re-Validate Clinical Data"):
                orig_pd = clinical_audit_df.to_pandas()
                for idx, row in edited_clin.iterrows():
                    orig_row = orig_pd[orig_pd['Notice_ID'] == row['Notice_ID']].iloc[0]
                    # Verify if Payload OR Bill Amount changed
                    if float(row['Bill_Amount']) != float(orig_row['Bill_Amount']) or str(row.get('Clinical_Payload', '')) != str(orig_row.get('Clinical_Payload', '')):
                        database.update_patient_record(
                            notice_id=row['Notice_ID'],
                            abha_id=str(orig_row['ABHA_ID']).strip(),
                            patient_name=str(orig_row['Patient_Name']).strip(),
                            notice_date=orig_row['Notice_Date'],
                            consent_status=orig_row['Consent_Status'],
                            clinical_payload=str(row.get('Clinical_Payload', '')).strip(),
                            bill_amount=float(row['Bill_Amount']) if pd.notna(row['Bill_Amount']) else 0.0,
                            validated_icd10=str(orig_row.get('Validated_ICD10', '')).strip()
                        )
                        database.log_audit_event("CLINICAL_OVERRIDE", str(row['Notice_ID']), "Clinical Desk", "Updated Clinical Data/Billing manually")
                raw_df = database.get_all_records()
                validated_df = ingress.validate_dataframe(raw_df)
                database.save_records_bulk(validated_df.to_dicts())
                st.session_state.processed_df = database.get_all_records()
                st.cache_data.clear()
                st.rerun()

st.markdown("---")
st.markdown("<div style='text-align: center; color: #444654;'>🛡️ <b>OmniIngest Phase 0.3:</b> The Master Build | Professional Clinical Data Ingestion</div>", unsafe_allow_html=True)
