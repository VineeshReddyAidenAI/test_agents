"""The tool registry and the SINGLE execution chokepoint.

Every tool the agents can use is registered here, and EVERY tool call is
executed through `registry.dispatch(...)`. There is exactly one place where
tools run.

=============================  GOVERNANCE SEAM  =============================
`dispatch()` is the chokepoint our external platform (Agent Lifecycle Hub)
plugs into later. To attach enforcement you call `set_interceptor(fn)` from
OUTSIDE this codebase — no agent code changes. By default there is NO
interceptor and NO policy here. This file deliberately contains zero allow/deny
logic, zero PII handling, zero rate limits. The agent just runs its tools.
============================================================================
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from .context import ToolContext

ToolHandler = Callable[[dict, ToolContext], Any]
# An interceptor receives the call record BEFORE execution. External governance
# may inspect it and raise to deny. We never set one here.
Interceptor = Callable[[dict], None]


@dataclass(frozen=True)
class ToolSpec:
    name: str                 # stable, governable name (e.g. "fetch_record")
    description: str
    parameters: dict          # JSON Schema for the arguments
    handler: ToolHandler
    writes: bool = False       # side-effect-explicit: read (False) vs write (True)

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }

    def public(self) -> dict:
        return {"name": self.name, "description": self.description, "writes": self.writes}


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolSpec] = {}
        self._trace: list[dict] = []
        self._interceptor: Optional[Interceptor] = None

    # ---- registration ----
    def register(self, spec: ToolSpec) -> None:
        if spec.name in self._tools:
            raise ValueError(f"Tool already registered: {spec.name}")
        self._tools[spec.name] = spec

    def tool(self, name: str, description: str, parameters: dict, writes: bool = False):
        """Decorator form of register()."""
        def deco(fn: ToolHandler) -> ToolHandler:
            self.register(ToolSpec(name, description, parameters, fn, writes))
            return fn
        return deco

    def get(self, name: str) -> ToolSpec:
        return self._tools[name]

    def openai_tools(self, names: tuple[str, ...]) -> list[dict]:
        return [self._tools[n].to_openai() for n in names]

    # ---- the governance seam (no-op by default) ----
    def set_interceptor(self, fn: Optional[Interceptor]) -> None:
        """Attach/detach external enforcement. Not used by the agent itself."""
        self._interceptor = fn

    # ---- THE SINGLE CHOKEPOINT ----
    def dispatch(self, name: str, arguments: dict, context: ToolContext) -> Any:
        spec = self._tools[name]
        context.operation = name

        call_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            **context.snapshot(),
            "writes": spec.writes,
            "arguments": arguments,
        }

        # External governance hook. Default is None → nothing happens here.
        # The platform may inspect call_record and raise to deny.
        if self._interceptor is not None:
            self._interceptor(call_record)

        result = spec.handler(arguments, context)

        # Observability only (NOT enforcement): keep a recent call trace so the
        # chokepoint is visible in the UI. No redaction, no policy.
        self._trace.append({**call_record, "result": result})
        self._trace[:] = self._trace[-200:]
        return result

    def recent(self, limit: int = 50) -> list[dict]:
        return self._trace[-limit:]


# The one registry every agent and tool uses.
registry = ToolRegistry()
