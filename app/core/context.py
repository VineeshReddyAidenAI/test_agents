"""Call context that travels with every tool invocation.

This is *clean context only*. The agent makes these fields available so the
governance platform can use them later (authorize by actor/role/operation). The
agent itself NEVER branches on them — no "if role == admin" logic lives here.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ToolContext:
    actor_id: str          # who initiated this (end user / service account)
    actor_role: str        # their role or group, e.g. "support_agent"
    agent_id: str          # which agent is running
    operation: str | None = None  # set to the tool name at dispatch time

    def snapshot(self) -> dict:
        return {
            "actor_id": self.actor_id,
            "actor_role": self.actor_role,
            "agent_id": self.agent_id,
            "operation": self.operation,
        }
