"""Block 7: authorized voice, captions and avatar/motion contracts."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
import hashlib, json
from content_factory_core import ProductionJob, JobStatus, MediaRef
from content_factory_handoff import ToolTask, ToolResult, run_machine

class AVError(RuntimeError): pass
class AVTruth(str,Enum): LIVE="LIVE"; SIMULATED="SIMULATED"; NOT_CHECKED="NOT_CHECKED"

@dataclass(frozen=True)
class VoiceProfile:
    voice_id:str; owner:str; languages:tuple[str,...]; consent_ref:str; enabled:bool=True
@dataclass(frozen=True)
class CaptionCue:
    start_ms:int; end_ms:int; text:str
    def __post_init__(self):
        if self.start_ms<0 or self.end_ms<=self.start_ms or not self.text.strip(): raise ValueError("invalid caption cue")
@dataclass(frozen=True)
class NarrationPlan:
    plan_id:str; job_id:str; revision:int; language:str; script:str; voice_id:str; cues:tuple[CaptionCue,...]; avatar_mode:str="none"

class VoiceRegistry:
    def __init__(self,profiles=()): self._p={p.voice_id:p for p in profiles}
    def authorize(self,voice_id,language):
        p=self._p.get(voice_id)
        if not p or not p.enabled or not p.consent_ref.strip(): raise AVError("voice not explicitly authorized")
        if language not in p.languages: raise AVError("voice language not authorized")
        return p

class AVPlanner:
    def __init__(self,registry:VoiceRegistry): self.registry=registry
    def create(self,job:ProductionJob,*,script:str,language:str,voice_id:str,cues=(),avatar_mode="none"):
        if job.status not in (JobStatus.STORYBOARDING,JobStatus.RENDERING): raise AVError("AV planning requires production state")
        self.registry.authorize(voice_id,language)
        script=" ".join(str(script).split())
        if not script: raise AVError("script required")
        cues=tuple(cues)
        last=-1
        for cue in cues:
            if cue.start_ms<last: raise AVError("caption cues overlap/out of order")
            last=cue.end_ms
        canonical={"job":job.job_id,"revision":job.revision,"language":language,"script":script,"voice":voice_id,"cues":[c.__dict__ for c in cues],"avatar":avatar_mode}
        pid=hashlib.sha256(json.dumps(canonical,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
        return NarrationPlan(pid,job.job_id,job.revision,language,script,voice_id,cues,avatar_mode)

class ContractAVAdapter:
    truth=AVTruth.SIMULATED
    def __init__(self,name:str,output:MediaRef): self.name=name; self.output=output
    def run(self,task): return ToolResult(task.job_id,task.revision,task.task_id,[self.output],self.name)

def execute_av(job:ProductionJob,plan:NarrationPlan,*,voice_machine,avatar_machine=None):
    if plan.job_id!=job.job_id or plan.revision!=job.revision: raise AVError("stale/cross-job narration plan")
    voice=run_machine(job,voice_machine,ToolTask(job.job_id,job.revision,"voice",[],{"voice_id":plan.voice_id,"language":plan.language,"script":plan.script}))
    results=[voice]
    if plan.avatar_mode!="none":
        if avatar_machine is None: raise AVError("avatar requested but machine unavailable")
        results.append(run_machine(job,avatar_machine,ToolTask(job.job_id,job.revision,"avatar",voice.outputs,{"mode":plan.avatar_mode})))
    return tuple(results)

def attach_narration(job:ProductionJob,plan:NarrationPlan):
    if plan.job_id!=job.job_id or plan.revision!=job.revision: raise AVError("narration envelope mismatch")
    if job.status in (JobStatus.READY_FOR_HUMAN,JobStatus.APPROVED,JobStatus.PUBLISH_QUEUED,JobStatus.PUBLISHED,JobStatus.REJECTED): raise AVError("cannot mutate finalized job")
    payload={"plan_id":plan.plan_id,"language":plan.language,"voice_id":plan.voice_id,"script":plan.script,"avatar_mode":plan.avatar_mode,"cues":[c.__dict__ for c in plan.cues]}
    slot=f"narration_plan:r{job.revision}"; old=job.metadata.get(slot)
    if old is not None and old!=payload: raise AVError("narration replacement requires new revision")
    job.metadata[slot]=payload
