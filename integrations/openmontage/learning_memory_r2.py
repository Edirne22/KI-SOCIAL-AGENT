"""Private R2 persistence for OpenMontage learning memory.

No public URLs, no auto-approval and no automatic publication.
"""
from __future__ import annotations

import json

from integrations.openmontage.learning_memory import record_feedback, serialize_memory

MEMORY_KEY = "openmontage/memory/creative-feedback-v1.json"
MAX_MEMORY_BYTES = 128 * 1024


def load_memory(storage) -> dict:
    try:
        response = storage.get_object(Key=MEMORY_KEY)
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code in ("NoSuchKey", "404", "NotFound"):
            return {"schema": 1, "records": []}
        raise
    raw = response["Body"].read(MAX_MEMORY_BYTES + 1)
    if len(raw) > MAX_MEMORY_BYTES:
        raise ValueError("Learning memory exceeds limit")
    memory = json.loads(raw.decode("utf-8"))
    if not isinstance(memory, dict) or memory.get("schema") != 1 or not isinstance(memory.get("records"), list):
        raise ValueError("Invalid learning memory")
    return memory


def save_memory(storage, memory: dict) -> None:
    storage.put_object(Key=MEMORY_KEY, Body=serialize_memory(memory), ContentType="application/json")


def persist_feedback(storage, *, video_id: str, decision: str, style: dict | None = None) -> dict:
    """Read-update-write. Callers must serialize concurrent updates externally."""
    updated = record_feedback(load_memory(storage), video_id=video_id, decision=decision, style=style)
    save_memory(storage, updated)
    return updated
