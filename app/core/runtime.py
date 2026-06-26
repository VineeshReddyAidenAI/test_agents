"""The agent runtime: a standard OpenAI tool-calling loop.

The model reasons and decides which tools to call; every tool call is executed
through the single chokepoint (`registry.dispatch`). The loop carries the
ToolContext but never inspects it for policy — it just passes it along.
"""
from __future__ import annotations

import json
import time

from ..config import get_settings
from ..llm import LLMError, get_client
from .agent import Agent
from .context import ToolContext
from .registry import registry

MAX_STEPS = 8


def _stats(steps: list[dict], started: float) -> dict:
    """Small per-run summary: latency and read/write tool-call counts."""
    return {
        "elapsed_ms": round((time.perf_counter() - started) * 1000),
        "tool_calls": len(steps),
        "reads": sum(1 for s in steps if not s["writes"]),
        "writes": sum(1 for s in steps if s["writes"]),
    }


def run_agent(agent: Agent, context: ToolContext, user_input: str) -> dict:
    client = get_client()
    settings = get_settings()
    tools = registry.openai_tools(agent.tool_names)

    messages: list[dict] = [
        {"role": "system", "content": agent.system_prompt},
        {"role": "user", "content": user_input},
    ]
    steps: list[dict] = []
    started = time.perf_counter()

    for _ in range(MAX_STEPS):
        try:
            resp = client.chat.completions.create(
                model=settings.openai_model,
                temperature=settings.openai_temperature,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        except Exception as exc:  # noqa: BLE001
            raise LLMError(f"OpenAI request failed: {exc}") from exc

        msg = resp.choices[0].message

        # Rebuild the assistant message cleanly for the next turn.
        assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
        if msg.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in msg.tool_calls
            ]
        messages.append(assistant_msg)

        if not msg.tool_calls:
            return {
                "output": msg.content or "",
                "tool_calls": steps,
                "context": context.snapshot(),
                "stats": _stats(steps, started),
            }

        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            spec = registry.get(tc.function.name)
            result = registry.dispatch(tc.function.name, args, context)  # the chokepoint
            steps.append(
                {
                    "operation": tc.function.name,
                    "writes": spec.writes,
                    "arguments": args,
                    "result": result,
                    "actor_id": context.actor_id,
                    "actor_role": context.actor_role,
                }
            )
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, default=str),
                }
            )

    return {
        "output": "(stopped: reached the maximum number of tool-calling steps)",
        "tool_calls": steps,
        "context": context.snapshot(),
        "stats": _stats(steps, started),
    }
