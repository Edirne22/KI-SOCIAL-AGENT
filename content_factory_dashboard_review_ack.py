"""Acknowledge a canonical Factory review without losing cross-store crash safety.

The canonical job is committed FIRST by the review applier. Only then may
the previously atomically claimed private R2 review-state be conditionally
acknowledged with its original ETag. A failed/unknown ACK is safe to retry:
the canonical job's immutable review ID prevents applying it twice.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
from uuid import UUID

from content_factory_core import JobStatus
from content_factory_dashboard_review_applier import ReviewApplyError


class AmbiguousReviewAck(ReviewApplyError):
    pass


def _code(exc):
    try:
        return str(exc.response["Error"]["Code"])
    except (AttributeError, KeyError, TypeError):
        return ""


def _read_state(job_id,storage):
    try:
        if not isinstance(job_id,str) or str(UUID(job_id)) != job_id:
            raise ValueError("invalid job ID")
        response=storage.client.get_object(
            Bucket=storage.bucket,Key="ai-central/v1/preview-state/"+job_id+".json")
        if not isinstance(response.get("ETag"),str) or not response["ETag"]:
            raise ValueError("missing conditional-write ETag")
        raw=response["Body"].read(8193)
        if len(raw)>8192:
            raise ValueError("oversized review state")
        state=json.loads(raw)
        if not isinstance(state,dict):
            raise ValueError("invalid review state")
        return state,response["ETag"]
    except Exception as exc:
        raise AmbiguousReviewAck("private review ACK state unavailable") from exc


def acknowledge_persisted_review(job_id,*,storage,repository):
    state,etag=_read_state(job_id,storage)
    review=state.get("review")
    if (state.get("schema")!="FACTORY-PREVIEW-STATE-V1" or
        state.get("job_id")!=job_id or
        state.get("state") not in ("REVIEW_REQUESTED","REVIEW_APPLIED") or
        state.get("preview_id") is not None or
        not isinstance(review,dict)):
        raise ReviewApplyError("no valid previously requested review to acknowledge")
    request_id=review.get("request_id")
    try:
        if not isinstance(request_id,str) or str(UUID(request_id))!=request_id:
            raise ValueError("review ID")
    except (ValueError,AttributeError) as exc:
        raise ReviewApplyError("invalid immutable review request ID") from exc

    job_record=repository.get_job(job_id)
    job=job_record.job
    expected={"request_id":request_id,"preview_id":review.get("preview_id"),
        "job_id":job_id,"revision":review.get("revision"),
        "manifest":review.get("manifest"),"action":review.get("action"),
        "text":review.get("text")}
    slot="dashboard_review:"+request_id
    status=(JobStatus.CHANGES_REQUESTED if review.get("action")=="change"
            else JobStatus.REJECTED if review.get("action")=="discard" else None)
    if (status is None or job.status!=status or
        job.metadata.get(slot)!=expected or
        (status==JobStatus.CHANGES_REQUESTED and job.revision!=review["revision"]+1) or
        (status==JobStatus.REJECTED and job.revision!=review["revision"])):
        raise ReviewApplyError("canonical job has not committed this exact review")

    if state["state"]=="REVIEW_APPLIED":
        if review.get("status")!="APPLIED_TO_FACTORY":
            raise ReviewApplyError("ambiguous previously acknowledged review")
        return "ALREADY_ACKNOWLEDGED"
    if review.get("status")!="PENDING_FACTORY_APPLICATION":
        raise ReviewApplyError("review request no longer pending")

    acknowledged={**state,"state":"REVIEW_APPLIED",
        "review":{**review,"status":"APPLIED_TO_FACTORY",
                  "applied_at":datetime.now(timezone.utc).isoformat(),
                  "canonical_store_version":job_record.store_version}}
    key="ai-central/v1/preview-state/"+job_id+".json"
    try:
        storage.client.put_object(
            Bucket=storage.bucket,Key=key,
            Body=json.dumps(acknowledged,sort_keys=True).encode("utf-8"),
            ContentType="application/json",IfMatch=etag)
    except Exception as exc:
        # Never blindly overwrite a newer preview/revision. On unknown
        # result, the next invocation re-reads R2 and canonical job.
        if _code(exc) in ("412","PreconditionFailed","409","ConditionalRequestConflict"):
            raise AmbiguousReviewAck("preview state changed during review ACK") from exc
        raise AmbiguousReviewAck("review ACK outcome uncertain; re-read before retry") from exc
    return "ACKNOWLEDGED"
