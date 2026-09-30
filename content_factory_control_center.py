"""Block 9: control-center boundary and safe existing-publisher bridge."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
from typing import Protocol
from content_factory_core import ProductionJob, JobStatus

class ControlCenterError(RuntimeError): pass
@dataclass(frozen=True)
class ControlRequest:
    request_id:str; channel:str; actor:str; action:str; job_id:str; revision:int; payload:str=""
@dataclass(frozen=True)
class PublishReceipt:
    handoff_key:str; platform:str; external_id:str; proof:str

class ExistingPublisherPort(Protocol):
    name:str
    def publish(self,job:ProductionJob,platform:str,handoff_key:str)->PublishReceipt: ...

class PublisherBridge:
    def __init__(self): self._receipts={}
    def publish(self,job:ProductionJob,*,platform:str,publisher:ExistingPublisherPort):
        if job.status!=JobStatus.PUBLISH_QUEUED: raise ControlCenterError("publisher requires human-approved publish queue")
        key=job.publish_handoff_key
        if not key: raise ControlCenterError("missing canonical publish handoff")
        slot=(key,platform)
        if slot in self._receipts: return self._receipts[slot]
        receipt=publisher.publish(job,platform,key)
        if receipt.handoff_key!=key or receipt.platform!=platform: raise ControlCenterError("publisher receipt correlation mismatch")
        self._receipts[slot]=receipt
        return receipt
    def mark_complete(self,job:ProductionJob,receipts):
        receipts=tuple(receipts)
        if job.status!=JobStatus.PUBLISH_QUEUED: raise ControlCenterError("completion requires queued job")
        if not receipts: raise ControlCenterError("publish proof required")
        key=job.publish_handoff_key
        if any(r.handoff_key!=key or not r.external_id or not r.proof for r in receipts): raise ControlCenterError("invalid publish proof")
        job.metadata[f"publish_proof:r{job.revision}"]=[r.__dict__ for r in receipts]
        job.transition(JobStatus.PUBLISHED)

class ControlCenter:
    """Single-user command boundary shared by web UI and Telegram."""
    CHANNELS={"web","telegram"}
    ACTIONS={"view","change","discard","post"}
    def validate(self,job:ProductionJob,req:ControlRequest):
        if req.channel not in self.CHANNELS or req.action not in self.ACTIONS: raise ControlCenterError("unsupported control request")
        if req.actor!="buelent": raise ControlCenterError("human authority actor required")
        if req.job_id!=job.job_id or req.revision!=job.revision: raise ControlCenterError("stale/cross-job control request")
        if req.action in {"change","discard","post"} and job.status!=JobStatus.READY_FOR_HUMAN: raise ControlCenterError("decision requires Golden Tablet ready state")
        return True

class ContractPublisher:
    """CI-only publisher simulation; never a live platform claim."""
    name="contract-publisher"; truth="SIMULATED"
    def publish(self,job,platform,handoff_key):
        eid=hashlib.sha256(f"{handoff_key}|{platform}".encode()).hexdigest()[:16]
        return PublishReceipt(handoff_key,platform,f"sim-{eid}","SIMULATED_PUBLISH_PROOF")
