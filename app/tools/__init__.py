"""Tool definitions.

Importing this package registers every tool into the single shared registry
(`app.core.registry.registry`). Tools are plain capabilities: they read or
write data and return results. They contain NO permission checks, NO PII
filtering, NO policy — governance is enforced at the chokepoint by the platform.
"""
from . import (  # noqa: F401
    claims_tools,
    customer_tools,
    fraud_tools,
    knowledge_tools,
    underwriting_tools,
)

__all__ = [
    "knowledge_tools",
    "customer_tools",
    "underwriting_tools",
    "claims_tools",
    "fraud_tools",
]
