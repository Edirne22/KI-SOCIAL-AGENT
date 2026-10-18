"""Shared persistent R2 memory contract for any KI-SOCIAL-AGENT role.

R2 is storage only. The caller is responsible for loading context before execution,
and for explicitly recording reviewed outcomes after execution.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

MAX_BYTES = 128 * 1024
MAX_ENTRIES = 100
AGENT_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}$")
KINDS = frozenset({"lesson", "failure", "success", "preference"})


def memory_key(agent_id: str) -> str:
    if not isinstance(agent_id, str) or not AGENT_ID.fullmatch(agent_id):
        raise ValueError("Invalid agent ID")
    return f"agents/memory/v1/{agent_id}.json"


def _decode(storage, key: str) -> dict:
    try:
        response = storage.get_object(Key=key)
    except Exception as exc:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code")
        if code in ("NoSuchKey", "NotFound", "404"):
            return {"schema": 1, "entries": []}
        raise
    data = response["Body"].read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Agent memory too large")
    result = json.loads(data.decode("utf-8"))
    if not isinstance(result, dict) or result.get("schema") != 1 or not isinstance(result.get("entries"), list):
        raise ValueError("Invalid agent memory schema")
    return result


def load_context(storage, agent_id: str, *, limit: int = 20) -> dict:
    """Load both personal and shared experience; no agent execution occurs here."""
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Invalid context limit")
    personal = _decode(storage, memory_key(agent_id))
    shared = _decode(storage, memory_key("shared"))
    return {"agent_id": agent_id, "personal": personal["entries"][-limit:],
            "shared": shared["entries"][-limit:]}


def append_experience(storage, agent_id: str, *, kind: str, summary: str, reviewed: bool = False) -> dict:
    """Persist reviewed learning only. Caller must serialize parallel writes."""
    key = memory_key(agent_id)
    if kind not in KINDS or not isinstance(summary, str) or not 1 <= len(summary.strip()) <= 1500:
        raise ValueError("Invalid experience")
    if reviewed is not True:
        raise ValueError("Unreviewed experience cannot enter durable memory")
    memory = _decode(storage, key)
    entries = memory["entries"]
    if not all(isinstance(entry, dict) for entry in entries):
        raise ValueError("Invalid entries")
    entries.append({"kind": kind, "summary": summary.strip(),
                    "reviewed": True, "at": datetime.now(timezone.utc).isoformat()})
    updated = {"schema": 1, "entries": entries[-MAX_ENTRIES:]}
    payload = json.dumps(updated, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if len(payload) > MAX_BYTES:
        raise ValueError("Agent memory too large")
    storage.put_object(Key=key, Body=payload, ContentType="application/json")
    return updated
