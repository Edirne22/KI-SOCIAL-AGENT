"""Explicit authorized factory dispatch for an OpenMontage video job.

No implicit legacy fallback, no publishing and no external deployments.
"""
from __future__ import annotations

import json

from content_factory_core import JobStatus
from content_factory_handoff import HandoffError
from content_factory_media_production import (
    MediaProductionError, MediaProductionPlan, MediaProductionRunner, MediaStage, MediaStep,
)
from integrations.openmontage.factory_bridge import OpenMontageFactoryAdapter


def dispatch_openmontage(job, *, agent_role_id, research, storyboard, media_manifest, storage, producer=None):
    """Authorize the agent and run a job-bound OpenMontage render through the factory runner."""
    if not isinstance(agent_role_id, str) or not agent_role_id.strip():
        raise HandoffError("OpenMontage dispatch requires explicit agent identity")
    if job.status not in (JobStatus.STORYBOARDING, JobStatus.RENDERING):
        raise MediaProductionError("OpenMontage dispatch requires storyboard/render state")
    if not all(isinstance(x, dict) for x in (research, storyboard, media_manifest)):
        raise MediaProductionError("OpenMontage dispatch requires structured inputs")
    payload = json.dumps({
        "job_id": job.job_id, "revision": job.revision,
        "research": research, "storyboard": storyboard, "media_manifest": media_manifest,
    }, ensure_ascii=False)
    plan = MediaProductionPlan(job.job_id, job.revision, "openmontage",
        (MediaStep("openmontage_render", MediaStage.RENDER, "openmontage", (),
            (("openmontage_payload", payload),)),))
    adapter = OpenMontageFactoryAdapter(storage, producer=producer)
    return MediaProductionRunner().execute(job, plan, {"openmontage": adapter},
        agent_role_id=agent_role_id)
