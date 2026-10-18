"""Automatic Scene Planning (Storyboard) for OpenMontage V3 (Block 3 / P1-G).

Generates structured storyboard.json payloads from verified research data.
"""
from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Dict, List, Optional


SUPPORTED_DURATIONS = (30, 60, 90, 180, 300)
SUPPORTED_FORMATS = ("9:16", "16:9")
SUPPORTED_LANGUAGES = ("de", "tr")
FILM_TYPES = (
    "news",
    "race_report",
    "rider_profile",
    "team_feature",
    "weekend_preview",
    "weekly_review",
    "technical_report",
    "turkish_news",
    "technology_news",
    "product_explainer",
)

TRANSITIONS = ("fade", "wipeleft", "circleopen")


def build_storyboard(
    research_data: Dict[str, Any],
    target_duration: int = 60,
    aspect_ratio: str = "9:16",
    language: str = "de",
    film_type: str = "news",
    agent_memory: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Builds a structured storyboard.json payload from verified research. Raises ValueError if research is empty."""
    stories = research_data.get("stories", [])

    # P1-G: Abort cleanly on empty research! Do NOT invent fake motorsport news.
    if not stories:
        raise ValueError("Storyboard creation aborted: Research payload contains no verified stories (empty research).")

    if type(target_duration) is not int or not 15 <= target_duration <= 300:
        raise ValueError("Target duration must be a whole number from 15 to 300 seconds")

    if aspect_ratio not in SUPPORTED_FORMATS:
        aspect_ratio = "9:16"

    if language not in SUPPORTED_LANGUAGES:
        language = "de"

    if film_type not in FILM_TYPES:
        film_type = "news"

    # Apply only reviewed, explicitly supported creative preferences.
    # Memory never changes source verification or publishing authorization.
    preferred_transition = None
    if isinstance(agent_memory, dict):
        for role in ("creative_director", "07_video_optimization"):
            role_context = agent_memory.get(role, {})
            if not isinstance(role_context, dict):
                continue
            for entry in reversed(role_context.get("personal", []) + role_context.get("shared", [])):
                if not isinstance(entry, dict) or entry.get("reviewed") is not True:
                    continue
                if entry.get("kind") != "preference":
                    continue
                summary = entry.get("summary", "")
                if not isinstance(summary, str):
                    continue
                for candidate in TRANSITIONS:
                    if summary.strip().lower() == f"transition:{candidate}":
                        preferred_transition = candidate
                        break
                if preferred_transition:
                    break
            if preferred_transition:
                break

    # Max duration for creative_renderer single-pass rendering is 300s
    render_max_duration = min(300, target_duration)

    raw_scene_count = max(3, min(8, math.ceil(render_max_duration / 6.0)))
    if len(stories) >= raw_scene_count:
        selected_stories = stories[:raw_scene_count]
    else:
        selected_stories = [stories[i % len(stories)] for i in range(raw_scene_count)]

    scene_count = len(selected_stories)
    overlap = 0.6

    target_total_frames = render_max_duration * 30 + 18 * (scene_count - 1)
    base_frames_per_scene = target_total_frames // scene_count
    extra_frames = target_total_frames % scene_count

    scenes = []
    for i, story in enumerate(selected_stories):
        scene_num = i + 1
        is_last = (i == scene_count - 1)

        raw_title = story.get("title", "")
        title = raw_title[:38] + ".." if len(raw_title) > 40 else raw_title
        if not title:
            title = f"Scene {scene_num}"

        riders = story.get("riders", [])
        series = story.get("series", "Motorsport")

        if language == "tr":
            speaker_text = f"Haber {scene_num}: {story.get('summary', title)}"
            overlay = f"{series}: {title}"
            audio_hint = "Enerjik motor sporu müziği"
        else:
            speaker_text = f"Meldung {scene_num}: {story.get('summary', title)}"
            overlay = f"{series}: {title}"
            audio_hint = "Dynamischer Motorsport-Soundtrack"
            if film_type in ("technology_news", "product_explainer"):
                speaker_text = str(story.get("summary") or title)
                overlay = title
                audio_hint = "Dynamischer, thematisch passender Soundtrack"

        zoom = "in" if i % 2 == 0 else "out"
        motion = "right" if i % 2 == 0 else "left"
        transition = (preferred_transition or TRANSITIONS[i % len(TRANSITIONS)]) if not is_last else None

        media_req = (
            "technical_detail_clip" if film_type in ("product_explainer", "technology_news")
            else "driver_info_card" if riders else "racing_action_clip"
        )

        scene_frames = base_frames_per_scene + (1 if i < extra_frames else 0)
        scene_duration = scene_frames / 30.0

        scenes.append({
            "scene_number": scene_num,
            "title": title,
            "duration": scene_duration,
            "source_reference": story.get("story_id") or story.get("original_url", ""),
            "speaker_text": speaker_text,
            "text_overlay": overlay,
            "media_request": media_req,
            # Media metadata is passed through, never inferred from news source.
            "media_url": story.get("media_url"),
            "media_source": story.get("media_source"),
            "media_license": story.get("media_license"),
            "media_candidates": story.get("media_candidates", []),
            # Future avatar pointing anchors; not yet used by renderer.
            "visual_target": story.get("visual_target"),
            "visual_anchor": story.get("visual_anchor"),
            "zoom": zoom,
            "motion": motion,
            "transition": transition,
            "audio_hint": audio_hint,
            "riders": riders,
            "series": series,
        })

    total_frames = sum(round(s["duration"] * 30) for s in scenes) - round(overlap * 30) * (len(scenes) - 1)
    actual_duration = total_frames / 30.0

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "film_type": film_type,
        "target_duration_seconds": target_duration,
        "actual_duration_seconds": actual_duration,
        "aspect_ratio": aspect_ratio,
        "language": language,
        "scene_count": len(scenes),
        "scenes": scenes,
    }
