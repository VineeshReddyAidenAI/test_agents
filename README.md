# Insurance Agent Suite — governance-ready (OpenAI + FastAPI)

Five OpenAI agents (Policy Q&A, Customer Service Email, Underwriting Advisor,
Claims Adjudication, Fraud Detection) built to be **governed by an external platform** (the
"Agent Lifecycle Hub"). The agents themselves contain **no** guardrails — no
permission checks, no PII filtering, no allow/deny, no rate limits. They are
pure capability: reason, call tools, return results.

All enforcement is added **later, outside the agent**, at one place.

## Core idea

```
            ┌────────────────────── agent (this repo) ──────────────────────┐
 user ─►   LLM reasons  ─►  picks a tool  ─►  registry.dispatch(name,args,ctx)  ─►  tool runs
            └───────────────────────────────────────────────│──────────────┘
                                                             │
                                       ◄── ONE CHOKEPOINT ───┘
                       External governance (Agent Lifecycle Hub) attaches here
                       later via registry.set_interceptor(...) — no agent code change.
```

- **Tools have stable names** (`fetch_record`, `send_email`, `record_claim_decision`, …) so the portal can authorize by name.
- **Every tool runs through one dispatcher** — [app/core/registry.py](app/core/registry.py) `dispatch()`.
- **Clean context travels with each call** (`actor_id`, `actor_role`, `operation`) — made available, never acted on by the agent.
- **Tools are side-effect-explicit** — each is `writes=True` or `writes=False`; sensitive actions (`send_email`, `record_claim_decision`) are their own named tools.

## What is intentionally NOT here

No keyword/blocklist filtering · no per-tool permission logic · no "agent decides
what's allowed" · no PII redaction / safety policy · no dollar ceilings or fraud
gates. Those are governance concerns enforced externally.

## The agents

| Agent (`id`) | What it does | Tools (read / **write**) |
|--------------|--------------|--------------------------|
| Policy Q&A (`policy-qa`) | Answers from the internal KB with citations | `search_knowledge_base`, `get_kb_article` |
| CS Email (`cs-email`) | Looks up a policy, drafts / sends a reply | `fetch_customer_record`, **`save_email_draft`**, **`send_email`** |
| Underwriting (`underwriting`) | Assesses applicant risk, records a recommendation | `get_actuarial_guidelines`, `lookup_applicant`, **`record_recommendation`** |
| Claims (`claims`) | Determines coverage, records a decision | `fetch_claim`, `fetch_policy`, **`record_claim_decision`** |
| Fraud Detection (`fraud-detection`) | Checks watchlists, flags suspicious claims | `fetch_claim`, `fetch_policy`, `check_fraud_watchlist` *(external API call)*, **`flag_claim_for_investigation`** |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env      # then set OPENAI_API_KEY in .env
```

## Run

```bash
uvicorn app.main:app --reload
```

- **http://127.0.0.1:8000/** → web UI (served by the same app, no second port).
  Pick an agent, set the actor context, run an instruction, and watch every tool
  call flow through the chokepoint. "Capabilities" and "Chokepoint Trace" views
  show the governance surface.
- **http://127.0.0.1:8000/docs** → Swagger UI for the raw API.

## API

| Method | Path | What it does |
|--------|------|--------------|
| GET  | `/` | Redirects to the UI |
| GET  | `/agents` | Capability manifest for each agent (tools, suggestions) |
| POST | `/agents/{agent_id}/invoke` | Run an agent: `{ "input", "actor_id", "actor_role" }` |
| GET  | `/trace` | Recent tool calls through the chokepoint |
| GET  | `/info` | Service info + whether the key is configured |

```bash
curl -X POST localhost:8000/agents/claims/invoke \
  -H "Content-Type: application/json" \
  -d '{"input":"Adjudicate claim CLM-55012.","actor_id":"user-001","actor_role":"adjuster"}'
```

The response includes the agent's `output` and a `tool_calls` list (operation,
`writes`, arguments, result, actor, role) — the exact calls a governance layer
would authorize.

## How governance plugs in later (no agent change)

```python
from app.core.registry import registry

def enforce(call_record):
    # call_record = {timestamp, actor_id, actor_role, agent_id, operation, writes, arguments}
    # external policy decides; raise to deny.
    ...

registry.set_interceptor(enforce)   # attach from outside; the agents are untouched
```

## Project layout

```
app/
  main.py                FastAPI app (mounts UI, /info, /health)
  config.py  llm.py      settings + OpenAI client (no governance config)
  core/
    context.py           ToolContext (actor_id, actor_role, operation) — carried, not enforced
    registry.py          ToolRegistry + THE single dispatch() chokepoint + interceptor seam
    runtime.py           OpenAI tool-calling loop
    agent.py             Agent manifest (prompt + tool names)
    store.py             reads KB / policies / claims / applicants
  tools/
    knowledge_tools.py   search_knowledge_base, get_kb_article
    customer_tools.py    fetch_customer_record, save_email_draft, send_email
    underwriting_tools.py get_actuarial_guidelines, lookup_applicant, record_recommendation
    claims_tools.py      fetch_claim, fetch_policy, record_claim_decision
    fraud_tools.py       check_fraud_watchlist, flag_claim_for_investigation
  agents/__init__.py     the 5 agent manifests
  api/                   routes.py, schemas.py
  data/                  knowledge_base.md, policies.json, claims.json, applicants.json
  static/index.html      single-page UI
ledgers/                 write-tool side effects (gitignored)
```
