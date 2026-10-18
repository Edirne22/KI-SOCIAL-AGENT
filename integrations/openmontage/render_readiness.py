"""Check private OpenMontage plans before any rendering or publication."""
from __future__ import annotations


def assess_render_readiness(plan: dict) -> dict:
    if not isinstance(plan, dict) or not plan.get("request_id"):
        raise ValueError("Missing private request")
    scenes = plan.get("storyboard")
    sources = plan.get("verified_sources")
    if plan.get("status") != "STORYBOARD_DRAFT" or not isinstance(scenes, list) or not scenes:
        return {"ready": False, "reason": "STORYBOARD_NOT_READY"}
    if not isinstance(sources, list) or not sources:
        return {"ready": False, "reason": "RESEARCH_NOT_VERIFIED"}
    urls = {source.get("url") for source in sources if isinstance(source, dict) and source.get("source_status") == "official"}
    if not urls:
        return {"ready": False, "reason": "RESEARCH_NOT_VERIFIED"}
    if any(not isinstance(scene, dict) or not scene.get("source_reference") for scene in scenes):
        return {"ready": False, "reason": "SCENE_SOURCE_MISSING"}
    # Rendering is a separate, explicit action; never treat a storyboard as a rendered video.
    return {"ready": True, "reason": "READY_FOR_RENDER_PREPARATION", "scene_count": len(scenes)}
