"""Agent API: capability manifests, invocation, and the chokepoint trace."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .. import tools  # noqa: F401  (import registers all tools into the registry)
from ..agents import AGENTS
from ..core.context import ToolContext
from ..core.registry import registry
from ..core.runtime import run_agent
from ..llm import LLMError
from .schemas import InvokeRequest

router = APIRouter()


@router.get("/agents", tags=["agents"], summary="List agents and their capabilities (tools)")
def list_agents():
    return {"agents": [a.manifest() for a in AGENTS.values()]}


@router.post("/agents/{agent_id}/invoke", tags=["agents"], summary="Run an agent")
def invoke(agent_id: str, req: InvokeRequest):
    agent = AGENTS.get(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_id}")
    context = ToolContext(actor_id=req.actor_id, actor_role=req.actor_role, agent_id=agent_id)
    try:
        result = run_agent(agent, context, req.input)
    except LLMError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return {"agent_id": agent_id, **result}


@router.get("/trace", tags=["observability"], summary="Recent tool calls through the chokepoint")
def trace(limit: int = 50):
    # Observability only — this is the single point every tool call passes
    # through, and where external governance attaches enforcement later.
    return {"calls": registry.recent(limit)}
