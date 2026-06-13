# PS4: Data Access Audit & Insider Threat Detection
# Cybersecurity Hackathon Project — CLAUDE.md

---

## Project Overview

Build an AI-powered insider threat detection system that ingests enterprise data
access logs, establishes per-user behavioral baselines, detects anomalies using
statistical methods, and generates LLM-powered incident narratives with risk scores.

**Hackathon target:** Precision >75%, Recall >70%, F1 >0.72 on provided ground truth labels.

---

## Skills to Load When Needed

- For any frontend/UI work: read `@docs/frontend-notes.md` (or check SKILL.md at `/mnt/skills/public/frontend-design/SKILL.md`)
- For notebook structure guidance: refer to `@docs/notebook-guide.md`
- Always check `@docs/architecture.md` before modifying core pipeline logic

---

## Folder Structure

```
project-root/
├── CLAUDE.md                        ← you are here
├── README.md                        ← setup + run instructions
├── requirements.txt                 ← all Python deps
│
├── data/                            ← organizer-provided CSVs (read-only)
│   ├── data_access_logs.csv         ← 1,200 access events, 365 days
│   ├── user_profiles.csv            ← 100 user baseline profiles
│   ├── data_access_labels.csv       ← ground truth: event-level anomaly labels
│   └── user_profile_labels.csv      ← ground truth: user-level risk labels
│
├── src/                             ← core pipeline modules (importable)
│   ├── ingestor.py                  ← load, merge, normalize all CSVs
│   ├── baseline.py                  ← build per-user statistical profiles
│   ├── detector.py                  ← Z-score anomaly scoring engine
│   ├── suppressor.py                ← false positive suppression rules
│   ├── llm_narrator.py              ← Gemini API calls + prompt templates
│   └── evaluator.py                 ← Precision / Recall / F1 calculation
│
├── api/
│   └── main.py                      ← FastAPI backend serving dashboard data
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── IncidentDashboard.jsx ← prioritized alert list
│       │   ├── IncidentCard.jsx      ← per-incident drill-down
│       │   ├── UserProfile.jsx       ← behavioral overview per user
│       │   └── MetricsPanel.jsx      ← P/R/F1 display
│       └── index.jsx
│
├── notebooks/
│   ├── 01_eda_and_baseline.ipynb    ← exploratory analysis + baseline visualization
│   └── 02_anomaly_detection_evaluation.ipynb ← model validation + F1 scoring
│
└── docs/
    ├── architecture.md              ← pipeline design decisions
    ├── frontend-notes.md            ← UI/UX decisions
    └── notebook-guide.md           ← notebook structure reference
```

**Rule:** Never duplicate logic between `src/` and notebooks. Notebooks import from `src/`.

---

## Tech Stack

### Backend / Pipeline
| Tool | Version | Purpose |
|------|---------|---------|
| Python | 3.11+ | Core language |
| pandas | latest | Data ingestion, merging, manipulation |
| numpy | latest | Statistical calculations |
| scipy | latest | Z-score, IQR anomaly scoring |
| scikit-learn | latest | Precision, Recall, F1 evaluation |
| FastAPI | latest | REST API serving dashboard |
| uvicorn | latest | ASGI server for FastAPI |

### LLM
| Tool | Details |
|------|---------|
| Google Generative AI SDK | `pip install google-generativeai` |
| Model | `gemini-2.0-flash` |
| Key source | Google AI Studio (aistudio.google.com) — free tier |
| Env var | `GEMINI_API_KEY` in `.env` file (never commit this) |

### Frontend
| Tool | Purpose |
|------|---------|
| React 18 | Dashboard UI |
| Recharts | Risk score charts, anomaly timelines |
| Tailwind CSS | Styling |
| Vite | Build tool |

### Notebooks
| Tool | Purpose |
|------|---------|
| Jupyter | EDA + evaluation notebooks |
| matplotlib / seaborn | Visualizations inside notebooks |
| All `src/` modules | Imported directly — no logic duplication |

---

## Architecture — 5-Layer Pipeline

```
Layer 1  DATA SOURCES
         data_access_logs.csv + user_profiles.csv
         data_access_labels.csv + user_profile_labels.csv
              ↓
Layer 2  INGESTION & NORMALIZATION  [src/ingestor.py]
         - Merge logs with user profiles on user_id
         - Normalize all timestamps to UTC
         - Handle null/missing fields gracefully
         - Tag source_system per event
              ↓
Layer 3  BEHAVIORAL BASELINE ENGINE  [src/baseline.py]
         - Use first 30 days as training window
         - Per-user: hour distribution, avg rowcount, typical systems, destinations
         - Separate baselines for: employees / contractors / service accounts / admins
              ↓
Layer 4  ANOMALY SCORING + FP SUPPRESSION  [src/detector.py + src/suppressor.py]
         Deviation scoring (Z-score / IQR) across 4 dimensions:
           1. Time deviation — off-hours access
           2. Volume spike — rows vs baseline mean
           3. System deviation — first-time resource access
           4. Destination risk — USB / external email / cloud
         Composite risk score: 0–100
         False positive suppression:
           - Month-end close (Finance bulk access expected)
           - On-call duties (elevated access expected)
           - Role change within last 30 days
           - Contractor with <30 days tenure (limited baseline)
           - Service accounts (separate baseline logic)
              ↓
Layer 5  LLM REASONING  [src/llm_narrator.py]
         - Only flagged events (risk score > threshold) sent to Gemini
         - Input: user profile + 30-day baseline + anomalous event details
         - Output: narrative explanation + severity + confidence + 3 recommended actions
              ↓
OUTPUT   DASHBOARD + EVALUATION  [api/main.py + frontend/ + src/evaluator.py]
         - React dashboard: prioritized incident list + user profiles + metrics
         - Evaluation script: Precision / Recall / F1 vs ground truth labels
         - PDF/JSON incident report: 20+ flagged incidents with narratives
```

---

## Coding Rules

- Every `src/` module must be importable with no side effects on import
- All functions must have type hints and a one-line docstring
- Never hardcode file paths — use a `config.py` or constants at the top of each file
- Never commit `.env` or any file containing `GEMINI_API_KEY`
- Timestamps: always normalize to UTC immediately on ingest, never later
- Risk scores: always integers 0–100, never floats
- All Gemini API calls go through `src/llm_narrator.py` only — nowhere else
- Notebooks must be runnable top-to-bottom with `Kernel → Restart & Run All`
- Notebooks import from `src/` — never redefine logic inside a notebook cell

---

## False Positive Suppression Rules (implement in src/suppressor.py)

These are worth 20 points on the rubric — implement all of them:

1. **Month-end close** — Finance/Accounting department, last 3 days of month → downgrade severity by one level
2. **On-call flag** — User marked `on_call=true` in profile → suppress time-deviation flag only
3. **Role change** — `role_change_date` within last 30 days → suppress system-deviation flag
4. **New contractor** — `account_type=contractor` AND `tenure_months < 3` → widen baseline thresholds by 2x
5. **Service account** — `account_type=service_account` → use separate 24x7 baseline, never flag time deviation
6. **Legitimate bulk export** — `query_type=BACKUP` or `query_type=WAREHOUSE_REFRESH` → suppress volume flag

---

## Gemini Prompt Template (implement in src/llm_narrator.py)

```
You are a cybersecurity analyst. Analyze this data access anomaly and respond in JSON only.

USER PROFILE:
- Name: {username}
- Role: {job_title}, {department}
- Tenure: {tenure_months} months
- Approved systems: {approved_data_assets}
- Typical hours: {typical_access_hours}
- Avg queries/day: {avg_queries_per_day}
- Avg rowcount/query: {avg_rowcount_per_query}
- HR high-risk flag: {high_risk_flag}

BEHAVIORAL BASELINE (last 30 days):
- Typical access hours: {baseline_hours}
- Average rowcount per session: {baseline_avg_rows}
- Systems normally accessed: {baseline_systems}
- Typical destinations: {baseline_destinations}

ANOMALOUS EVENT:
- Timestamp: {timestamp}
- Action: {query_type} on {data_asset}
- Rowcount: {rowcount} (baseline avg: {baseline_avg_rows})
- Destination: {destination}
- Sensitivity: {data_sensitivity}
- Anomaly signals: {anomaly_signals_list}

Respond ONLY with this JSON structure, no other text:
{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": <integer 0-100>,
  "narrative": "<2-3 sentence plain English explanation of why this is suspicious>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"]
}
```

---

## Evaluation Targets (src/evaluator.py)

```python
# Target metrics — measure against data_access_labels.csv
Precision  > 0.75   # minimize false positives
Recall     > 0.70   # don't miss real threats
F1 Score   > 0.72   # overall balance

# Also compute per-severity breakdown:
# CRITICAL, HIGH, MEDIUM separately
```

---

## Git Workflow — Commit After Each Feature

Every implementation step below gets its own commit before moving to the next.
Use conventional commit messages.

```bash
git add .
git commit -m "feat: <feature name>"
git push origin main
```

Never combine multiple steps into one commit.

---

## Implementation Steps (in order)

Work through these steps sequentially. Complete and commit each before starting the next.

### Step 1 — Project Scaffold
- [ ] Initialize git repo, create folder structure above
- [ ] Create `requirements.txt` with all deps
- [ ] Create `.gitignore` (exclude `.env`, `__pycache__`, `.ipynb_checkpoints`, `node_modules`)
- [ ] Create empty placeholder files for all `src/` modules
- [ ] Create `README.md` with setup instructions
- [ ] **Commit:** `feat: project scaffold and folder structure`

### Step 2 — Data Ingestion & Normalization (src/ingestor.py)
- [ ] `load_access_logs()` — load `data_access_logs.csv`, parse timestamps to UTC
- [ ] `load_user_profiles()` — load `user_profiles.csv`
- [ ] `load_labels()` — load both label files for evaluation
- [ ] `merge_logs_with_profiles()` — join on `user_id`, left join
- [ ] `handle_nulls()` — fill or flag missing fields consistently
- [ ] Verify: merged dataframe has no duplicate columns, timestamps all UTC
- [ ] **Commit:** `feat: data ingestion and normalization layer`

### Step 3 — Behavioral Baseline Engine (src/baseline.py)
- [ ] `build_user_baseline(user_df)` — single user, returns dict of stats
- [ ] `build_all_baselines(df)` — all users, returns dict keyed by user_id
- [ ] Baseline fields: `hour_distribution`, `avg_rowcount`, `std_rowcount`, `typical_systems`, `typical_destinations`, `account_type`
- [ ] Separate logic for: employee / contractor / service_account / admin
- [ ] Training window: first 30 days of data only
- [ ] **Commit:** `feat: per-user behavioral baseline engine`

### Step 4 — Anomaly Scoring Engine (src/detector.py)
- [ ] `score_time_deviation(event, baseline)` → 0–25
- [ ] `score_volume_deviation(event, baseline)` → 0–25
- [ ] `score_system_deviation(event, baseline)` → 0–25
- [ ] `score_destination_risk(event, baseline)` → 0–25
- [ ] `compute_risk_score(event, baseline)` → 0–100 composite
- [ ] `score_all_events(df, baselines)` → df with `risk_score` and `anomaly_signals` columns
- [ ] **Commit:** `feat: statistical anomaly scoring engine`

### Step 5 — False Positive Suppression (src/suppressor.py)
- [ ] Implement all 6 suppression rules listed above
- [ ] `suppress(event, user_profile)` → returns adjusted event with `suppressed=True/False` and `suppression_reason`
- [ ] `apply_suppression(df, profiles)` → full dataframe with suppression applied
- [ ] Unit test each rule with a hardcoded example
- [ ] **Commit:** `feat: false positive suppression layer with 6 rules`

### Step 6 — LLM Narrator (src/llm_narrator.py)
- [ ] Load `GEMINI_API_KEY` from `.env` using `python-dotenv`
- [ ] `build_prompt(event, baseline, user_profile)` → formatted string
- [ ] `generate_narrative(event, baseline, user_profile)` → parsed JSON dict
- [ ] `narrate_all_incidents(flagged_df, baselines, profiles)` → df with narrative columns
- [ ] Handle API errors gracefully — fallback narrative on failure
- [ ] Only call Gemini for events with `risk_score >= 50` to conserve quota
- [ ] **Commit:** `feat: Gemini LLM narrative generation layer`

### Step 7 — Evaluation Module (src/evaluator.py)
- [ ] `calculate_metrics(predictions_df, labels_df)` → dict with precision, recall, f1
- [ ] `per_severity_metrics(predictions_df, labels_df)` → breakdown by CRITICAL/HIGH/MEDIUM
- [ ] `print_evaluation_report(metrics)` → formatted console output
- [ ] Verify targets: precision >0.75, recall >0.70, F1 >0.72
- [ ] **Commit:** `feat: evaluation metrics against ground truth labels`

### Step 8 — FastAPI Backend (api/main.py)
- [ ] `GET /incidents` — returns top 20 incidents sorted by risk_score desc
- [ ] `GET /incidents/{id}` — single incident with full narrative + recommended actions
- [ ] `GET /users` — all user risk profiles
- [ ] `GET /metrics` — precision, recall, F1 scores
- [ ] `GET /health` — sanity check endpoint
- [ ] Run full pipeline on startup, cache results in memory
- [ ] Enable CORS for React frontend
- [ ] **Commit:** `feat: FastAPI backend with incident and metrics endpoints`

### Step 9 — React Dashboard (frontend/)
- [ ] Scaffold with Vite + React + Tailwind
- [ ] `IncidentDashboard.jsx` — sortable list of incidents with severity badges
- [ ] `IncidentCard.jsx` — drill-down: risk score, anomaly signals, narrative, recommended actions
- [ ] `UserProfile.jsx` — baseline stats + risk flag per user
- [ ] `MetricsPanel.jsx` — Precision / Recall / F1 displayed as metric cards
- [ ] Connect all components to FastAPI endpoints
- [ ] **Commit:** `feat: React dashboard with incident list and metrics panel`

### Step 10 — EDA Notebook (notebooks/01_eda_and_baseline.ipynb)
- [ ] Import from `src/ingestor` and `src/baseline` — no logic redefined
- [ ] Section 1: Data overview — shapes, dtypes, null counts, date range
- [ ] Section 2: Access pattern distributions — hour of day, dept, sensitivity, action type
- [ ] Section 3: Anomaly distribution — from ground truth labels
- [ ] Section 4: Per-user baseline visualizations — 3–4 example users with charts
- [ ] Section 5: Key findings markdown summary
- [ ] Pre-run with all outputs saved
- [ ] **Commit:** `feat: EDA and baseline analysis notebook`

### Step 11 — Evaluation Notebook (notebooks/02_anomaly_detection_evaluation.ipynb)
- [ ] Import from `src/detector`, `src/suppressor`, `src/evaluator`
- [ ] Section 1: Run detector on full dataset
- [ ] Section 2: Precision / Recall / F1 — overall + per severity
- [ ] Section 3: Confusion matrix visualization
- [ ] Section 4: False positive analysis — suppression rule effectiveness
- [ ] Section 5: 5–6 example incidents — system output vs ground truth side by side
- [ ] Section 6: Scaling notes — how the system handles 1M+ daily events
- [ ] Pre-run with all outputs saved
- [ ] **Commit:** `feat: anomaly detection evaluation notebook`

### Step 12 — Polish & Final Submission Prep
- [ ] Generate sample incident report (20+ incidents) as JSON + readable text
- [ ] Final `README.md` with: setup, run instructions, architecture summary, metric results
- [ ] Verify both notebooks run clean with `Kernel → Restart & Run All`
- [ ] Verify FastAPI + React run together locally
- [ ] Deliverables checklist from problem statement — confirm all boxes checked
- [ ] **Commit:** `feat: final polish and submission prep`
- [ ] **Tag release:** `git tag v1.0.0 && git push origin v1.0.0`

---

## Deliverables Checklist (from problem statement)

- [ ] GitHub repo with code, `requirements.txt`, clear README
- [ ] `notebooks/01_eda_and_baseline.ipynb` — with saved outputs
- [ ] `notebooks/02_anomaly_detection_evaluation.ipynb` — with saved outputs
- [ ] 20+ flagged access events with LLM-generated explanations
- [ ] Risk dashboard (React frontend)
- [ ] False positive analysis documented (in notebook + suppressor.py comments)
- [ ] Technical docs in `docs/` — approach, feature engineering, scaling plan
- [ ] 5-minute presentation: problem → solution → live demo → metrics

---

## Scaling Notes (document in evaluation notebook)

Even though sample data is 1,200 events, architecture is designed to scale:

- **Streaming ingestion:** Replace CSV reads with Apache Kafka consumer
- **Distributed baselines:** Partition by `user_id` on Apache Spark
- **LLM throttling:** Only top 5% risk scores (flagged events) sent to Gemini — at 1M events/day, that is ~50,000 LLM calls max, batched via async
- **Storage:** SQLite → PostgreSQL with partitioned tables by date
- **Performance target:** 1M events processed in <120 seconds on a 4-core machine

---

## Environment Setup

```bash
# Python environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment variables
cp .env.example .env
# Add your GEMINI_API_KEY to .env

# Run backend
cd api && uvicorn main:app --reload

# Run frontend
cd frontend && npm install && npm run dev

# Run notebooks
jupyter notebook notebooks/
```

---

## Current Status

- [x] Architecture decided
- [x] Tech stack finalized
- [x] Data sources confirmed (organizer-provided)
- [x] CLAUDE.md created
- [ ] Step 1: Project scaffold — NOT STARTED