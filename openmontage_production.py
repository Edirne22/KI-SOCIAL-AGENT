"""Automated Video Production Engine for OpenMontage V3 (Block 5 / P1-F).

Connects research, storyboard, and media manifest to creative_renderer.
Validates produced MP4 outputs with ffprobe quality inspections.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from integrations.openmontage import creative_renderer
import openmontage_fact_checker as fc
from scripts.openmontage_media_contract import validate_local_scene_media

logger = logging.getLogger(__name__)


def produce_video(
    research_data: Dict[str, Any],
    storyboard_data: Dict[str, Any],
    media_manifest_data: Dict[str, Any],
    output_dir: Path,
    music_file: Optional[Path] = None,
    *, media_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Render demo or licensed local media; media_root explicitly enables local mode."""
    # Step 1: Verify fact checks on research
    verified_research = fc.verify_research_payload(research_data)
    if verified_research.get("verified_item_count", 0) == 0:
        raise ValueError("Video production aborted: Research payload contains no verified stories (empty research).")

    # Step 2: Validate media manifest
    if not media_manifest_data or not isinstance(media_manifest_data, dict) or "manifest" not in media_manifest_data:
        raise ValueError("Video production failed: Invalid or missing media manifest data")

    # Rights gates apply to both demo and local mode.
    manifest_items = media_manifest_data["manifest"]
    if not isinstance(manifest_items, list) or not manifest_items:
        raise ValueError("Video production failed: Empty media manifest")
    if not media_manifest_data.get("all_rights_verified") or any(
        not isinstance(item, dict) or not item.get("rights_verified")
        for item in manifest_items
    ):
        raise ValueError("Video production failed: Unverified media rights")

    # Step 3: Prepare scenes for creative_renderer
    sb_scenes = storyboard_data.get("scenes", [])
    if not sb_scenes:
        raise ValueError("Video production failed: Storyboard contains no scenes")

    render_scenes = []
    for sc in sb_scenes:
        title = sc.get("title", "Scene")[:38]
        duration = float(sc.get("duration", 4.0))
        duration = round(duration * 30) / 30.0
        duration = max(1.5, min(60.0, duration))

        zoom = sc.get("zoom", "in")
        motion = sc.get("motion", "right")
        transition = sc.get("transition")

        render_scenes.append({
            "title": title,
            "duration": duration,
            "zoom": zoom,
            "motion": motion,
            "transition": transition,
        })

    # Ensure last scene transition is None
    if render_scenes:
        render_scenes[-1]["transition"] = None

    local_mode = media_root is not None or any('local_path' in item for item in manifest_items)
    local_options = {}
    if local_mode:
        local_options = {'media': validate_local_scene_media(storyboard_data, media_manifest_data),
                         'media_root': media_root}

    # Step 4: Trigger creative_renderer
    out_path = Path(output_dir).absolute()
    render_report = creative_renderer.render(
        output=out_path,
        scenes=render_scenes,
        music=music_file,
        **local_options,
    )

    movie_file = out_path / "creative-demo.mp4"
    ffprobe_file = out_path / "ffprobe.json"

    # Step 5: Verify technical output with ffprobe
    probe_data = creative_renderer.verify(movie_file, scenes=render_scenes)

    production_report = {
        "status": "COMPLETED",
        "output_directory": str(out_path),
        "video_file": str(movie_file),
        "ffprobe_file": str(ffprobe_file),
        "render_report": render_report,
        "verified_stories_count": verified_research.get("verified_item_count", 0),
        "scene_count": len(render_scenes),
        "duration_seconds": render_report.get("duration", 0.0),
        "sha256": render_report.get("sha256", ""),
        "bytes": render_report.get("bytes", 0),
        "media_mode": "licensed_local" if local_mode else "synthetic_only",
        "source_media_included": render_report.get("source_media_included", False),
        "subtitles_and_audio": {
            "subtitles_burned_in": False,
            "spoken_voice_present": False,
            "audio_track_present": True,
            "audio_codec": "aac",
        },
        "probe": probe_data,
    }

    (out_path / "production_summary.json").write_text(json.dumps(production_report, indent=2) + "\n", encoding="utf-8")
    return production_report
