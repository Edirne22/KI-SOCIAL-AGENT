"""Apply an authenticated dashboard review *request* to the durable Factory job.

This is an offline adapter for a proven persistent SQLite volume. It must not
be executed on GitHub's ephemeral runner as if that runner held live jobs.
The private R2 review-state is a transport envelope, never the canonical job.
No post/publisher code is reachable from this adapter.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from content_factory_core import JobStatus
from content_factory_golden_tablet import GoldenTablet, HumanDecisionService
from content_factory_repository import ConcurrentUpdateError, SQLiteJobRepository


class ReviewApplyError(RuntimeError):
    """Untrusted, outdated, or unprovable user review must not mutate jobs."""


@dataclass(frozen=True)
class AppliedReview:
    job_id: str
    request_id: str
    revision: int
    decision: str
    result: str
    store_version: int


def _uuid(value: object) -> str:
    if not isinstance(value, str):
        raise ReviewApplyError("invalid review identifier")
    try:
        canonical = str(UUID(value))
    except (ValueError, AttributeError) as exc:
        raise ReviewApplyError("invalid review identifier") from exc
    if canonical != value:
        raise ReviewApplyError("noncanonical review identifier")
    return value


def _load_json(storage, key: str) -> dict:
    try:
        response = storage.client.get_object(Bucket=storage.bucket, Key=key)
        raw = response["Body"].read(8193)
        if len(raw) > 8192 or not raw:
            raise ReviewApplyError("review envelope too large or missing")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ReviewApplyError("review envelope not an object")
        return data
    except ReviewApplyError:
        raise
    except Exception as exc:
        raise ReviewApplyError("private review envelope unavailable") from exc


def apply_review_request(job_id: str, *, storage, repository: SQLiteJobRepository) -> AppliedReview:
    """Process one previously authenticated R2 review intent using SQLite CAS.

    Crash safety: the immutable request ID and outcome are stored in the SAME
    SQLite transaction as the canonical decision. Re-delivery after a crash
    returns ALREADY_APPLIED, never increments revision or acts a second time.
    R2 state is deliberately left REVIEW_REQUESTED: it is NOT an atomic
    cross-store completion receipt. Reconciliation/ack is a separate operation.
    """
    _uuid(job_id)
    if not isinstance(repository, SQLiteJobRepository):
        raise ReviewApplyError("durable canonical SQLite repository required")
    state = _load_json(storage, f"ai-central/v1/preview-state/{job_id}.json")
    review = state.get("review")
    if (state.get("schema") != "FACTORY-PREVIEW-STATE-V1" or
        state.get("job_id") != job_id or state.get("state") != "REVIEW_REQUESTED" or
        state.get("preview_id") is not None or not isinstance(review, dict)):
        raise ReviewApplyError("no authenticated pending review")
    request_id = _uuid(review.get("request_id"))
    preview_id = _uuid(review.get("preview_id"))
    if (review.get("schema") != "FACTORY-REVIEW-INTENT-V1" or
        review.get("actor") != "authenticated_dashboard_owner" or
        review.get("status") != "PENDING_FACTORY_APPLICATION" or
        review.get("action") not in ("change", "discard") or
        review.get("job_id") != job_id or
        review.get("manifest") != state.get("manifest") or
        review.get("revision") != state.get("revision") or
        not isinstance(review.get("text"), str) or
        len(review["text"]) > 2000 or
        (review["action"] == "change" and not review["text"].strip()) or
        (review["action"] == "discard" and review["text"])):
        raise ReviewApplyError("invalid or unauthorized review envelope")

    # Independent immutable preview binds original media and caption; a
    # review-state JSON on its own cannot grant authority to change a job.
    preview = _load_json(storage, f"ai-central/v1/previews/{preview_id}.json")
    if (preview.get("schema") != "FACTORY-MEDIA-PREVIEW-V1" or
        preview.get("preview_id") != preview_id or
        preview.get("job_id") != job_id or
        preview.get("revision") != review["revision"] or
        preview.get("manifest") != review["manifest"] or
        preview.get("state") != "READY_FOR_HUMAN" or
        preview.get("qm_passed") is not True):
        raise ReviewApplyError("review/preview correlation mismatch")

    stored = repository.get_job(job_id)
    job = stored.job
    slot = f"dashboard_review:{request_id}"
    committed = job.metadata.get(slot)
    expected = {"request_id": request_id, "preview_id": preview_id,
                "job_id": job_id, "revision": review["revision"],
                "manifest": review["manifest"], "action": review["action"],
                "text": review["text"]}
    if committed is not None:
        if committed != expected:
            raise ReviewApplyError("replayed request has conflicting payload")
        result_status = (JobStatus.CHANGES_REQUESTED if review["action"] == "change"
                         else JobStatus.REJECTED)
        if job.status != result_status:
            raise ReviewApplyError("historical review no longer matches current job")
        return AppliedReview(job_id, request_id, review["revision"], review["action"],
                             "ALREADY_APPLIED", stored.store_version)

    if (job.status != JobStatus.READY_FOR_HUMAN or
        job.revision != review["revision"] or
        job.approval_manifest() != review["manifest"] or
        state.get("revision") != job.revision or
        state.get("manifest") != job.approval_manifest()):
        raise ReviewApplyError("canonical Factory job changed since review")

    media = preview.get("media")
    if (not isinstance(media, dict) or
        len(job.media) != 1 or
        job.media[0].media_id != media.get("media_id") or
        job.media[0].sha256 != media.get("sha256") or
        job.media[0].size_bytes != media.get("size_bytes") or
        job.media[0].mime_type != media.get("mime_type") or
        media.get("key") != job.media[0].uri.removeprefix(f"r2://{storage.bucket}/") or
        not job.media[0].uri.startswith(f"r2://{storage.bucket}/")):
        raise ReviewApplyError("preview media differs from canonical approval")

    # This is NOT a fabrication of completed fact checking. The actual
    # preview was registered only after independent media/FInalQM gates.
    # Original report ID is not persisted in V1 preview docs; no POST allowed.
    tablet = GoldenTablet(job_id, job.revision, review["manifest"],
                          preview.get("caption", ""), (job.media[0].media_id,),
                          "review-only-no-publishing", ())
    job.metadata[slot] = expected
    decision = HumanDecisionService()
    try:
        if review["action"] == "change":
            decision.change(job, tablet, review["text"])
        else:
            decision.discard(job, tablet)
        updated = repository.save_job(job, expected_store_version=stored.store_version)
    except ConcurrentUpdateError as exc:
        raise ReviewApplyError("concurrent canonical job update") from exc
    return AppliedReview(job_id, request_id, review["revision"], review["action"],
                         "APPLIED_TO_PERSISTENT_FACTORY_PENDING_R2_ACK",
                         updated.store_version)
