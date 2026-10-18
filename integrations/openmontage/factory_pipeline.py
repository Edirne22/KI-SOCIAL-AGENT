"""OpenMontage factory production orchestration (no publication or fabricated news)."""
from __future__ import annotations

from content_factory_core import JobStatus, ProductionJob
from integrations.openmontage.factory_dispatch import dispatch_openmontage
from openmontage_fact_checker import verify_research_payload
from openmontage_media_sourcing import build_media_manifest
from openmontage_storyboard import build_storyboard


def produce_verified_montage(job: ProductionJob, *, agent_role_id: str, research: dict,
                             storage, producer=None, target_duration=60,
                             aspect_ratio="9:16", language="de"):
    """Take externally sourced research through verified storyboard and authorized render."""
    if job.status != JobStatus.STORYBOARDING:
        raise ValueError("OpenMontage job must be in STORYBOARDING state")
    verified = verify_research_payload(research)
    if verified.get("verified_item_count", 0) < 1:
        raise ValueError("No fresh verified stories; refusing synthetic news")
    storyboard = build_storyboard(verified, target_duration=target_duration,
                                  aspect_ratio=aspect_ratio, language=language)
    manifest = build_media_manifest(storyboard)
    if not manifest.get("all_rights_verified"):
        raise ValueError("Media rights not verified")
    return dispatch_openmontage(job, agent_role_id=agent_role_id, research=verified,
                                storyboard=storyboard, media_manifest=manifest,
                                storage=storage, producer=producer)
