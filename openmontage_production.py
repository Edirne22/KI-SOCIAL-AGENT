"""Automated Video Production Engine for OpenMontage V3 (Block 5).

Connects research, storyboard, and media manifest to creative_renderer.
Validates produced MP4 outputs with ffprobe quality inspections.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional

from integrations.openmontage import creative_renderer
import openmontage_fact_checker as fc


def produce_video(
    research_data: Dict[str, Any],
    storyboard_data: Dict[str, Any],
    media_manifest_data: Dict[str, Any],
    output_dir: Path,
    music_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Produces synthetic MP4 video and validates output specs."""
    # Step 1: Verify fact checks on research
    verified_research = fc.verify_research_payload(research_data)
    if verified_research.get("verified_item_count", 0) == 0 and research_data.get("stories"):
        raise ValueError("Video production aborted: All research items failed fact checking (fail-closed)")

    # Step 2: Prepare scenes for creative_renderer
    sb_scenes = storyboard_data.get("scenes", [])
    if not sb_scenes:
        raise ValueError("Video production failed: Storyboard contains no scenes")

    render_scenes = []
    for sc in sb_scenes:
        title = sc.get("title", "Scene")[:38]
        duration = float(sc.get("duration", 4.0))
        # Ensure duration is valid for frame grid (30fps)
        duration = round(duration * 30) / 30.0
        duration = max(1.5, min(15.0, duration))

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

    # Step 3: Trigger creative_renderer
    out_path = Path(output_dir).absolute()
    render_report = creative_renderer.render(
        output=out_path,
        scenes=render_scenes,
        music=music_file,
    )

    movie_file = out_path / "creative-demo.mp4"
    ffprobe_file = out_path / "ffprobe.json"

    # Step 4: Verify technical output with ffprobe
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
        "probe": probe_data,
    }

    (out_path / "production_summary.json").write_text(json.dumps(production_report, indent=2) + "\n", encoding="utf-8")
    return production_report
