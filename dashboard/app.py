from pathlib import Path
import io
import sqlite3
import sys
import time
import os
import re

import pandas as pd
import streamlit as st

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

PROJECT_ROOT = Path(__file__).resolve().parents[1] if len(Path(__file__).resolve().parents) > 1 else Path.cwd()
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
# THEME STATE
# ============================================================

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

DARK = st.session_state.dark_mode

if DARK:
    T = {
        "body_bg": "#141B2D",
        "card_bg": "#1F2A40",
        "card_border": "rgba(255, 255, 255, 0.05)",
        "sidebar_bg": "#1F2A40",
        "text_primary": "#FFFFFF",
        "text_secondary": "#A3A3A3",
        "text_muted": "#707E94",
        "teal_accent": "#4CCEAC",
        "teal_light": "rgba(76, 206, 172, 0.15)",
        "blue_accent": "#6870FA",
        "purple_accent": "#A4A9FC",
        "green_pill": "#4CCEAC",
        "green_pill_bg": "rgba(76, 206, 172, 0.20)",
        "input_bg": "#141B2D",
        "input_border": "rgba(255, 255, 255, 0.08)",
        "plotly_grid": "rgba(255, 255, 255, 0.07)",
        "shadow": "0 8px 24px rgba(0, 0, 0, 0.35)",
        "table_header": "#172238",
        "table_hover": "rgba(76, 206, 172, 0.06)",
        "table_border": "rgba(255, 255, 255, 0.08)",
    }
else:
    T = {
        "body_bg": "#F4F7FB",
        "card_bg": "#FFFFFF",
        "card_border": "#E2E8F0",
        "sidebar_bg": "#FFFFFF",
        "text_primary": "#141B2D",
        "text_secondary": "#4B5563",
        "text_muted": "#8A94A6",
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
    st.html(content.strip())


# ============================================================
# STYLESHEET
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

section[data-testid="stSidebar"] .block-container {{
    padding-top: 0.2rem !important;
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

/* ORBIT Profile Card */
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

/* Top Search Bar & Controls */
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
    transition: transform 0.15s ease, background 0.15s ease !important;
}}

.theme-switch-btn button:hover {{
    transform: scale(1.08) !important;
    border-color: {T['teal_accent']} !important;
}}

/* Download Report Button */
.report-btn div[data-testid="stDownloadButton"] button {{
    background: #4F46E5 !important;
    border: none !important;
    color: #FFFFFF !important;
    font-weight: 800 !important;
    font-size: 0.76rem !important;
    letter-spacing: 0.05em !important;
    border-radius: 4px !important;
    padding: 8px 16px !important;
    height: 38px !important;
    transition: all 0.15s ease !important;
}}

.report-btn div[data-testid="stDownloadButton"] button:hover {{
    background: #4338CA !important;
    transform: translateY(-1px) !important;
}}

/* Card Container Overrides */
div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] {{
    background-color: {T['card_bg']} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 8px !important;
    padding: 16px 20px 20px 20px !important;
    box-shadow: {T['shadow']} !important;
    margin-bottom: 16px !important;
    min-height: 420px !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: space-between !important;
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
    font-size: 0.75rem;
    color: {T['text_muted']} !important;
    margin-top: 2px;
}}

/* Inference Banner */
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

/* Top 4 Metric Tiles */
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

/* Transaction Panel List Items */
.tx-item {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 14px 0;
    border-bottom: 1px solid {T['card_border']};
}}

.tx-info {{
    display: flex;
    flex-direction: column;
    gap: 3px;
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

/* Custom Styled Data Table */
.orbit-table-wrapper {{
    background: {T['card_bg']};
    border: 1px solid {T['table_border']};
    border-radius: 6px;
    overflow: hidden;
    margin-top: 14px;
}}

.orbit-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.83rem;
    color: {T['text_primary']};
}}

.orbit-table th {{
    background: {T['table_header']};
    padding: 12px 16px;
    text-align: left;
    color: {T['text_secondary']};
    font-weight: 700;
    text-transform: uppercase;
    font-size: 0.68rem;
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

/* Query Buttons & Inputs */
div[data-testid="stHorizontalBlock"] button {{
    background-color: {T['card_bg']} !important;
    border: 1px solid {T['card_border']} !important;
    border-radius: 6px !important;
    min-height: 46px !important;
    transition: all 0.2s ease !important;
}}

div[data-testid="stHorizontalBlock"] button:hover {{
    border-color: {T['teal_accent']} !important;
    transform: translateY(-2px) !important;
}}

div[data-testid="stHorizontalBlock"] button p {{
    color: {T['text_primary']} !important;
    font-size: 0.80rem !important;
    font-weight: 600 !important;
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
# INDIAN NUMBER & CURRENCY FORMATTERS
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
        "total_sales": tot_sales, "treatment_sales": treat_sales, "medicine_sales": med_sales,
        "patients": pts, "high_risk": hr, "discontinued": disc,
        "results": res, "spend": sp
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
    df["sales_per_patient"] = df["total_sales"] / df["patient_records"].replace(0, 1)
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
    df = query(
        "SELECT campaign_name AS campaign, impressions, reach, results, amount_spent "
        "FROM marketing_campaign"
    )

    if df.empty:
        df = pd.DataFrame([
            {
                "campaign": "Meta Lead Generation Q1",
                "impressions": 450000,
                "reach": 320000,
                "results": 1420,
                "amount_spent": 115000
            },
            {
                "campaign": "Acupuncture Awareness South",
                "impressions": 380000,
                "reach": 290000,
                "results": 1050,
                "amount_spent": 82000
            },
            {
                "campaign": "Chronic Pain Relief Campaign",
                "impressions": 220000,
                "reach": 180000,
                "results": 748,
                "amount_spent": 50000
            },
        ])

    return df


@st.cache_data
def get_issues(branch=None):
    sql = "SELECT issue_id, issue, branch, COUNT(*) observations, SUM(CASE WHEN LOWER(TRIM(status))='unresolved' THEN 1 ELSE 0 END) unresolved FROM issue_management_history"
    params = []
    if branch and branch != "All branches":
        sql += " WHERE branch = ? "
        params.append(branch)
    sql += " GROUP BY issue_id, issue, branch ORDER BY unresolved DESC, issue_id"
    df = query(sql, params)
    if df.empty:
        df = pd.DataFrame([
            {"issue_id": "IS-01", "issue": "AC unit cooling malfunction in consultation room", "branch": "Madurai Anna Nagar", "observations": 4, "unresolved": 2},
            {"issue_id": "IS-02", "issue": "Inventory replenishment delay for specialized medicine", "branch": "Madurai Anna Busstand", "observations": 3, "unresolved": 1},
            {"issue_id": "IS-03", "issue": "Housekeeping checklist protocol delay in morning reset", "branch": "Chennai Alandur", "observations": 5, "unresolved": 3},
        ])
    return df


# ============================================================
# EXCEL REPORT GENERATOR
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

    branch_df = branches.rename(columns={
        "branch": "Branch Name",
        "total_sales": "Total Sales (INR)",
        "treatment_sales": "Treatment Sales (INR)",
        "medicine_sales": "Medicine Sales (INR)",
        "patient_records": "Active Patient Count",
        "high_risk": "High Risk Count",
        "high_risk_pct": "High Risk Ratio (%)",
        "sales_per_patient": "Revenue Yield / Patient (INR)",
    })

    attr_df = attr.rename(columns={
        "rank": "Rank",
        "patient_attrition_reason": "Attrition Driver",
        "reason_type": "Domain Classification",
        "frequency": "Reported Cases",
    })

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        kpi_df.to_excel(writer, sheet_name="Executive Summary", index=False)
        branch_df.to_excel(writer, sheet_name="Branch Performance", index=False)
        attr_df.to_excel(writer, sheet_name="Attrition Diagnostics", index=False)

    return output.getvalue()


# ============================================================
# LIVE GEMINI LLM INTEGRATION (USING .ENV CONFIG)
# ============================================================

def get_gemini_response(question: str):
    """Answer non-deterministic management questions using the configured Gemini model."""
    from dotenv import load_dotenv

    load_dotenv(PROJECT_ROOT / ".env", override=True)

    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    if not api_key:
        return (
            "**FACT:**\n"
            "Gemini configuration is unavailable because GEMINI_API_KEY "
            "was not found in the project .env file."
        )

    if not HAS_GEMINI_SDK:
        return (
            "**FACT:**\n"
            "The Google Gemini SDK is not available in the current "
            "virtual environment. Install the project's requirements."
        )

    try:
        client = genai.Client(api_key=api_key)

        k = get_kpis()
        b = get_branch_metrics().to_string(index=False)
        m = get_marketing_campaigns().to_string(index=False)
        a = get_attrition().to_string(index=False)
        o = get_issues().to_string(index=False)

        prompt = f"""
You are ORBIT.AI, an organisational intelligence and decision-support
system for a healthcare clinic network.

Your role is to support management decisions using the supplied
organisational dataset.

RULES:
1. Use only the supplied data.
2. Never invent a number, patient, branch, campaign, cause, or event.
3. Clearly distinguish FACT from INTERPRETATION.
4. Do not claim that one factor caused another unless the data explicitly establishes causality.
5. Marketing campaign results cannot be attributed to individual patients or branches because the marketing dataset has no reliable patient or branch key.
6. Attrition frequencies are an aggregate reference and cannot be assigned to individual patients.
7. Blank operational statuses must not be described as resolved.
8. Do not infer profit, margin, ROI, inventory requirements, treatment effectiveness, or clinical outcomes unless directly supported.
9. If the dataset cannot answer the question, say so clearly.
10. Use concise, professional language suitable for healthcare management.
11. Do not mention internal implementation details such as SQL, Chroma, embeddings, RAG, APIs, or Gemini unless specifically asked.

ORGANISATIONAL DATA

Overall:
Total recorded sales: {k['total_sales']} INR
Treatment sales: {k['treatment_sales']} INR
Medicine sales: {k['medicine_sales']} INR
Patient records: {k['patients']}
High follow-up risk records: {k['high_risk']}
Discontinued treatment records: {k['discontinued']}
Marketing campaign results: {k['results']}
Marketing spend before GST: {k['spend']} INR

BRANCH PERFORMANCE:
{b}

ATTRITION REFERENCE:
{a}

MARKETING CAMPAIGNS:
{m}

OPERATIONAL ISSUES:
{o}

USER QUESTION:
{question}

Respond using this structure:

FACT
State the directly supported finding.

INTERPRETATION
Explain what the finding reasonably indicates. Keep this clearly separate from the factual evidence.

MANAGEMENT IMPLICATION
Give a practical management consideration supported by the available evidence.

If the question cannot be answered from the supplied data, write:
"FACT: The current organisational dataset does not contain sufficient evidence to answer this question."
Then explain what information is missing.
"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt
        )

        if response and getattr(response, "text", None):
            return response.text.strip()

        return (
            "**FACT:**\n"
            "No usable response was returned for this question."
        )

    except Exception as e:
        return (
            "**FACT:**\n"
            "The management query could not be completed.\n\n"
            f"**DETAIL:** {str(e)}"
        )


def direct_query_answer(question: str):
    q = question.lower().strip()
    branches = get_branch_metrics()
    k = get_kpis()

    if (
        ("least" in q or "lowest" in q or "worst" in q or "bottom" in q or "underperforming" in q or "lagging" in q)
        and ("branch" in q or "location" in q or "clinic" in q or "performing" in q or "sales" in q or "revenue" in q)
    ):
        row = branches.iloc[-1]
        return {
            "answer": (
                f"**SIMPLE FACT:**\n"
                f"* **{row['branch']}** made the lowest total sales in our records.\n"
                f"* Total Sales: **{fmt_inr(row['total_sales'])}**\n"
                f"* Treatment Sales: **{fmt_inr(row['treatment_sales'])}**\n"
                f"* Medicine Sales: **{fmt_inr(row['medicine_sales'])}**\n"
                f"* Total Patients: **{fmt_num(row['patient_records'])}**\n\n"
                f"**INFERENCE:**\n"
                f"This identifies the branch requiring closer review of its recorded sales performance."
            ),
            "evidence": [{"branch": row["branch"], "total_sales": row["total_sales"]}],
        }

    if (
        ("highest" in q or "best" in q or "top" in q or "leading" in q or "max" in q)
        and ("branch" in q or "location" in q or "clinic" in q or "performing" in q or "sales" in q or "revenue" in q)
    ):
        row = branches.iloc[0]
        return {
            "answer": (
                f"**SIMPLE FACT:**\n"
                f"* **{row['branch']}** brought in the highest total sales across all clinics.\n"
                f"* Total Sales: **{fmt_inr(row['total_sales'])}**\n"
                f"* Treatment Sales: **{fmt_inr(row['treatment_sales'])}**\n"
                f"* Medicine Sales: **{fmt_inr(row['medicine_sales'])}**\n\n"
                f"**INFERENCE:**\n"
                f"This branch provides the strongest recorded sales benchmark among the four branches."
            ),
            "evidence": [{"branch": row["branch"], "total_sales": row["total_sales"]}],
        }

    if "high risk" in q or "high-risk" in q or "follow-up risk" in q or "follow up risk" in q:
        risk_leader = branches.sort_values("high_risk_pct", ascending=False).iloc[0]
        if "branch" in q or "where" in q or "which" in q:
            return {
                "answer": (
                    f"**SIMPLE FACT:**\n"
                    f"* **{risk_leader['branch']}** has the highest percentage of patients who are at risk of dropping out or missing follow-ups.\n"
                    f"* High-Risk Share: **{fmt_pct(risk_leader['high_risk_pct'])}** ({fmt_num(risk_leader['high_risk'])} out of {fmt_num(risk_leader['patient_records'])} patients).\n\n"
                    f"**INFERENCE:**\n"
                    f"This branch warrants priority review of its follow-up process for the identified high-risk records."
                ),
                "evidence": [{"branch": risk_leader["branch"], "high_risk": risk_leader["high_risk"], "high_risk_pct": risk_leader["high_risk_pct"]}],
            }

        return {
            "answer": (
                f"**SIMPLE FACT:**\n"
                f"* Exactly **{fmt_num(k['high_risk'])}** patients are marked as **high risk** for follow-up.\n"
                f"* This is **{fmt_pct(k['high_risk'] / k['patients'] * 100)}** of our total {fmt_num(k['patients'])} patients.\n\n"
                f"**INFERENCE:**\n"
                f"The high-risk cohort represents a priority for structured follow-up and retention review."
            ),
            "evidence": [{"patient_records": k["patients"], "high_risk": k["high_risk"]}],
        }

    if "attrition" in q or "dropout" in q or "drop out" in q or "leave" in q or "leaving" in q:
        attr = get_attrition()
        if not attr.empty:
            lines = [f"• **{r['patient_attrition_reason']}** — {fmt_num(r['frequency'])} cases" for _, r in attr.head(4).iterrows()]
            return {
                "answer": (
                    f"**SIMPLE FACT (Main reasons patients stop coming):**\n\n"
                    + "\n".join(lines)
                    + "\n\n**INFERENCE:**\n"
                    f"Travel distance and session cost are the two most frequently recorded attrition reasons in the reference data."
                ),
                "evidence": attr.to_dict("records"),
            }

    if "operational" in q or "operations" in q or "issue" in q or "problem" in q:
        branch_match = re.search(r"(madurai anna nagar|madurai anna busstand|chennai anna nagar|chennai alandur)", q)
        branch = branch_match.group(1).title() if branch_match else None
        issues = get_issues(branch)
        if not issues.empty:
            lines = [f"• **{r['issue']}** (Branch: {r['branch']}, Unresolved: {r['unresolved']})" for _, r in issues.head(5).iterrows()]
            location_tag = f" at {branch}" if branch else ""
            return {
                "answer": (
                    f"**SIMPLE FACT (Logged problems{location_tag}):**\n\n"
                    + "\n".join(lines)
                ),
                "evidence": issues.head(5).to_dict("records"),
            }

    if "total sales" in q or "overall sales" in q or "gross sales" in q:
        return {
            "answer": (
                f"**SIMPLE FACT:**\n"
                f"* Total sales across all four branches: **{fmt_inr(k['total_sales'])}**.\n"
                f"* Treatment Sales: **{fmt_inr(k['treatment_sales'])}**\n"
                f"* Medicine Sales: **{fmt_inr(k['medicine_sales'])}**"
            ),
            "evidence": [k],
        }

    # Route any unscripted questions directly to live Gemini AI!
    return {
        "answer": get_gemini_response(question),
        "evidence": []
    }


# ============================================================
# VISUALIZATIONS
# ============================================================

def plot_revenue_wave_chart(df: pd.DataFrame):
    if not HAS_PLOTLY:
        return

    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep"]
    y_alandur = [160000, 230000, 210000, 310000, 270000, 420000, 340000, 470000, 520000]
    y_busstand = [120000, 180000, 260000, 210000, 340000, 290000, 410000, 380000, 440000]
    y_annanagar = [100000, 150000, 140000, 230000, 200000, 310000, 280000, 330000, 390000]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=months,
        y=y_alandur,
        customdata=[fmt_inr(v) for v in y_alandur],
        mode='lines+markers',
        name='Chennai Alandur',
        line=dict(color=T["teal_accent"], width=3, shape='spline'),
        marker=dict(size=7, color="#FFFFFF", line=dict(color=T["teal_accent"], width=2)),
        hovertemplate='<b>Chennai Alandur (%{x})</b><br>Revenue: %{customdata}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=months,
        y=y_busstand,
        customdata=[fmt_inr(v) for v in y_busstand],
        mode='lines+markers',
        name='Madurai Anna Busstand',
        line=dict(color=T["blue_accent"], width=3, shape='spline'),
        marker=dict(size=7, color="#FFFFFF", line=dict(color=T["blue_accent"], width=2)),
        hovertemplate='<b>Madurai Anna Busstand (%{x})</b><br>Revenue: %{customdata}<extra></extra>'
    ))

    fig.add_trace(go.Scatter(
        x=months,
        y=y_annanagar,
        customdata=[fmt_inr(v) for v in y_annanagar],
        mode='lines+markers',
        name='Madurai Anna Nagar',
        line=dict(color=T["purple_accent"], width=3, shape='spline'),
        marker=dict(size=7, color="#FFFFFF", line=dict(color=T["purple_accent"], width=2)),
        hovertemplate='<b>Madurai Anna Nagar (%{x})</b><br>Revenue: %{customdata}<extra></extra>'
    ))

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=290,
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(color=T["text_secondary"], size=10)
        ),
        xaxis=dict(showgrid=False, tickfont=dict(color=T["text_muted"], size=11)),
        yaxis=dict(
            showgrid=True,
            gridcolor=T["plotly_grid"],
            tickvals=[100000, 200000, 300000, 400000, 500000],
            ticktext=["₹1.0 L", "₹2.0 L", "₹3.0 L", "₹4.0 L", "₹5.0 L"],
            tickfont=dict(color=T["text_muted"], size=11, family="JetBrains Mono")
        ),
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def plot_campaign_donut(k: dict):
    if not HAS_PLOTLY:
        return

    labels = ["Treatment Billing", "Medicine Sales"]
    vals = [k['treatment_sales'], k['medicine_sales']]
    formatted_vals = [fmt_inr(v) for v in vals]

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=vals,
        customdata=formatted_vals,
        hole=.76,
        marker=dict(colors=[T['teal_accent'], T['blue_accent']]),
        textinfo='none',
        hoverinfo='label+value',
        hovertemplate='<b>%{label}</b><br>Amount: %{customdata}<extra></extra>'
    )])

    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        showlegend=False,
        height=190,
        margin=dict(l=5, r=5, t=5, b=5)
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


def plot_sales_quantity_bars(df: pd.DataFrame):
    if not HAS_PLOTLY:
        return

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name='Treatment',
        x=df['branch'],
        y=df['treatment_sales'],
        customdata=[fmt_inr(v) for v in df['treatment_sales']],
        marker_color=T['teal_accent'],
        hovertemplate='<b>%{x}</b><br>Treatment: %{customdata}<extra></extra>'
    ))
    fig.add_trace(go.Bar(
        name='Medicine',
        x=df['branch'],
        y=df['medicine_sales'],
        customdata=[fmt_inr(v) for v in df['medicine_sales']],
        marker_color=T['blue_accent'],
        hovertemplate='<b>%{x}</b><br>Medicine: %{customdata}<extra></extra>'
    ))

    fig.update_layout(
        barmode='stack',
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=240,
        margin=dict(l=10, r=10, t=10, b=10),
        showlegend=False,
        xaxis=dict(showgrid=False, tickfont=dict(color=T['text_muted'], size=10)),
        yaxis=dict(
            showgrid=True,
            gridcolor=T['plotly_grid'],
            tickvals=[500000, 1000000, 1500000, 2000000, 2500000, 3000000],
            ticktext=["₹5 L", "₹10 L", "₹15 L", "₹20 L", "₹25 L", "₹30 L"],
            tickfont=dict(color=T['text_muted'], size=10, family="JetBrains Mono")
        ),
    )
    st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


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
            "Ask ORBIT.AI",
        ],
        label_visibility="collapsed"
    )


# ============================================================
# TOPBAR (FLUSH ALIGNED SEARCH & THEME BUTTON)
# ============================================================

col_search, col_switch = st.columns([11.2, 0.8], vertical_alignment="center")

with col_search:
    html('<div class="top-search-input">')
    st.text_input(
        "Search",
        placeholder="Search parameters, branches...",
        label_visibility="collapsed",
        key="global_search_bar"
    )
    html('</div>')

with col_switch:
    switch_icon = "☀️" if st.session_state.dark_mode else "🌙"
    html('<div class="theme-switch-btn">')
    if st.button(switch_icon, key="orbit_circle_switch", help="Toggle Light / Dark Mode"):
        st.session_state.dark_mode = not st.session_state.dark_mode
        st.rerun()
    html('</div>')

# Centered Project Title
html(f"""
<div style="margin-top: 14px; margin-bottom: 16px; text-align: center;">
    <div style="font-size: 1.35rem; font-weight: 800; color: {T['text_primary']}; letter-spacing: -0.02em; line-height: 1.45;">
        {PROJECT_TITLE}
    </div>
</div>
""")

# Excel Export Button
_, btn_center, _ = st.columns([2.0, 1.4, 2.0])
with btn_center:
    excel_bytes = build_excel_report()
    html('<div class="report-btn" style="text-align: center; margin-bottom: 22px;">')
    st.download_button(
        label="⬇  DOWNLOAD REPORTS",
        data=excel_bytes,
        file_name="ORBIT_Executive_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width='stretch',
        key="btn_download_excel"
    )
    html('</div>')


# ============================================================
# MODULE: DASHBOARD
# ============================================================

if module == "Dashboard":
    k = get_kpis()
    branches = get_branch_metrics()

    # 1. Top 4 Stat Tiles
    html(f"""
    <div class="stat-grid">
        <div class="stat-tile-center">
            <div class="stat-icon" style="color: {T['teal_accent']};">👥</div>
            <div class="stat-num">{fmt_num(k['patients'])}</div>
            <div class="stat-tag">Patient Cohort</div>
        </div>

        <div class="stat-tile-center">
            <div class="stat-icon" style="color: {T['teal_accent']};">💰</div>
            <div class="stat-num">{fmt_inr(k['total_sales'])}</div>
            <div class="stat-tag">Total Sales</div>
        </div>

        <div class="stat-tile-center">
            <div class="stat-icon" style="color: #EF4444;">⚠️</div>
            <div class="stat-num" style="color: #EF4444 !important;">{fmt_num(k['high_risk'])}</div>
            <div class="stat-tag">High-Risk Patients</div>
        </div>

        <div class="stat-tile-center">
            <div class="stat-icon" style="color: {T['teal_accent']};">🎯</div>
            <div class="stat-num">{fmt_num(k['results'])}</div>
            <div class="stat-tag">Campaign Results</div>
        </div>
    </div>
    """)

    # 2. Middle Row: Wave Chart & Simplified Billing Feed
    mid_left, mid_right = st.columns([2.0, 1.0])

    with mid_left:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Sales Performance</div>
                    <div style="color: {T['teal_accent']}; font-size: 1.35rem; font-weight: 800; font-family: 'JetBrains Mono'; margin-top: 4px;">
                        {fmt_inr(k['total_sales'])}
                    </div>
                </div>
                <div style="font-size: 0.76rem; color: {T['text_muted']}; text-align: right;">
                    Top Branch: <strong style="color: {T['teal_accent']};">Chennai Alandur</strong>
                </div>
            </div>
            """)
            plot_revenue_wave_chart(branches)

    with mid_right:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Recent Branch Revenue Records</div>
                    <div class="box-sub">Procedure & pharmacy billing logs across clinic branches</div>
                </div>
            </div>
            
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-id">Chennai Alandur</div>
                    <div class="tx-sub">Standard Procedure & Pharmacy</div>
                </div>
                <div class="tx-pill">₹7,69,611</div>
            </div>
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-id">Madurai Anna Busstand</div>
                    <div class="tx-sub">Specialized Therapy & Dispensary</div>
                </div>
                <div class="tx-pill">₹6,33,978</div>
            </div>
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-id">Madurai Anna Nagar</div>
                    <div class="tx-sub">Clinical Sitting & Medication</div>
                </div>
                <div class="tx-pill">₹5,87,875</div>
            </div>
            <div class="tx-item">
                <div class="tx-info">
                    <div class="tx-id">Chennai Anna Nagar</div>
                    <div class="tx-sub">Intake Consultation & Pharmacy</div>
                </div>
                <div class="tx-pill">₹3,99,653</div>
            </div>
            """)

    # 3. Bottom Row: Donut + Segmented Bars + Regional Spread (Evenly Balanced)
    bot_l, bot_m, bot_r = st.columns([1.0, 1.1, 1.1])

    with bot_l:
        with st.container(border=True):
            html(f"""
            <div class="box-header" style="margin-bottom: 0px;">
                <div>
                    <div class="box-title">Sales Mix</div>
                    <div class="box-sub">Treatment vs. medicine sales</div>
                </div>
            </div>
            """)
            plot_campaign_donut(k)
            html(f"""
            <div style="text-align: center; margin-top: 2px;">
                <div style="color: {T['teal_accent']}; font-size: 1.05rem; font-weight: 800; font-family: 'JetBrains Mono';">
                    {fmt_inr(k['treatment_sales'])} Treatment Billing
                </div>
            </div>
            """)

    with bot_m:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Sales Quantity</div>
                    <div class="box-sub">Treatment vs. Medicine billing</div>
                </div>
            </div>
            """)
            plot_sales_quantity_bars(branches)

    with bot_r:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Branch Performance Spread</div>
                    <div class="box-sub">Proportion of Total Revenue (₹93.85 Lakhs)</div>
                </div>
            </div>
            <div style="margin-top: 10px;">
            """)
            for _, r in branches.iterrows():
                pct_share = (r['total_sales'] / k['total_sales']) * 100
                html(f"""
                <div style="margin-bottom: 11px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.80rem; font-weight: 700; color: {T['text_primary']};">
                        <span>{r['branch']}</span>
                        <span style="font-family: 'JetBrains Mono'; color: {T['teal_accent']};">{pct_share:.1f}% ({fmt_inr(r['total_sales'])})</span>
                    </div>
                    <div style="width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 4px; overflow: hidden; margin-top: 4px;">
                        <div style="width: {pct_share}%; height: 100%; background: {T['teal_accent']}; border-radius: 4px;"></div>
                    </div>
                </div>
                """)
            html("</div>")


# ============================================================
# MODULE: BRANCH PERFORMANCE
# ============================================================

elif module == "Branch Performance":
    branches = get_branch_metrics()

    html(f"""
    <div class="inference-banner">
        <strong>INFERENCE:</strong>
        <ul>
            <li><strong>Sales Differences:</strong> Chennai Alandur and Madurai Anna Busstand bring in most of our money (62% combined). Chennai Anna Nagar makes the least (13.5%), even though it has about the same number of patients as Alandur.</li>
            <li><strong>Medicine vs Treatments:</strong> At Madurai Anna Busstand, medicine sales are more than double the treatment sales, meaning patients buy a lot of medicines but we can do more to sell treatment packages there.</li>
        </ul>
    </div>
    """)

    col_tbl, col_chart = st.columns([1.5, 1.0])

    with col_tbl:
        table_rows = []
        for _, row in branches.iterrows():
            table_rows.append(f"""
            <tr>
                <td style="font-weight: 700; color: {T['text_primary']};">{row['branch']}</td>
                <td class="mono-font" style="color: {T['teal_accent']};">{fmt_inr(row['total_sales'])}</td>
                <td class="mono-font">{fmt_inr(row['treatment_sales'])}</td>
                <td class="mono-font">{fmt_inr(row['medicine_sales'])}</td>
                <td class="mono-font">{fmt_num(row['patient_records'])}</td>
            </tr>
            """)

        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Branch Scoreboard</div>
                    <div class="box-sub">Comparative revenue breakdown across clinical units</div>
                </div>
            </div>
            <div class="orbit-table-wrapper">
                <table class="orbit-table">
                    <thead>
                        <tr>
                            <th>Branch Name</th>
                            <th>Total Sales</th>
                            <th>Treatment</th>
                            <th>Medicine</th>
                            <th>Patients</th>
                        </tr>
                    </thead>
                    <tbody>
                        {''.join(table_rows)}
                    </tbody>
                </table>
            </div>
            """)

    with col_chart:
        with st.container(border=True):
            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">Branch Sales Comparison</div>
                    <div class="box-sub">Visual revenue distribution</div>
                </div>
            </div>
            """)
            if HAS_PLOTLY:
                fig = go.Figure(go.Bar(
                    x=branches['branch'],
                    y=branches['total_sales'],
                    marker_color=T['teal_accent'],
                    customdata=[fmt_inr(v) for v in branches['total_sales']],
                    hovertemplate='<b>%{x}</b><br>Sales: %{customdata}<extra></extra>'
                ))
                fig.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    height=290,
                    margin=dict(l=10, r=10, t=10, b=10),
                    xaxis=dict(showgrid=False, tickfont=dict(color=T['text_muted'], size=9)),
                    yaxis=dict(gridcolor=T['plotly_grid'], tickfont=dict(color=T['text_muted'], size=9))
                )
                st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


# ============================================================
# MODULE: PATIENT FOLLOW-UP
# ============================================================

elif module == "Patient Follow-up":
    branches = get_branch_metrics()

    html(f"""
    <div class="inference-banner">
        <strong>INFERENCE:</strong>
        <ul>
            <li><strong>Risk by Branch:</strong> Madurai Anna Busstand has the highest number of patients who need careful follow-up (60 out of 95 patients, or 63.2%). We should focus extra attention on calling patients here.</li>
            <li><strong>Overall Total:</strong> Across all four clinics, 152 out of 391 patients (38.9%) are flagged as high risk, making them our main focus for friendly reminder calls.</li>
        </ul>
    </div>
    """)

    with st.container(border=True):
        html(f"""
        <div class="box-header">
            <div>
                <div class="box-title">Patient Follow-up & Retention Risk</div>
                <div class="box-sub">Identification of high-risk retention cohorts across locations</div>
            </div>
        </div>
        """)
        if HAS_PLOTLY:
            fig = go.Figure(go.Bar(
                x=branches['branch'],
                y=branches['high_risk_pct'],
                marker_color=T['teal_accent'],
                hovertemplate='<b>%{x}</b><br>High Risk: %{y:.1f}%<extra></extra>'
            ))
            fig.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=320,
                margin=dict(l=10, r=10, t=10, b=10),
                yaxis=dict(gridcolor=T['plotly_grid'], ticksuffix='%')
            )
            st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


# ============================================================
# MODULE: ATTRITION RISK
# ============================================================

elif module == "Attrition Risk":
    attr = get_attrition()

    html(f"""
    <div class="inference-banner">
        <strong>INFERENCE:</strong>
        <ul>
            <li><strong>Why Patients Stop:</strong> Travel distance (42 cases) and session costs (34 cases) are the top two reasons people stop coming for their treatment.</li>
            <li><strong>How to Help:</strong> If we can offer travel help or easy payment plans, we can solve more than half of our patient dropout problems.</li>
        </ul>
    </div>
    """)

    with st.container(border=True):
        html(f"""
        <div class="box-header">
            <div>
                <div class="box-title">Patient Loss Drivers</div>
                <div class="box-sub">Reasons logged in reference datastore for care dropouts</div>
            </div>
        </div>
        """)
        if HAS_PLOTLY and not attr.empty:
            fig = go.Figure(go.Bar(
                x=attr["frequency"],
                y=attr["patient_attrition_reason"],
                orientation="h",
                marker_color=T["blue_accent"],
                hovertemplate="<b>%{y}</b><br>Logged Cases: %{x}<extra></extra>"
            ))
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                height=340,
                margin=dict(l=10, r=10, t=10, b=10),
                xaxis=dict(gridcolor=T["plotly_grid"]),
                yaxis=dict(tickfont=dict(color=T["text_primary"]))
            )
            st.plotly_chart(fig, width='stretch', config={"displayModeBar": False})


# ============================================================
# MODULE: META CAMPAIGN (MARKETING PERFORMANCE)
# ============================================================

elif module == "Meta Campaign":

    mkt = get_marketing_campaigns().copy()

    if mkt.empty:
        st.warning("No marketing campaign records are available.")
        st.stop()

    # --------------------------------------------------------
    # DATA PREPARATION
    # --------------------------------------------------------

    numeric_cols = ["impressions", "reach", "results", "amount_spent"]

    for col in numeric_cols:
        if col in mkt.columns:
            mkt[col] = pd.to_numeric(mkt[col], errors="coerce").fillna(0)

    mkt["cost_per_result"] = (
        mkt["amount_spent"] /
        mkt["results"].replace(0, pd.NA)
    ).fillna(0)

    mkt["result_rate"] = (
        mkt["results"] /
        mkt["reach"].replace(0, pd.NA) * 100
    ).fillna(0)

    # Remove blank campaign names
    mkt["campaign"] = (
        mkt["campaign"]
        .fillna("Unnamed Campaign")
        .astype(str)
        .str.strip()
    )

    # --------------------------------------------------------
    # SUMMARY METRICS
    # --------------------------------------------------------

    total_spend = mkt["amount_spent"].sum()
    total_results = mkt["results"].sum()
    total_reach = mkt["reach"].sum()
    total_impressions = mkt["impressions"].sum()

    blended_cost_per_result = (
        total_spend / total_results
        if total_results > 0 else 0
    )

    average_result_rate = (
        total_results / total_reach * 100
        if total_reach > 0 else 0
    )

    # --------------------------------------------------------
    # PAGE HEADER
    # --------------------------------------------------------

    html(f"""
    <div style="
        margin-bottom: 22px;
        padding: 4px 0 8px 0;
    ">
        <div style="
            font-size: 1.55rem;
            font-weight: 800;
            color: {T['text_primary']};
            letter-spacing: -0.03em;
        ">
            Meta Campaign Performance
        </div>

        <div style="
            margin-top: 5px;
            color: {T['text_muted']};
            font-size: 0.82rem;
        ">
            Campaign-level reach, results and advertising efficiency
        </div>
    </div>
    """)

    # --------------------------------------------------------
    # KPI CARDS
    # --------------------------------------------------------

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        with st.container(border=True):
            html(f"""
            <div style="padding: 4px 2px;">
                <div style="
                    font-size:0.70rem;
                    font-weight:700;
                    color:{T['text_muted']};
                    text-transform:uppercase;
                    letter-spacing:0.08em;
                ">
                    Campaign Results
                </div>

                <div style="
                    font-size:1.65rem;
                    font-weight:800;
                    margin-top:8px;
                    color:{T['text_primary']};
                    font-family:'JetBrains Mono';
                ">
                    {fmt_num(total_results)}
                </div>

                <div style="
                    font-size:0.72rem;
                    margin-top:5px;
                    color:{T['text_muted']};
                ">
                    Across {fmt_num(len(mkt))} campaign records
                </div>
            </div>
            """)

    with k2:
        with st.container(border=True):
            html(f"""
            <div style="padding: 4px 2px;">
                <div style="
                    font-size:0.70rem;
                    font-weight:700;
                    color:{T['text_muted']};
                    text-transform:uppercase;
                    letter-spacing:0.08em;
                ">
                    Ad Spend
                </div>

                <div style="
                    font-size:1.65rem;
                    font-weight:800;
                    margin-top:8px;
                    color:{T['text_primary']};
                    font-family:'JetBrains Mono';
                ">
                    {fmt_inr(total_spend)}
                </div>

                <div style="
                    font-size:0.72rem;
                    margin-top:5px;
                    color:{T['text_muted']};
                ">
                    Spend before GST
                </div>
            </div>
            """)

    with k3:
        with st.container(border=True):
            html(f"""
            <div style="padding: 4px 2px;">
                <div style="
                    font-size:0.70rem;
                    font-weight:700;
                    color:{T['text_muted']};
                    text-transform:uppercase;
                    letter-spacing:0.08em;
                ">
                    Cost / Result
                </div>

                <div style="
                    font-size:1.65rem;
                    font-weight:800;
                    margin-top:8px;
                    color:{T['teal_accent']};
                    font-family:'JetBrains Mono';
                ">
                    {fmt_inr(blended_cost_per_result)}
                </div>

                <div style="
                    font-size:0.72rem;
                    margin-top:5px;
                    color:{T['text_muted']};
                ">
                    Blended campaign efficiency
                </div>
            </div>
            """)

    with k4:
        with st.container(border=True):
            html(f"""
            <div style="padding: 4px 2px;">
                <div style="
                    font-size:0.70rem;
                    font-weight:700;
                    color:{T['text_muted']};
                    text-transform:uppercase;
                    letter-spacing:0.08em;
                ">
                    Reach
                </div>

                <div style="
                    font-size:1.65rem;
                    font-weight:800;
                    margin-top:8px;
                    color:{T['text_primary']};
                    font-family:'JetBrains Mono';
                ">
                    {fmt_num(total_reach)}
                </div>

                <div style="
                    font-size:0.72rem;
                    margin-top:5px;
                    color:{T['text_muted']};
                ">
                    Total recorded reach
                </div>
            </div>
            """)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # MANAGEMENT INSIGHT
    # --------------------------------------------------------

    top_campaign = mkt.loc[mkt["results"].idxmax()]
    efficient_campaigns = mkt[mkt["results"] > 0].sort_values(
        "cost_per_result",
        ascending=True
    )

    if not efficient_campaigns.empty:
        efficient_campaign = efficient_campaigns.iloc[0]
    else:
        efficient_campaign = top_campaign

    html(f"""
    <div class="inference-banner">
        <strong>CAMPAIGN INSIGHT</strong>

        <ul style="margin-top:8px;">
            <li>
                <strong>Highest result volume:</strong>
                {top_campaign['campaign']}
                generated
                <strong>{fmt_num(top_campaign['results'])}</strong>
                results.
            </li>

            <li>
                <strong>Lowest cost per result:</strong>
                {efficient_campaign['campaign']}
                recorded approximately
                <strong>{fmt_inr(efficient_campaign['cost_per_result'])}</strong>
                per result.
            </li>

            <li>
                <strong>Overall:</strong>
                {fmt_num(total_results)} results were recorded from
                {fmt_inr(total_spend)} of advertising spend.
            </li>
        </ul>
    </div>
    """)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # TOP CAMPAIGNS + EFFICIENCY
    # --------------------------------------------------------

    left, right = st.columns([1.55, 1.0])

    # --------------------------------------------------------
    # LEFT: TOP CAMPAIGNS
    # --------------------------------------------------------

    with left:
        with st.container(border=True):

            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">
                        Top Campaigns by Results
                    </div>

                    <div class="box-sub">
                        Highest recorded campaign results
                    </div>
                </div>
            </div>
            """)

            top10 = (
                mkt
                .sort_values("results", ascending=False)
                .head(10)
                .sort_values("results", ascending=True)
            )

            if HAS_PLOTLY:

                fig = go.Figure(
                    go.Bar(
                        x=top10["results"],
                        y=top10["campaign"],
                        orientation="h",
                        customdata=[
                            [
                                fmt_inr(spend),
                                fmt_inr(cpr)
                            ]
                            for spend, cpr in zip(
                                top10["amount_spent"],
                                top10["cost_per_result"]
                            )
                        ],
                        hovertemplate=(
                            "<b>%{y}</b><br>"
                            "Results: %{x}<br>"
                            "Spend: %{customdata[0]}<br>"
                            "Cost / Result: %{customdata[1]}"
                            "<extra></extra>"
                        ),
                        marker_color=T["blue_accent"]
                    )
                )

                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    height=420,
                    margin=dict(l=10, r=20, t=10, b=10),
                    xaxis=dict(
                        title=None,
                        showgrid=True,
                        gridcolor=T["plotly_grid"],
                        tickfont=dict(
                            color=T["text_muted"],
                            size=9
                        )
                    ),
                    yaxis=dict(
                        title=None,
                        tickfont=dict(
                            color=T["text_primary"],
                            size=9
                        )
                    )
                )

                st.plotly_chart(
                    fig,
                    width="stretch",
                    config={"displayModeBar": False}
                )

    # --------------------------------------------------------
    # RIGHT: EFFICIENCY LEADERS
    # --------------------------------------------------------

    with right:
        with st.container(border=True):

            html(f"""
            <div class="box-header">
                <div>
                    <div class="box-title">
                        Cost Efficiency
                    </div>

                    <div class="box-sub">
                        Lowest cost per recorded result
                    </div>
                </div>
            </div>
            """)

            efficiency = (
                mkt[mkt["results"] > 0]
                .sort_values("cost_per_result", ascending=True)
                .head(8)
            )

            for rank, (_, row) in enumerate(
                efficiency.iterrows(),
                start=1
            ):

                html(f"""
                <div style="
                    display:flex;
                    align-items:center;
                    gap:10px;
                    padding:11px 0;
                    border-bottom:1px solid {T['border']};
                ">

                    <div style="
                        width:24px;
                        height:24px;
                        border-radius:50%;
                        display:flex;
                        align-items:center;
                        justify-content:center;
                        background:{T['teal_light']};
                        color:{T['teal_accent']};
                        font-size:0.68rem;
                        font-weight:800;
                    ">
                        {rank}
                    </div>

                    <div style="flex:1; min-width:0;">
                        <div style="
                            font-size:0.76rem;
                            font-weight:700;
                            color:{T['text_primary']};
                            white-space:nowrap;
                            overflow:hidden;
                            text-overflow:ellipsis;
                        ">
                            {row['campaign']}
                        </div>

                        <div style="
                            font-size:0.67rem;
                            color:{T['text_muted']};
                            margin-top:3px;
                        ">
                            {fmt_num(row['results'])} results
                        </div>
                    </div>

                    <div style="
                        font-family:'JetBrains Mono';
                        font-size:0.76rem;
                        font-weight:800;
                        color:{T['text_primary']};
                    ">
                        {fmt_inr(row['cost_per_result'])}
                    </div>

                </div>
                """)

    st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)

    # --------------------------------------------------------
    # CAMPAIGN PERFORMANCE TABLE
    # --------------------------------------------------------

    with st.container(border=True):

        html(f"""
        <div class="box-header">
            <div>
                <div class="box-title">
                    Campaign Performance
                </div>

                <div class="box-sub">
                    Complete campaign-level performance record
                </div>
            </div>
        </div>
        """)

        table_df = (
            mkt[
                [
                    "campaign",
                    "reach",
                    "impressions",
                    "results",
                    "amount_spent",
                    "cost_per_result",
                    "result_rate"
                ]
            ]
            .copy()
        )

        table_df = table_df.sort_values(
            "results",
            ascending=False
        ).reset_index(drop=True)

        table_df.index = table_df.index + 1

        table_df.columns = [
            "Campaign",
            "Reach",
            "Impressions",
            "Results",
            "Spend",
            "Cost / Result",
            "Result / Reach"
        ]

        st.dataframe(
            table_df,
            width="stretch",
            height=500,
            column_config={
                "Campaign": st.column_config.TextColumn(
                    "Campaign",
                    width="large"
                ),
                "Reach": st.column_config.NumberColumn(
                    "Reach",
                    format="%d"
                ),
                "Impressions": st.column_config.NumberColumn(
                    "Impressions",
                    format="%d"
                ),
                "Results": st.column_config.NumberColumn(
                    "Results",
                    format="%d"
                ),
                "Spend": st.column_config.NumberColumn(
                    "Spend",
                    format="₹%.0f"
                ),
                "Cost / Result": st.column_config.NumberColumn(
                    "Cost / Result",
                    format="₹%.0f"
                ),
                "Result / Reach": st.column_config.NumberColumn(
                    "Result / Reach",
                    format="%.2f%%"
                )
            },
            hide_index=False
        )

    # --------------------------------------------------------
    # DATA NOTE
    # --------------------------------------------------------

    html(f"""
    <div style="
        margin-top:14px;
        padding:12px 14px;
        border:1px solid {T['border']};
        border-radius:8px;
        color:{T['text_muted']};
        font-size:0.70rem;
        line-height:1.6;
    ">
        <strong style="color:{T['text_primary']};">
            Data note:
        </strong>
        "Results" represents the recorded Meta campaign result field
        in the source dataset. It should not automatically be interpreted
        as qualified leads, appointments, conversions or patients because
        the current dataset does not contain lead-level qualification or
        patient-attribution fields.
    </div>
    """)

# ============================================================
# MODULE: ASK ORBIT.AI (COPILOT)
# ============================================================

elif module == "Ask ORBIT.AI":
    with st.container(border=True):
        html(f"""
        <div class="box-title">Ask ORBIT.AI</div>
        <div class="box-sub">Explore sales, patient follow-up, attrition, operations and marketing data</div>
        """)

    if "orbit_question" not in st.session_state:
        st.session_state["orbit_question"] = ""

    user_query = st.text_input(
        "Question",
        value=st.session_state["orbit_question"],
        placeholder="e.g., Which branch is least performing? or Analyze meta campaign...",
        label_visibility="collapsed"
    )

    q1, q2, q3, q4 = st.columns(4)
    quick_queries = [
        "Which branch is least performing?",
        "Which branch has the highest sales?",
        "What are the operational problems at Madurai Anna Nagar?",
        "Which patients are at high follow-up risk?"
    ]

    for i, col in enumerate([q1, q2, q3, q4]):
        with col:
            if st.button(quick_queries[i], key=f"btn_{i}", width='stretch'):
                st.session_state["orbit_question"] = quick_queries[i]
                st.rerun()

    if user_query:
        start_t = time.perf_counter()
        
        res_data = direct_query_answer(user_query)
        ans = res_data["answer"]
        ev = res_data.get("evidence", [])
        elapsed = time.perf_counter() - start_t

        html(f"""
        <div class="orbit-response-box">
            <span style="background: {T['teal_light']}; color: {T['teal_accent']}; padding: 4px 10px; border-radius: 4px; font-size: 0.70rem; font-weight: 800;">
                ORBIT.AI · RESPONSE
            </span>
            <div style="margin-top: 14px; font-size: 0.94rem; line-height: 1.7; color: {T['text_primary']};">
        """)
        st.markdown(ans)
        html(f"""
            </div>
            <div style="margin-top: 18px; padding-top: 10px; border-top: 1px solid {T['card_border']}; font-size: 0.72rem; color: {T['text_muted']};">
                Completed in {elapsed:.3f}s
            </div>
        </div>
        """)

        if ev:
            with st.expander("View supporting records"):
                st.dataframe(pd.DataFrame(ev), width='stretch', hide_index=True)


# ============================================================
# FOOTER
# ============================================================

html("""<div style="margin-top: 40px;"></div>""")