"""Register real, integrity-verified Factory videos for the existing private dashboard.

Call only after actual FinalQM PASSES, with existing private R2Storage
and a persisted ProductionJob. The dashboard's authenticated Worker reads
this server-owned R2 index; no public R2 URLs or new provider are needed.
"""
from __future__ import annotations

import json
from dataclasses import asdict
from uuid import uuid4
from media_storage import R2Storage
from content_factory_core import JobStatus, ProductionJob
from content_factory_golden_tablet import FinalQMReport
from content_factory_golden_media import present_verified_golden_tablet

INDEX_PREFIX = "ai-central/v1/previews/"
MAX_DASHBOARD_VIDEO_BYTES = 32 * 1024 * 1024


def register_verified_video_preview(job: ProductionJob, report: FinalQMReport, *, storage: R2Storage) -> str:
    """Write a backend-only preview index after independently verifying R2 bytes.

    Returns the opaque ID; does NOT send Telegram, approve, publish or
    create an external URL. When editing/revision changes, the caller must
    revoke obsolete preview IDs before showing a newer revision (separate
    orchestration step, not implied by this helper).
    """
    if not isinstance(storage, R2Storage):
        raise ValueError("production preview requires private R2Storage")
    if job.status != JobStatus.QM:
        raise ValueError("job must be in QM before registration")
    videos = [m for m in job.media if m.mime_type == "video/mp4"]
    if len(videos) != 1:
        raise ValueError("exactly one finalized MP4 video required")
    media = videos[0]
    expected_prefix = f"r2://{storage.bucket}/media/{media.media_id}/"
    if not media.uri.startswith(expected_prefix):
        raise ValueError("media is not in the canonical private R2 media prefix")
    if media.size_bytes > MAX_DASHBOARD_VIDEO_BYTES:
        raise ValueError("dashboard MVP supports videos up to 32 MiB")
    # The verified gate re-downloads from private R2, recalculates size/hash
    # and validates report/job revision before transitioning to READY_FOR_HUMAN.
    verified = present_verified_golden_tablet(job, report, storage=storage)
    if media.media_id not in verified.tablet.media_ids:
        raise ValueError("video not part of human approval manifest")
    key = media.uri[len(f"r2://{storage.bucket}/"):]
    preview_id = str(uuid4())
    record = {
        "schema": "FACTORY-MEDIA-PREVIEW-V1",
        "preview_id": preview_id,
        "state": JobStatus.READY_FOR_HUMAN.name,
        "qm_passed": True,
        "job_id": job.job_id,
        "revision": job.revision,
        "manifest": verified.tablet.manifest,
        "caption": verified.tablet.caption,
        "media": {
            "media_id": media.media_id,
            "key": key,
            "mime_type": media.mime_type,
            "size_bytes": media.size_bytes,
            "sha256": media.sha256,
        },
    }
    # Created exclusively via private backend credentials; the public UI has
    # read-only endpoints, and the private R2 bucket remains inaccessible.
    storage.client.put_object(
        Bucket=storage.bucket, Key=INDEX_PREFIX + preview_id + ".json",
        Body=json.dumps(record, ensure_ascii=False, sort_keys=True).encode("utf-8"),
        ContentType="application/json",
    )
    return preview_id
