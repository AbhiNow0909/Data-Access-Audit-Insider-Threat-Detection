# Architecture

5-layer pipeline: **Ingest → Baseline → Score → Suppress → Narrate**, plus
Evaluate. See `CLAUDE.md` for the full design. This doc is filled in as each
layer lands.

## Data reality (as shipped in `data/raw/`)

The actual organizer CSVs differ from the early design assumptions:

| Designed for | Actually available |
|---|---|
| `data_access_labels.csv`, `user_profile_labels.csv` | **Not provided** — no ground-truth labels |
| `rowcount`, `destination`, `data_asset` columns | Not present |
| profile `typical_access_hours`, `avg_*`, `high_risk_flag`, `tenure_months` | Not present |

**Access logs** (`data_access_logs.csv`, 1,200 rows, Apr 2025–Apr 2026):
`timestamp, user_id, username, action, resource, resource_sensitivity, status,
source_ip, time_classification`

**User profiles** (`user_profiles.csv`, 100 rows):
`user_id, username, email, department, job_title, privilege_level,
systems_access, last_login, days_inactive, is_active, hire_date`

### Consequences for the design
- **Baselines are learned from each user's FULL history** (not a 30-day window):
  the data is ~12 events/user/year, so a fixed window leaves ~64% of users with
  no baseline. A cohort baseline (by `privilege_level`) is the fallback for
  thin/zero-history users and admins. See `src/baseline.py`.
- **`source_ip` is effectively unique per event** (~1 IP per event), so the
  "new IP" signal carries little information here; Dim 5 leans on
  privilege x time rather than IP novelty (see `src/detector.py`).
- **5-dimension scoring over real columns** (see CLAUDE.md for point matrices):
  (1) time, (2) action x sensitivity, (3) unauthorized system access vs
  `systems_access`, (4) stale/inactive account, (5) IP & privilege. The
  original volume-spike and destination-risk dims are dropped — no source columns.
- **Three-tier evaluation** (`src/evaluator.py`): Tier 1 known-anomaly recall,
  Tier 2 full P/R/F1 vs rule-derived labels (`src/labeler.py`), Tier 3 plug-in
  organizer labels when available.
