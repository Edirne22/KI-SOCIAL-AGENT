"""Block 9 guarded bridge from canonical private Factory jobs to Meta's existing FB video uploader.

No scheduled caller is installed. Only a separately, explicitly approved,
non-synthetic editorial job with immutable evidence can reach this adapter.
Instagram Reels requires Meta-reachable time-limited media delivery; it stays
fail-closed until a verified private signed gateway exists.
"""
from __future__ import annotations

import os
from uuid import UUID

from content_factory_control_center import ControlCenterError, PublishReceipt
from content_factory_core import JobStatus
from content_factory_publish_ledger import AmbiguousPublication
from content_factory_r2_job_repository import R2JobRepository
from content_factory_r2_publish_ledger import R2PublishLedger
from media_storage import R2Storage


def _nonempty(value):
    return isinstance(value,str) and bool(value.strip())


def _eligible(job):
    if (job.status != JobStatus.PUBLISH_QUEUED or
        not job.human_approved_at or
        job.human_approved_revision != job.revision or
        job.human_approved_manifest != job.approval_manifest() or
        not job.publish_handoff_key or
        len(job.media) != 1 or job.media[0].mime_type != "video/mp4"):
        raise ControlCenterError("canonical human-approved MP4 queue required")
    if job.instruction == "block6-verified-source" or job.metadata.get("technical_test_only"):
        raise ControlCenterError("technical/synthetic previews can never publish")
    evidence = job.publish_payload.get("editorial_evidence")
    if not isinstance(evidence,dict) or not (
        evidence.get("source_fact_contract") is True and
        evidence.get("human_writing") is True and
        evidence.get("media_rights") is True and
        evidence.get("synthetic") is False and
        _nonempty(evidence.get("final_qm_report_id"))):
        raise ControlCenterError("explicit immutable editorial/facts/rights evidence missing")
    human = job.metadata.get(f"human_post:r{job.revision}")
    if not isinstance(human,dict) or (
        human.get("actor") != "authenticated_dashboard_owner" or
        human.get("revision") != job.revision or
        human.get("manifest") != job.approval_manifest()):
        raise ControlCenterError("missing exact dashboard per-post human decision")
    try:
        if str(UUID(human.get("request_id",""))) != human["request_id"]:
            raise ValueError("noncanonical ID")
    except (ValueError,TypeError,AttributeError) as exc:
        raise ControlCenterError("unverifiable per-post decision ID") from exc


class ExistingFacebookVideoPort:
    """Use existing facebook_publish.post_video_to_facebook, not a second publisher."""
    name="facebook"
    truth="LIVE"

    def __init__(self, storage: R2Storage):
        self.storage=storage

    def preflight(self,job):
        if not os.environ.get("FACEBOOK_PAGE_ID") or not os.environ.get("FACEBOOK_PAGE_TOKEN"):
            raise ControlCenterError("existing Facebook credentials unavailable")
        _eligible(job)
        # Read private bytes before making an irreversible publish reservation.
        self.storage.resolve_local(job.media[0])

    def publish(self,job,platform,handoff_key):
        if platform!="facebook" or job.publish_handoff_key!=handoff_key:
            raise ControlCenterError("wrong platform or publish handoff")
        _eligible(job)
        self.preflight(job)
        from facebook_publish import post_video_to_facebook
        try:
            external_id=post_video_to_facebook(
                os.environ["FACEBOOK_PAGE_ID"],os.environ["FACEBOOK_PAGE_TOKEN"],
                job.publish_payload["caption"],str(self.storage.resolve_local(job.media[0])))
        except Exception as exc:
            raise AmbiguousPublication("Facebook outcome uncertain; verify before retry") from exc
        if not _nonempty(external_id):
            raise AmbiguousPublication("Facebook did not return a provider video ID; reconcile")
        # Provider API receipt != independently proven public visibility.
        return PublishReceipt(handoff_key,"facebook",str(external_id),"META_GRAPH_VIDEO_ID_RECEIVED")


class CanonicalPrivatePublisherBridge:
    """Reads shared canonical job and private bytes before first-writer R2 claim."""

    def __init__(self,repository:R2JobRepository,storage:R2Storage,ledger:R2PublishLedger):
        if not isinstance(repository,R2JobRepository) or not isinstance(storage,R2Storage) or not isinstance(ledger,R2PublishLedger):
            raise ControlCenterError("real shared private R2 system-of-record required")
        self.repository=repository
        self.storage=storage
        self.ledger=ledger

    def publish(self,job_id,*,platform,publisher):
        # An untrusted workflow/job ID is never a substitute for canonical
        # approval; no caller may supply an arbitrary in-memory approved job.
        if not isinstance(job_id,str):
            raise ControlCenterError("invalid canonical job ID")
        job=self.repository.get_job(job_id).job
        _eligible(job)
        if platform not in ("instagram","facebook") or publisher.name!=platform or publisher.truth!="LIVE":
            raise ControlCenterError("verified live platform adapter required")
        # Fail before claiming if the provider cannot run or media is missing.
        publisher.preflight(job)
        self.storage.resolve_local(job.media[0])
        receipt=self.ledger.reserve(job,platform)
        if receipt is not None:
            return receipt
        try:
            submitted=publisher.publish(job,platform,job.publish_handoff_key)
        except Exception as exc:
            raise AmbiguousPublication("platform result uncertain; manual provider reconciliation required") from exc
        if (not isinstance(submitted,PublishReceipt) or
            submitted.handoff_key!=job.publish_handoff_key or submitted.platform!=platform):
            raise AmbiguousPublication("invalid platform receipt; do not retry post")
        return self.ledger.record_receipt(job.publish_handoff_key,platform,submitted)


class InstagramDeliveryNotYetVerified(ControlCenterError):
    """Never substitute the private R2 URI for a Meta-fetchable video URL."""


class ExistingInstagramReelPort:
    name="instagram"
    truth="NOT_CONFIGURED"
    def preflight(self,job):
        raise InstagramDeliveryNotYetVerified(
            "Instagram requires a separately verified expiring private media delivery gateway")
    def publish(self,job,platform,handoff_key):
        raise InstagramDeliveryNotYetVerified("no safe Instagram private-R2 media delivery configured")
