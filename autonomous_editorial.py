"""Autonomous editorial intake for event- and schedule-driven production.

This module finds/accepts editorial opportunities and creates canonical
ProductionJobs. It deliberately has no publisher or approval capability.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
from typing import List, Optional

from content_factory_service import CreateJobResult, InMemoryJobService


class TriggerKind(str, Enum):
    EVENT = "event"
    SCHEDULE = "schedule"


@dataclass(frozen=True)
class EditorialTrigger:
    trigger_id: str
    kind: TriggerKind
    title: str
    series: str
    source_urls: List[str] = field(default_factory=list)
    rider: Optional[str] = None
    event_name: Optional[str] = None
    relevance: int = 0
    requested_formats: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.trigger_id.strip() or not self.title.strip():
            raise ValueError("trigger_id and title are required")
        if not 0 <= self.relevance <= 100:
            raise ValueError("relevance must be 0..100")


@dataclass(frozen=True)
class EditorialDecision:
    action: str
    reason: str
    job_id: Optional[str] = None
    created: bool = False


class AutonomousEditorialDesk:
    """Turns relevant discoveries/scheduled race work into production jobs."""

    def __init__(self, jobs: InMemoryJobService, *, production_threshold: int = 70) -> None:
        if not 0 <= production_threshold <= 100:
            raise ValueError("production_threshold must be 0..100")
        self.jobs = jobs
        self.production_threshold = production_threshold

    def consider(self, trigger: EditorialTrigger) -> EditorialDecision:
        if trigger.relevance < self.production_threshold:
            return EditorialDecision("skip", "below production threshold")

        formats = trigger.requested_formats or ["editorial-best-fit"]
        subject = trigger.rider or trigger.event_name or trigger.title
        instruction = (
            f"Autonomous editorial production: {subject}. "
            f"Series: {trigger.series}. "
            f"Formats: {', '.join(formats)}. "
            "Research and cross-check current facts, then create the best-fit "
            "content draft for Bülent. Never publish without human approval."
        )
        fingerprint = hashlib.sha256(
            f"{trigger.kind.value}|{trigger.trigger_id}".encode("utf-8")
        ).hexdigest()
        result: CreateJobResult = self.jobs.create_job(
            instruction, idempotency_key=f"editorial:{fingerprint}"
        )
        job = result.job
        if result.created:
            job.metadata.update({
                "origin": "autonomous_editorial",
                "trigger_kind": trigger.kind.value,
                "trigger_id": trigger.trigger_id,
                "title": trigger.title,
                "series": trigger.series,
                "rider": trigger.rider,
                "event_name": trigger.event_name,
                "source_urls": list(trigger.source_urls),
                "requested_formats": list(formats),
                "relevance": trigger.relevance,
                "human_approval_required": True,
            })
        return EditorialDecision("produce", "relevant autonomous opportunity", job.job_id, result.created)
