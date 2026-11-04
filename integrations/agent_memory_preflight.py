"""Fail-closed memory preflight for agent entrypoints.

Invoke before handing work to an agent. Memory is context, never authorization.
"""
from __future__ import annotations

from pathlib import Path

from integrations.agent_memory import load_context, memory_key, MAX_BYTES


def prepare_repository_agent_context(*, agent_id: str, job: dict, root=Path('.')) -> dict:
    """Explicit read-only Git-backed context, never an automatic R2 fallback.

    These are existing public repository rules, not a copy of private R2 memory.
    Missing/empty/oversized context blocks execution just like the R2 preflight.
    """
    memory_key(agent_id)  # Apply the same ID/path boundary as the R2 backend.
    if not isinstance(job, dict) or not job.get('job_id'):
        raise ValueError('A job_id is required')
    root = Path(root).resolve()

    def entry(relative):
        path = (root / relative).resolve()
        if not path.is_relative_to(root):
            raise ValueError('Repository memory path escapes root')
        with path.open('rb') as handle:
            data = handle.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES or not data.strip():
            raise ValueError('Invalid repository memory size')
        return {'source': relative, 'summary': data.decode('utf-8')}

    context = {'agent_id': agent_id,
               'personal': [entry(f'agents/{agent_id}.md')],
               'shared': [entry(path) for path in (
                   'memory/USER_PREFERENCES.md', 'memory/LEARNED_RULES.md',
                   'memory/MEMORY_CONTEXT.md')]}
    return {'job': dict(job), 'agent_id': agent_id, 'memory': context,
            'memory_loaded': True, 'memory_backend': 'repository'}


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
