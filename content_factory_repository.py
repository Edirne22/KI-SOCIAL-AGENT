"""Durable SQLite repository for Content Factory jobs and execution attempts.

The database is the system of record for Block 2. Writes use optimistic
concurrency (CAS) so Web/Telegram/workers cannot silently overwrite each other.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
import sqlite3
from pathlib import Path
from typing import Optional

from content_factory_core import JobStatus, MediaRef, ProductionJob, utc_now


class ConcurrentUpdateError(RuntimeError):
    pass


class IdempotencyConflictError(RuntimeError):
    pass


class AttemptState(str, Enum):
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    RECONCILE = "reconcile"


@dataclass(frozen=True)
class StoredJob:
    job: ProductionJob
    store_version: int


@dataclass(frozen=True)
class StepAttempt:
    job_id: str
    revision: int
    step: str
    idempotency_key: str
    state: AttemptState
    attempt_no: int
    started_at: str
    updated_at: str
    result_json: Optional[str] = None
    error: Optional[str] = None


def _job_to_json(job: ProductionJob) -> str:
    return json.dumps(job.to_dict(), sort_keys=True, separators=(",", ":"))


def _job_from_json(raw: str) -> ProductionJob:
    data = json.loads(raw)
    data["status"] = JobStatus(data["status"])
    data["media"] = [MediaRef(**item) for item in data.get("media", [])]
    return ProductionJob(**data)


class SQLiteJobRepository:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    store_version INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency (
                    idempotency_key TEXT PRIMARY KEY,
                    job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    instruction TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS attempts (
                    job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    revision INTEGER NOT NULL,
                    step TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL,
                    state TEXT NOT NULL,
                    attempt_no INTEGER NOT NULL,
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    result_json TEXT,
                    error TEXT,
                    PRIMARY KEY (job_id, revision, step, idempotency_key)
                );
                CREATE INDEX IF NOT EXISTS idx_attempts_state
                    ON attempts(state);
                """
            )

    def create_job(self, instruction: str, *, idempotency_key: str) -> tuple[StoredJob, bool]:
        key = idempotency_key.strip()
        if not key:
            raise ValueError("idempotency_key is required")
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            existing = conn.execute(
                "SELECT i.instruction, j.payload, j.store_version "
                "FROM idempotency i JOIN jobs j ON j.job_id=i.job_id "
                "WHERE i.idempotency_key=?", (key,)
            ).fetchone()
            if existing:
                if existing["instruction"] != instruction:
                    raise IdempotencyConflictError(
                        "idempotency key reused with different instruction"
                    )
                return StoredJob(_job_from_json(existing["payload"]), existing["store_version"]), False
            job = ProductionJob(instruction=instruction)
            conn.execute(
                "INSERT INTO jobs(job_id,payload,store_version,updated_at) VALUES(?,?,?,?)",
                (job.job_id, _job_to_json(job), 1, utc_now()),
            )
            conn.execute(
                "INSERT INTO idempotency(idempotency_key,job_id,instruction) VALUES(?,?,?)",
                (key, job.job_id, instruction),
            )
            return StoredJob(job, 1), True

    def get_job(self, job_id: str) -> StoredJob:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload,store_version FROM jobs WHERE job_id=?", (job_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"unknown job: {job_id}")
        return StoredJob(_job_from_json(row["payload"]), row["store_version"])

    def save_job(self, job: ProductionJob, *, expected_store_version: int) -> StoredJob:
        payload = _job_to_json(job)
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            cursor = conn.execute(
                "UPDATE jobs SET payload=?,store_version=store_version+1,updated_at=? "
                "WHERE job_id=? AND store_version=?",
                (payload, utc_now(), job.job_id, expected_store_version),
            )
            if cursor.rowcount != 1:
                exists = conn.execute(
                    "SELECT 1 FROM jobs WHERE job_id=?", (job.job_id,)
                ).fetchone()
                if exists is None:
                    raise KeyError(f"unknown job: {job.job_id}")
                raise ConcurrentUpdateError("stale job write blocked")
        return StoredJob(job, expected_store_version + 1)

    def begin_attempt(
        self, *, job_id: str, revision: int, step: str, idempotency_key: str
    ) -> tuple[StepAttempt, bool]:
        if not step.strip() or not idempotency_key.strip():
            raise ValueError("step and idempotency_key are required")
        now = utc_now()
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            job = conn.execute(
                "SELECT payload FROM jobs WHERE job_id=?", (job_id,)
            ).fetchone()
            if job is None:
                raise KeyError(f"unknown job: {job_id}")
            canonical = _job_from_json(job["payload"])
            if canonical.revision != revision:
                raise ConcurrentUpdateError("stale revision attempt blocked")
            existing = conn.execute(
                "SELECT * FROM attempts WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (job_id, revision, step, idempotency_key),
            ).fetchone()
            if existing:
                return self._attempt(existing), False
            conn.execute(
                "INSERT INTO attempts(job_id,revision,step,idempotency_key,state,attempt_no,"
                "started_at,updated_at) VALUES(?,?,?,?,?,?,?,?)",
                (job_id, revision, step, idempotency_key, AttemptState.RUNNING.value, 1, now, now),
            )
            row = conn.execute(
                "SELECT * FROM attempts WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (job_id, revision, step, idempotency_key),
            ).fetchone()
            return self._attempt(row), True

    def finish_attempt(
        self, *, job_id: str, revision: int, step: str, idempotency_key: str,
        success: bool, result: Optional[dict] = None, error: Optional[str] = None,
    ) -> StepAttempt:
        now = utc_now()
        state = AttemptState.SUCCEEDED if success else AttemptState.FAILED
        result_json = json.dumps(result, sort_keys=True) if result is not None else None
        with self._connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT state FROM attempts WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (job_id, revision, step, idempotency_key),
            ).fetchone()
            if row is None:
                raise KeyError("unknown execution attempt")
            if row["state"] != AttemptState.RUNNING.value:
                raise ConcurrentUpdateError("completed attempt cannot be overwritten")
            conn.execute(
                "UPDATE attempts SET state=?,updated_at=?,result_json=?,error=? "
                "WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (state.value, now, result_json, error, job_id, revision, step, idempotency_key),
            )
            row = conn.execute(
                "SELECT * FROM attempts WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (job_id, revision, step, idempotency_key),
            ).fetchone()
            return self._attempt(row)

    def mark_interrupted_attempts_for_reconciliation(self) -> int:
        """Crash recovery: never blindly replay an external side effect."""
        now = utc_now()
        with self._connect() as conn:
            cursor = conn.execute(
                "UPDATE attempts SET state=?,updated_at=?,error=COALESCE(error,?) WHERE state=?",
                (
                    AttemptState.RECONCILE.value, now,
                    "process interrupted; external side effect must be reconciled before retry",
                    AttemptState.RUNNING.value,
                ),
            )
            return cursor.rowcount

    def get_attempt(
        self, *, job_id: str, revision: int, step: str, idempotency_key: str
    ) -> StepAttempt:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM attempts WHERE job_id=? AND revision=? AND step=? AND idempotency_key=?",
                (job_id, revision, step, idempotency_key),
            ).fetchone()
        if row is None:
            raise KeyError("unknown execution attempt")
        return self._attempt(row)

    @staticmethod
    def _attempt(row: sqlite3.Row) -> StepAttempt:
        return StepAttempt(
            job_id=row["job_id"], revision=row["revision"], step=row["step"],
            idempotency_key=row["idempotency_key"], state=AttemptState(row["state"]),
            attempt_no=row["attempt_no"], started_at=row["started_at"],
            updated_at=row["updated_at"], result_json=row["result_json"], error=row["error"],
        )
