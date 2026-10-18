"""Produce a private, fail-closed planning record from a verified R2 request."""
from __future__ import annotations

import json
import os
from pathlib import Path

from integrations.openmontage.private_request_store import get_request
from integrations.openmontage.r2_client import from_environment


def build_plan(request: dict) -> dict:
    return {
        "request_id": request["request_id"],
        "status": "NEEDS_RESEARCH",
        "topic": request["prompt"],
        "verified_sources": [],
        "storyboard": [],
        "message": "Private topic received. No sources verified; no video authorized.",
    }


def main():
    request_id = os.environ["REQUEST_ID"]
    request = get_request(from_environment(), request_id=request_id)
    import hashlib
    import hmac
    chat = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not chat or not hmac.compare_digest(
        request["owner_chat_sha256"], hashlib.sha256(chat.encode()).hexdigest()
    ):
        raise SystemExit("Unauthorized planning request")
    plan = build_plan(request)
    # Topic is private. Store plan only in the private R2 bucket, not public Actions artifacts.
    import io
    storage = from_environment()
    storage.put_object(
        Key=f"openmontage/plans/{request_id}.json",
        Body=(json.dumps(plan, ensure_ascii=False) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    print("Private planning record saved; verified sources: 0")


if __name__ == "__main__":
    main()
