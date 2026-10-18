"""Fail-closed standalone OpenMontage render from previously verified research."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from openmontage_fact_checker import verify_research_payload
from scripts.openmontage_media_contract import validate_scene_media, validate_local_scene_media
from openmontage_media_sourcing import build_media_manifest
from openmontage_production import produce_video
from openmontage_storyboard import build_storyboard


def render_verified_research(research: dict, output_dir: Path, *,
                             duration: int = 35, language: str = "de",
                             scene_config: dict | None = None,
                             media_root: Path | None = None) -> dict:
    verified = verify_research_payload(research)
    if not verified["verified_item_count"]:
        raise ValueError("No verified research stories; render refused")
    storyboard = build_storyboard(verified, target_duration=duration,
                                  aspect_ratio="9:16", language=language)
    # Local configuration supplies media only; verified editorial scenes stay intact.
    if scene_config is not None or media_root is not None:
        if not isinstance(scene_config, dict) or media_root is None:
            raise ValueError("LOCAL_MEDIA_INVALID: scene_config and media_root required together")
        manifest = {"manifest": scene_config.get("scenes"),
                    "all_rights_verified": scene_config.get("all_rights_verified")}
        validate_local_scene_media(storyboard, manifest)
        # B71 performs path/format/size/full decoding checks before creating output.
        return produce_video(verified, storyboard, manifest, output_dir, media_root=media_root)
    manifest = build_media_manifest(storyboard)
    if not manifest["all_rights_verified"]:
        raise ValueError("MEDIA_RESEARCH_INCOMPLETE: verified licensed scene media missing")
    # Validate the scene-to-media contract before any production side effect.
    validate_scene_media(storyboard, manifest)
    # Only explicitly licensed direct media enters the remote intake.
    if any(item.get("external_media_accepted") is not True for item in manifest["manifest"]):
        raise RuntimeError("SOURCE_MEDIA_NOT_LICENSED: approved real media required for every scene")
    from scripts.openmontage_licensed_media_intake import download_licensed_scenes
    with TemporaryDirectory(prefix="openmontage-licensed-") as temp:
        media_root_path = Path(temp) / "media"
        local_config = download_licensed_scenes(manifest["manifest"], media_root_path)
        local_manifest = {"manifest": local_config["scenes"], "all_rights_verified": True}
        validate_local_scene_media(storyboard, local_manifest)
        return produce_video(verified, storyboard, local_manifest, output_dir,
                             media_root=media_root_path)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--research", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--duration", type=int, default=35)
    parser.add_argument("--language", choices=("de", "tr"), default="de")
    parser.add_argument("--scene-config", type=Path,
                        help="Local media JSON: scenes with scene_number/local_path/license/rights")
    parser.add_argument("--media-root", type=Path, help="Operator-controlled local media directory")
    args = parser.parse_args()
    scene_config = None
    if args.scene_config is not None:
        with args.scene_config.open('rb') as source:
            payload = source.read(32769)
        if len(payload) > 32768:
            raise ValueError("LOCAL_MEDIA_INVALID: scene configuration exceeds 32 KiB")
        scene_config = json.loads(payload.decode('utf-8'))
    research = json.loads(args.research.read_text(encoding="utf-8"))
    result = render_verified_research(research, args.output,
                                      duration=args.duration, language=args.language,
                                      scene_config=scene_config, media_root=args.media_root)
    print(json.dumps({"status": result["status"],
                      "video_file": result["video_file"],
                      "duration_seconds": result["duration_seconds"],
                      "synthetic_only": result.get("source_media_included") is not True,
                      "creative_acceptance": result.get("creative_acceptance", "NOT_EVALUATED"),
                      "creative_issues": result.get("creative_issues", [])}))


if __name__ == "__main__":
    main()
