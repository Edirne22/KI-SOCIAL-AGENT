"""Pre-render agent handoff audit. No renderer, network or publication side effects."""
from __future__ import annotations

from openmontage_fact_checker import verify_research_payload
from openmontage_storyboard import build_storyboard
from openmontage_media_sourcing import build_media_manifest


def audit_agent_chain(research: dict, *, duration: int = 60) -> dict:
    """Execute research -> fact checker -> creative director -> media gate.

    A fact-check pass means only internal consistency; independent source
    verification must be supplied by the research agent separately.
    """
    checked = verify_research_payload(research)
    trace = [{"agent": "05_research_synthesist", "status": "received",
              "items": len(research.get("stories", []))},
             {"agent": "fact_checker", "status": "completed",
              "passed": checked["verified_item_count"],
              "rejected": checked["rejected_item_count"]}]
    if not checked["stories"]:
        return {"status": "BLOCKED_NO_VERIFIED_RESEARCH", "trace": trace,
                "rejected": checked["rejected_stories"], "production_started": False}
    board = build_storyboard({"stories": checked["stories"]}, target_duration=duration,
                             film_type="product_explainer")
    trace.append({"agent": "creative_director", "status": "completed",
                  "scenes": len(board["scenes"])})
    manifest = build_media_manifest(board)
    missing = [{"scene_number": item["scene_number"],
                "reason": item["verification_result"]}
               for item in manifest["manifest"] if not item["rights_verified"]]
    trace.append({"agent": "07_video_optimization", "status": "pre_render_checked",
                  "missing_media": len(missing)})
    return {"status": "READY_FOR_MANUAL_REVIEW" if not missing else "BLOCKED_MEDIA_MISSING",
            "trace": trace, "checked_research": checked,
            "storyboard": board, "media_manifest": manifest,
            "missing_media": missing, "production_started": False}
