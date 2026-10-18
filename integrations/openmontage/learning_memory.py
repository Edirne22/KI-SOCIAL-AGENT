"""Bounded learning memory for approved OpenMontage creative choices.

This module stores user feedback, not self-modifying code or automatic publishing.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

MAX_RECORDS = 200
ALLOWED_DECISIONS = frozenset({"approved", "rejected", "revision_requested"})


def record_feedback(memory: dict, *, video_id: str, decision: str, style: dict | None = None) -> dict:
    if not isinstance(video_id, str) or not video_id or len(video_id) > 100:
        raise ValueError("Invalid video ID")
    if decision not in ALLOWED_DECISIONS:
        raise ValueError("Unsupported feedback decision")
    if style is None:
        style = {}
    if not isinstance(style, dict) or any(k not in ("duration_seconds", "transition", "language", "format") for k in style):
        raise ValueError("Unsupported style metadata")
    records = list(memory.get("records", [])) if isinstance(memory, dict) else []
    if not isinstance(records, list):
        raise ValueError("Invalid memory records")
    entry = {"video_id": video_id, "decision": decision, "style": style,
             "recorded_at": datetime.now(timezone.utc).isoformat()}
    records = [r for r in records if isinstance(r, dict) and r.get("video_id") != video_id]
    records.append(entry)
    return {"schema": 1, "records": records[-MAX_RECORDS:]}


def suggested_style(memory: dict) -> dict:
    """Prefer the most common style of approved work; never treat it as a publish approval."""
    records = memory.get("records", []) if isinstance(memory, dict) else []
    approved = [r for r in records if isinstance(r, dict) and r.get("decision") == "approved"]
    if not approved:
        return {}
    suggestions = {}
    for key in ("duration_seconds", "transition", "language", "format"):
        values = [r.get("style", {}).get(key) for r in approved if isinstance(r.get("style"), dict)]
        values = [v for v in values if isinstance(v, (str, int, float)) and not isinstance(v, bool)]
        if values:
            suggestions[key] = max(set(values), key=lambda v: (values.count(v), str(v)))
    return suggestions


def serialize_memory(memory: dict) -> bytes:
    data = json.dumps(memory, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(data) > 128 * 1024:
        raise ValueError("Memory too large")
    return data
