"""FastAPI backend serving the dashboard. Implemented in Step 8."""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Insider Threat Detection API")


@app.get("/health")
def health() -> dict:
    """Sanity-check endpoint."""
    return {"status": "ok"}
