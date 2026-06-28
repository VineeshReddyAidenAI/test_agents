"""Fraud detection tools. Used by the Fraud Detection agent.

  check_fraud_watchlist         -> read (simulated EXTERNAL API call to a 3rd party)
  flag_claim_for_investigation  -> write (the autonomous decision / SIU referral)

No policy here: the tools just run. Whether an external call or a fraud flag is
permitted for this actor is decided externally at the chokepoint.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..config import LEDGER_DIR
from ..core.context import ToolContext
from ..core.registry import registry

# Tiny stand-in for a third-party watchlist/sanctions service.
_WATCHLIST = {
    "marcus webb": {
        "list": "internal_siu",
        "reason": "named in a prior fraud investigation (2023)",
    },
}


@registry.tool(
    name="check_fraud_watchlist",
    description="Check a claimant against external fraud / sanctions watchlists (third-party API). Read-only external call.",
    parameters={
        "type": "object",
        "properties": {
            "claimant_name": {"type": "string"},
            "policy_id": {"type": "string"},
        },
        "required": ["claimant_name"],
    },
    writes=False,
)
def check_fraud_watchlist(args: dict, ctx: ToolContext) -> dict:
    name = (args.get("claimant_name") or "").strip().lower()
    hit = _WATCHLIST.get(name)
    base = {"source": "external_watchlist_api", "claimant": args.get("claimant_name")}
    if hit:
        return {**base, "match": True, **hit}
    return {**base, "match": False}


@registry.tool(
    name="flag_claim_for_investigation",
    description="Flag a claim for SIU (Special Investigations Unit) review with a risk level and reason.",
    parameters={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
            "reason": {"type": "string"},
        },
        "required": ["claim_id", "risk_level", "reason"],
    },
    writes=True,
)
def flag_claim_for_investigation(args: dict, ctx: ToolContext) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_id": args.get("claim_id"),
        "risk_level": args.get("risk_level"),
        "reason": args.get("reason"),
        "flagged_by": ctx.actor_id,
    }
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "fraud_flags.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return {"status": "flagged_for_investigation", "ledger": str(path)}
