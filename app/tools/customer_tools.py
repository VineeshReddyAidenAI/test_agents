"""Customer / policy tools. Used by the Customer Service Email agent.

Note the side-effect-explicit split:
  fetch_customer_record  -> read
  save_email_draft       -> write (draft)
  send_email             -> write (SENSITIVE, its own named tool)

The agent may call send_email freely; whether that is allowed is a governance
decision made externally, not here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

from ..config import LEDGER_DIR
from ..core import store
from ..core.context import ToolContext
from ..core.registry import registry


def _append_ledger(filename: str, record: dict) -> str:
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    path = LEDGER_DIR / filename
    with open(path, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")
    return str(path)


@registry.tool(
    name="fetch_customer_record",
    description="Look up a customer's policy record by policy ID (contact info, product, status, renewal).",
    parameters={
        "type": "object",
        "properties": {"policy_id": {"type": "string"}},
        "required": ["policy_id"],
    },
    writes=False,
)
def fetch_customer_record(args: dict, ctx: ToolContext) -> dict:
    policy = store.get_policy(args.get("policy_id", ""))
    if policy is None:
        return {"error": f"Policy {args.get('policy_id')} not found."}
    return policy


@registry.tool(
    name="save_email_draft",
    description="Save a draft email reply for a customer. Returns a draft id.",
    parameters={
        "type": "object",
        "properties": {
            "policy_id": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["policy_id", "subject", "body"],
    },
    writes=True,
)
def save_email_draft(args: dict, ctx: ToolContext) -> dict:
    record = {
        "kind": "draft",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "policy_id": args.get("policy_id"),
        "subject": args.get("subject"),
        "body": args.get("body"),
        "saved_by": ctx.actor_id,
    }
    path = _append_ledger("email_drafts.jsonl", record)
    return {"status": "draft_saved", "ledger": path}


@registry.tool(
    name="send_email",
    description="Send an email to the customer on a policy. This delivers a real message.",
    parameters={
        "type": "object",
        "properties": {
            "policy_id": {"type": "string"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["policy_id", "subject", "body"],
    },
    writes=True,
)
def send_email(args: dict, ctx: ToolContext) -> dict:
    record = {
        "kind": "sent",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "policy_id": args.get("policy_id"),
        "subject": args.get("subject"),
        "body": args.get("body"),
        "sent_by": ctx.actor_id,
    }
    path = _append_ledger("sent_emails.jsonl", record)
    return {"status": "sent", "ledger": path}
