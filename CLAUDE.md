# PS4: Data Access Audit & Insider Threat Detection
# Cybersecurity Hackathon — CLAUDE.md

---

## Project Overview

Build an AI-powered insider threat detection system that ingests enterprise data
access logs, establishes per-user behavioral baselines, scores anomalies using
statistical methods across 5 dimensions, and generates LLM-powered incident
narratives with risk scores and recommended actions.

**Problem Statement:** PS4 — Data Access Audit & Insider Threat Detection
**LLM:** Gemini 2.0 Flash via Google AI Studio (free tier)
**Evaluation:** Three-tier strategy (see Evaluation section below)

---

## Skills to Load When Needed

- Frontend/UI work → read `@docs/frontend-notes.md`
- Notebook structure → read `@docs/notebook-guide.md`
- Pipeline logic changes → read `@docs/architecture.md` first

---

## Folder Structure

```
project-root/
├── CLAUDE.md                             ← you are here
├── README.md                             ← setup + run instructions
├── requirements.txt                      ← all Python deps
├── .env.example                          ← template: GEMINI_API_KEY=your_key_here
├── config.py                             ← all file paths + constants (no hardcoding)
│
├── data/
│   ├── raw/                              ← READ-ONLY — organizer-provided, never modified
│   │   ├── data_access_logs.csv          ← access events (timestamp, action, resource, etc.)
│   │   └── user_profiles.csv            ← user accounts (privilege, systems_access, etc.)
│   └── output/                          ← WRITTEN BY PIPELINE — never commit these
│       ├── scored_incidents.csv          ← all events + risk scores + anomaly signals
│       ├── flagged_incidents.csv         ← risk_score >= 50 only, with LLM narratives
│       └── derived_labels.csv           ← rule-derived ground truth (src/labeler.py)
│
├── src/                                  ← core pipeline — all importable, no side effects
│   ├── ingestor.py                       ← load, merge, normalize CSVs
│   ├── baseline.py                       ← per-user statistical profiles + IP baselining
│   ├── detector.py                       ← 5-dimension anomaly scoring engine
│   ├── suppressor.py                     ← false positive suppression rules
│   ├── labeler.py                        ← derive ground truth labels from domain rules
│   ├── llm_narrator.py                   ← Gemini API calls + prompt builder
│   └── evaluator.py                      ← three-tier evaluation framework
│
├── api/
│   └── main.py                           ← FastAPI backend — runs pipeline on startup
│
├── frontend/
│   ├── package.json
│   └── src/
│       ├── App.jsx
│       ├── components/
│       │   ├── IncidentDashboard.jsx     ← prioritized alert list, sortable
│       │   ├── IncidentCard.jsx          ← drill-down: score, signals, narrative, actions
│       │   ├── UserProfile.jsx           ← per-user baseline + risk overview
│       │   └── MetricsPanel.jsx          ← evaluation metrics display
│       └── index.jsx
│
├── notebooks/
│   ├── 01_eda_and_baseline.ipynb         ← exploratory analysis + baseline visualization
│   └── 02_anomaly_detection_evaluation.ipynb ← detection validation + metrics
│
└── docs/
    ├── architecture.md                   ← pipeline design decisions
    ├── frontend-notes.md                 ← UI decisions
    └── notebook-guide.md                 ← notebook structure reference
```

**Immutable rule:** `data/raw/` is never written to. All pipeline output goes to `data/output/`.
**Immutable rule:** Notebooks never redefine logic — they import from `src/` only.
**Immutable rule:** All file paths come from `config.py` — never hardcoded in any module.

---

## Actual Data Columns (confirmed from organizer files)

### `data/raw/data_access_logs.csv`
| Column | Type | Notes |
|--------|------|-------|
| `timestamp` | datetime | Normalize to UTC on ingest |
| `user_id` | string | Join key |
| `username` | string | Display only |
| `action` | string | login, sql_query, admin_operation, EXPORT, DELETE, etc. |
| `resource` | string | Table, file, or system accessed |
| `resource_sensitivity` | string | low / medium / high / restricted |
| `status` | string | success / failed |
| `source_ip` | string | Used for IP baseline anomaly detection |
| `time_classification` | string | Pre-computed: business_hours / unusual_hours / night / weekend |

### `data/raw/user_profiles.csv`
| Column | Type | Notes |
|--------|------|-------|
| `user_id` | string | Join key |
| `username` | string | Display only |
| `email` | string | Display only |
| `department` | string | Used for FP suppression (month-end) |
| `job_title` | string | Context for LLM narrator |
| `privilege_level` | string | user / power-user / admin — used in scoring |
| `systems_access` | string | Pipe-separated approved systems list |
| `last_login` | datetime | Context only |
| `days_inactive` | int | Used in Dimension 4 stale account scoring |
| `is_active` | bool | Used in Dimension 4 stale account scoring |
| `hire_date` | datetime | Derive tenure: (today - hire_date).days / 30 |

### Columns confirmed NOT present (do not reference anywhere)
`rowcount`, `destination`, `anomaly_marker`, `account_type`, `access_tier`,
`typical_access_hours`, `approved_data_assets`, `avg_rowcount_per_query`,
`high_risk_flag`, `tenure_months`, `on_call`, `role_change_date`

---

## Tech Stack

### Backend / Pipeline
| Tool | Purpose |
|------|---------|
| Python 3.11+ | Core language |
| pandas | Ingestion, merging, column computation |
| numpy | Numerical operations |
| scikit-learn | Precision, Recall, F1 in evaluator |
| python-dotenv | Load GEMINI_API_KEY from .env |
| FastAPI | REST API serving dashboard |
| uvicorn | ASGI server |

### LLM
| Setting | Value |
|---------|-------|
| SDK | `pip install google-generativeai` |
| Model | `gemini-2.0-flash` |
| Key | `GEMINI_API_KEY` in `.env` — never commit |
| Source | aistudio.google.com — free tier |
| Threshold | Only events with `risk_score >= 50` sent to Gemini |

### Frontend
| Tool | Purpose |
|------|---------|
| React 18 + Vite | Dashboard UI |
| Recharts | Risk charts, severity breakdown |
| Tailwind CSS | Styling |

### Notebooks
| Tool | Purpose |
|------|---------|
| Jupyter | EDA + evaluation |
| matplotlib / seaborn | Visualizations |
| All `src/` modules | Imported — no logic redefined in notebooks |

---

## Architecture — 5-Layer Pipeline

```
Layer 1  DATA SOURCES (read-only)
         data/raw/data_access_logs.csv
         data/raw/user_profiles.csv
              ↓
Layer 2  INGESTION & NORMALIZATION  [src/ingestor.py]
         - load_access_logs()       → parse timestamps to UTC
         - load_user_profiles()     → parse systems_access pipe-separated list to Python list
         - merge_logs_with_profiles() → left join on user_id
         - handle_nulls()           → fill or flag missing fields
         Output: single enriched dataframe in memory
              ↓
Layer 3  BEHAVIORAL BASELINE ENGINE  [src/baseline.py]
         Training window: chronologically first 30 days of log data
         Per-user baseline dict contains:
           - seen_ips: set of source_ip values observed
           - typical_time_classifications: Counter of time_classification values
           - typical_actions: Counter of action values
           - typical_resources: set of resources accessed
           - tenure_months: derived from hire_date
         Separate baseline profiles for:
           admin (privilege_level=admin), standard user, inactive account
              ↓
Layer 4  ANOMALY SCORING + FP SUPPRESSION
         [src/detector.py + src/suppressor.py]

         5-DIMENSION SCORING — composite 0-100 (all integers):

         DIM 1 — Time Anomaly                              max 20 pts
           Column: time_classification
           business_hours → 0  |  unusual_hours → 8
           weekend → 12        |  night → 20

         DIM 2 — Action × Sensitivity Risk                 max 25 pts
           Columns: action + resource_sensitivity
           Cross-score matrix:
                               low  medium  high  restricted
           login/SELECT         0     2      8      15
           UPDATE/INSERT        1     5     12      20
           admin_operation      3     8     18      23
           EXPORT/DELETE        5    10     20      25
           status=failed        +5 bonus added to any cell above

         DIM 3 — Unauthorized System Access                max 25 pts
           Columns: resource + systems_access (profile)
           resource IN systems_access     →  0 pts
           resource NOT IN systems_access → 25 pts

         DIM 4 — Stale / Inactive Account                  max 15 pts
           Columns: is_active + days_inactive (profile)
           is_active=False      → 15 pts
           days_inactive > 90   → 12 pts
           days_inactive 31-90  →  8 pts
           days_inactive 8-30   →  4 pts
           days_inactive 0-7    →  0 pts

         DIM 5 — IP & Privilege Anomaly                    max 15 pts
           Columns: source_ip (log) + privilege_level (profile) + baseline.seen_ips
           source_ip not in baseline.seen_ips  →  8 pts
           privilege_level=admin + night       →  7 pts
           Both signals present               → 15 pts

         composite risk_score = sum(dim1..dim5), clipped to 0-100 (integer)
         anomaly_signals = list of human-readable strings for each dim that fired

         FALSE POSITIVE SUPPRESSION [src/suppressor.py]:
           1. Month-end close: department in [Finance, Accounting]
              AND day-of-month >= 28 → downgrade severity one level
           2. Admin privilege: privilege_level=admin + time=night
              → suppress Dim1 only (admins work odd hours)
           3. New hire: tenure_months < 3
              → suppress Dim3 only (new hires access unfamiliar systems)
           4. Inactive but flagged for review: is_active=False
              → do NOT suppress — escalate to CRITICAL regardless
           5. Failed access on non-sensitive resource: status=failed
              AND resource_sensitivity in [low, medium]
              → suppress Dim2 failed bonus only
              ↓
Layer 5  LLM REASONING  [src/llm_narrator.py]
         Input: enriched event + user profile + baseline dict
         Only events with risk_score >= 50 sent to Gemini
         Output per incident: severity, confidence (0-100), narrative, recommended_actions[]
              ↓
OUTPUT   [data/output/ + api/main.py + frontend/]
         scored_incidents.csv    → ALL events with risk scores (written by pipeline)
         flagged_incidents.csv   → risk_score >= 50 with LLM narratives
         derived_labels.csv      → rule-derived ground truth from src/labeler.py
         FastAPI serves all three files to React dashboard
```

---

## Output File Convention

Pipeline writes three files to `data/output/` — **never to `data/raw/`**.

```python
# config.py — all paths defined here, imported everywhere
from pathlib import Path

ROOT = Path(__file__).parent
DATA_RAW       = ROOT / "data" / "raw"
DATA_OUTPUT    = ROOT / "data" / "output"

LOGS_CSV       = DATA_RAW    / "data_access_logs.csv"
PROFILES_CSV   = DATA_RAW    / "user_profiles.csv"

SCORED_CSV     = DATA_OUTPUT / "scored_incidents.csv"
FLAGGED_CSV    = DATA_OUTPUT / "flagged_incidents.csv"
LABELS_CSV     = DATA_OUTPUT / "derived_labels.csv"
```

`data/output/` is in `.gitignore` — output files are never committed.
FastAPI reads from `data/output/` on startup after running the pipeline.
Notebooks load from `data/output/` for the evaluation notebook (no re-running pipeline).

---

## Evaluation — Three-Tier Strategy  [src/evaluator.py]

Ground truth label files were not included in the organizer sample data.
An email has been sent requesting them. Build all three tiers — they stack.

### Tier 1 — Known Anomaly Recall (always available)
The README documents 6 explicitly named anomalous access_ids:
```python
KNOWN_ANOMALIES = {
    'ACC-000007': 'BULK_EXPORT_UNUSUAL',
    'ACC-000012': 'NIGHT_BULK_EXPORT_CRITICAL',
    'ACC-000013': 'NIGHT_BULK_EXPORT_CRITICAL',
    'ACC-000017': 'BULK_EXPORT_UNUSUAL',
    'ACC-000028': 'ANALYST_ACCESSING_RESTRICTED',
    'ACC-000029': 'INTERN_BULK_PII_ACCESS',
}
```
Metric: did the system flag all 6? At what severity?
Function: `evaluate_known_anomalies(scored_df) -> dict`

### Tier 2 — Derived Label Evaluation (src/labeler.py)
Build ground truth from domain rules using real columns:
```python
# labeler.py derives is_anomaly + anomaly_type + derived_severity per event
# Rules based on: time_classification, resource_sensitivity,
#                 systems_access, action, status, is_active, days_inactive
# Output written to data/output/derived_labels.csv
```
Compute full Precision, Recall, F1 against derived labels.
Document labeling methodology transparently in notebook Section 1.
Function: `evaluate_against_derived(scored_df, labels_df) -> dict`

### Tier 3 — Organizer Label Evaluation (plug-in when available)
If organizers provide label files, drop them in `data/raw/` and run:
Function: `evaluate_against_labels(scored_df, labels_df) -> dict`
This function accepts any labels dataframe — source agnostic.

### Unified Report
```python
def full_evaluation_report(scored_df, profiles_df, organizer_labels_df=None):
    """
    Runs all available tiers. Uses organizer labels if provided,
    always runs Tier 1 and Tier 2 regardless.
    Prints unified report + returns metrics dict.
    """
```
**Targets (against derived labels):** Precision > 0.75, Recall > 0.70, F1 > 0.72

---

## Gemini Prompt Template  [src/llm_narrator.py]

Only called for events where risk_score >= 50. Returns JSON only.

```
You are a cybersecurity analyst reviewing a data access anomaly.
Respond ONLY with the JSON structure below — no preamble, no markdown.

USER:
  Name: {username} | Role: {job_title} | Dept: {department}
  Privilege: {privilege_level}
  Account: active={is_active}, days_inactive={days_inactive}
  Approved systems: {systems_access}
  Tenure: {tenure_months} months

EVENT:
  Time: {timestamp} ({time_classification})
  Action: {action} on {resource}
  Sensitivity: {resource_sensitivity}
  Status: {status}
  Source IP: {source_ip} ({'KNOWN' if ip_known else 'UNKNOWN — not in 30-day baseline'})

DETECTION:
  Risk score: {risk_score}/100
  Signals fired: {anomaly_signals}

{{
  "severity": "CRITICAL|HIGH|MEDIUM|LOW",
  "confidence": <integer 0-100>,
  "narrative": "<2-3 sentences: what happened, why suspicious, what it could mean>",
  "recommended_actions": ["<action 1>", "<action 2>", "<action 3>"]
}}
```

---

## Coding Rules

- Every `src/` module importable with zero side effects on import
- All functions: type hints + one-line docstring
- All file paths from `config.py` — never hardcoded in any module
- Never commit `.env` — add to `.gitignore` on Step 1
- Timestamps: normalize to UTC in `ingestor.py` — never elsewhere
- Risk scores: always `int`, always clipped to 0–100
- `systems_access` column: parse pipe-separated string to Python `list` in ingestor
- All Gemini calls go through `src/llm_narrator.py` only
- Notebooks: runnable top-to-bottom via `Kernel → Restart & Run All`
- `data/output/` files: regenerated by pipeline — never manually edited

---

## Git Workflow

One commit per implementation step. Never combine steps.

```bash
git add .
git commit -m "feat: <feature name>"
git push origin main
```

---

## Implementation Steps (sequential — commit after each)

### Step 1 — Project Scaffold
- [ ] Initialize git repo
- [ ] Create full folder structure including `data/raw/`, `data/output/`
- [ ] Write `config.py` with all path constants
- [ ] Write `requirements.txt`
- [ ] Write `.gitignore`: `.env`, `__pycache__`, `.ipynb_checkpoints`,
      `node_modules`, `data/output/`, `venv/`
- [ ] Write `.env.example` with `GEMINI_API_KEY=your_key_here`
- [ ] Create empty placeholder files for all `src/` modules
- [ ] Write stub `README.md`
- [ ] **Commit:** `feat: project scaffold and folder structure`

### Step 2 — Data Ingestion & Normalization  (src/ingestor.py)
- [ ] `load_access_logs() -> pd.DataFrame`
      Parse timestamps to UTC. Validate all 9 expected columns present.
- [ ] `load_user_profiles() -> pd.DataFrame`
      Parse `systems_access` pipe-separated string → Python list column.
      Derive `tenure_months` from `hire_date`.
- [ ] `merge_logs_with_profiles(logs, profiles) -> pd.DataFrame`
      Left join on `user_id`. Suffix duplicates with `_log` / `_profile`.
- [ ] `handle_nulls(df) -> pd.DataFrame`
      Fill or flag — document every decision in docstring.
- [ ] Verify: no duplicate columns, all timestamps UTC, `systems_access` is list type
- [ ] **Commit:** `feat: data ingestion and normalization layer`

### Step 3 — Behavioral Baseline Engine  (src/baseline.py)
- [ ] `build_user_baseline(user_events_df, profile_row) -> dict`
      Returns: `seen_ips` (set), `typical_time_classifications` (Counter),
      `typical_actions` (Counter), `typical_resources` (set), `tenure_months` (float)
- [ ] `build_all_baselines(df, profiles) -> dict[str, dict]`
      Key: user_id. Training window: chronologically first 30 days of log data.
- [ ] Handle users with < 7 days of history: mark baseline as `low_confidence=True`
- [ ] Separate logic for `privilege_level=admin` — wider expected patterns
- [ ] **Commit:** `feat: per-user behavioral baseline engine`

### Step 4 — Anomaly Scoring Engine  (src/detector.py)
- [ ] `score_time(row) -> int` — Dim 1, max 20, uses `time_classification`
- [ ] `score_action_sensitivity(row) -> int` — Dim 2, max 25, cross-score matrix above
- [ ] `score_system_access(row, profile) -> int` — Dim 3, max 25, resource vs systems_access
- [ ] `score_stale_account(profile) -> int` — Dim 4, max 15, is_active + days_inactive
- [ ] `score_ip_privilege(row, profile, baseline) -> int` — Dim 5, max 15
- [ ] `build_anomaly_signals(row, profile, baseline, scores) -> list[str]`
      Human-readable signal strings for each dimension that fired (score > 0)
- [ ] `compute_risk_score(row, profile, baseline) -> tuple[int, list[str]]`
      Returns (composite_score clipped 0-100, signals_list)
- [ ] `score_all_events(df, profiles, baselines) -> pd.DataFrame`
      Adds columns: `dim1`..`dim5`, `risk_score`, `anomaly_signals`
      Writes full result to `config.SCORED_CSV`
- [ ] **Commit:** `feat: 5-dimension anomaly scoring engine`

### Step 5 — False Positive Suppression  (src/suppressor.py)
- [ ] `suppress(row, profile) -> dict`
      Returns `{'suppressed': bool, 'reason': str, 'adjusted_severity': str}`
- [ ] Implement all 5 suppression rules from architecture section above
- [ ] `apply_suppression(scored_df, profiles) -> pd.DataFrame`
      Adds columns: `suppressed`, `suppression_reason`, `adjusted_severity`
- [ ] Write one inline unit test per rule using assert statements at bottom of file
      (run with `python src/suppressor.py` — prints PASS/FAIL per rule)
- [ ] **Commit:** `feat: false positive suppression with 5 rules`

### Step 6 — Ground Truth Labeler  (src/labeler.py)
- [ ] `derive_label(row, profile) -> dict`
      Returns `{'is_anomaly': bool, 'anomaly_type': str|None, 'derived_severity': str}`
      Rules: stale account access, unauthorized sensitive access,
      off-hours privileged action, failed restricted access
- [ ] `label_all_events(df, profiles) -> pd.DataFrame`
      Writes result to `config.LABELS_CSV`
- [ ] Document labeling methodology in module docstring — judges will read this
- [ ] **Commit:** `feat: rule-derived ground truth labeler`

### Step 7 — LLM Narrator  (src/llm_narrator.py)
- [ ] Load `GEMINI_API_KEY` from `.env` via `python-dotenv`
- [ ] `build_prompt(row, profile, baseline) -> str`
      Uses exact prompt template from architecture section above
- [ ] `generate_narrative(row, profile, baseline) -> dict`
      Calls Gemini, parses JSON response, returns dict with
      severity / confidence / narrative / recommended_actions
- [ ] `generate_narrative_safe(row, profile, baseline) -> dict`
      Wraps above in try/except — returns fallback dict on any API error
- [ ] `narrate_flagged_incidents(scored_df, profiles, baselines) -> pd.DataFrame`
      Filters risk_score >= 50, calls generate_narrative_safe per row,
      adds narrative columns, writes to `config.FLAGGED_CSV`
- [ ] **Commit:** `feat: Gemini LLM narrative generation`

### Step 8 — Evaluation Module  (src/evaluator.py)
- [ ] `evaluate_known_anomalies(scored_df) -> dict`
      Tier 1: checks all 6 README-named access_ids are flagged, at correct severity
- [ ] `evaluate_against_derived(scored_df, labels_df) -> dict`
      Tier 2: full P/R/F1 using derived_labels.csv
- [ ] `evaluate_against_labels(scored_df, labels_df) -> dict`
      Tier 3: same logic, accepts any labels_df (organizer or derived)
- [ ] `per_severity_metrics(scored_df, labels_df) -> dict`
      Breakdown by CRITICAL / HIGH / MEDIUM
- [ ] `full_evaluation_report(scored_df, profiles_df, organizer_labels_df=None)`
      Runs all available tiers, prints unified report, returns metrics dict
- [ ] **Commit:** `feat: three-tier evaluation framework`

### Step 9 — FastAPI Backend  (api/main.py)
- [ ] On startup: run full pipeline (ingest → baseline → score → suppress → narrate → label)
      Cache all results in module-level variables
- [ ] `GET /incidents` — flagged_incidents sorted by risk_score desc, top 50
- [ ] `GET /incidents/{access_id}` — single incident full detail
- [ ] `GET /users` — all user profiles with their max risk_score
- [ ] `GET /metrics` — evaluation report dict (all three tiers)
- [ ] `GET /health` — pipeline status + record counts
- [ ] Enable CORS for React dev server (localhost:5173)
- [ ] **Commit:** `feat: FastAPI backend with full pipeline integration`

### Step 10 — React Dashboard  (frontend/)
- [ ] Scaffold: `npm create vite@latest frontend -- --template react`
      Install: `tailwindcss`, `recharts`, `axios`
- [ ] `MetricsPanel.jsx` — P/R/F1 cards + tier indicators
- [ ] `IncidentDashboard.jsx` — sortable table: severity badge, risk score,
      username, resource, time_classification, action
- [ ] `IncidentCard.jsx` — click-through: all scores per dimension,
      signals list, Gemini narrative, recommended actions
- [ ] `UserProfile.jsx` — profile stats, days_inactive, is_active flag,
      all incidents for that user
- [ ] Connect all to FastAPI via axios
- [ ] **Commit:** `feat: React dashboard with incident and metrics views`

### Step 11 — EDA Notebook  (notebooks/01_eda_and_baseline.ipynb)
All cells import from `src/` — zero logic redefined in notebook.
- [ ] Section 1: Data overview — shape, dtypes, null counts, date range,
      unique users, unique resources
- [ ] Section 2: Distribution plots — time_classification, resource_sensitivity,
      action types, department breakdown
- [ ] Section 3: Baseline visualization — 3 example users showing
      seen_ips count, time_classification distribution, resource variety
- [ ] Section 4: Anomaly signal preview — manually inspect the 6 known
      anomalous access_ids from README
- [ ] Section 5: Key findings markdown summary
- [ ] Pre-run all cells — save with outputs visible
- [ ] **Commit:** `feat: EDA and baseline analysis notebook`

### Step 12 — Evaluation Notebook  (notebooks/02_anomaly_detection_evaluation.ipynb)
All cells import from `src/` — zero logic redefined.
- [ ] Section 1: Labeling methodology — explain derive_label rules,
      show label distribution, justify design decisions
- [ ] Section 2: Detection results — load scored_incidents.csv,
      show risk score distribution histogram
- [ ] Section 3: Full evaluation report — call full_evaluation_report(),
      display all three tiers, highlight P/R/F1 against targets
- [ ] Section 4: FP suppression analysis — how many events suppressed,
      by which rule, before/after comparison
- [ ] Section 5: Example incidents — 5 detailed walkthroughs:
      event → signals fired → score → Gemini narrative → recommended action
- [ ] Section 6: Scaling architecture — document how system handles 1M+ daily events
      (Kafka, Spark, async LLM batching, PostgreSQL partitioning)
- [ ] Pre-run all cells — save with outputs visible
- [ ] **Commit:** `feat: anomaly detection evaluation notebook`

### Step 13 — Final Polish & Submission
- [ ] Verify `data/output/flagged_incidents.csv` has 20+ incidents with narratives
- [ ] Final `README.md`: setup, run instructions, architecture summary,
      metric results, design decisions
- [ ] Verify both notebooks run clean: `Kernel → Restart & Run All`
- [ ] Verify FastAPI + React run together: no console errors, all endpoints respond
- [ ] Run deliverables checklist below — confirm every box checked
- [ ] **Commit:** `feat: final polish and submission prep`
- [ ] **Tag:** `git tag v1.0.0 && git push origin v1.0.0`

---

## Deliverables Checklist (from problem statement)

- [ ] GitHub repo — code, `requirements.txt`, clear README
- [ ] `notebooks/01_eda_and_baseline.ipynb` — saved outputs visible
- [ ] `notebooks/02_anomaly_detection_evaluation.ipynb` — saved outputs visible
- [ ] 20+ flagged incidents with LLM narratives (`data/output/flagged_incidents.csv`)
- [ ] Risk dashboard — React frontend running against FastAPI
- [ ] False positive analysis — in notebook Section 4 + suppressor.py docstrings
- [ ] Technical docs — `docs/` folder covering approach, scoring, scaling
- [ ] 5-minute presentation — problem → solution → live demo → metrics

---

## Scaling Notes (document in notebook Section 6)

Current sample: ~300 events. Architecture targets 1M+ daily events:

- **Ingestion:** Replace CSV reads with Apache Kafka consumer, partition by user_id
- **Baselines:** Compute on Apache Spark, store in Redis for sub-ms lookup
- **Scoring:** Embarrassingly parallel — map score_all_events across partitions
- **LLM throttling:** Only risk_score >= 50 sent to Gemini (~5% of events at scale)
  Batched via asyncio, rate-limited to stay within free tier quotas
- **Storage:** `data/output/` CSVs → PostgreSQL with date-partitioned tables
- **Performance target:** 1M events < 120 seconds on 4-core machine

---

## Environment Setup

```bash
# Python
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Environment
cp .env.example .env
# Edit .env and set GEMINI_API_KEY=<your key from aistudio.google.com>

# Run pipeline + backend
cd api && uvicorn main:app --reload

# Run frontend (separate terminal)
cd frontend && npm install && npm run dev

# Run notebooks
jupyter notebook notebooks/
```

---

## Current Status

- [x] Problem statement selected: PS4
- [x] Tech stack finalized (Gemini 2.0 Flash, FastAPI, React)
- [x] Actual data columns confirmed from organizer files
- [x] Scoring dimensions redesigned around real columns (5 dims, 0-100)
- [x] Output file convention decided (data/output/, read-only raw/)
- [x] Three-tier evaluation strategy designed (label files pending from organizers)
- [x] CLAUDE.md fully updated
- [ ] Step 1: Project scaffold