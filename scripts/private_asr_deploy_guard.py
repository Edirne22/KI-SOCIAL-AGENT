"""Strict deploy health validation; never print untrusted response values."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def check_health(raw: str, http_status: str, research: str, video: str) -> str:
    if http_status != "200":
        return "HTTP_NOT_200"
    try:
        data = json.loads(raw)
    except (ValueError, TypeError):
        return "INVALID_JSON"
    if not isinstance(data, dict):
        return "INVALID_OBJECT"
    if data.get("ready") is not True:
        return "NOT_READY"
    for field, expected, label in (
        ("research_runtime_revision", research, "RESEARCH"),
        ("private_video_runtime_revision", video, "VIDEO"),
    ):
        if field not in data:
            return label + "_REVISION_MISSING"
        if not isinstance(data[field], str):
            return label + "_REVISION_INVALID"
        if data[field] != expected:
            return label + "_REVISION_MISMATCH"
    return "TARGET_REVISION_OK"


def main() -> int:
    path, status, research, video = sys.argv[1:]
    try:
        raw = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        reason = "RESPONSE_UNREADABLE"
    else:
        reason = check_health(raw, status, research, video)
    print("PRIVATE_ASR_HEALTH_CHECK=" + reason)
    return 0 if reason == "TARGET_REVISION_OK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
