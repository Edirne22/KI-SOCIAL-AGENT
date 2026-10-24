"""Produce a private, fail-closed planning record from a verified R2 request."""
from __future__ import annotations

import json
import os
from pathlib import Path

from integrations.openmontage.private_request_store import get_request
from integrations.openmontage.r2_client import from_environment
from integrations.agent_memory_preflight import prepare_agent_context, require_agent_memory


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
    storage = from_environment()
    # Read each role's R2 memory before research and storyboard planning.
    from integrations.openmontage.research_memory_playbook import ensure_research_playbook
    ensure_research_playbook(storage)
    memory_context = {}
    for role in ("05_research_synthesist", "creative_director", "07_video_optimization"):
        prepared = prepare_agent_context(storage, agent_id=role, job={"job_id": request_id})
        memory_context[role] = require_agent_memory(prepared)["memory"]
    plan = build_plan(request)
    plan["agent_memory_context"] = memory_context
    plan["output_profile"] = {"name": "Instagram Reels", "width": 1080,
                              "height": 1920, "aspect_ratio": "9:16",
                              "preferred_duration_seconds": 30, "duration_policy": "editorial_flexible", "language": "de"}
    # Owner authorizes private production without intermediate approval.
    # This is a planning policy, not evidence of completed production.
    plan["approval_gates"] = {
        "proposal": "AUTO_AUTHORIZED", "script": "AUTO_AUTHORIZED",
        "storyboard": "AUTO_AUTHORIZED", "assets": "AUTO_AUTHORIZED",
        "render": "AUTO_AUTHORIZED", "quality_check": "AUTO_AUTHORIZED",
        "private_preview": "AUTO_AUTHORIZED",
        "publication": "AWAITING_APPROVAL",
    }
    from openmontage_research import build_research
    # Agent 05 must attempt topic-specific live discovery, not only static scouts.
    # Discovery is recorded privately but never promoted to verified facts.
    from scripts.openmontage_agent05_oncu_live import run as agent05_live
    live_report = agent05_live(queries=(request["prompt"],))
    plan["agent05_live_status"] = live_report["status"]
    plan["agent05_live_attempts"] = live_report["attempts"]
    plan["agent05_live_finding_count"] = len(live_report["findings"])
    plan["agent05_media_candidate_count"] = len(live_report["media_candidates"])
    storage.put_object(
        Key=f"openmontage/research-discovery/{request_id}.json",
        Body=(json.dumps(live_report, ensure_ascii=False) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    if "quickshifter" in request["prompt"].casefold() or "schaltassistent" in request["prompt"].casefold():
        from scripts.openmontage_quickshifter_research import quickshifter_research
        research = quickshifter_research()
    else:
        research = build_research(request["prompt"])
    from openmontage_fact_checker import verify_research_payload
    checked_research = verify_research_payload(research)
    plan["fact_checked_item_count"] = checked_research["verified_item_count"]
    plan["needs_date_verification_count"] = checked_research["needs_date_verification_count"]
    if checked_research["verified_item_count"]:
        storage.put_object(
            Key=f"openmontage/research/{request_id}.json",
            Body=(json.dumps(checked_research, ensure_ascii=False) + "\n").encode("utf-8"),
            ContentType="application/json",
        )
    if checked_research["verified_item_count"]:
        from scripts.openmontage_social_copy import build_social_copy
        plan["social_copy_draft"] = build_social_copy(checked_research)
    plan["verified_sources"] = [
        {"title": story["title"], "url": story["original_url"], "source_status": story["source_status"]}
        for story in checked_research["stories"] if story["source_status"] == "official"
    ]
    plan["status"] = "RESEARCH_READY" if plan["verified_sources"] else "NEEDS_RESEARCH"
    plan["research_item_count"] = research["item_count"]
    if plan["verified_sources"] and plan["approval_gates"]["proposal"] == "AUTO_AUTHORIZED":
        from openmontage_storyboard import build_storyboard
        verified_urls = {source["url"] for source in plan["verified_sources"]}
        verified_stories = [
            story for story in checked_research["stories"]
            if story["source_status"] == "official" and story["original_url"] in verified_urls
        ]
        if verified_stories:
            # Editorial runtime follows verified information density, not a fixed 30s slot.
            information_units = sum(
                1 + (len(str(story.get("summary") or "").split()) // 45)
                for story in verified_stories[:8]
            )
            editorial_duration = min(90, max(15, information_units * 8))
            plan["output_profile"]["selected_duration_seconds"] = editorial_duration
            storyboard = build_storyboard(
                {"stories": verified_stories},
                target_duration=editorial_duration,
                aspect_ratio=plan["output_profile"]["aspect_ratio"],
                agent_memory=memory_context,
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
    storage.put_object(
        Key=f"openmontage/plans/{request_id}.json",
        Body=(json.dumps(plan, ensure_ascii=False) + "\n").encode("utf-8"),
        ContentType="application/json",
    )
    print("Private planning saved; publication still requires owner approval")


if __name__ == "__main__":
    main()
