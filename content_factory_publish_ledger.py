"""Block 9 durable publish reservation: fail closed on unknown platform outcomes.

This filesystem implementation is suitable ONLY for a shared durable Linux volume.
A new GitHub Actions runner's ephemeral disk is NOT such a volume. Before deploying
across workers use a durable atomically-conditional object/database backend with the
same contract. No platform requests are made by this module without human approval.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path

from content_factory_core import JobStatus, ProductionJob
from content_factory_control_center import ControlCenterError, PublishReceipt


class AmbiguousPublication(ControlCenterError):
    """An earlier worker may have posted; reconcile with platform before retry."""


class FilePublishLedger:
    """One atomic reservation per approved handoff/platform on a durable volume."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _paths(self, handoff_key: str, platform: str):
        if not handoff_key or not platform or not isinstance(handoff_key, str) or not isinstance(platform, str):
            raise ControlCenterError("invalid publication identity")
        digest = hashlib.sha256(json.dumps([handoff_key, platform], separators=(",", ":")).encode()).hexdigest()
        return self.root / (digest + ".intent.json"), self.root / (digest + ".receipt.json")

    @staticmethod
    def _read(path):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise AmbiguousPublication("publication ledger unreadable: manual reconciliation required") from exc

    @staticmethod
    def _sync_dir(root):
        fd = os.open(root, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    def receipt(self, handoff_key: str, platform: str):
        intent, result = self._paths(handoff_key, platform)
        if not result.exists():
            return None
        doc = self._read(result)
        if (doc.get("handoff_key"), doc.get("platform")) != (handoff_key, platform):
            raise AmbiguousPublication("publication receipt correlation invalid")
        if not isinstance(doc.get("external_id"), str) or not doc["external_id"]:
            raise AmbiguousPublication("publication receipt missing external id")
        if not isinstance(doc.get("proof"), str) or not doc["proof"]:
            raise AmbiguousPublication("publication receipt missing proof")
        if not intent.exists():
            raise AmbiguousPublication("receipt exists without reserved publication")
        return PublishReceipt(**{k: doc[k] for k in ("handoff_key", "platform", "external_id", "proof")})

    def reserve(self, job: ProductionJob, platform: str):
        """Return existing receipt or reserve; never re-send an in-flight request."""
        if job.status != JobStatus.PUBLISH_QUEUED or not job.publish_handoff_key:
            raise ControlCenterError("durable publication requires human-approved queue")
        if job.human_approved_manifest != job.approval_manifest() or job.human_approved_revision != job.revision:
            raise ControlCenterError("approved media/revision mismatch")
        handoff_key = job.publish_handoff_key
        intent, result = self._paths(handoff_key, platform)
        completed = self.receipt(handoff_key, platform)
        if completed is not None:
            return completed
        payload = json.dumps({"handoff_key": handoff_key, "platform": platform, "state": "IN_FLIGHT"},
                             sort_keys=True, separators=(",", ":")).encode()
        try:
            fd = os.open(intent, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError as exc:
            raise AmbiguousPublication("existing in-flight claim: inspect provider before retry") from exc
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            self._sync_dir(self.root)
        except BaseException as exc:
            # The intent may already be durable; NEVER delete/retry blindly.
            raise AmbiguousPublication("publication reservation outcome uncertain") from exc
        return None

    def record_receipt(self, handoff_key: str, platform: str, receipt: PublishReceipt):
        """Record verified provider proof or evidence from deliberate reconciliation."""
        intent, result = self._paths(handoff_key, platform)
        if receipt.handoff_key != handoff_key or receipt.platform != platform or not receipt.external_id or not receipt.proof:
            raise ControlCenterError("publication receipt mismatch")
        if not intent.exists():
            raise ControlCenterError("cannot record receipt without reserved approval")
        claim = self._read(intent)
        if claim != {"handoff_key": handoff_key, "platform": platform, "state": "IN_FLIGHT"}:
            raise AmbiguousPublication("publication intent mismatch")
        previous = self.receipt(handoff_key, platform)
        if previous is not None:
            if previous != receipt:
                raise AmbiguousPublication("conflicting publication receipt")
            return previous
        # Atomic replacement avoids partial success records after a crash.
        fd, name = tempfile.mkstemp(prefix=".publish-receipt-", dir=self.root)
        tmp = Path(name)
        try:
            os.fchmod(fd, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as output:
                json.dump(asdict(receipt), output, sort_keys=True)
                output.flush()
                os.fsync(output.fileno())
            # A ledger is single-writer per claimed key; concurrent reconciliation
            # must be serialized by its supervising worker.
            os.replace(tmp, result)
            self._sync_dir(self.root)
        finally:
            tmp.unlink(missing_ok=True)
        return receipt


class DurablePublisherBridge:
    """ExistingPublisherPort adapter; no retry after unknown publication outcome."""

    def __init__(self, ledger: FilePublishLedger):
        self.ledger = ledger

    def publish(self, job: ProductionJob, *, platform: str, publisher):
        previous = self.ledger.reserve(job, platform)
        if previous is not None:
            return previous
        key = job.publish_handoff_key
        try:
            response = publisher.publish(job, platform, key)
        except Exception as exc:
            raise AmbiguousPublication("publisher outcome uncertain: reconcile manually") from exc
        return self.ledger.record_receipt(key, platform, response)
