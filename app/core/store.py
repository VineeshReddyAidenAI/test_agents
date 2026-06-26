"""Read access to the demo data files (knowledge base, policies, claims).

In a real deployment these would be database / document-store queries gated by
access controls. Here they are flat files loaded once and cached.
"""
from __future__ import annotations

import json
from functools import lru_cache

from ..config import DATA_DIR


@lru_cache
def knowledge_base() -> str:
    return (DATA_DIR / "knowledge_base.md").read_text(encoding="utf-8")


@lru_cache
def _policies() -> dict:
    return json.loads((DATA_DIR / "policies.json").read_text(encoding="utf-8"))


@lru_cache
def _claims() -> dict:
    return json.loads((DATA_DIR / "claims.json").read_text(encoding="utf-8"))


@lru_cache
def _applicants() -> dict:
    return json.loads((DATA_DIR / "applicants.json").read_text(encoding="utf-8"))


def get_policy(policy_id: str) -> dict | None:
    return _policies().get(policy_id)


def list_policy_ids() -> list[str]:
    return list(_policies().keys())


def get_claim(claim_id: str) -> dict | None:
    return _claims().get(claim_id)


def list_claim_ids() -> list[str]:
    return list(_claims().keys())


def get_applicant(applicant_id: str) -> dict | None:
    return _applicants().get(applicant_id)


def list_applicant_ids() -> list[str]:
    return list(_applicants().keys())
