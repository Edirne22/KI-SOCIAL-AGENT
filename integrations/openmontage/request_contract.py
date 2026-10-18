"""Safe OpenMontage request handoff: prompt never placed in workflow dispatch or logs."""
from __future__ import annotations

import hashlib
import json
import re


class MontageRequestError(ValueError):
    pass


def build_request(*, request_id: str, prompt: str, owner_chat: str) -> dict:
    if not re.fullmatch(r"(?:tg|manual)-[0-9]{1,20}", request_id):
        raise MontageRequestError("invalid request id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 2000:
        raise MontageRequestError("prompt must contain 1-2000 characters")
    if not isinstance(owner_chat, str) or not owner_chat.strip():
        raise MontageRequestError("owner chat required")
    return {"schema": 1, "request_id": request_id, "prompt": prompt.strip(),
            "owner_chat_sha256": hashlib.sha256(owner_chat.encode()).hexdigest(),
            "state": "PENDING"}


def load_request(data: bytes, *, expected_request_id: str) -> dict:
    if len(data) > 8192:
        raise MontageRequestError("request too large")
    try:
        request = json.loads(data)
    except (ValueError, UnicodeError) as exc:
        raise MontageRequestError("invalid request payload") from exc
    if not isinstance(request, dict) or request.get("schema") != 1 or request.get("request_id") != expected_request_id:
        raise MontageRequestError("request correlation mismatch")
    if request.get("state") != "PENDING":
        raise MontageRequestError("request not pending")
    build_request(request_id=expected_request_id, prompt=request.get("prompt"),
                  owner_chat=request.get("owner_chat_sha256", ""))
    if not re.fullmatch(r"[0-9a-f]{64}", request.get("owner_chat_sha256", "")):
        raise MontageRequestError("invalid owner fingerprint")
    return request


def serialize_request(*, request_id: str, prompt: str, owner_chat: str) -> bytes:
    """Serialize owner-validated request; never put the prompt in Actions inputs."""
    request = build_request(request_id=request_id, prompt=prompt, owner_chat=owner_chat)
    return (json.dumps(request, ensure_ascii=False, sort_keys=True) + "\\n").encode("utf-8")
