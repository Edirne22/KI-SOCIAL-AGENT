"""Canonical content-factory job model and state machine.

Stdlib-only on purpose: this module is the stable boundary that API, storage,
SupoClip and future UI adapters may depend on.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import hashlib
import json
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JobStatus(str, Enum):
    CREATED = "created"
    INGESTING = "ingesting"
    TRANSCRIBING = "transcribing"
    RESEARCHING = "researching"
    WRITING = "writing"
    STORYBOARDING = "storyboarding"
    RENDERING = "rendering"
    QM = "qm"
    READY_FOR_HUMAN = "ready_for_human"
    CHANGES_REQUESTED = "changes_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISH_QUEUED = "publish_queued"
    PUBLISHED = "published"
    FAILED = "failed"


ALLOWED_TRANSITIONS = {
    JobStatus.CREATED: {JobStatus.INGESTING, JobStatus.REJECTED, JobStatus.FAILED},
    JobStatus.INGESTING: {JobStatus.TRANSCRIBING, JobStatus.RESEARCHING, JobStatus.FAILED},
    JobStatus.TRANSCRIBING: {JobStatus.RESEARCHING, JobStatus.FAILED},
    JobStatus.RESEARCHING: {JobStatus.WRITING, JobStatus.FAILED},
    JobStatus.WRITING: {JobStatus.STORYBOARDING, JobStatus.FAILED},
    JobStatus.STORYBOARDING: {JobStatus.RENDERING, JobStatus.FAILED},
    JobStatus.RENDERING: {JobStatus.QM, JobStatus.FAILED},
    JobStatus.QM: {JobStatus.READY_FOR_HUMAN, JobStatus.RENDERING, JobStatus.FAILED},
    JobStatus.READY_FOR_HUMAN: {JobStatus.CHANGES_REQUESTED, JobStatus.APPROVED, JobStatus.REJECTED},
    JobStatus.CHANGES_REQUESTED: {JobStatus.RENDERING, JobStatus.RESEARCHING, JobStatus.REJECTED},
    JobStatus.APPROVED: {JobStatus.PUBLISH_QUEUED},
    JobStatus.PUBLISH_QUEUED: {JobStatus.PUBLISHED, JobStatus.FAILED},
    JobStatus.REJECTED: set(),
    JobStatus.PUBLISHED: set(),
    JobStatus.FAILED: set(),
}


@dataclass(frozen=True)
class MediaRef:
    media_id: str
    uri: str
    sha256: str
    size_bytes: int
    mime_type: str
    provenance: str
    version: int = 1
    created_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.media_id or not self.uri or not self.sha256:
            raise ValueError("media_id, uri and sha256 are required")
        if self.size_bytes < 0 or self.version < 1:
            raise ValueError("invalid media size/version")
        if len(self.sha256) != 64:
            raise ValueError("sha256 must be a 64-character hex digest")
        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise ValueError("sha256 must be hexadecimal") from exc


@dataclass
class ProductionJob:
    instruction: str
    job_id: str = field(default_factory=lambda: str(uuid4()))
    status: JobStatus = JobStatus.CREATED
    revision: int = 1
    media: List[MediaRef] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    human_approved_at: Optional[str] = None
    human_approved_revision: Optional[int] = None
    human_approved_manifest: Optional[str] = None
    publish_handoff_key: Optional[str] = None
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if not self.instruction.strip():
            raise ValueError("instruction must not be empty")

    def approval_manifest(self) -> str:
        """Fingerprint the exact revision and immutable media set shown to the human."""
        publish_metadata = {
            key: self.metadata.get(key)
            for key in ("caption", "platforms", "title", "requested_formats")
            if key in self.metadata
        }
        payload = {
            "job_id": self.job_id,
            "revision": self.revision,
            "publish_metadata": publish_metadata,
            "media": [
                {
                    "media_id": m.media_id, "uri": m.uri, "sha256": m.sha256,
                    "size_bytes": m.size_bytes, "mime_type": m.mime_type,
                    "provenance": m.provenance, "version": m.version,
                }
                for m in sorted(self.media, key=lambda item: item.media_id)
            ],
        }
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def transition(self, target: JobStatus, *, actor: str = "system") -> None:
        target = JobStatus(target)
        if target not in ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(f"illegal status transition: {self.status.value} -> {target.value}")
        if target in {JobStatus.APPROVED, JobStatus.REJECTED, JobStatus.CHANGES_REQUESTED} and actor != "human":
            raise PermissionError(f"{target.value} requires human authority")
        if self.status == JobStatus.APPROVED and target != JobStatus.PUBLISH_QUEUED:
            raise PermissionError("approved revision can only enter publish queue")
        self.status = target
        self.updated_at = utc_now()
        if target == JobStatus.APPROVED:
            self.human_approved_at = self.updated_at
            self.human_approved_revision = self.revision
            self.human_approved_manifest = self.approval_manifest()
        if target == JobStatus.CHANGES_REQUESTED:
            self.revision += 1
            self.human_approved_at = None
            self.human_approved_revision = None
            self.human_approved_manifest = None
            self.publish_handoff_key = None

    def publish_handoff(self) -> str:
        if self.status == JobStatus.PUBLISH_QUEUED and self.publish_handoff_key:
            return self.publish_handoff_key
        if self.status != JobStatus.APPROVED:
            raise PermissionError("publish handoff requires explicit human approval")
        if self.human_approved_revision != self.revision:
            raise PermissionError("approved revision does not match current revision")
        if self.human_approved_manifest != self.approval_manifest():
            raise PermissionError("approved media manifest changed after human approval")
        if self.publish_handoff_key is None:
            self.publish_handoff_key = f"{self.job_id}:r{self.revision}:{self.human_approved_manifest[:16]}"
        self.transition(JobStatus.PUBLISH_QUEUED)
        return self.publish_handoff_key

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["status"] = self.status.value
        return data
