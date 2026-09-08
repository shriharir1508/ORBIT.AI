PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS branch_master (
    branch_id INTEGER PRIMARY KEY AUTOINCREMENT,
    branch_name TEXT NOT NULL UNIQUE,
    city TEXT
);

CREATE TABLE IF NOT EXISTS employee_master (
    employee_id TEXT PRIMARY KEY,
    employee_name TEXT,
    branch_name TEXT,
    designation TEXT,
    status TEXT
);

CREATE TABLE IF NOT EXISTS patient_followup (
    patient_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id TEXT,
    branch_name TEXT,
    branch_city TEXT,
    date_of_first_sitting TEXT,
    disease TEXT,
    disease_category TEXT,
    sitting_count INTEGER,
    followup_status TEXT,
    remark TEXT,
    days_since_first_sitting INTEGER,
    engagement_level TEXT,
    contactability TEXT,
    followup_risk TEXT,
    treatment_continuation_status TEXT
);

CREATE TABLE IF NOT EXISTS patient_attrition_reference (
    attrition_reference_id INTEGER PRIMARY KEY AUTOINCREMENT,
    attrition_reason TEXT,
    frequency INTEGER,
    percentage REAL,
    remarks TEXT
);

CREATE TABLE IF NOT EXISTS marketing_campaign (
    campaign_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    campaign_name TEXT,
    campaign_date TEXT,
    results INTEGER,
    cost_per_result REAL,
    impressions INTEGER,
    reach INTEGER,
    instagram_follows INTEGER,
    instagram_profile_visits INTEGER,
    ctr REAL,
    amount_spent REAL,
    gst REAL,
    total_amount REAL
);

CREATE TABLE IF NOT EXISTS sales (
    sales_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    year INTEGER,
    month TEXT,
    branch_name TEXT,
    standard_treatment REAL,
    variable_treatment REAL,
    total_treatment REAL,
    total_medicine_sales REAL,
    total_sales REAL
);

CREATE TABLE IF NOT EXISTS brand_assessment (
    assessment_id INTEGER PRIMARY KEY AUTOINCREMENT,
    assessment_area TEXT,
    score REAL,
    findings TEXT
);

CREATE TABLE IF NOT EXISTS issue_management (
    issue_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
    issue TEXT,
    branch_name TEXT,
    link TEXT,
    issue_date TEXT,
    status TEXT
);