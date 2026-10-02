"""Block 9: cross-process private R2 ledger for strictly human-approved posts.

Cloudflare R2 implements conditional S3 PutObject IfNoneMatch="*", allowing
atomic first-writer reservations across independent processes. A recorded
IN_FLIGHT intent is permanent until external platform reconciliation. A
timeout after any uncertain PUT is NEVER permission to retry publication.
No new paid provider, social request, or public URL exists in this module.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
import json

from content_factory_control_center import ControlCenterError, PublishReceipt
from content_factory_core import JobStatus, ProductionJob
from content_factory_publish_ledger import AmbiguousPublication


PREFIX = "ai-central/v1/publish-ledger/"
MAX_LEDGER_RECORD = 8192


def _error_code(exc: Exception) -> str:
    try:
        return str(exc.response["Error"]["Code"])
    except (AttributeError, KeyError, TypeError):
        return ""


class R2PublishLedger:
    """Shared, no-blind-retry ledger backed by conditional private R2 writes."""

    def __init__(self, storage):
        if not getattr(storage, "bucket", None) or not getattr(storage, "client", None):
            raise ControlCenterError("private R2 storage required")
        self.storage = storage

    def _paths(self, handoff_key: str, platform: str):
        if not isinstance(handoff_key, str) or not handoff_key or platform not in ("instagram", "facebook"):
            raise ControlCenterError("valid canonical handoff and supported platform required")
        digest = hashlib.sha256(json.dumps([handoff_key, platform],
                              separators=(",", ":")).encode()).hexdigest()
        prefix = PREFIX + digest + "/"
        return prefix + "intent.json", prefix + "receipt.json"

    def _get(self, key):
        try:
            response = self.storage.client.get_object(Bucket=self.storage.bucket, Key=key)
            raw = response["Body"].read(MAX_LEDGER_RECORD + 1)
            if not raw or len(raw) > MAX_LEDGER_RECORD:
                raise AmbiguousPublication("R2 ledger record oversized or absent body")
            doc = json.loads(raw)
            if not isinstance(doc, dict):
                raise AmbiguousPublication("R2 ledger record invalid")
            return doc
        except AmbiguousPublication:
            raise
        except Exception as exc:
            if _error_code(exc) in ("NoSuchKey", "404", "NotFound"):
                return None
            raise AmbiguousPublication("R2 ledger retrieval uncertain") from exc

    def _create(self, key: str, payload: dict) -> bool:
        data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        try:
            self.storage.client.put_object(
                Bucket=self.storage.bucket, Key=key, Body=data,
                ContentType="application/json", IfNoneMatch="*")
            return True
        except Exception as exc:
            if _error_code(exc) in ("PreconditionFailed", "412", "ConditionalRequestConflict", "409"):
                return False
            # Even transport errors after a server-side commit are ambiguous.
            raise AmbiguousPublication("conditional R2 write outcome uncertain") from exc

    def receipt(self, handoff_key: str, platform: str):
        intent_key, receipt_key = self._paths(handoff_key, platform)
        doc = self._get(receipt_key)
        if doc is None:
            return None
        if (doc.get("schema") != "FACTORY-PUBLISH-RECEIPT-V1" or
            doc.get("handoff_key") != handoff_key or doc.get("platform") != platform or
            not isinstance(doc.get("external_id"), str) or not doc["external_id"] or
            not isinstance(doc.get("proof"), str) or not doc["proof"] or
            doc["proof"].startswith("SIMULATED")):
            raise AmbiguousPublication("untrusted or mismatched R2 receipt")
        self._assert_claim(intent_key, handoff_key, platform)
        return PublishReceipt(handoff_key, platform, doc["external_id"], doc["proof"])

    def _assert_claim(self, key, handoff_key, platform):
        claim = self._get(key)
        if claim != {"schema": "FACTORY-PUBLISH-CLAIM-V1",
                     "handoff_key": handoff_key, "platform": platform,
                     "state": "IN_FLIGHT"}:
            raise AmbiguousPublication("R2 publication claim missing or changed")

    def reserve(self, job: ProductionJob, platform: str):
        if (job.status != JobStatus.PUBLISH_QUEUED or
            not job.publish_handoff_key or not job.human_approved_at or
            job.human_approved_revision != job.revision or
            job.human_approved_manifest != job.approval_manifest() or
            job.publish_handoff_key !=
                f"{job.job_id}:r{job.revision}:{job.human_approved_manifest[:16]}"):
            raise ControlCenterError("immutable canonical human approval required")
        intent_key, _ = self._paths(job.publish_handoff_key, platform)
        existing = self.receipt(job.publish_handoff_key, platform)
        if existing is not None:
            return existing
        claim = {"schema": "FACTORY-PUBLISH-CLAIM-V1",
                 "handoff_key": job.publish_handoff_key,
                 "platform": platform, "state": "IN_FLIGHT"}
        if not self._create(intent_key, claim):
            # Claim already present, a failed write raced, or status uncertain:
            # NEVER send again without external reconciliation.
            raise AmbiguousPublication("existing R2 publication claim; reconcile before retry")
        return None

    def record_receipt(self, handoff_key: str, platform: str, receipt: PublishReceipt):
        if (receipt.handoff_key != handoff_key or receipt.platform != platform or
            not receipt.external_id or not receipt.proof or
            receipt.proof.startswith("SIMULATED") or receipt.external_id.startswith("sim-")):
            raise ControlCenterError("real, correlated platform receipt required")
        intent_key, receipt_key = self._paths(handoff_key, platform)
        self._assert_claim(intent_key, handoff_key, platform)
        previous = self.receipt(handoff_key, platform)
        if previous is not None:
            if previous != receipt:
                raise AmbiguousPublication("conflicting provider receipts")
            return previous
        doc = {"schema": "FACTORY-PUBLISH-RECEIPT-V1", **asdict(receipt)}
        if not self._create(receipt_key, doc):
            prior = self.receipt(handoff_key, platform)
            if prior != receipt:
                raise AmbiguousPublication("concurrent conflicting R2 receipt")
            return prior
        return receipt
