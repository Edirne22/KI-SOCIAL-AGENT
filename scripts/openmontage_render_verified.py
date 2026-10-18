"""Fail-closed standalone OpenMontage render from previously verified research."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from openmontage_fact_checker import verify_research_payload
from openmontage_media_sourcing import build_media_manifest
from openmontage_production import produce_video
from openmontage_storyboard import build_storyboard


def render_verified_research(research: dict, output_dir: Path, *,
                             duration: int = 35, language: str = "de") -> dict:
    verified = verify_research_payload(research)
    if not verified["verified_item_count"]:
        raise ValueError("No verified research stories; render refused")
    storyboard = build_storyboard(verified, target_duration=duration,
                                  aspect_ratio="9:16", language=language)
    manifest = build_media_manifest(storyboard)
    if not manifest["all_rights_verified"]:
        raise ValueError("Media rights verification failed")
    from scripts.openmontage_agent_handoff import require_handoff
    require_handoff(verified, storyboard, manifest)
    result = produce_video(verified, storyboard, manifest, output_dir)
    # Technical render success is not editorial acceptance of a real-media film.
    if result.get("source_media_included") is not True:
        result["creative_acceptance"] = "BLOCKED_NO_REAL_MEDIA"
        result["creative_issues"] = ["MEDIA_RESEARCH_INCOMPLETE", "SOURCE_MEDIA_NOT_RENDERED"]
    elif result.get("subtitles_and_audio", {}).get("spoken_voice_present") is not True:
        result["creative_acceptance"] = "BLOCKED_NO_NARRATION"
        result["creative_issues"] = ["SPOKEN_VOICE_MISSING"]
    else:
        result["creative_acceptance"] = "REQUIRES_OWNER_REVIEW"
        result["creative_issues"] = []
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=35)
    parser.add_argument("--language", choices=("de", "tr"), default="de")
    args = parser.parse_args()
    research = json.loads(args.research.read_text(encoding="utf-8"))
    result = render_verified_research(research, args.output,
                                      duration=args.duration, language=args.language)
    print(json.dumps({"status": result["status"],
                      "video_file": result["video_file"],
                      "duration_seconds": result["duration_seconds"],
                      "synthetic_only": result.get("source_media_included") is not True,
                      "creative_acceptance": result["creative_acceptance"],
                      "creative_issues": result["creative_issues"]}))


if __name__ == "__main__":
    main()
