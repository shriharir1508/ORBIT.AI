# ORBIT.AI

## Project Title

ORBIT: An AI-Enabled Unified Organisational Intelligence and Decision Support System

## Purpose

ORBIT.AI is a management decision-support system that integrates fragmented organisational data into a unified analytical environment.

It combines:

- Data engineering
- Structured analytics
- Semantic retrieval
- Hybrid retrieval
- Gemini-based AI
- Management dashboard
- Evidence-based decision support

## Core Architecture

Data Sources
→ Data Ingestion
→ Cleaning & Validation
→ Unified Database
→ Analytics
→ Hybrid Retrieval
→ Gemini AI Agent
→ Management Dashboard
→ Decision Support

## Locked Data Domains

### 1. Patient Intelligence
Patient follow-up, engagement, risk, continuation and attrition-related information.

### 2. Marketing Intelligence
Meta campaign performance including results, spend, reach, impressions, CTR and cost metrics.

Marketing data does NOT contain reliable patient-level or branch-level attribution.

### 3. Sales Intelligence
Branch-level monthly sales and treatment/medicine sales components.

### 4. Operations Intelligence
Employees, operational forms and clinic issue management information.

Blank operational forms are treated as schemas only. No records will be fabricated.

## Core Rules

1. Never fabricate data.
2. Never modify raw source files.
3. Preserve source traceability.
4. Do not assume Patient ID is unique.
5. Use a safe record-level identifier where required.
6. Preserve unresolved business ambiguities.
7. Do not infer causality without evidence.
8. Do not use AI to calculate numerical metrics.
9. Numerical metrics must come from deterministic SQL/Pandas analytics.
10. Use semantic retrieval only for genuinely narrative information.
11. Use hybrid retrieval when both structured and narrative evidence are required.
12. Clearly distinguish FACT, INFERENCE and UNKNOWN.
13. Recommendations must be separated from evidence.
14. Do not expose unnecessary patient or employee information to the AI model.
15. Madipakkam must not be invented or assumed to exist.
16. Empty source forms must remain empty in the database.

## AI Agent

The ORBIT.AI agent will use the Google Gemini API.

The model must receive relevant evidence before generating an answer.

AI responses should follow:

ANSWER
FACTS
INFERENCE
EVIDENCE
LIMITATIONS
MANAGEMENT IMPLICATION
RECOMMENDED ACTION

## Retrieval Strategy

Structured questions:
SQLite / SQL / Pandas

Semantic questions:
Vector retrieval

Hybrid questions:
SQLite + vector retrieval

The LLM must not independently calculate business metrics.

## Provenance

Important AI outputs must be traceable through:

AI Answer
→ Evidence
→ Database / Vector Record
→ Processed Dataset
→ Original Source

## Dashboard

The management dashboard will contain:

1. Executive Overview
2. Patient Intelligence
3. Sales Intelligence
4. Marketing Intelligence
5. Operations Intelligence
6. Branch Performance
7. Risks & Exceptions
8. Ask ORBIT.AI

## Technology

- Python
- Pandas
- SQLite
- Streamlit
- Plotly
- ChromaDB
- Sentence Transformers
- Google Gemini API

## Development Principle

Build the minimum technically sufficient system.

Avoid unnecessary technologies, frameworks and infrastructure.

No Docker.
No FastAPI.
No React.
No microservices.
No unnecessary notebooks.
No unnecessary orchestration frameworks.

The objective is a working, defensible SIP prototype rather than unnecessary technical complexity.