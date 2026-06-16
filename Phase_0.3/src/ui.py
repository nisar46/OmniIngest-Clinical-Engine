
import streamlit as st
import altair as alt

def setup_page():
    st.set_page_config(page_title="OmniIngest ABDM 2.0", page_icon="🏥", layout="wide")
    
    # Custom CSS for "Modern GenAI" aesthetics
    st.markdown("""
        <style>
        /* Main Background with Mesh Gradient */
        .stApp {
            background: radial-gradient(circle at 50% 50%, #0d1117 0%, #010409 100%);
            color: #e6edf3;
        }
        
        /* Header & Sidebar Glassmorphism */
        header, [data-testid="stSidebar"] {
            background-color: rgba(22, 27, 34, 0.8) !important;
            backdrop-filter: blur(12px);
            border-right: 1px solid rgba(255, 255, 255, 0.05);
        }
        
        /* Buttons - High-End Glow */
        .stButton>button {
            width: 100%;
            border-radius: 12px;
            height: 3.5em;
            background: linear-gradient(135deg, #10a37f 0%, #0e8c6d 100%);
            color: white;
            border: 1px solid rgba(255, 255, 255, 0.1);
            font-weight: 700;
            letter-spacing: 0.5px;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            box-shadow: 0 4px 15px rgba(16, 163, 127, 0.2);
        }
        .stButton>button:hover {
            box-shadow: 0 0 25px rgba(16, 163, 127, 0.6);
            transform: translateY(-2px);
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        
        /* Metrics - Premium Glassmorphism */
        div[data-testid="stMetric"] {
            background: rgba(33, 38, 45, 0.4);
            padding: 25px;
            border-radius: 16px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
            transition: transform 0.3s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: scale(1.02);
            border: 1px solid rgba(16, 163, 127, 0.3);
        }
        
        /* File Uploader Customization */
        section[data-testid="stFileUploadDropzone"] {
            background-color: rgba(22, 27, 34, 0.4);
            border: 2px dashed #10a37f !important;
            border-radius: 16px;
            padding: 2rem;
        }
        
        /* Dataframe (Table) - Professional Polish */
        .stDataFrame {
            background: rgba(13, 17, 23, 0.6) !important;
            border: 1px solid rgba(48, 54, 61, 0.8) !important;
            border-radius: 12px !important;
        }
        
        /* Tabs Styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 10px;
            background-color: transparent;
        }
        .stTabs [data-baseweb="tab"] {
            height: 40px;
            white-space: pre;
            background-color: rgba(33, 38, 45, 0.5);
            border-radius: 8px 8px 0px 0px;
            color: #8b949e;
            border: none;
        }
        .stTabs [aria-selected="true"] {
            background-color: #161b22;
            color: #10a37f !important;
        }
        </style>
        """, unsafe_allow_html=True)

def render_header():
    st.title("🏥 OmniIngest | Enterprise Clinical Gateway")
    st.markdown("<p style='color: #8b949e;'>Phase 0.3: High-Performance Clinical Ingestion Master Build</p>", unsafe_allow_html=True)
    st.markdown("---")

def render_governance_sidebar(governance_logs):
    st.sidebar.markdown("""
        <div style='background-color: #3e1616; padding: 15px; border-radius: 8px; border: 2px solid #ff4d4d; margin-bottom: 20px; text-align: center;'>
            <h4 style='margin: 0; color: #ff8080;'>🚨 [DPDP RULE 8.3 ACTIVE]</h4>
            <small style='color: #8b949e;'>Real-time PII Hard-Purge Enabled</small>
        </div>
    """, unsafe_allow_html=True)
    
    st.sidebar.markdown("### 📜 Governance Log")
    log_container = st.sidebar.empty()
    if governance_logs:
        log_container.code("\n".join(governance_logs), language="bash")
    else:
        log_container.code("# System Ready\n# Awaiting Ingress...", language="bash")

def render_revoked_warning():
    st.markdown("""
        <div style='background-color: #3e1616; color: #ff8080; padding: 15px; border-radius: 8px; border: 1px solid #ff4d4d; margin-bottom: 20px;'>
            <h3 style='margin:0; color: #ff8080;'>⚠️ SESSION REVOKED</h3>
            <p style='margin:5px 0 0 0;'>Data purged per DPDP Rule 8. System locked until session reset.</p>
        </div>
    """, unsafe_allow_html=True)

def get_chart(data):
    # Ensure color column is used
    base = alt.Chart(data).encode(
        x=alt.X('Status', sort=None),
        y='Count',
        color=alt.Color('Color', scale=None),
        tooltip=['Status', 'Count']
    )
    chart = base.mark_bar().properties(
        title="Ingestion Health"
    )
    return chart
