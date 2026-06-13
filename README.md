# Data Access Audit & Insider Threat Detection (PS-04)

AI-powered insider-threat detection: ingest enterprise data-access logs, learn
per-user behavioral baselines, score anomalies statistically, suppress
predictable false positives, and generate LLM-written incident narratives with
risk scores and recommended actions.

**Targets:** Precision > 75%, Recall > 70%, F1 > 0.72, with explainable alerts.

---

## Pipeline (5 layers)

```
Ingest → Baseline → Score + Suppress → LLM Narrate → Dashboard + Evaluate
src/ingestor  src/baseline  src/detector  src/llm_narrator   api/ + frontend/
              src/suppressor                                  src/evaluator
```

See [docs/architecture.md](docs/architecture.md) for design decisions and the
important notes on how the implementation adapts to the actual dataset schema.

---

## Project layout

```
src/        importable pipeline modules (config, ingestor, baseline, detector,
            suppressor, llm_narrator, evaluator)
api/        FastAPI backend serving dashboard data
frontend/   React + Vite dashboard (Step 9)
notebooks/  01_eda_and_baseline, 02_anomaly_detection_evaluation
docs/       architecture / frontend / notebook guides
sample_data/  organizer-provided CSVs (read-only)
outputs/    generated incident reports (gitignored)
```

---

## Dataset (`sample_data/`)

> The shipped CSVs differ from the original problem-statement examples. These are
> the **actual** columns the pipeline is built against.

**`data_access_logs.csv`** — 1,200 events, Apr 2025 – Apr 2026

| column | values |
|---|---|
| `timestamp` | event time |
| `user_id`, `username` | who |
| `action` | login, sql_query, api_call, file_access, export_data, admin_operation |
| `resource` | HRIS, PROD_DB, Admin_Console, BI_Tool, Customer_Vault, SIEM, Data_Lake, GL_System, Email_Archive, File_Share |
| `resource_sensitivity` | low, medium, high |
| `status` | success, failure |
| `source_ip` | originating IP |
| `time_classification` | business_hours, night, weekend, unusual_hours |

**`user_profiles.csv`** — 100 users

| column | values |
|---|---|
| `user_id`, `username`, `email` | identity |
| `department` | 12 departments (Marketing, Finance, …) |
| `job_title` | Lead, Administrator, Architect, … |
| `privilege_level` | user, power-user, admin, service-account |
| `systems_access` | pipe-separated grant list, e.g. `Azure_AD\|Salesforce` |
| `last_login`, `days_inactive`, `is_active`, `hire_date` | account status |

**No ground-truth label files and no `anomaly_marker` column ship with the
data.** Evaluation therefore uses a transparent heuristic weak-label scheme
(see [src/evaluator.py](src/evaluator.py)); swap in real labels via
[src/config.py](src/config.py) if provided.

---

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows  (macOS/Linux: source venv/bin/activate)
pip install -r requirements.txt

copy .env.example .env         # then add your GEMINI_API_KEY
```

Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com).

## Run

```bash
# Backend API
cd api && uvicorn main:app --reload

# Frontend dashboard
cd frontend && npm install && npm run dev

# Notebooks
jupyter notebook notebooks/
```

---

## Status

Step 1 (scaffold) complete. Steps 2–12 tracked in [CLAUDE.md](CLAUDE.md).
