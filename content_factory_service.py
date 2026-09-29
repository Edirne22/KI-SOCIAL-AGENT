"""Application boundary used by future HTTP/Telegram/Web clients."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from content_factory_core import ProductionJob


@dataclass
class CreateJobResult:
    job: ProductionJob
    created: bool


class InMemoryJobService:
    """MVP contract. Persistent repository replaces this backend later."""

    def __init__(self) -> None:
        self._jobs: Dict[str, ProductionJob] = {}
        self._idempotency: Dict[str, str] = {}

    def create_job(self, instruction: str, *, idempotency_key: str) -> CreateJobResult:
        key = idempotency_key.strip()
        if not key:
            raise ValueError("idempotency_key is required")
        existing_id = self._idempotency.get(key)
        if existing_id:
            return CreateJobResult(self._jobs[existing_id], False)
        job = ProductionJob(instruction=instruction)
        self._jobs[job.job_id] = job
        self._idempotency[key] = job.job_id
        return CreateJobResult(job, True)

    def get_job(self, job_id: str) -> ProductionJob:
        try:
            return self._jobs[job_id]
        except KeyError as exc:
            raise KeyError(f"unknown job: {job_id}") from exc
