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
    """Missing verified capability delivery always fails before platform claim."""


class ExistingInstagramReelPort:
    """Existing Graph API endpoints with new short-lived verified private R2 input.

    No schedule or automatic caller. The bridge performs the FIRST-WRITER R2
    publication claim before any Graph request. No irreversible Graph POST is
    blindly retried on errors, timeouts or ambiguous responses.
    """
    name = "instagram"
    truth = "LIVE"

    def __init__(self, repository=None, storage=None, *,
                 gateway_origin=None, issue_delivery=None):
        self.repository = repository
        self.storage = storage
        self.gateway_origin = gateway_origin
        self.issue_delivery = issue_delivery

    def preflight(self, job):
        _eligible(job)
        if (not os.environ.get("INSTAGRAM_USER_ID") or
            not os.environ.get("INSTAGRAM_ACCESS_TOKEN")):
            raise InstagramDeliveryNotYetVerified("existing Instagram credentials missing")
        if (not isinstance(self.repository, R2JobRepository) or
            not isinstance(self.storage, R2Storage) or
            not _nonempty(self.gateway_origin) or not callable(self.issue_delivery)):
            raise InstagramDeliveryNotYetVerified("verified private signed R2 delivery not configured")
        # Avoid creating an unrecoverable claim for missing private bytes.
        self.storage.resolve_local(job.media[0])

    def publish(self, job, platform, handoff_key):
        if platform != "instagram" or job.publish_handoff_key != handoff_key:
            raise ControlCenterError("wrong canonical Instagram handoff")
        self.preflight(job)
        # A high entropy URL only exists AFTER the bridge obtains the unique
        # canonical per-platform R2 IN_FLIGHT first-writer claim.
        url = self.issue_delivery(
            self.repository, self.storage, job.job_id,
            gateway_origin=self.gateway_origin, explicitly_approved=True)
        from urllib.parse import urlsplit, parse_qs
        from instagram_reels import GRAPH_API, wait_for_container
        import requests
        pieces = urlsplit(url)
        if (pieces.scheme != "https" or
            (pieces.scheme + "://" + pieces.netloc).rstrip("/") != self.gateway_origin.rstrip("/") or
            pieces.path != "/api/meta-delivery" or
            set(parse_qs(pieces.query)) != {"id", "token"}):
            raise AmbiguousPublication("untrusted ephemeral media URL; reconcile R2 claim")
        # Meta fetchability is checked using exactly this private capability.
        try:
            ready = requests.head(url, timeout=12, allow_redirects=False)
        except requests.RequestException as exc:
            raise AmbiguousPublication("private Meta delivery readiness uncertain") from exc
        if (ready.status_code != 200 or
            ready.headers.get("Content-Type", "").split(";")[0].strip().lower() != "video/mp4" or
            ready.headers.get("Content-Length") != str(job.media[0].size_bytes)):
            raise AmbiguousPublication("private Meta delivery HEAD failed, reconcile claim")

        user_id = os.environ["INSTAGRAM_USER_ID"]
        token = os.environ["INSTAGRAM_ACCESS_TOKEN"]
        try:
            created = requests.post(f"{GRAPH_API}/{user_id}/media",data={
                "media_type": "REELS", "video_url": url,
                "caption": job.publish_payload["caption"],
                "share_to_feed": "true", "access_token": token,
            }, timeout=65)
        except requests.RequestException as exc:
            raise AmbiguousPublication("Meta create-container outcome uncertain") from exc
        if created.status_code != 200:
            raise AmbiguousPublication("Meta did not accept canonical Reel media container")
        try:
            creation_id = created.json().get("id")
        except ValueError as exc:
            raise AmbiguousPublication("Meta create response invalid") from exc
        if not _nonempty(creation_id):
            raise AmbiguousPublication("Meta omitted creation ID; reconcile")
        # Existing read-only polling may retry GET, but never repeats POST.
        if not wait_for_container(str(creation_id), token):
            raise AmbiguousPublication("Meta processing not verified; reconcile before publishing")
        try:
            posted = requests.post(f"{GRAPH_API}/{user_id}/media_publish",data={
                "creation_id": str(creation_id), "access_token": token
            },timeout=65)
        except requests.RequestException as exc:
            raise AmbiguousPublication("Meta publish outcome uncertain; never retry automatically") from exc
        if posted.status_code != 200:
            raise AmbiguousPublication("Meta publish returned a non-success; provider reconciliation required")
        try:
            external_id = posted.json().get("id")
        except ValueError as exc:
            raise AmbiguousPublication("Meta publish receipt unreadable") from exc
        if not _nonempty(external_id):
            raise AmbiguousPublication("Meta omitted final media ID; reconcile")
        # A provider media ID is not proof that the Instagram post is publicly visible.
        return PublishReceipt(handoff_key, "instagram", str(external_id),
                              "META_GRAPH_REEL_ID_RECEIVED")
