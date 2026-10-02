"""Private R2 canonical Factory job store for shared, ephemeral-safe workers.

Object ETag CAS is mandatory. R2 supports S3 conditional PutObject If-Match
and If-None-Match. Unknown write results are NEVER treated as failed writes
that are safe to replay. No browser route can write these privileged objects.
"""
from __future__ import annotations

import json
from uuid import UUID

from content_factory_core import ProductionJob, JobStatus
from content_factory_repository import (
    StoredJob, ConcurrentUpdateError, _job_from_json, _job_to_json,
)

PREFIX = "ai-central/v1/factory-jobs/"
MAX_JOB_BYTES = 512 * 1024


class AmbiguousJobWrite(ConcurrentUpdateError):
    """Re-read the persisted job before attempting another transition."""


class R2JobRepository:
    def __init__(self, storage):
        if not getattr(storage, "bucket", None) or not getattr(storage, "client", None):
            raise ValueError("private R2 storage required")
        self.storage = storage

    @staticmethod
    def _key(job_id: str):
        try:
            if not isinstance(job_id, str) or str(UUID(job_id)) != job_id:
                raise ValueError("noncanonical ID")
        except (ValueError, AttributeError) as exc:
            raise ValueError("canonical UUID job_id required") from exc
        return PREFIX + job_id + ".json"

    @staticmethod
    def _code(exc):
        try:
            return str(exc.response["Error"]["Code"])
        except (AttributeError, KeyError, TypeError):
            return ""

    @staticmethod
    def _pack(job, store_version):
        payload = {"schema": "FACTORY-CANONICAL-R2-JOB-V1",
                   "job_id": job.job_id, "store_version": store_version,
                   "job": json.loads(_job_to_json(job))}
        data = json.dumps(payload,sort_keys=True,separators=(",", ":")).encode("utf-8")
        if len(data) > MAX_JOB_BYTES:
            raise ValueError("canonical job exceeds private storage bound")
        return data

    def _load(self, job_id):
        key = self._key(job_id)
        try:
            result = self.storage.client.get_object(Bucket=self.storage.bucket,Key=key)
            etag = result.get("ETag")
            raw = result["Body"].read(MAX_JOB_BYTES + 1)
        except Exception as exc:
            if self._code(exc) in ("NoSuchKey", "404", "NotFound"):
                raise KeyError("unknown canonical Factory job") from exc
            raise AmbiguousJobWrite("private canonical Factory job retrieval uncertain") from exc
        try:
            if not isinstance(etag, str) or not etag or len(raw) > MAX_JOB_BYTES:
                raise ValueError("invalid private R2 job metadata")
            doc = json.loads(raw)
            if (doc.get("schema") != "FACTORY-CANONICAL-R2-JOB-V1" or
                doc.get("job_id") != job_id or
                not isinstance(doc.get("store_version"), int) or
                doc["store_version"] < 1 or not isinstance(doc.get("job"), dict)):
                raise ValueError("corrupt canonical R2 job")
            job = _job_from_json(json.dumps(doc["job"]))
            if job.job_id != job_id:
                raise ValueError("foreign canonical job")
            return StoredJob(job,doc["store_version"]),etag
        except (TypeError, ValueError) as exc:
            raise AmbiguousJobWrite("invalid canonical R2 job; manual inspection needed") from exc

    def get_job(self, job_id):
        return self._load(job_id)[0]

    def register_job(self, job: ProductionJob):
        """Create the first canonical job before making its preview visible."""
        if job.status != JobStatus.READY_FOR_HUMAN or not job.media:
            raise ValueError("only verified human-ready Factory jobs may be registered")
        key = self._key(job.job_id)
        try:
            self.storage.client.put_object(
                Bucket=self.storage.bucket,Key=key,Body=self._pack(job,1),
                ContentType="application/json",IfNoneMatch="*")
        except Exception as exc:
            if self._code(exc) in ("412", "PreconditionFailed","409","ConditionalRequestConflict"):
                raise ConcurrentUpdateError("canonical Factory job already registered") from exc
            raise AmbiguousJobWrite("canonical job registration outcome uncertain") from exc
        return StoredJob(job,1)

    def save_job(self, job: ProductionJob, *, expected_store_version: int):
        stored, etag = self._load(job.job_id)
        if stored.store_version != expected_store_version:
            raise ConcurrentUpdateError("stale canonical job store version")
        next_version = expected_store_version + 1
        try:
            self.storage.client.put_object(
                Bucket=self.storage.bucket,Key=self._key(job.job_id),
                Body=self._pack(job,next_version),ContentType="application/json",
                IfMatch=etag)
        except Exception as exc:
            if self._code(exc) in ("412", "PreconditionFailed","409","ConditionalRequestConflict"):
                raise ConcurrentUpdateError("concurrent canonical R2 job write") from exc
            raise AmbiguousJobWrite("canonical job write outcome uncertain; re-read before retry") from exc
        return StoredJob(job,next_version)
