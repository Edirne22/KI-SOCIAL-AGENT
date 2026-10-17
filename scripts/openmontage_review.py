"""Editorial review state only. No social publisher integration."""
from __future__ import annotations
import json
import re
from pathlib import Path

VALID = {"approve", "reject"}
ID = re.compile(r"^[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$")


def record_review(media_id: str, decision: str, *, chat_id: str,
                  authorized_chat_id: str, state_path: Path) -> str:
    if not authorized_chat_id or str(chat_id) != str(authorized_chat_id):
        raise PermissionError("Owner-only review")
    if not isinstance(media_id, str) or not ID.fullmatch(media_id):
        raise ValueError("Invalid media ID")
    if decision not in VALID:
        raise ValueError("Invalid editorial decision")
    state_path = Path(state_path)
    data = json.loads(state_path.read_text()) if state_path.exists() else {}
    if media_id in data:
        if data[media_id] != decision:
            raise ValueError("Decision already recorded; manual review required")
        return "already-recorded"
    data[media_id] = decision
    state_path.parent.mkdir(parents=True, exist_ok=True)
    temp = state_path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, sort_keys=True) + "\n")
    temp.replace(state_path)
    return "recorded"
