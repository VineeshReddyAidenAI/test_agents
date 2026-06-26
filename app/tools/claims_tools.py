"""Claims tools. Used by the Claims Adjudication agent.

`record_claim_decision` is the sensitive write (the "production write" /
autonomous decision). It applies whatever decision the agent makes — there is
no dollar ceiling, no fraud gate, no policy-status check here. Those are
governance decisions enforced externally at the chokepoint.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..config import LEDGER_DIR
from ..core import store
from ..core.context import ToolContext
from ..core.registry import registry


@registry.tool(
    name="fetch_claim",
    description="Fetch a claim record by claim ID (loss details, amount, coverage, dates).",
    parameters={
        "type": "object",
        "properties": {"claim_id": {"type": "string"}},
        "required": ["claim_id"],
    },
    writes=False,
)
def fetch_claim(args: dict, ctx: ToolContext) -> dict:
    claim = store.get_claim(args.get("claim_id", ""))
    if claim is None:
        return {"error": f"Claim {args.get('claim_id')} not found."}
    return claim


@registry.tool(
    name="fetch_policy",
    description="Fetch the policy a claim belongs to, for coverage context.",
    parameters={
        "type": "object",
        "properties": {"policy_id": {"type": "string"}},
        "required": ["policy_id"],
    },
    writes=False,
)
def fetch_policy(args: dict, ctx: ToolContext) -> dict:
    policy = store.get_policy(args.get("policy_id", ""))
    if policy is None:
        return {"error": f"Policy {args.get('policy_id')} not found."}
    return policy


@registry.tool(
    name="record_claim_decision",
    description="Record a final claim decision (approve/deny) with the payable amount and reasoning.",
    parameters={
        "type": "object",
        "properties": {
            "claim_id": {"type": "string"},
            "decision": {"type": "string", "enum": ["approve", "deny"]},
            "payable_amount": {"type": "number"},
            "reasoning": {"type": "string"},
        },
        "required": ["claim_id", "decision", "payable_amount", "reasoning"],
    },
    writes=True,
)
def record_claim_decision(args: dict, ctx: ToolContext) -> dict:
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "claim_id": args.get("claim_id"),
        "decision": args.get("decision"),
        "payable_amount": args.get("payable_amount"),
        "reasoning": args.get("reasoning"),
        "decided_by": ctx.actor_id,
    }
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / "claim_decisions.jsonl"
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return {"status": "decision_recorded", "ledger": str(path)}
