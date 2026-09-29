"""Machine-to-machine handoff contract for the Edirne 22 factory."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Protocol

from content_factory_core import MediaRef, ProductionJob


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
    if task.job_id != job.job_id or task.revision != job.revision:
        raise HandoffError("invalid task envelope")
    result = machine.run(task)
    validate_result(job, task, result)
    for media in result.outputs:
        if all(existing.media_id != media.media_id for existing in job.media):
            job.media.append(media)
    return result
