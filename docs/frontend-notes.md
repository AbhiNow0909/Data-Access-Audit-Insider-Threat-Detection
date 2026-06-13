# Frontend notes

React 18 + Vite + Tailwind dark dashboard. Talks to the FastAPI backend via
axios (`src/api.js`, base URL `VITE_API_URL` or `http://localhost:8000`).

## Run
```bash
cd frontend
npm install
npm run dev      # http://localhost:5173  (backend must be running on :8000)
```

## Components
- **MetricsPanel** — Precision / Recall / F1 cards with target ✓/✗, flagged
  volume + confusion counts, critical-recall. Source: `GET /metrics`.
- **IncidentDashboard** — prioritized, clickable incident list with severity
  badges and risk scores. Source: `GET /incidents`.
- **IncidentCard** — drill-down for the selected incident: the five dimension
  scores as bars, anomaly-signal chips, the analyst narrative (labelled Gemini
  vs rule-based fallback) and recommended actions. Source: `GET /incidents/{id}`.
- **UserProfile** — per-user risk table (privilege, dormancy, flagged count, max
  risk). Source: `GET /users`.
- **EventTester** ("Test Event" tab) — interactive form to score an arbitrary
  ad-hoc event + actor (an unseen user is fine), returning the same outputs as
  the batch system: risk score, dimension bars, signals, narrative, actions.
  Source: `POST /score`. Self-contained — does not touch the batch dataset.

## Decisions
- Single-page, two-tab layout (Incidents / Users) — fast to demo, no router.
- Incident identity is an integer `incident_id` (row index) because the data has
  no `access_id`.
- Severity → colour mapping centralised in `src/util.js`.
- App shows a clear "start the backend" message if the API is unreachable.
