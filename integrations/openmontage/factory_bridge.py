"""OpenMontage -> Content Factory media bridge. Explicit, authorized machine port.

This adapter only consumes validated, job-bound JSON payloads and stores actual MP4
bytes. It does not publish, deploy, or claim a live renderer without a real producer.
"""
from __future__ import annotations

import json
from pathlib import Path
import tempfile

from content_factory_handoff import ToolResult, ToolTask
from content_factory_media_production import ExecutionTruth, MediaProductionError


class OpenMontageFactoryAdapter:
    name = "openmontage"
    truth = ExecutionTruth.LIVE

    def __init__(self, storage, producer=None):
        self.storage = storage
        if producer is None:
            from openmontage_production import produce_video
            producer = produce_video
        self.producer = producer

    def run(self, task: ToolTask) -> ToolResult:
        if task.inputs:
            raise MediaProductionError("OpenMontage bridge requires manifest, not implicit source media")
        try:
            payload = json.loads(task.parameters["openmontage_payload"])
        except (KeyError, ValueError, TypeError) as exc:
            raise MediaProductionError("missing or invalid OpenMontage payload") from exc
        if not isinstance(payload, dict) or payload.get("job_id") != task.job_id or payload.get("revision") != task.revision:
            raise MediaProductionError("OpenMontage cross-job or stale payload")
        if not all(isinstance(payload.get(key), dict) for key in ("research", "storyboard", "media_manifest")):
            raise MediaProductionError("OpenMontage research/storyboard/media manifest required")
        with tempfile.TemporaryDirectory(prefix="factory-openmontage-") as temp:
            output = Path(temp) / "render"
            report = self.producer(
                research_data=payload["research"],
                storyboard_data=payload["storyboard"],
                media_manifest_data=payload["media_manifest"],
                output_dir=output,
            )
            if not isinstance(report, dict) or report.get("status") != "COMPLETED":
                raise MediaProductionError("OpenMontage render not completed")
            video = output / "creative-demo.mp4"
            reported = Path(str(report.get("video_file", ""))).resolve()
            if reported != video.resolve() or not video.is_file() or video.stat().st_size == 0:
                raise MediaProductionError("OpenMontage did not produce expected MP4")
            ref = self.storage.put_file(
                video,
                provenance=f"openmontage:{task.task_id}:r{task.revision}",
                mime_type="video/mp4",
            )
        return ToolResult(task.job_id, task.revision, task.task_id, [ref], self.name)
