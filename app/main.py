"""FastAPI entrypoint.

Run with:  uvicorn app.main:app --reload
Then open: http://127.0.0.1:8000/docs
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .api.routes import router
from .config import get_settings

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(
    title="Insurance Agent Suite (OpenAI)",
    version="2.1.2",
    description=(
        "Four governance-READY OpenAI agents (Policy Q&A, Customer Service Email, "
        "Underwriting Advisor, Claims Adjudication). Each is pure capability: a "
        "system prompt plus stably-named tools that all execute through a single "
        "chokepoint (registry.dispatch). No guardrails live in the agents — "
        "enforcement is attached externally by the Agent Lifecycle Hub."
    ),
)

app.include_router(router)


@app.get("/", include_in_schema=False)
def root():
    # Land users on the UI; service info lives at /info.
    return RedirectResponse(url="/ui/")


@app.get("/info", tags=["meta"], summary="Service info and configuration status")
def info():
    settings = get_settings()
    return {
        "service": "Insurance Agent Suite",
        "openai_model": settings.openai_model,
        "openai_key_configured": bool(settings.openai_api_key),
        "agents": ["policy-qa", "cs-email", "underwriting", "claims"],
        "governance": "external (Agent Lifecycle Hub) — enforced at registry.dispatch chokepoint",
        "ui": "/ui/",
        "docs": "/docs",
    }


@app.get("/health", tags=["meta"])
def health():
    return {"status": "ok"}


# Serve the single-page frontend from the same app (no separate port / CORS).
app.mount("/ui", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
