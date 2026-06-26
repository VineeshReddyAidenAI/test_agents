"""Request bodies for the agent API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class InvokeRequest(BaseModel):
    """Invoke an agent with a natural-language instruction and caller context.

    actor_id / actor_role are clean context passed through to the tool
    chokepoint. The agent does not act on them — governance will, later.
    """

    input: str = Field(..., examples=["What is the grace period for a missed payment?"])
    actor_id: str = Field("user-001", examples=["user-001"])
    actor_role: str = Field("support_agent", examples=["support_agent"])
