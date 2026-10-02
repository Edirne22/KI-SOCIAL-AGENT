"""Immutable private revision intake after a VERIFIED, persisted human CHANGE ACK.

The output is an edit-review ticket, NOT an approved render, a verified
creative modification, a new video preview, or permission to publish.
"""
from __future__ import annotations

import json
from uuid import UUID

from content_factory_core import JobStatus
from content_factory_dashboard_review_ack import _read_state
from content_factory_r2_job_repository import R2JobRepository

PREFIX = "ai-central/v1/factory-edit-requests/"
MAX_BYTES = 16 * 1024


class RevisionIntakeError(RuntimeError):
    """No trusted, exact and still-current human CHANGE request."""


class AmbiguousRevisionIntake(RevisionIntakeError):
    """Unknown conditional-write result; inspect durable R2 before retry."""


def _uuid(value):
    if not isinstance(value, str):
        raise RevisionIntakeError("review/job ID must be canonical UUID")
    try:
        if str(UUID(value)) != value:
            raise ValueError("not canonical")
    except (ValueError, AttributeError) as exc:
        raise RevisionIntakeError("review/job ID must be canonical UUID") from exc
    return value


def _code(exc):
    try:
        return str(exc.response["Error"]["Code"])
    except (AttributeError, KeyError, TypeError):
        return ""


def _existing(storage, key):
    try:
        result = storage.client.get_object(Bucket=storage.bucket, Key=key)
        raw = result["Body"].read(MAX_BYTES + 1)
    except Exception as exc:
        if _code(exc) in ("NoSuchKey", "404", "NotFound"):
            return None
        raise AmbiguousRevisionIntake("edit intake retrieval uncertain") from exc
    if not raw or len(raw) > MAX_BYTES:
        raise AmbiguousRevisionIntake("malformed existing immutable edit intake")
    try:
        data = json.loads(raw)
    except (ValueError, UnicodeDecodeError) as exc:
        raise AmbiguousRevisionIntake("invalid existing edit intake JSON") from exc
    if not isinstance(data, dict):
        raise AmbiguousRevisionIntake("existing edit intake not an object")
    return data


def derive_canonical_edit_request(job_id, *, storage, repository):
    """Atomically create/reconcile one ticket for exact canonical ACK.

    Calling this after ACK, and again on the independent review consumer's
    replay branch, heals the crash window between R2 review ACK and ticket
    creation. Neither a browser text value nor a guessed task ID may enter.
    """
    _uuid(job_id)
    if not isinstance(repository, R2JobRepository):
        raise RevisionIntakeError("shared durable R2 canonical repository required")
    state, _ = _read_state(job_id, storage)
    review = state.get("review") if isinstance(state, dict) else None
    if (state.get("schema") != "FACTORY-PREVIEW-STATE-V1" or
            state.get("job_id") != job_id or
            state.get("state") != "REVIEW_APPLIED" or
            state.get("preview_id") is not None or
            not isinstance(review, dict) or
            review.get("schema") != "FACTORY-REVIEW-INTENT-V1" or
            review.get("actor") != "authenticated_dashboard_owner" or
            review.get("status") != "APPLIED_TO_FACTORY" or
            review.get("action") != "change"):
        raise RevisionIntakeError("exact authenticated human CHANGE ACK required")

    request_id = _uuid(review.get("request_id"))
    preview_id = _uuid(review.get("preview_id"))
    prior = review.get("revision")
    ack_version = review.get("canonical_store_version")
    text = review.get("text")
    if (type(prior) is not int or prior < 1 or
            type(ack_version) is not int or ack_version < 1 or
            not isinstance(text, str) or not text.strip() or
            len(text) > 2000 or text != text.strip() or
            review.get("job_id") != job_id or
            review.get("revision") != state.get("revision") or
            review.get("manifest") != state.get("manifest") or
            not isinstance(review.get("manifest"), str) or
            len(review["manifest"]) != 64):
        raise RevisionIntakeError("invalid immutable acknowledged review values")

    record = repository.get_job(job_id)
    job = record.job
    expected = {
        "request_id": request_id, "preview_id": preview_id,
        "job_id": job_id, "revision": prior,
        "manifest": review["manifest"], "action": "change",
        "text": text,
    }
    if (record.store_version < ack_version or
            job.revision != prior + 1 or
            job.status != JobStatus.CHANGES_REQUESTED or
            job.metadata.get("dashboard_review:" + request_id) != expected or
            job.metadata.get(f"human_change:r{prior}") != text or
            job.publish_handoff_key is not None or
            job.human_approved_revision is not None or
            job.human_approved_manifest is not None or
            len(job.media) != 1):
        raise RevisionIntakeError("canonical changed revision does not match ACK")

    original = job.media[0]
    if not original.uri.startswith("r2://" + storage.bucket + "/"):
        raise RevisionIntakeError("original media must remain private in same R2 bucket")
    ticket = {
        "schema": "FACTORY-EDIT-INTAKE-V1",
        "job_id": job_id,
        "revision": job.revision,
        "source_revision": prior,
        "request_id": request_id,
        "preview_id": preview_id,
        "source_approval_manifest": review["manifest"],
        "human_request": text,
        "source_media": {
            "media_id": original.media_id,
            "uri": original.uri,
            "sha256": original.sha256,
            "size_bytes": original.size_bytes,
            "mime_type": original.mime_type,
            "version": original.version,
            "provenance": original.provenance,
        },
        "state": "AWAITING_CREATIVE_PLAN",
        "render_approved": False,
        "publish_approved": False,
    }
    key = f"{PREFIX}{job_id}/r{job.revision}-{request_id}.json"
    existing = _existing(storage, key)
    if existing is not None:
        if existing != ticket:
            raise AmbiguousRevisionIntake("existing edit ticket conflicts with canonical review")
        return "ALREADY_QUEUED", key
    data = json.dumps(ticket, sort_keys=True, separators=(",", ":")).encode("utf-8")
    if len(data) > MAX_BYTES:
        raise RevisionIntakeError("private edit ticket exceeds safety bound")
    try:
        storage.client.put_object(
            Bucket=storage.bucket, Key=key, Body=data,
            ContentType="application/json", IfNoneMatch="*",
        )
    except Exception as exc:
        # Lost-ACK writes are reconciled by exact immutable contents, never
        # retried blindly and never replaced by an untrusted second payload.
        recovered = _existing(storage, key)
        if recovered == ticket:
            return "RECOVERED_AFTER_UNCERTAIN_WRITE", key
        raise AmbiguousRevisionIntake("conditional edit intake outcome uncertain") from exc
    return "QUEUED_AWAITING_CREATIVE_PLAN", key
