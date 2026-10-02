"""Block9 issuer for ephemeral Meta-reachable private R2 video capabilities.

This is a server-only primitive: it never publishes a post, never creates a
public bucket and never prints the capability. The caller must have exclusive,
authenticated editorial dispatch authority outside this module.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import secrets
from urllib.parse import urlencode, urlsplit
from uuid import uuid4

from content_factory_core import JobStatus
from content_factory_control_center import ControlCenterError
from content_factory_meta_video_ports import _eligible
from content_factory_r2_job_repository import R2JobRepository
from media_storage import R2Storage

PREFIX = "ai-central/v1/meta-delivery/grants/"
MAX_BYTES = 32 * 1024 * 1024


def issue_private_meta_delivery(repository: R2JobRepository, storage: R2Storage,
                                job_id: str, *, gateway_origin: str,
                                lifetime_seconds: int = 3600,
                                explicitly_approved: bool = False) -> str:
    """Create a time-limited capability only for an EXACTLY human-approved job.

    No GitHub workflow with a synthetic preview or environment-only auto trigger
    may call this without another verified editorial action. The URL is a
    bearer capability and should be handed to the existing publisher only,
    NEVER written into Actions logs, markdown, HTML, or long-lived metadata.
    """
    if explicitly_approved is not True:
        raise ControlCenterError("separate confirmed per-post media delivery required")
    origin = urlsplit(gateway_origin)
    if (origin.scheme != "https" or not origin.hostname or
        not origin.hostname.endswith(".workers.dev") or origin.username or
        origin.password or origin.port or origin.path not in ("", "/") or
        origin.query or origin.fragment):
        raise ControlCenterError("approved existing HTTPS Worker origin required")
    if not isinstance(lifetime_seconds, int) or not 60 <= lifetime_seconds <= 7200:
        raise ControlCenterError("private Meta delivery TTL must be 1-120 minutes")
    if not isinstance(repository, R2JobRepository) or not isinstance(storage, R2Storage):
        raise ControlCenterError("real private R2 repository and media storage required")

    job = repository.get_job(job_id).job
    _eligible(job)
    if job.status != JobStatus.PUBLISH_QUEUED or not job.publish_handoff_key:
        raise ControlCenterError("exact canonical publish queue required")
    media = job.media[0]
    if (media.mime_type != "video/mp4" or not 1 <= media.size_bytes <= MAX_BYTES or
        not media.uri.startswith(f"r2://{storage.bucket}/")):
        raise ControlCenterError("bounded private MP4 required")
    # Actual original R2 bytes must exist and match immutable MediaRef SHA.
    local: Path = storage.resolve_local(media)
    if local.stat().st_size != media.size_bytes or storage._sha256(local) != media.sha256:
        raise ControlCenterError("verified private video not found")
    key = storage._object_key(media)
    if not key.endswith(".mp4"):
        raise ControlCenterError("private video must have MP4 object key")

    now = datetime.now(timezone.utc)
    grant_id = str(uuid4())
    token = secrets.token_urlsafe(32)
    grant = {
        "schema": "META-PRIVATE-R2-DELIVERY-V1",
        "id": grant_id,
        "job_id": job.job_id,
        "media_id": media.media_id,
        "key": key,
        "sha256": media.sha256,
        "size_bytes": media.size_bytes,
        "mime_type": "video/mp4",
        "approval_manifest": job.human_approved_manifest,
        "handoff_key": job.publish_handoff_key,
        "token_sha256": hashlib.sha256(token.encode()).hexdigest(),
        "issued_at": now.isoformat().replace("+00:00", "Z"),
        "expires_at": (now + timedelta(seconds=lifetime_seconds)).isoformat().replace("+00:00", "Z"),
    }
    try:
        storage.client.put_object(
            Bucket=storage.bucket, Key=PREFIX + grant_id + ".json",
            Body=json.dumps(grant, sort_keys=True, separators=(",", ":")).encode(),
            ContentType="application/json", IfNoneMatch="*"
        )
    except Exception as exc:
        # Network timeout could mean the capability was persisted: do not retry,
        # and crucially never print the bearer token or URL to diagnostics.
        raise ControlCenterError("private delivery issuance uncertain; reconcile before retry") from exc
    return gateway_origin.rstrip("/") + "/api/meta-delivery?" + urlencode({"id":grant_id,"token":token})
