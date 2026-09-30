"""Block 8: final QM + Golden Tablet human authority boundary."""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, json
from content_factory_core import ProductionJob, JobStatus

class GoldenTabletError(RuntimeError): pass
@dataclass(frozen=True)
class QMCheck:
    name:str; passed:bool; detail:str=""
@dataclass(frozen=True)
class FinalQMReport:
    report_id:str; job_id:str; revision:int; checks:tuple[QMCheck,...]; audience_advisory:tuple[str,...]=()
    @property
    def passed(self): return bool(self.checks) and all(x.passed for x in self.checks)
@dataclass(frozen=True)
class GoldenTablet:
    job_id:str; revision:int; manifest:str; caption:str; media_ids:tuple[str,...]; qm_report_id:str; audience_advisory:tuple[str,...]

class FinalQM:
    def evaluate(self,job:ProductionJob,checks,*,audience_advisory=()):
        checks=tuple(checks)
        if job.status!=JobStatus.QM: raise GoldenTabletError("final QM requires qm state")
        canonical={"job":job.job_id,"revision":job.revision,"checks":[x.__dict__ for x in checks],"audience":list(audience_advisory)}
        rid=hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()
        return FinalQMReport(rid,job.job_id,job.revision,checks,tuple(audience_advisory))

def present_golden_tablet(job:ProductionJob,report:FinalQMReport)->GoldenTablet:
    if report.job_id!=job.job_id or report.revision!=job.revision: raise GoldenTabletError("stale/cross-job QM report")
    if not report.passed: raise GoldenTabletError("failed QM cannot reach human")
    if job.status!=JobStatus.QM: raise GoldenTabletError("job not in qm state")
    creative=job.metadata.get(f"creative_package:r{job.revision}")
    if not creative: raise GoldenTabletError("creative package missing")
    caption=creative["draft"]["caption"]
    job.publish_payload={"caption":caption,"creative_revision":job.revision}
    job.transition(JobStatus.READY_FOR_HUMAN)
    manifest=job.approval_manifest()
    return GoldenTablet(job.job_id,job.revision,manifest,caption,tuple(m.media_id for m in job.media),report.report_id,report.audience_advisory)

class HumanDecisionService:
    def post(self,job:ProductionJob,tablet:GoldenTablet):
        self._match(job,tablet); job.transition(JobStatus.APPROVED,actor="human"); return job.publish_handoff()
    def discard(self,job:ProductionJob,tablet:GoldenTablet):
        self._match(job,tablet); job.transition(JobStatus.REJECTED,actor="human")
    def change(self,job:ProductionJob,tablet:GoldenTablet,request:str):
        self._match(job,tablet)
        if not request.strip(): raise GoldenTabletError("change request required")
        job.metadata[f"human_change:r{job.revision}"]=request.strip()
        job.transition(JobStatus.CHANGES_REQUESTED,actor="human")
    def _match(self,job,tablet):
        if job.status!=JobStatus.READY_FOR_HUMAN: raise GoldenTabletError("human decision requires ready state")
        if tablet.job_id!=job.job_id or tablet.revision!=job.revision: raise GoldenTabletError("stale/cross-job tablet")
        if tablet.manifest!=job.approval_manifest(): raise GoldenTabletError("tablet payload/media changed after preview")
