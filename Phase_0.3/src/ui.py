import streamlit as st
import altair as alt
import pandas as pd
from .database import get_all_records, rule_8_3_incinerator

def setup_page():
    st.set_page_config(page_title="OmniIngest ABDM 2.0", page_icon="🏥", layout="wide")
    st.markdown("""
        <style>
        .main { background-color: #0e1117; }
        .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
        </style>
    """, unsafe_allow_html=True)

def render_header():
    st.title("🏥 OmniIngest | Enterprise Clinical Gateway")
    st.markdown("<div style='color: #4682B4;'>Phase 0.3: High-Performance Clinical Ingestion Master Build</div>", unsafe_allow_html=True)
    st.markdown("---")

def render_governance_sidebar():
    st.sidebar.markdown("""
    <div style='background-color: #8b0000; padding: 10px; border-radius: 5px; text-align: center; color: white;'>
    🚨 [DPDP RULE 8.3 ACTIVE]<br>Real-time PII Hard-Purge Enabled
    </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 🛡️ Governance Actions")
    
    # THE RULE 8.3 KILL-SWITCH
    purge_id = st.sidebar.text_input("Enter ABHA ID to Incinerate")
    if st.sidebar.button("🔥 EXECUTE RULE 8.3 PURGE"):
        if purge_id:
            rule_8_3_incinerator(purge_id)
            st.sidebar.success(f"Record {purge_id} Hard-Deleted.")
            st.rerun()
        else:
            st.sidebar.error("Please enter a valid ABHA ID")

def render_vault_view():
    st.subheader("🗄️ The 7-Pillar Clinical Vault")
    df = get_all_records() # Fetches joined data from the new DB pillars
    
    if not df.is_empty():
        # Using Polars for high-speed display
        st.dataframe(df.to_pandas(), use_container_width=True)
    else:
        st.info("Vault is currently empty. Awaiting clinical ingress...")

def get_chart(data):
    base = alt.Chart(data).encode(
        x=alt.X('Status', sort=None),
        y='Count',
        color=alt.Color('Status', scale=alt.Scale(domain=['PROCESSED', 'PURGED'], range=['#00ff00', '#ff0000'])),
        tooltip=['Status', 'Count']
    )
    return base.mark_bar().properties(title="Ingestion Health Metrics")
