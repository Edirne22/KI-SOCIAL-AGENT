"""Fail-closed memory preflight for agent entrypoints.

Invoke before handing work to an agent. Memory is context, never authorization.
"""
from __future__ import annotations

from integrations.agent_memory import load_context


def prepare_agent_context(storage, *, agent_id: str, job: dict, limit: int = 20) -> dict:
    if not isinstance(job, dict) or not job.get("job_id"):
        raise ValueError("A job_id is required")
    context = load_context(storage, agent_id, limit=limit)
    return {"job": dict(job), "agent_id": agent_id,
            "memory": context, "memory_loaded": True}


def require_agent_memory(prepared: dict) -> dict:
    if not isinstance(prepared, dict) or prepared.get("memory_loaded") is not True:
        raise RuntimeError("Agent memory preflight missing")
    context = prepared.get("memory")
    if not isinstance(context, dict) or not isinstance(context.get("personal"), list) or not isinstance(context.get("shared"), list):
        raise RuntimeError("Invalid agent memory context")
    return prepared
