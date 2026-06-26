"""Knowledge-base tools (read-only). Used by the Policy Q&A agent."""
from __future__ import annotations

import re

from ..core import store
from ..core.context import ToolContext
from ..core.registry import registry

_SECTION_RE = re.compile(r"^##\s+(KB-\d+)\s+—\s+(.+)$", re.MULTILINE)


def _sections() -> list[tuple[str, str, str]]:
    kb = store.knowledge_base()
    matches = list(_SECTION_RE.finditer(kb))
    out = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(kb)
        out.append((m.group(1), m.group(2).strip(), kb[start:end].strip()))
    return out


@registry.tool(
    name="search_knowledge_base",
    description="Search the internal policy knowledge base and return the most relevant articles.",
    parameters={
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "What to search for."},
            "top_k": {"type": "integer", "description": "Max articles to return.", "default": 4},
        },
        "required": ["query"],
    },
    writes=False,
)
def search_knowledge_base(args: dict, ctx: ToolContext) -> dict:
    query = args.get("query", "")
    top_k = int(args.get("top_k", 4))
    terms = {w for w in re.findall(r"[a-zA-Z]{3,}", query.lower())}
    scored = []
    for sid, title, body in _sections():
        hay = f"{title} {body}".lower()
        score = sum(hay.count(t) for t in terms)
        scored.append((score, sid, title, body))
    scored.sort(key=lambda x: x[0], reverse=True)
    hits = [
        {"id": sid, "title": title, "content": body}
        for score, sid, title, body in scored
        if score > 0
    ][:top_k]
    return {"matches": hits, "count": len(hits)}


@registry.tool(
    name="get_kb_article",
    description="Fetch a single knowledge-base article by its ID (e.g. 'KB-002').",
    parameters={
        "type": "object",
        "properties": {"article_id": {"type": "string"}},
        "required": ["article_id"],
    },
    writes=False,
)
def get_kb_article(args: dict, ctx: ToolContext) -> dict:
    aid = args.get("article_id", "")
    for sid, title, body in _sections():
        if sid == aid:
            return {"id": sid, "title": title, "content": body}
    return {"error": f"Article {aid} not found."}
