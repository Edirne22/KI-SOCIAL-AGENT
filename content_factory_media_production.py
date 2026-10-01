"""Block 6: media-production planning and safe machine execution."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import hashlib, shutil, subprocess, tempfile
from typing import Protocol

from content_factory_core import MediaRef, ProductionJob, JobStatus
from content_factory_creative import CreativeBrief, ContentFormat
from content_factory_handoff import ToolTask, ToolResult, run_machine, HandoffError
from media_storage import MediaStorageAdapter

class MediaProductionError(RuntimeError): pass
class ExecutionTruth(str,Enum): LIVE="LIVE"; SIMULATED="SIMULATED"; NOT_CHECKED="NOT_CHECKED"
class MediaStage(str,Enum): CLIP="clip"; GENERATE="generate"; EDIT="edit"; RENDER="render"

@dataclass(frozen=True)
class MediaStep:
    step_id:str; stage:MediaStage; machine:str; input_media_ids:tuple[str,...]; parameters:tuple[tuple[str,str],...]=()
@dataclass(frozen=True)
class MediaProductionPlan:
    job_id:str; revision:int; brief_id:str; steps:tuple[MediaStep,...]

class MediaProductionPlanner:
    def plan(self,job:ProductionJob,brief:CreativeBrief)->MediaProductionPlan:
        if job.status not in (JobStatus.STORYBOARDING,JobStatus.RENDERING):
            raise MediaProductionError("media planning requires storyboard/render state")
        ids=tuple(m.media_id for m in job.media)
        steps=[]
        if brief.content_format in (ContentFormat.REEL,ContentFormat.VIDEO):
            if ids: steps.append(MediaStep("clip","clip","chopify",ids,(("aspect","9:16"),("style","podcast"),("whisper_model","tiny"))))
            else:
                prompt=" | ".join(x for x in (brief.hook,brief.angle,*[b.visual_intent for b in brief.beats]) if str(x).strip())
                steps.append(MediaStep("generate","generate","agnes_video",(),(("prompt",prompt),("language",brief.language))))
            steps.append(MediaStep("edit","edit","openchatcut",()))
            steps.append(MediaStep("render","render","ffmpeg",()))
        elif brief.content_format in (ContentFormat.IMAGE,ContentFormat.CAROUSEL):
            if not ids:
                prompt=" | ".join(x for x in (brief.hook,brief.angle,*[b.visual_intent for b in brief.beats]) if str(x).strip())
                steps.append(MediaStep("generate","generate","image_router",(),(("prompt",prompt),("language",brief.language))))
        return MediaProductionPlan(job.job_id,job.revision,brief.brief_id,tuple(steps))

class ExternalMediaPort(Protocol):
    name:str
    truth:ExecutionTruth
    def run(self,task:ToolTask)->ToolResult: ...

class ContractMediaAdapter:
    """Explicit simulation adapter for CI; never presented as live integration."""
    truth=ExecutionTruth.SIMULATED
    def __init__(self,name:str,output:MediaRef): self.name=name; self.output=output
    def run(self,task): return ToolResult(task.job_id,task.revision,task.task_id,[self.output],self.name)

class ImageRouterAdapter:
    """LIVE bridge from the existing ImageRouter bytes API into factory storage."""
    name="image_router"; truth=ExecutionTruth.LIVE
    def __init__(self,storage:MediaStorageAdapter,router=None):
        self.storage=storage
        if router is None:
            from image_router import ImageRouter
            router=ImageRouter()
        self.router=router
    def run(self,task:ToolTask)->ToolResult:
        if task.inputs:
            raise MediaProductionError("image generation does not accept source media")
        prompt=str(task.parameters.get("prompt","")).strip()
        if not prompt:
            raise MediaProductionError("image generation requires bound prompt")
        image_bytes=self.router.generate_image(prompt)
        if not isinstance(image_bytes,(bytes,bytearray)) or not image_bytes:
            raise MediaProductionError("image router returned no image bytes")
        with tempfile.TemporaryDirectory(prefix="factory-image-") as tmp:
            out=Path(tmp)/f"{task.job_id}-{task.revision}-{task.task_id}.png"
            out.write_bytes(bytes(image_bytes))
            ref=self.storage.put_file(
                out,
                provenance=f"image_router:{task.task_id}:r{task.revision}",
                mime_type="image/png",
            )
        return ToolResult(task.job_id,task.revision,task.task_id,[ref],self.name)

class AgnesVideoAdapter:
    """LIVE bridge from the existing Agnes video API into factory storage."""
    name="agnes_video"; truth=ExecutionTruth.LIVE
    def __init__(self,storage:MediaStorageAdapter,generator=None):
        self.storage=storage
        if generator is None:
            from generate_agnes_media import agnes_generate_video
            generator=agnes_generate_video
        self.generator=generator
    def run(self,task:ToolTask)->ToolResult:
        if task.inputs:
            raise MediaProductionError("Agnes video generation does not accept source media")
        prompt=str(task.parameters.get("prompt","")).strip()
        if not prompt:
            raise MediaProductionError("video generation requires bound prompt")
        video_bytes=self.generator(prompt)
        if not isinstance(video_bytes,(bytes,bytearray)) or not video_bytes:
            raise MediaProductionError("Agnes video generation returned no video bytes")
        with tempfile.TemporaryDirectory(prefix="factory-video-") as tmp:
            out=Path(tmp)/f"{task.job_id}-{task.revision}-{task.task_id}.mp4"
            out.write_bytes(bytes(video_bytes))
            ref=self.storage.put_file(out,provenance=f"agnes_video:{task.task_id}:r{task.revision}",mime_type="video/mp4")
        return ToolResult(task.job_id,task.revision,task.task_id,[ref],self.name)

class FFmpegAdapter:
    name="ffmpeg"; truth=ExecutionTruth.LIVE
    def __init__(self,storage:MediaStorageAdapter,workdir:Path,ffmpeg_bin:str="ffmpeg"):
        self.storage=storage; self.workdir=Path(workdir); self.ffmpeg_bin=ffmpeg_bin
    def run(self,task:ToolTask)->ToolResult:
        if not task.inputs: raise MediaProductionError("ffmpeg render requires input")
        if shutil.which(self.ffmpeg_bin) is None: raise MediaProductionError("ffmpeg unavailable")
        src=self.storage.resolve_local(task.inputs[0]); self.workdir.mkdir(parents=True,exist_ok=True)
        out=self.workdir/f"{task.job_id}-{task.revision}-{task.task_id}.mp4"
        cmd=[self.ffmpeg_bin,"-y","-i",str(src),"-map_metadata","-1","-c","copy",str(out)]
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=120,check=False)
        if p.returncode!=0: raise MediaProductionError("ffmpeg render failed")
        ref=self.storage.put_file(out,provenance=f"ffmpeg:{task.task_id}",mime_type="video/mp4")
        return ToolResult(task.job_id,task.revision,task.task_id,[ref],self.name)

class MediaProductionRunner:
    def execute(self,job:ProductionJob,plan:MediaProductionPlan,machines:dict[str,ExternalMediaPort]):
        if plan.job_id!=job.job_id or plan.revision!=job.revision: raise MediaProductionError("stale/cross-job media plan")
        results=[]; last=[]
        for step in plan.steps:
            machine=machines.get(step.machine)
            if machine is None: raise MediaProductionError(f"machine unavailable: {step.machine}")
            ids=step.input_media_ids or tuple(m.media_id for m in last)
            canonical={m.media_id:m for m in job.media}
            inputs=[]
            for mid in ids:
                if mid not in canonical: raise MediaProductionError("media plan references foreign input")
                inputs.append(canonical[mid])
            task=ToolTask(job.job_id,job.revision,step.step_id,inputs,dict(step.parameters))
            result=run_machine(job,machine,task); results.append(result); last=result.outputs
        return tuple(results)

def attach_media_plan(job:ProductionJob,plan:MediaProductionPlan):
    if plan.job_id!=job.job_id or plan.revision!=job.revision: raise MediaProductionError("media plan envelope mismatch")
    if job.status in (JobStatus.READY_FOR_HUMAN,JobStatus.APPROVED,JobStatus.PUBLISH_QUEUED,JobStatus.PUBLISHED,JobStatus.REJECTED):
        raise MediaProductionError("cannot mutate finalized job")
    payload={"job_id":plan.job_id,"revision":plan.revision,"brief_id":plan.brief_id,
             "steps":[{"step_id":s.step_id,"stage":s.stage.value,"machine":s.machine,"input_media_ids":list(s.input_media_ids),"parameters":dict(s.parameters)} for s in plan.steps]}
    slot=f"media_plan:r{job.revision}"; old=job.metadata.get(slot)
    if old is not None and old!=payload: raise MediaProductionError("media plan replacement requires new revision")
    job.metadata[slot]=payload
