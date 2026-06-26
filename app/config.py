"""Application settings, loaded from environment / .env file.

Note: there are intentionally NO governance settings here (no PII rules, no
approval limits, no allow/deny config). Governance is enforced externally by the
Agent Lifecycle Hub, not by this agent.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
# Where write-tools persist their side effects (decisions, drafts, ...).
LEDGER_DIR = BASE_DIR.parent / "ledgers"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Key is optional so the app can boot and serve the UI without it; agent
    # invocation raises a clear error if it is missing.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.2


@lru_cache
def get_settings() -> Settings:
    return Settings()
