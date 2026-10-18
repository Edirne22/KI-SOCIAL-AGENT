"""Pre-render nervous-system audit: distinguish valid facts from renderable media."""
from __future__ import annotations


def inspect_handoff(research: dict, storyboard: dict, manifest: dict) -> dict:
    issues = []
    stories = research.get("stories", [])
    if not stories or not research.get("verified_item_count"):
        issues.append("RESEARCH_NOT_VERIFIED")
    scenes = storyboard.get("scenes", [])
    assets = manifest.get("manifest", [])
    if not scenes or len(assets) != len(scenes):
        issues.append("MEDIA_HANDOFF_INCOMPLETE")
    if not assets or not all(
        isinstance(asset, dict)
        and asset.get("external_media_accepted") is True
        and asset.get("media_url")
        and asset.get("rights_verified") is True
        for asset in assets
    ):
        issues.append("MEDIA_RESEARCH_INCOMPLETE")
    if not scenes or not all(
        isinstance(scene, dict) and scene.get("speaker_text")
        for scene in scenes
    ):
        issues.append("CREATIVE_SCRIPT_INCOMPLETE")
    return {"status": "BLOCKED" if issues else "HANDOFF_READY",
            "issues": issues, "scene_count": len(scenes),
            "accepted_media_count": sum(
                isinstance(asset, dict) and asset.get("external_media_accepted") is True
                for asset in assets)}


def require_handoff(research: dict, storyboard: dict, manifest: dict) -> dict:
    report = inspect_handoff(research, storyboard, manifest)
    if report["status"] != "HANDOFF_READY":
        raise ValueError("OPENMONTAGE_AGENT_HANDOFF_BLOCKED: " + ",".join(report["issues"]))
    return report
