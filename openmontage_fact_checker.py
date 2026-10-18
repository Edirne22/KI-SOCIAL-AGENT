"""Fact and Recency Checker for OpenMontage V3 (Block 2 / P0-B).

Integrates racing quality guards to ensure recency, driver/team consistency,
and rumor classification with a strict fail-closed policy.
"""
from __future__ import annotations

from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Tuple

import motogp_quality_manager as gq
import racing_final_guard as fg

logger = logging.getLogger(__name__)


def check_recency(published_at_iso: str, max_days: int = 7) -> Tuple[bool, str]:
    """Ensures news article has a valid date within acceptable freshness window and not in the future."""
    if not published_at_iso:
        return False, "Missing publication date (fail-closed)"
    try:
        dt = datetime.fromisoformat(published_at_iso.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)

        # Check for future dates
        if dt > now:
            return False, f"Publication date is in the future: {published_at_iso}"

        age_days = (now - dt).total_seconds() / 86400.0
        if age_days > max_days:
            return False, f"Article is {age_days:.1f} days old (max allowed: {max_days} days)"
        return True, f"Article age ok: {age_days:.1f} days"
    except Exception as e:
        return False, f"Invalid date format: {e}"


def verify_story_facts(story: Dict[str, Any]) -> Dict[str, Any]:
    """Applies strict racing quality filters and recency rules to a research story."""
    title = story.get("title", "")
    summary = story.get("summary", "")
    text = f"{title} {summary}".strip()

    # Evergreen technical explainers do not require a recent news timestamp.
    # Explicit classification is required: missing dates still reject news.
    content_type = story.get("content_type", "news")
    evergreen = content_type in ("technical_explainer", "product_explainer")
    is_fresh, freshness_msg = (
        (True, "Evergreen technical explanation; news recency not applicable")
        if evergreen else check_recency(story.get("published_at", ""), max_days=7)
    )

    errors = []
    warnings = []

    if not is_fresh:
        errors.append(freshness_msg)

    if evergreen and story.get("source_status") != "official":
        errors.append("Evergreen explanation requires an official source")

    # Check promotional or marketing content
    if any(p in text.casefold() for p in fg.PROMO):
        errors.append("Promo/Vlog/Marketing content detected rather than racing news")

    # Check series matching via racing_final_guard logic
    expected_series = fg.expected_series({"title": title, "summary": summary, "series": story.get("series", "")})
    if expected_series and expected_series != "unknown":
        declared_series = story.get("series", "")
        if declared_series and declared_series != expected_series and declared_series != "Motorsport":
            errors.append(f"Series mismatch: story says '{declared_series}' but facts indicate '{expected_series}'")

    # Rider matching check
    matched_riders = gq.rider_matches(text)

    # Source & Rumor status check
    source_status = story.get("source_status", "journalistic")
    if source_status == "rumor":
        warnings.append("Marked as rumor; must be explicitly framed as unconfirmed speculation in video script")

    # Fail-closed decision: story must pass recency and have zero fact errors
    passed = len(errors) == 0

    verified = dict(story)
    verified["fact_check_passed"] = passed
    verified["recency_passed"] = is_fresh
    verified["freshness_message"] = freshness_msg
    verified["expected_series"] = expected_series
    verified["detected_riders"] = matched_riders
    verified["fact_errors"] = errors
    verified["fact_warnings"] = warnings

    return verified


def verify_research_payload(research_data: Dict[str, Any]) -> Dict[str, Any]:
    """Verifies all stories inside a research payload, filtering out failed stories."""
    verified_stories = []
    rejected_stories = []

    for story in research_data.get("stories", []):
        checked = verify_story_facts(story)
        if checked["fact_check_passed"]:
            verified_stories.append(checked)
        else:
            rejected_stories.append(checked)

    res = dict(research_data)
    res["verified_item_count"] = len(verified_stories)
    res["rejected_item_count"] = len(rejected_stories)
    res["stories"] = verified_stories
    res["rejected_stories"] = rejected_stories
    # Keep undated news as private research leads, not as publishable facts.
    # Downstream production sees only verified res["stories"].
    res["needs_date_verification"] = [
        {
            "story_id": story.get("story_id"),
            "title": story.get("title"),
            "original_url": story.get("original_url"),
            "reason": "Publication date missing; cross-check required",
        }
        for story in rejected_stories
        if not story.get("published_at")
        and story.get("content_type", "news") not in ("technical_explainer", "product_explainer")
    ]
    res["needs_date_verification_count"] = len(res["needs_date_verification"])
    return res
