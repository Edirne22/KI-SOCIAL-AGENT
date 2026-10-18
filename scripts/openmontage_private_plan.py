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
    from openmontage_research import build_research
    research = build_research(request["prompt"])
    plan["verified_sources"] = [
        {"title": story["title"], "url": story["original_url"], "source_status": story["source_status"]}
        for story in research["stories"] if story["source_status"] == "official"
    ]
    plan["status"] = "RESEARCH_READY" if plan["verified_sources"] else "NEEDS_RESEARCH"
    plan["research_item_count"] = research["item_count"]
    if plan["verified_sources"]:
        from openmontage_storyboard import build_storyboard
        verified_urls = {source["url"] for source in plan["verified_sources"]}
        verified_stories = [
            story for story in research["stories"]
            if story["source_status"] == "official" and story["original_url"] in verified_urls
        ]
        if verified_stories:
            storyboard = build_storyboard(
                {"stories": verified_stories}, target_duration=60, aspect_ratio="9:16",
                language="tr" if any(word in request["prompt"].casefold() for word in ("türk", "turkish", "türkçe")) else "de",
            )
            plan["storyboard"] = storyboard["scenes"]
            plan["storyboard_metadata"] = {
                "duration_seconds": storyboard["actual_duration_seconds"],
                "aspect_ratio": storyboard["aspect_ratio"],
                "language": storyboard["language"],
            }
            plan["status"] = "STORYBOARD_DRAFT"
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
