"""Persistent application service for Content Factory Block 2."""
from __future__ import annotations

from dataclasses import dataclass

from content_factory_core import ProductionJob
from content_factory_repository import SQLiteJobRepository, StoredJob


@dataclass(frozen=True)
class PersistentCreateJobResult:
    job: ProductionJob
    store_version: int
    created: bool


class PersistentJobService:
    def __init__(self, repository: SQLiteJobRepository):
        self.repository = repository

    def create_job(self, instruction: str, *, idempotency_key: str) -> PersistentCreateJobResult:
        stored, created = self.repository.create_job(
            instruction, idempotency_key=idempotency_key
        )
        return PersistentCreateJobResult(stored.job, stored.store_version, created)

    def get_job(self, job_id: str) -> StoredJob:
        return self.repository.get_job(job_id)

    def save_job(self, job: ProductionJob, *, expected_store_version: int) -> StoredJob:
        return self.repository.save_job(job, expected_store_version=expected_store_version)
