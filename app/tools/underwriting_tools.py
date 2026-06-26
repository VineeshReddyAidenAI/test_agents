"""Underwriting tools. Used by the Underwriting Risk Advisor agent."""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..config import LEDGER_DIR
from ..core import store
from ..core.context import ToolContext
from ..core.registry import registry

_ACTUARIAL_GUIDE = {
    "product": "auto",
    "base_annual_premium": 1200,
    "loadings": {
        "driver_under_25": "+35%",
        "each_at_fault_accident_3yr": "+20%",
        "each_moving_violation_3yr": "+8%",
        "annual_mileage_over_20000": "+12%",
        "credit_insurance_score_below_600": "+18% (where permitted)",
    },
    "credits": {"clean_record_5yr_plus": "-15%"},
}


@registry.tool(
    name="get_actuarial_guidelines",
    description="Return the actuarial reference table (base premium, risk loadings, credits) for auto underwriting.",
    parameters={"type": "object", "properties": {}},
    writes=False,
)
def get_actuarial_guidelines(args: dict, ctx: ToolContext) -> dict:
    return _ACTUARIAL_GUIDE


@registry.tool(
    name="lookup_applicant",
    description="Look up an insurance applicant's profile by applicant ID.",
    parameters={
        "type": "object",
        "properties": {"applicant_id": {"type": "string"}},
        "required": ["applicant_id"],
    },
    writes=False,
)
def lookup_applicant(args: dict, ctx: ToolContext) -> dict:
    applicant = store.get_applicant(args.get("applicant_id", ""))
    if applicant is None:
        return {"error": f"Applicant {args.get('applicant_id')} not found."}
    return applicant


@registry.tool(
    name="record_recommendation",
    description="Record an underwriting recommendation (approve/decline/refer) with a premium adjustment and rationale.",
    parameters={
        "type": "object",
        "properties": {
            "applicant_id": {"type": "string"},
            "recommendation": {"type": "string", "enum": ["approve", "decline", "refer"]},
            "risk_score": {"type": "integer"},
            "premium_adjustment_pct": {"type": "number"},
            "rationale": {"type": "string"},
        },
        "required": ["applicant_id", "recommendation", "rationale"],
    },
    writes=True,
)
def record_recommendation(args: dict, ctx: ToolContext) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "applicant_id": args.get("applicant_id"),
        "recommendation": args.get("recommendation"),
        "risk_score": args.get("risk_score"),
        "premium_adjustment_pct": args.get("premium_adjustment_pct"),
        "rationale": args.get("rationale"),
        "recorded_by": ctx.actor_id,
    }
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "underwriting_recommendations.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return {"status": "recommendation_recorded", "ledger": str(path)}
