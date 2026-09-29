"""Machine-to-machine handoff contract for the Edirne 22 factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Protocol

from content_factory_core import JobStatus, MediaRef, ProductionJob


@dataclass(frozen=True)
class ToolTask:
    job_id: str
    revision: int
    task_id: str
    inputs: List[MediaRef] = field(default_factory=list)
    parameters: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ToolResult:
    job_id: str
    revision: int
    task_id: str
    outputs: List[MediaRef]
    machine: str


class FactoryMachine(Protocol):
    name: str

    def run(self, task: ToolTask) -> ToolResult:
        ...


class HandoffError(RuntimeError):
    pass


def validate_result(job: ProductionJob, task: ToolTask, result: ToolResult) -> None:
    if task.job_id != job.job_id or result.job_id != job.job_id:
        raise HandoffError("cross-job media handoff blocked")
    if task.revision != job.revision or result.revision != job.revision:
        raise HandoffError("stale or foreign revision blocked")
    if result.task_id != task.task_id:
        raise HandoffError("task correlation mismatch")
    seen = set()
    for media in result.outputs:
        if media.media_id in seen:
            raise HandoffError("duplicate media output")
        seen.add(media.media_id)


def run_machine(job: ProductionJob, machine: FactoryMachine, task: ToolTask) -> ToolResult:
    if job.status in {
        JobStatus.READY_FOR_HUMAN, JobStatus.APPROVED, JobStatus.PUBLISH_QUEUED,
        JobStatus.PUBLISHED, JobStatus.REJECTED, JobStatus.FAILED,
    }:
        raise HandoffError(f"machine execution blocked in {job.status.value} state")
    if task.job_id != job.job_id or task.revision != job.revision:
        raise HandoffError("invalid task envelope")
    canonical = {media.media_id: media for media in job.media}
    for supplied in task.inputs:
        known = canonical.get(supplied.media_id)
        if known is None or known != supplied:
            raise HandoffError("task input is not canonical job media")
    result = machine.run(task)
    validate_result(job, task, result)
    if result.machine != machine.name:
        raise HandoffError("machine provenance mismatch")
    for media in result.outputs:
        known = canonical.get(media.media_id)
        if known is not None and known != media:
            raise HandoffError("immutable media id collision")
        if known is None:
            job.media.append(media)
            canonical[media.media_id] = media
    return result
