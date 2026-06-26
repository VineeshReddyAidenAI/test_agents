"""Agent manifest — capabilities only.

An agent is: an id, a name/description (for the portal), a system prompt that
describes its job, and the STABLE tool names it may use. No risk tier, no
autonomy mode, no required reviews — those are governance attributes defined in
the portal, not in the agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .registry import registry


@dataclass(frozen=True)
class Suggestion:
    label: str
    input: str


@dataclass(frozen=True)
class Agent:
    agent_id: str
    name: str
    description: str
    system_prompt: str
    tool_names: tuple[str, ...]
    suggestions: tuple[Suggestion, ...] = field(default_factory=tuple)

    def manifest(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "description": self.description,
            "tools": [registry.get(n).public() for n in self.tool_names],
            "suggestions": [{"label": s.label, "input": s.input} for s in self.suggestions],
        }
