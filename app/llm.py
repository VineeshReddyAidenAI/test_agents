"""OpenAI client access. One place to read the key and the model defaults."""
from __future__ import annotations

from functools import lru_cache

from openai import OpenAI

from .config import get_settings


class LLMError(RuntimeError):
    """Raised when the LLM is misconfigured or a request fails."""


@lru_cache
def get_client() -> OpenAI:
    settings = get_settings()
    if not settings.openai_api_key:
        raise LLMError(
            "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key, "
            "or export OPENAI_API_KEY in your environment."
        )
    return OpenAI(api_key=settings.openai_api_key)
