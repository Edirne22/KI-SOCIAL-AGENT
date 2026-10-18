"""Explicit, reviewed agent-learning writeback after completed jobs.

Use only after an authorized reviewer confirms the lesson; no model output
automatically becomes durable knowledge or an approval.
"""
from __future__ import annotations

from integrations.agent_memory import append_experience, load_context


def record_reviewed_outcome(storage, *, agent_id: str, job_id: str,
                            outcome: str, lesson: str, reviewed: bool,
                            share: bool = False) -> dict:
    if not isinstance(job_id, str) or not job_id.strip() or len(job_id) > 128:
        raise ValueError("Valid job_id required")
    if outcome not in ("success", "failure", "lesson", "preference"):
        raise ValueError("Invalid outcome")
    if reviewed is not True:
        raise PermissionError("Unreviewed outcome cannot be stored")
    if not isinstance(lesson, str) or not lesson.strip():
        raise ValueError("Lesson required")
    # Job IDs are retained as plain provenance; no secrets or raw model transcripts.
    summary = f"[job:{job_id.strip()}] {lesson.strip()}"
    updated = append_experience(storage, agent_id, kind=outcome,
                                summary=summary, reviewed=True)
    if share:
        # Separate explicit write to shared memory; caller serializes writers.
        append_experience(storage, "shared", kind=outcome,
                          summary=f"[agent:{agent_id}] {summary}", reviewed=True)
    return {"agent_id": agent_id, "job_id": job_id, "entries": len(updated["entries"]),
            "shared": share}


def review_history(storage, *, agent_id: str, limit: int = 20) -> dict:
    return load_context(storage, agent_id, limit=limit)
