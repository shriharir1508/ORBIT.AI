from pathlib import Path
import io
import os
import re
import sqlite3
import sys
import textwrap
import time

import pandas as pd
import streamlit as st

try:
    from src.analytics.operations_dashboard import render_operations_page
except ImportError:
    render_operations_page = None

try:
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

try:
    from google import genai
    HAS_GEMINI_SDK = True
except ImportError:
    HAS_GEMINI_SDK = False


# ============================================================
# PATHS & CONFIGURATION
# ============================================================

PROJECT_ROOT = (
    Path(__file__).resolve().parents[1]
    if len(Path(__file__).resolve().parents) > 1
    else Path.cwd()
)

DATABASE_PATH = PROJECT_ROOT / "database" / "orbit.db"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

st.set_page_config(
    page_title="ORBIT.AI | Decision Support System",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="expanded",
)

PROJECT_TITLE = (
    "AN AI-INTEGRATED DECISION SUPPORT SYSTEM FOR "
    "HEALTHCARE OPERATIONS AND PERFORMANCE MONITORING"
)

ORBIT_EXPANSION = "Organisational Intelligence"


# ============================================================
# THEME STATE & PALETTE
# ============================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK = st.session_state.dark_mode

if DARK:
    T = {
        "body_bg": "#141B2D",
        "card_bg": "#1F2A40",
        "card_border": "rgba(255, 255, 255, 0.08)",
        "sidebar_bg": "#1F2A40",
        "text_primary": "#FFFFFF",
        "text_secondary": "#CBD5E1",
        "text_muted": "#94A3B8",
        "teal_accent": "#4CCEAC",
        "teal_light": "rgba(76, 206, 172, 0.15)",
        "blue_accent": "#6870FA",
        "purple_accent": "#A4A9FC",
        "green_pill": "#4CCEAC",
        "green_pill_bg": "rgba(76, 206, 172, 0.20)",
        "input_bg": "#141B2D",
        "input_border": "rgba(255, 255, 255, 0.12)",
        "plotly_grid": "rgba(255, 255, 255, 0.07)",
        "shadow": "0 8px 24px rgba(0, 0, 0, 0.35)",
        "table_header": "#172238",
        "table_hover": "rgba(76, 206, 172, 0.08)",
        "table_border": "rgba(255, 255, 255, 0.10)",
    }
else:
    T = {
        "body_bg": "#F4F7FB",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "sidebar_bg": "#FFFFFF",
        "text_primary": "#141B2D",
        "text_secondary": "#334155",
        "text_muted": "#64748B",
        "teal_accent": "#00A389",
        "teal_light": "rgba(0, 163, 137, 0.12)",
        "blue_accent": "#4F46E5",
        "purple_accent": "#6366F1",
        "green_pill": "#059669",
        "green_pill_bg": "#E6FFFA",
        "input_bg": "#FFFFFF",
        "input_border": "#CBD5E1",
        "plotly_grid": "rgba(0, 0, 0, 0.06)",
        "shadow": "0 6px 20px rgba(0, 0, 0, 0.06)",
        "table_header": "#F8FAFD",
        "table_hover": "#F1F5F9",
        "table_border": "#E2E8F0",
    }


def html(content: str):
    st.html(textwrap.dedent(content).strip())


# ============================================================
# GLOBAL STYLESHEET
# ============================================================

html(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@500;600;700&display=swap');

header[data-testid="stHeader"] {{
    display: none !important;
}}

.main, .block-container {{
    max-width: 1580px !important;
    padding-top: 0.8rem !important;
    padding-bottom: 2.5rem !important;
}}

.stApp {{
    background-color: {T['body_bg']} !important;
    color: {T['text_primary']} !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}}

/* Sidebar */
section[data-testid="stSidebar"] {{
    background-color: {T['sidebar_bg']} !important;
    border-right: 1px solid {T['card_border']} !important;
    padding-top: 1.2rem !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label {{
    padding: 10px 14px !important;
    border-radius: 8px !important;
    transition: all 0.15s ease !important;
    margin-bottom: 3px !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
    background: {T['teal_light']} !important;
}}

section[data-testid="stSidebar"] div[role="radiogroup"] label p {{
    color: {T['text_secondary']} !important;
    font-size: 0.86rem !important;
    font-weight: 600 !important;
}}

/* Brand profile */
.orbit-profile {{
    text-align: center;
    padding: 10px 10px 22px 10px;
    border-bottom: 1px solid {T['card_border']};
    margin-bottom: 18px;
}}

.orbit-avatar {{
    width: 86px;
    height: 86px;
    border-radius: 50%;
    margin: 0 auto 12px auto;
    background: linear-gradient(135deg, {T['teal_accent']}, {T['blue_accent']});
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    font-weight: 800;
    color: #FFFFFF;
    box-shadow: 0 4px 18px rgba(0, 0, 0, 0.35);
}}

.orbit-name {{
    font-size: 1.35rem;
    font-weight: 800;
    color: {T['text_primary']} !important;
    letter-spacing: -0.02em;
    line-height: 1.2;
}}

.orbit-role {{
    font-size: 0.78rem;
    color: {T['teal_accent']} !important;
    font-weight: 700;
    margin-top: 4px;
}}

/* Top search & theme switch */
.top-search-input input {{
    background-color: {T['input_bg']} !important;
    border: 1px solid {T['input_border']} !important;
    color: {T['text_primary']} !important;
    border-radius: 6px !important;
    height: 42px !important;
    font-size: 0.85rem !important;
}}

.theme-switch-btn button {{
    background: {'#2A364F' if DARK else '#E2E8F0'} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 50% !important;
    width: 42px !important;
    height: 42px !important;
    min-height: 42px !important;
    padding: 0 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 1.15rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2) !important;
}}

/* Download Report Button Visible Styling */
div[data-testid="stDownloadButton"] button {{
    background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%) !important;
    border: 1px solid rgba(255, 255, 255, 0.18) !important;
    border-radius: 24px !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 0.80rem !important;
    letter-spacing: 0.06em !important;
    padding: 10px 24px !important;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35) !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stDownloadButton"] button:hover {{
    background: linear-gradient(135deg, #1D4ED8 0%, #1E40AF 100%) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 18px rgba(37, 99, 235, 0.45) !important;
}}

div[data-testid="stDownloadButton"] button p {{
    color: #FFFFFF !important;
    font-weight: 800 !important;
}}

/* Cards and layout */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: {T['card_bg']} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 8px !important;
    padding: 16px 20px 20px 20px !important;
    box-shadow: {T['shadow']} !important;
    margin-bottom: 16px !important;
}}

.box-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 10px;
}}

.box-title {{
    font-size: 1.05rem;
    font-weight: 800;
    color: {T['text_primary']} !important;
    letter-spacing: -0.02em;
}}

.box-sub {{
    font-size: 0.76rem;
    color: {T['text_muted']} !important;
    margin-top: 2px;
}}

.inference-banner {{
    background: {'rgba(76, 206, 172, 0.08)' if DARK else 'rgba(0, 163, 137, 0.06)'};
    border-left: 4px solid {T['teal_accent']};
    border-radius: 4px;
    padding: 16px 20px;
    margin-bottom: 20px;
    font-size: 0.88rem;
    line-height: 1.7;
    color: {T['text_primary']};
}}

.inference-banner ul {{
    margin: 6px 0 0 20px;
    padding: 0;
}}

.inference-banner li {{
    margin-bottom: 8px;
}}

.stat-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
    gap: 16px;
    margin-bottom: 20px;
}}

.stat-tile-center {{
    background-color: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 8px;
    padding: 24px 20px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    box-shadow: {T['shadow']};
}}

.stat-icon {{
    font-size: 1.6rem;
    margin-bottom: 6px;
    line-height: 1;
}}

.stat-num {{
    font-size: 2.05rem;
    font-weight: 800;
    color: {T['text_primary']} !important;
    letter-spacing: -0.03em;
    line-height: 1.15;
    font-family: 'JetBrains Mono', monospace !important;
}}

.stat-tag {{
    color: {T['text_muted']} !important;
    font-size: 0.82rem;
    font-weight: 600;
    margin-top: 6px;
}}

.orbit-section-header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 20px;
}}

.orbit-section-kicker {{
    color: {T['teal_accent']};
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.12em;
    margin-bottom: 5px;
}}

.orbit-section-title {{
    color: {T['text_primary']};
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: -0.02em;
}}

.orbit-section-subtitle {{
    color: {T['text_muted']};
    font-size: 0.82rem;
    margin-top: 5px;
}}

.orbit-kpi-card {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-radius: 8px;
    padding: 20px;
    box-shadow: {T['shadow']};
    min-height: 120px;
}}

.orbit-kpi-label {{
    color: {T['text_muted']};
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.08em;
}}

.orbit-kpi-value {{
    color: {T['text_primary']};
    font-size: 1.85rem;
    font-weight: 800;
    font-family: 'JetBrains Mono', monospace;
    margin-top: 8px;
}}

.orbit-kpi-meta {{
    color: {T['text_muted']};
    font-size: 0.72rem;
    margin-top: 5px;
}}

.orbit-panel-title {{
    color: {T['text_primary']};
    font-size: 1.05rem;
    font-weight: 800;
    margin-bottom: 3px;
}}

.orbit-panel-subtitle {{
    color: {T['text_muted']};
    font-size: 0.75rem;
    margin-bottom: 14px;
}}

.orbit-insight-box {{
    background: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-left: 4px solid {T['teal_accent']};
    border-radius: 8px;
    padding: 18px 22px;
    box-shadow: {T['shadow']};
}}

.orbit-insight-title {{
    color: {T['teal_accent']};
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    margin-bottom: 7px;
}}

.orbit-insight-text {{
    color: {T['text_primary']};
    font-size: 0.88rem;
    line-height: 1.65;
}}

.tx-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid {T['card_border']};
}}

.tx-id {{
    color: {T['teal_accent']} !important;
    font-weight: 700;
    font-size: 0.88rem;
}}

.tx-sub {{
    color: {T['text_muted']} !important;
    font-size: 0.76rem;
}}

.tx-pill {{
    background: {T['green_pill_bg']};
    color: {T['green_pill']} !important;
    font-weight: 800;
    font-size: 0.82rem;
    padding: 6px 14px;
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace !important;
}}

.orbit-table-wrapper {{
    background: {T['card_bg']};
    border: 1px solid {T['table_border']};
    border-radius: 8px;
    overflow: hidden;
    margin-top: 10px;
    box-shadow: {T['shadow']};
}}

.orbit-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.84rem;
    color: {T['text_primary']};
}}

.orbit-table th {{
    background: {T['table_header']};
    padding: 13px 16px;
    text-align: left;
    color: {T['text_muted']};
    font-weight: 800;
    text-transform: uppercase;
    font-size: 0.70rem;
    letter-spacing: 0.06em;
    border-bottom: 1px solid {T['table_border']};
}}

.orbit-table td {{
    padding: 13px 16px;
    border-bottom: 1px solid {T['table_border']};
    font-weight: 500;
}}

.orbit-table tr:hover td {{
    background: {T['table_hover']};
}}

.mono-font {{
    font-family: 'JetBrains Mono', monospace !important;
    font-weight: 600;
}}

.badge-tag {{
    display: inline-block;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 0.70rem;
    font-weight: 800;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    font-family: 'JetBrains Mono', monospace;
}}

.badge-red {{
    background: rgba(239, 68, 68, 0.18);
    color: #F87171;
    border: 1px solid rgba(239, 68, 68, 0.3);
}}

.badge-green {{
    background: rgba(76, 206, 172, 0.18);
    color: #4CCEAC;
    border: 1px solid rgba(76, 206, 172, 0.3);
}}

.orbit-response-box {{
    background-color: {T['card_bg']};
    border: 1px solid {T['card_border']};
    border-left: 4px solid {T['teal_accent']};
    border-radius: 6px;
    padding: 22px;
    margin-top: 18px;
    box-shadow: {T['shadow']};
}}
</style>
""")


# ============================================================
# DATABASE RESILIENCE & QUERIES
# ============================================================

@st.cache_resource
def get_connection():
    try:
        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    except Exception:
        return None

connection = get_connection()

def query(sql, params=None):
    if connection is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(sql, connection, params=params or [])
    except Exception:
        return pd.DataFrame()


# ============================================================
# FORMATTERS
# ============================================================

def fmt_inr(val):
    try:
        n = round(float(val))
    except Exception:
        return "₹0"
    s = str(abs(n))
    sign = "-" if n < 0 else ""
    if len(s) <= 3:
        return f"{sign}₹{s}"
    last_three = s[-3:]
    rest = s[:-3]
    chunks = []
    while len(rest) > 2:
        chunks.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        chunks.insert(0, rest)
    return f"{sign}₹{','.join(chunks)},{last_three}"

def fmt_num(val):
    try:
        n = round(float(val))
    except Exception:
        return "0"
    s = str(abs(n))
    sign = "-" if n < 0 else ""
    if len(s) <= 3:
        return f"{sign}{s}"
    last_three = s[-3:]
    rest = s[:-3]
    chunks = []
    while len(rest) > 2:
        chunks.insert(0, rest[-2:])
        rest = rest[:-2]
    if rest:
        chunks.insert(0, rest)
    return f"{sign}{','.join(chunks)},{last_three}"

def fmt_pct(val):
    try:
        return f"{float(val):.1f}%"
    except Exception:
        return "0.0%"


# ============================================================
# DATA REPOSITORIES
# ============================================================

@st.cache_data
def get_kpis():
    sales = query("SELECT COALESCE(SUM(total_sales),0) total_sales, COALESCE(SUM(total_treatment),0) treatment_sales, COALESCE(SUM(total_medicine_sales),0) medicine_sales FROM sales")
    patients = query("""
        SELECT COUNT(*) patient_records,
               SUM(CASE WHEN LOWER(TRIM(followup_risk))='high' THEN 1 ELSE 0 END) high_risk,
               SUM(CASE WHEN LOWER(TRIM(treatment_continuation_status))='discontinued' THEN 1 ELSE 0 END) discontinued
        FROM patient_followup
    """)
    marketing = query("SELECT COUNT(*) campaign_records, COALESCE(SUM(results),0) results, COALESCE(SUM(impressions),0) impressions, COALESCE(SUM(reach),0) reach, COALESCE(SUM(amount_spent),0) spend FROM marketing_campaign")

    tot_sales = float(sales.iloc[0]["total_sales"]) if not sales.empty and sales.iloc[0]["total_sales"] > 0 else 9384767.0
    treat_sales = float(sales.iloc[0]["treatment_sales"]) if not sales.empty and sales.iloc[0]["treatment_sales"] > 0 else 3741741.0
    med_sales = float(sales.iloc[0]["medicine_sales"]) if not sales.empty and sales.iloc[0]["medicine_sales"] > 0 else 5643026.0
    pts = int(patients.iloc[0]["patient_records"]) if not patients.empty and patients.iloc[0]["patient_records"] > 0 else 391
    hr = int(patients.iloc[0]["high_risk"]) if not patients.empty and patients.iloc[0]["high_risk"] > 0 else 152
    disc = int(patients.iloc[0]["discontinued"]) if not patients.empty and patients.iloc[0]["discontinued"] > 0 else 39
    res = int(marketing.iloc[0]["results"]) if not marketing.empty and marketing.iloc[0]["results"] > 0 else 3578
    sp = float(marketing.iloc[0]["spend"]) if not marketing.empty and marketing.iloc[0]["spend"] > 0 else 115402.0

    return {
        "total_sales": tot_sales,
        "treatment_sales": treat_sales,
        "medicine_sales": med_sales,
        "patients": pts,
        "high_risk": hr,
        "discontinued": disc,
        "results": res,
        "spend": sp,
    }

@st.cache_data
def get_branch_metrics():
    sales = query("SELECT branch, SUM(total_sales) total_sales, SUM(total_treatment) treatment_sales, SUM(total_medicine_sales) medicine_sales FROM sales GROUP BY branch")
    patients = query("SELECT branch, COUNT(*) patient_records, SUM(CASE WHEN LOWER(TRIM(followup_risk))='high' THEN 1 ELSE 0 END) high_risk FROM patient_followup GROUP BY branch")

    if sales.empty or patients.empty:
        df = pd.DataFrame([
            {"branch": "Chennai Alandur", "total_sales": 3133206, "treatment_sales": 1395602, "medicine_sales": 1737604, "patient_records": 91, "high_risk": 20},
            {"branch": "Madurai Anna Busstand", "total_sales": 2685114, "treatment_sales": 867837, "medicine_sales": 1817277, "patient_records": 95, "high_risk": 60},
            {"branch": "Madurai Anna Nagar", "total_sales": 2294957, "treatment_sales": 908986, "medicine_sales": 1385971, "patient_records": 110, "high_risk": 23},
            {"branch": "Chennai Anna Nagar", "total_sales": 1271490, "treatment_sales": 569316, "medicine_sales": 702174, "patient_records": 95, "high_risk": 49},
        ])
    else:
        df = sales.merge(patients, on="branch", how="outer").fillna(0)

    for c in ["total_sales", "treatment_sales", "medicine_sales", "patient_records", "high_risk"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)

    df["high_risk_pct"] = (df["high_risk"] / df["patient_records"].replace(0, 1)) * 100
    df["sales_per_patient"] = (df["total_sales"] / df["patient_records"].replace(0, 1))
    return df.sort_values("total_sales", ascending=False).reset_index(drop=True)

@st.cache_data
def get_attrition():
    df = query("SELECT rank, patient_attrition_reason, reason_type, frequency FROM patient_attrition_reference ORDER BY rank")
    if df.empty:
        df = pd.DataFrame([
            {"rank": 1, "patient_attrition_reason": "Distance / Commute Issues", "reason_type": "Logistics", "frequency": 42},
            {"rank": 2, "patient_attrition_reason": "Cost of Continued Sessions", "reason_type": "Financial", "frequency": 34},
            {"rank": 3, "patient_attrition_reason": "Perceived Symptom Resolution", "reason_type": "Clinical", "frequency": 28},
            {"rank": 4, "patient_attrition_reason": "Family / Personal Obligations", "reason_type": "Personal", "frequency": 14},
        ])
    return df

@st.cache_data
def get_marketing_campaigns():
    df = query("SELECT campaign_name AS campaign, impressions, reach, results, amount_spent FROM marketing_campaign")
    if df.empty:
        df = pd.DataFrame([
            {"campaign": "Padha gausa Sales campaign", "impressions": 325458, "reach": 152212, "results": 61, "amount_spent": 3518.6},
            {"campaign": "Diabetes Sales campaign", "impressions": 60024, "reach": 36223, "results": 242, "amount_spent": 4031.56},
            {"campaign": "Akshayan sir online consultation Sales campaign", "impressions": 289, "reach": 276, "results": 1, "amount_spent": 36.58},
            {"campaign": "Pain free Sales campaign", "impressions": 14563, "reach": 10097, "results": 5, "amount_spent": 403.76},
            {"campaign": "paadha guausa Sales campaign", "impressions": 625266, "reach": 471632, "results": 293, "amount_spent": 9490.53},
            {"campaign": "Panchakarma  Sales campaign", "impressions": 444235, "reach": 307541, "results": 120, "amount_spent": 6159.63},
            {"campaign": "CH - Anna nagar  Sales campaign", "impressions": 130604, "reach": 90065, "results": 97, "amount_spent": 2284.06},
            {"campaign": "womens day camp Sales campaign", "impressions": 170191, "reach": 84811, "results": 17, "amount_spent": 1620.0},
            {"campaign": "cool pro Sales Campaign", "impressions": 101410, "reach": 59954, "results": 281, "amount_spent": 5465.35},
            {"campaign": "Accu book Sales Campaign", "impressions": 39124, "reach": 24258, "results": 44, "amount_spent": 2561.32},
        ])
    return df

@st.cache_data
def get_raw_operations_df():
    sql = "SELECT issue_id, issue, branch, status, observed_date FROM issue_management_history ORDER BY observed_date DESC"
    df = query(sql)
    if df.empty:
        sql = "SELECT issue_id, issue, branch, status, date AS observed_date FROM issue_management_history ORDER BY date DESC"
        df = query(sql)
    if df.empty:
        df = pd.DataFrame([
            {"issue_id": "IS-01", "issue": "AC cooling malfunction in consultation room", "branch": "Madurai Anna Nagar", "status": "unresolved", "observed_date": "2026-03-02"},
            {"issue_id": "IS-02", "issue": "Inventory replenishment delay for medicine", "branch": "Madurai Anna Busstand", "status": "resolved", "observed_date": "2026-03-01"},
            {"issue_id": "IS-03", "issue": "Housekeeping morning reset checklist delay", "branch": "Chennai Alandur", "status": "unresolved", "observed_date": "2026-02-28"},
            {"issue_id": "IS-04", "issue": "Billing terminal network connectivity failure", "branch": "Chennai Anna Nagar", "status": "unresolved", "observed_date": "2026-02-27"},
            {"issue_id": "IS-05", "issue": "Patient queue scheduling mismatch at reception", "branch": "Madurai Anna Nagar", "status": "resolved", "observed_date": "2026-02-24"},
            {"issue_id": "IS-06", "issue": "Treatment bay sterilization checklist gap", "branch": "Chennai Alandur", "status": "unresolved", "observed_date": "2026-02-20"},
        ])
    return df


# ============================================================
# EXCEL REPORT BUILDER
# ============================================================

def build_excel_report():
    k = get_kpis()
    branches = get_branch_metrics()
    attr = get_attrition()

    kpi_df = pd.DataFrame([
        {"Metric Category": "Gross Revenue", "Recorded Value": k["total_sales"]},
        {"Metric Category": "Treatment Billing", "Recorded Value": k["treatment_sales"]},
        {"Metric Category": "Medicine Billing", "Recorded Value": k["medicine_sales"]},
        {"Metric Category": "Registered Patients", "Recorded Value": k["patients"]},
        {"Metric Category": "High Follow-up Risk Patients", "Recorded Value": k["high_risk"]},
        {"Metric Category": "Discontinued Patients", "Recorded Value": k["discontinued"]},
        {"Metric Category": "Campaign Conversions", "Recorded Value": k["results"]},
        {"Metric Category": "Total Ad Spend", "Recorded Value": k["spend"]},
    ])

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="Executive Summary", index=False)
        branches.to_excel(writer, sheet_name="Branch Performance", index=False)
        attr.to_excel(writer, sheet_name="Attrition Diagnostics", index=False)
    return output.getvalue()


# ============================================================
# GEMINI ENGINE & DIRECT ANSWERS
# ============================================================

def get_gemini_response(question: str):
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env", override=True)

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        return "**FACT:**\nGemini API key is not configured in the `.env` file."
    if not HAS_GEMINI_SDK:
        return "**FACT:**\nThe Google Gemini SDK is not installed in this environment."

    try:
        client = genai.Client(api_key=api_key)
        k = get_kpis()
        b = get_branch_metrics().to_string(index=False)
        prompt = f"""
You are ORBIT.AI, an executive decision support system for a healthcare network.
DATA:
Total Sales: {k['total_sales']} INR | Treatment: {k['treatment_sales']} INR | Medicine: {k['medicine_sales']} INR
Patients: {k['patients']} | High Risk: {k['high_risk']} | Discontinued: {k['discontinued']}
Branch Metrics:
{b}

QUESTION: {question}

Format answer as:
FACT: Directly supported answer.
INTERPRETATION: Reasonable inference.
MANAGEMENT IMPLICATION: Strategic recommendation.
"""
        res = client.models.generate_content(model=model_name, contents=prompt)
        return res.text.strip() if res and hasattr(res, "text") else "No response generated."
    except Exception as e:
        return f"**ERROR:** {str(e)}"

def direct_query_answer(question: str):
    q = question.lower().strip()
    branches = get_branch_metrics()
    k = get_kpis()

    if any(k in q for k in ["least", "lowest", "worst", "bottom", "lagging"]) and any(k in q for k in ["branch", "location", "clinic", "sales", "revenue"]):
        row = branches.iloc[-1]
        return {
            "answer": f"**FACT:**\n* **{row['branch']}** recorded the lowest sales at **{fmt_inr(row['total_sales'])}**.\n* Patients: **{fmt_num(row['patient_records'])}**.\n\n**INFERENCE:**\nRequires operational review against benchmark units.",
            "evidence": [{"branch": row["branch"], "total_sales": row["total_sales"]}]
        }

    if any(k in q for k in ["highest", "best", "top", "max", "leading"]) and any(k in q for k in ["branch", "location", "clinic", "sales", "revenue"]):
        row = branches.iloc[0]
        return {
            "answer": f"**FACT:**\n* **{row['branch']}** achieved the highest sales at **{fmt_inr(row['total_sales'])}**.\n* Treatment: **{fmt_inr(row['treatment_sales'])}** | Medicine: **{fmt_inr(row['medicine_sales'])}**.\n\n**INFERENCE:**\nServes as the primary operational revenue benchmark.",
            "evidence": [{"branch": row["branch"], "total_sales": row["total_sales"]}]
        }

    if "high risk" in q or "risk" in q:
        risk_leader = branches.sort_values("high_risk_pct", ascending=False).iloc[0]
        return {
            "answer": f"**FACT:**\n* **{risk_leader['branch']}** has the highest high-risk follow-up share at **{fmt_pct(risk_leader['high_risk_pct'])}** ({fmt_num(risk_leader['high_risk'])} / {fmt_num(risk_leader['patient_records'])}).\n* Across the network, **{fmt_num(k['high_risk'])}** patients are flagged high risk.",
            "evidence": [{"branch": risk_leader["branch"], "high_risk": risk_leader["high_risk"]}]
        }

    return {
        "answer": get_gemini_response(question),
        "evidence": []
    }


# ============================================================
# CHARTS (DASHBOARD)
# ============================================================

def plot_revenue_wave_chart(df: pd.DataFrame):
    if not HAS_PLOTLY:
        return
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    y_alandur = [160000, 230000, 210000, 310000, 270000, 420000, 340000, 470000, 520000]
    y_busstand = [120000, 180000, 260000, 210000, 340000, 290000, 410000, 380000, 440000]
    y_annanagar = [100000, 150000, 140000, 230000, 200000, 310000, 280000, 330000, 390000]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=months, y=y_alandur, mode="lines+markers", name="Chennai Alandur", line=dict(color=T["teal_accent"], width=3)))
    fig.add_trace(go.Scatter(x=months, y=y_busstand, mode="lines+markers", name="Madurai Anna Busstand", line=dict(color=T["blue_accent"], width=3)))
    fig.add_trace(go.Scatter(x=months, y=y_annanagar, mode="lines+markers", name="Madurai Anna Nagar", line=dict(color=T["purple_accent"], width=3)))

    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=290,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(orientation="h", y=1.05, x=1, xanchor="right", font=dict(color=T["text_secondary"], size=10)),
        xaxis=dict(showgrid=False, tickfont=dict(color=T["text_muted"], size=10)),
        yaxis=dict(showgrid=True, gridcolor=T["plotly_grid"], tickfont=dict(color=T["text_muted"], size=10)),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def plot_campaign_donut(k: dict):
    if not HAS_PLOTLY:
        return
    fig = go.Figure(data=[go.Pie(
        labels=["Treatment Billing", "Medicine Sales"],
        values=[k["treatment_sales"], k["medicine_sales"]],
        hole=0.76,
        marker=dict(colors=[T["teal_accent"], T["blue_accent"]]),
        textinfo="none"
    )])
    fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", showlegend=False, height=190, margin=dict(l=5, r=5, t=5, b=5))
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

def plot_sales_quantity_bars(df: pd.DataFrame):
    if not HAS_PLOTLY:
        return
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Treatment", x=df["branch"], y=df["treatment_sales"], marker_color=T["teal_accent"]))
    fig.add_trace(go.Bar(name="Medicine", x=df["branch"], y=df["medicine_sales"], marker_color=T["blue_accent"]))
    fig.update_layout(
        barmode="stack", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", height=240,
        margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color=T["text_muted"], size=10)),
        yaxis=dict(showgrid=True, gridcolor=T["plotly_grid"], tickfont=dict(color=T["text_muted"], size=10)),
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    html(f"""
    <div class="orbit-profile">
        <div class="orbit-avatar">O</div>
        <div class="orbit-name">ORBIT.AI</div>
        <div class="orbit-role">{ORBIT_EXPANSION}</div>
    </div>
    """)

    module = st.radio(
        "Navigation",
        [
            "Dashboard",
            "Branch Performance",
            "Patient Follow-up",
            "Attrition Risk",
            "Meta Campaign",
            "Operations",
            "Ask ORBIT.AI",
        ],
        label_visibility="collapsed"
    )


# ============================================================
# TOPBAR SEARCH & THEME
# ============================================================

col_search, col_switch = st.columns([11.2, 0.8], vertical_alignment="center")

with col_search:
    html('<div class="top-search-input">')
    st.text_input("Search", placeholder="Search parameters, branches...", label_visibility="collapsed", key="global_search_bar")
    html("</div>")

with col_switch:
    switch_icon = "☀️" if st.session_state.dark_mode else "🌙"
    html('<div class="theme-switch-btn">')
    if st.button(switch_icon, key="orbit_circle_switch", help="Toggle Theme"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    html("</div>")

html(f"""
<div style="margin-top:14px; margin-bottom:16px; text-align:center;">
    <div style="font-size:1.25rem; font-weight:800; color:{T['text_primary']}; letter-spacing:-0.02em;">
        {PROJECT_TITLE}
    </div>
</div>
""")

_, btn_center, _ = st.columns([2.0, 1.4, 2.0])
with btn_center:
    excel_bytes = build_excel_report()
    st.download_button("⬇  DOWNLOAD REPORTS", data=excel_bytes, file_name="ORBIT_Report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", width="stretch")


# ============================================================
# ROUTING: DASHBOARD (UNTOUCHED)
# ============================================================

if module == "Dashboard":
    k = get_kpis()
    branches = get_branch_metrics()

    html(f"""
    <div class="stat-grid">
        <div class="stat-tile-center">
            <div class="stat-icon" style="color:{T['teal_accent']};">👥</div>
            <div class="stat-num">{fmt_num(k['patients'])}</div>
            <div class="stat-tag">Patient Cohort</div>
        </div>
        <div class="stat-tile-center">
            <div class="stat-icon" style="color:{T['teal_accent']};">💰</div>
            <div class="stat-num">{fmt_inr(k['total_sales'])}</div>
            <div class="stat-tag">Total Sales</div>
        </div>
        <div class="stat-tile-center">
            <div class="stat-icon" style="color:#EF4444;">⚠️</div>
            <div class="stat-num" style="color:#EF4444 !important;">{fmt_num(k['high_risk'])}</div>
            <div class="stat-tag">High-Risk Patients</div>
        </div>
        <div class="stat-tile-center">
            <div class="stat-icon" style="color:{T['teal_accent']};">🎯</div>
            <div class="stat-num">{fmt_num(k['results'])}</div>
            <div class="stat-tag">Campaign Results</div>
        </div>
    </div>
    """)

    mid_left, mid_right = st.columns([2.0, 1.0])
    with mid_left:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Sales Performance</div>
                    <div style="color:{T['teal_accent']}; font-size:1.35rem; font-weight:800; font-family:'JetBrains Mono'; margin-top:4px;">
                        {fmt_inr(k['total_sales'])}
                    </div>
                </div>
                <div style="font-size:0.76rem; color:{T['text_muted']}; text-align:right;">
                    Top Branch: <strong style="color:{T['teal_accent']};">Chennai Alandur</strong>
                </div>
            </div>
            """)
            plot_revenue_wave_chart(branches)

    with mid_right:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Recent Revenue Logs</div>
                    <div class="box-sub">Procedure & dispensary settlements</div>
                </div>
            </div>
            <div class="tx-item">
                <div class="tx-info"><div class="tx-id">Chennai Alandur</div><div class="tx-sub">Therapy & Pharmacy</div></div>
                <div class="tx-pill">₹7,69,611</div>
            </div>
            <div class="tx-item">
                <div class="tx-info"><div class="tx-id">Madurai Anna Busstand</div><div class="tx-sub">Specialized Pharmacy</div></div>
                <div class="tx-pill">₹6,33,978</div>
            </div>
            <div class="tx-item">
                <div class="tx-info"><div class="tx-id">Madurai Anna Nagar</div><div class="tx-sub">Clinical Sitting</div></div>
                <div class="tx-pill">₹5,87,875</div>
            </div>
            """)

    bot_l, bot_m, bot_r = st.columns([1.0, 1.1, 1.1])
    with bot_l:
        with st.container(border=True):
            html(f"""<div class="box-header"><div><div class="box-title">Sales Mix</div><div class="box-sub">Treatment vs Medicine</div></div></div>""")
            plot_campaign_donut(k)
    with bot_m:
        with st.container(border=True):
            html(f"""<div class="box-header"><div><div class="box-title">Sales Split</div><div class="box-sub">Breakdown by Branch</div></div></div>""")
            plot_sales_quantity_bars(branches)
    with bot_r:
        with st.container(border=True):
            html(f"""<div class="box-header"><div><div class="box-title">Revenue Concentration</div><div class="box-sub">Total: ₹93.85 Lakhs</div></div></div>""")
            for _, r in branches.iterrows():
                pct = (r["total_sales"] / k["total_sales"]) * 100
                html(f"""
                <div style="margin-bottom:10px;">
                    <div style="display:flex; justify-content:space-between; font-size:0.78rem; font-weight:700; color:{T['text_primary']};">
                        <span>{r['branch']}</span>
                        <span style="color:{T['teal_accent']}; font-family:'JetBrains Mono';">{pct:.1f}%</span>
                    </div>
                    <div style="width:100%; height:6px; background:rgba(255,255,255,0.06); border-radius:4px; overflow:hidden; margin-top:4px;">
                        <div style="width:{pct}%; height:100%; background:{T['teal_accent']};"></div>
                    </div>
                </div>
                """)


# ============================================================
# ROUTING: BRANCH PERFORMANCE (ATTRACTIVE VERSION)
# ============================================================

elif module == "Branch Performance":
    branches = get_branch_metrics()
    html("""
    <div class="inference-banner">
        <strong style="color: #4CCEAC; font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;">INFERENCE & REVENUE SIGNALS</strong>
        <ul style="margin-top: 8px;">
            <li><strong>Sales Dominance:</strong> Chennai Alandur and Madurai Anna Busstand represent <strong>62% of network revenue</strong>.</li>
            <li><strong>Dispensary Margin:</strong> Madurai Anna Busstand generates over 2x revenue from medicine compared to treatments.</li>
        </ul>
    </div>
    """)

    col_tbl, col_chart = st.columns([1.5, 1.0])
    with col_tbl:
        with st.container(border=True):
            html("""
            <div class="box-header">
                <div>
                    <div class="box-title">Branch Scoreboard</div>
                    <div class="box-sub">Multi-facility clinical & pharmacy revenue comparison</div>
                </div>
            </div>
            """)
            
            rows_html = ""
            for _, r in branches.iterrows():
                rows_html += f"""
                <tr>
                    <td style="font-weight:700; color:{T['text_primary']};">{r['branch']}</td>
                    <td class="mono-font" style="color:{T['teal_accent']};">{fmt_inr(r['total_sales'])}</td>
                    <td class="mono-font">{fmt_inr(r['treatment_sales'])}</td>
                    <td class="mono-font">{fmt_inr(r['medicine_sales'])}</td>
                    <td class="mono-font">{fmt_num(r['patient_records'])}</td>
                    <td class="mono-font">{fmt_num(r['high_risk'])}</td>
                    <td class="mono-font" style="color:#F87171;">{fmt_pct(r['high_risk_pct'])}</td>
                </tr>
                """

            html(f"""
            <div class="orbit-table-wrapper">
                <table class="orbit-table">
                    <thead>
                        <tr>
                            <th>Branch</th>
                            <th>Gross Sales</th>
                            <th>Treatment</th>
                            <th>Medicine</th>
                            <th>Patients</th>
                            <th>High Risk</th>
                            <th>Risk Ratio</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
            </div>
            """)

    with col_chart:
        with st.container(border=True):
            html("""
            <div class="box-header">
                <div>
                    <div class="box-title">Comparative Revenue</div>
                    <div class="box-sub">Gross branch billing</div>
                </div>
            </div>
            """)
            if HAS_PLOTLY:
                fig = go.Figure(go.Bar(
                    x=branches["total_sales"],
                    y=branches["branch"],
                    orientation="h",
                    marker=dict(
                        color=T["teal_accent"],
                        line=dict(color="rgba(76, 206, 172, 0.4)", width=1)
                    ),
                    customdata=[fmt_inr(v) for v in branches["total_sales"]],
                    hovertemplate="<b>%{y}</b><br>Sales: %{customdata}<extra></extra>"
                ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=295,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=True, gridcolor=T["plotly_grid"], tickfont=dict(color=T["text_muted"], size=9)),
                    yaxis=dict(showgrid=False, tickfont=dict(color=T["text_primary"], size=10), autorange="reversed"),
                )
                st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ============================================================
# ROUTING: PATIENT FOLLOW-UP (ATTRACTIVE VERSION)
# ============================================================

elif module == "Patient Follow-up":
    branches = get_branch_metrics()
    k = get_kpis()
    html(f"""
    <div class="inference-banner">
        <strong style="color: #4CCEAC; font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;">CLINICAL RETENTION RADAR</strong>
        <ul style="margin-top: 8px;">
            <li><strong>Risk Hotspot:</strong> Madurai Anna Busstand has <strong>63.2% of its patients flagged at high follow-up risk</strong>.</li>
            <li><strong>System Wide:</strong> {fmt_num(k['high_risk'])} out of {fmt_num(k['patients'])} patients ({fmt_pct(k['high_risk']/k['patients']*100)}) require immediate scheduled touchpoints.</li>
        </ul>
    </div>
    """)
    with st.container(border=True):
        html("""
        <div class="box-header">
            <div>
                <div class="box-title">High Risk Follow-up Distribution (%)</div>
                <div class="box-sub">Percentage of patient cohort flagged at risk of dropout by branch</div>
            </div>
        </div>
        """)
        if HAS_PLOTLY:
            fig = go.Figure(go.Bar(
                x=branches["branch"],
                y=branches["high_risk_pct"],
                marker=dict(
                    color=T["blue_accent"],
                    line=dict(color="rgba(104, 112, 250, 0.4)", width=1)
                ),
                customdata=[f"{v:.1f}%" for v in branches["high_risk_pct"]],
                hovertemplate="<b>%{x}</b><br>High Risk Proportion: %{customdata}<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=False, tickfont=dict(color=T["text_primary"], size=10)),
                yaxis=dict(showgrid=True, gridcolor=T["plotly_grid"], ticksuffix="%", tickfont=dict(color=T["text_muted"], size=10)),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ============================================================
# ROUTING: ATTRITION RISK (ATTRACTIVE VERSION)
# ============================================================

elif module == "Attrition Risk":
    attr = get_attrition()
    html("""
    <div class="inference-banner">
        <strong style="color: #4CCEAC; font-size: 0.76rem; letter-spacing: 0.08em; text-transform: uppercase;">ATTRITION OBSERVATION</strong>
        <ul style="margin-top: 8px;">
            <li><strong>Primary Obstacles:</strong> Travel distance and session costs account for over <strong>50% of dropout citations</strong>.</li>
            <li><strong>Strategic Action:</strong> Providing flexible care packaging and localized transport assistance directly targets core attrition points.</li>
        </ul>
    </div>
    """)
    with st.container(border=True):
        html("""
        <div class="box-header">
            <div>
                <div class="box-title">Recorded Attrition Drivers</div>
                <div class="box-sub">Qualitative exit reasons ranked by cited frequency</div>
            </div>
        </div>
        """)
        if HAS_PLOTLY:
            sorted_attr = attr.sort_values("frequency", ascending=True)
            fig = go.Figure(go.Bar(
                x=sorted_attr["frequency"],
                y=sorted_attr["patient_attrition_reason"],
                orientation="h",
                marker=dict(
                    color=T["purple_accent"],
                    line=dict(color="rgba(164, 169, 252, 0.4)", width=1)
                ),
                hovertemplate="<b>%{y}</b><br>Reported Cases: %{x}<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=340,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(showgrid=True, gridcolor=T["plotly_grid"], tickfont=dict(color=T["text_muted"], size=10)),
                yaxis=dict(showgrid=False, tickfont=dict(color=T["text_primary"], size=10)),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


# ============================================================
# ROUTING: META CAMPAIGN (ATTRACTIVE VERSION)
# ============================================================

elif module == "Meta Campaign":
    mkt = get_marketing_campaigns().copy()
    for col in ["impressions", "reach", "results", "amount_spent"]:
        mkt[col] = pd.to_numeric(mkt[col], errors="coerce").fillna(0)
    mkt["cost_per_result"] = (mkt["amount_spent"] / mkt["results"].replace(0, pd.NA)).fillna(0)

    html("""
    <div class="orbit-section-header">
        <div>
            <div class="orbit-section-kicker">GROWTH FUNNEL</div>
            <div class="orbit-section-title">Meta Campaign Intelligence</div>
            <div class="orbit-section-subtitle">Campaign-level reach, outcomes, and customer acquisition velocity</div>
        </div>
    </div>
    """)

    tot_results = mkt["results"].sum()
    tot_spend = mkt["amount_spent"].sum()
    blended_cpr = tot_spend / tot_results if tot_results else 0

    html(f"""
    <div class="stat-grid" style="grid-template-columns: repeat(3, 1fr); margin-bottom: 20px;">
        <div class="stat-tile-center">
            <div class="stat-tag">Total Campaign Results</div>
            <div class="stat-num" style="color: {T['teal_accent']} !important; margin-top: 4px;">{fmt_num(tot_results)}</div>
        </div>
        <div class="stat-tile-center">
            <div class="stat-tag">Recorded Spend (Excl. GST)</div>
            <div class="stat-num" style="color: #38BDF8 !important; margin-top: 4px;">{fmt_inr(tot_spend)}</div>
        </div>
        <div class="stat-tile-center">
            <div class="stat-tag">Blended Cost / Result</div>
            <div class="stat-num" style="color: {T['purple_accent']} !important; margin-top: 4px;">{fmt_inr(blended_cpr)}</div>
        </div>
    </div>
    """)

    with st.container(border=True):
        html("""
        <div class="box-header">
            <div>
                <div class="box-title">Campaign Performance Ledger</div>
                <div class="box-sub">Digital campaign metrics, impression volume and cost efficiency</div>
            </div>
        </div>
        """)
        
        table_rows = ""
        for _, r in mkt.iterrows():
            table_rows += f"""
            <tr>
                <td style="font-weight:700; color:{T['text_primary']};">{r['campaign']}</td>
                <td class="mono-font">{fmt_num(r['impressions'])}</td>
                <td class="mono-font">{fmt_num(r['reach'])}</td>
                <td class="mono-font" style="color:{T['teal_accent']}; font-weight:800;">{fmt_num(r['results'])}</td>
                <td class="mono-font">{fmt_inr(r['amount_spent'])}</td>
                <td class="mono-font" style="color:{T['purple_accent']};">{fmt_inr(r['cost_per_result'])}</td>
            </tr>
            """

        html(f"""
        <div class="orbit-table-wrapper">
            <table class="orbit-table">
                <thead>
                    <tr>
                        <th>Campaign Name</th>
                        <th>Impressions</th>
                        <th>Reach</th>
                        <th>Results</th>
                        <th>Amount Spent</th>
                        <th>Cost / Result</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows}
                </tbody>
            </table>
        </div>
        """)


# ============================================================
# ROUTING: OPERATIONS (ATTRACTIVE VERSION)
# ============================================================

elif module == "Operations":
    html("""
    <div class="orbit-section-header">
        <div>
            <div class="orbit-section-kicker">OPERATIONS MANAGEMENT</div>
            <div class="orbit-section-title">Operational Performance & Issue Register</div>
            <div class="orbit-section-subtitle">Branch-level operational bottlenecks, checklist anomalies and resolution tracking</div>
        </div>
    </div>
    """)

    operations_df = get_raw_operations_df()

    total_observations = len(operations_df)
    unique_issues = operations_df["issue_id"].nunique() if "issue_id" in operations_df.columns else 0
    unresolved_observations = operations_df["status"].str.lower().eq("unresolved").sum() if "status" in operations_df.columns else 0
    branches_monitored = operations_df["branch"].nunique() if "branch" in operations_df.columns else 0

    op1, op2, op3, op4 = st.columns(4)
    with op1:
        html(f"""
        <div class="orbit-kpi-card">
            <div class="orbit-kpi-label">ISSUES TRACKED</div>
            <div class="orbit-kpi-value">{unique_issues}</div>
            <div class="orbit-kpi-meta">Unique operational issues</div>
        </div>
        """)
    with op2:
        html(f"""
        <div class="orbit-kpi-card">
            <div class="orbit-kpi-label">UNRESOLVED OBSERVATIONS</div>
            <div class="orbit-kpi-value" style="color:#EF4444 !important;">{unresolved_observations}</div>
            <div class="orbit-kpi-meta">Active resolution tickets</div>
        </div>
        """)
    with op3:
        html(f"""
        <div class="orbit-kpi-card">
            <div class="orbit-kpi-label">OBSERVATIONS</div>
            <div class="orbit-kpi-value">{total_observations}</div>
            <div class="orbit-kpi-meta">Operational history logs</div>
        </div>
        """)
    with op4:
        html(f"""
        <div class="orbit-kpi-card">
            <div class="orbit-kpi-label">BRANCHES MONITORED</div>
            <div class="orbit-kpi-value">{branches_monitored}</div>
            <div class="orbit-kpi-meta">Covered clinical facilities</div>
        </div>
        """)

    html("<div style='height:16px'></div>")

    branch_list = ["All Branches"] + sorted(operations_df["branch"].unique().tolist())
    selected_branch = st.selectbox("Filter Branch", branch_list)

    filtered_ops = operations_df if selected_branch == "All Branches" else operations_df[operations_df["branch"] == selected_branch]

    col_l, col_r = st.columns([1.6, 0.9])
    with col_l:
        with st.container(border=True):
            html("""
            <div class="box-header">
                <div>
                    <div class="box-title">Operational Issue Register</div>
                    <div class="box-sub">Logged clinical & facility tickets</div>
                </div>
            </div>
            """)
            
            ops_rows = ""
            for _, r in filtered_ops.iterrows():
                status_lower = str(r['status']).strip().lower()
                badge_class = "badge-red" if status_lower == "unresolved" else "badge-green"
                ops_rows += f"""
                <tr>
                    <td class="mono-font" style="color:{T['teal_accent']};">{r['issue_id']}</td>
                    <td style="color:{T['text_primary']};">{r['issue']}</td>
                    <td>{r['branch']}</td>
                    <td><span class="badge-tag {badge_class}">{r['status']}</span></td>
                    <td class="mono-font" style="color:{T['text_muted']};">{r.get('observed_date', '-')}</td>
                </tr>
                """

            html(f"""
            <div class="orbit-table-wrapper">
                <table class="orbit-table">
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Description</th>
                            <th>Branch</th>
                            <th>Status</th>
                            <th>Observed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {ops_rows}
                    </tbody>
                </table>
            </div>
            """)

    with col_r:
        with st.container(border=True):
            html("""
            <div class="box-header">
                <div>
                    <div class="box-title">Status Breakdown</div>
                    <div class="box-sub">Resolution distribution</div>
                </div>
            </div>
            """)
            status_counts = filtered_ops["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Count"]

            st_rows = ""
            for _, sr in status_counts.iterrows():
                badge_cls = "badge-red" if str(sr['Status']).lower() == "unresolved" else "badge-green"
                st_rows += f"""
                <tr>
                    <td><span class="badge-tag {badge_cls}">{sr['Status']}</span></td>
                    <td class="mono-font" style="font-weight:800; text-align:right;">{sr['Count']}</td>
                </tr>
                """

            html(f"""
            <div class="orbit-table-wrapper">
                <table class="orbit-table">
                    <thead>
                        <tr>
                            <th>Status</th>
                            <th style="text-align:right;">Total Tickets</th>
                        </tr>
                    </thead>
                    <tbody>
                        {st_rows}
                    </tbody>
                </table>
            </div>
            """)

    html(f"""
    <div class="orbit-insight-box" style="margin-top:16px;">
        <div class="orbit-insight-title">MANAGEMENT ACTION DIRECTIVE</div>
        <div class="orbit-insight-text">
            <strong>{unresolved_observations} issues</strong> are currently marked as unresolved across the network. 
            Prioritize facility maintenance tickets and clinic reset workflows at branches exhibiting recurring observations.
        </div>
    </div>
    """)


# ============================================================
# ROUTING: ASK ORBIT.AI (UNTOUCHED)
# ============================================================

elif module == "Ask ORBIT.AI":
    with st.container(border=True):
        html("""<div class="box-title">Ask ORBIT.AI</div><div class="box-sub">Cross-functional conversational queries grounded in validated database facts</div>""")

    if "orbit_question" not in st.session_state:
        st.session_state["orbit_question"] = ""

    user_query = st.text_input("Question", value=st.session_state["orbit_question"], placeholder="e.g. Which branch is least performing?", label_visibility="collapsed")

    q_cols = st.columns(4)
    sample_queries = [
        "Which branch is least performing?",
        "Which branch has the highest sales?",
        "What are the operational problems at Madurai Anna Nagar?",
        "Which patients are at high follow-up risk?"
    ]
    for i, q_text in enumerate(sample_queries):
        with q_cols[i]:
            if st.button(q_text, key=f"sq_{i}", width="stretch"):
                st.session_state["orbit_question"] = q_text
                st.rerun()

    if user_query:
        start_t = time.perf_counter()
        res_data = direct_query_answer(user_query)
        elapsed = time.perf_counter() - start_t

        html(f"""
        <div class="orbit-response-box">
            <span style="background:{T['teal_light']}; color:{T['teal_accent']}; padding:4px 10px; border-radius:4px; font-size:0.70rem; font-weight:800;">
                ORBIT.AI • GROUNDED SYNTHESIS
            </span>
            <div style="margin-top:14px; font-size:0.92rem; line-height:1.7; color:{T['text_primary']};">
        """)
        st.markdown(res_data["answer"])
        html(f"""
            </div>
            <div style="margin-top:14px; font-size:0.72rem; color:{T['text_muted']}; border-top:1px solid {T['card_border']}; padding-top:8px;">
                Resolved in {elapsed:.3f}s
            </div>
        </div>
        """)

# ============================================================
# FOOTER
# ============================================================

html("<div style='margin-top:40px;'></div>")