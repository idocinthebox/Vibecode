from __future__ import annotations


def normalize_agent_source(agent_source: str) -> str:
    raw = (agent_source or "unknown").strip()
    if not raw:
        return "unknown"
    lowered = raw.lower()
    if lowered in {"human", "paste", "unknown"}:
        return lowered
    if lowered.startswith("agent:"):
        return raw
    return f"agent:{raw}"
