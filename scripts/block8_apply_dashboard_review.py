"""One explicit dashboard-owned review event: real private R2 -> canonical job -> ACK.

Only change/discard requests may run. Never publishes or sends to Instagram/FB.
GitHub workflow is dispatched by an explicit authenticated Dashboard click.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import tempfile

from content_factory_dashboard_review_applier import apply_review_request
from content_factory_dashboard_review_ack import (
    _read_state, acknowledge_persisted_review,
)
from content_factory_r2_job_repository import R2JobRepository
from content_factory_revision_intake import derive_canonical_edit_request
from media_storage import R2Storage


def run(job_id: str, *, produce: bool = False):
    with tempfile.TemporaryDirectory(prefix="factory-review-") as td:
        storage=R2Storage.from_env(cache_root=Path(td)/"media")
        repo=R2JobRepository(storage)
        state,_=_read_state(job_id,storage)
        if produce:
            from content_factory_revision_render import produce_revision
            existing=repo.get_job(job_id).job
            render_state=existing.metadata.get("revision_render", {})
            if render_state.get("revision")==existing.revision and state.get("state")!="REVIEW_REQUESTED":
                result=produce_revision(job_id,storage=storage,repository=repo,workdir=Path(td)/"render")
                print("BLOCK8_REVISION_PRODUCTION "+result)
                return result
        if state.get("state")=="REVIEW_APPLIED":
            result=acknowledge_persisted_review(job_id,storage=storage,repository=repo)
            if (state.get("review") or {}).get("action")=="change":
                intake,_=derive_canonical_edit_request(job_id,storage=storage,repository=repo)
                print("BLOCK8_EDIT_INTAKE_VERIFIED "+intake)
            if produce and (state.get("review") or {}).get("action")=="change":
                rendered=produce_revision(job_id,storage=storage,repository=repo,workdir=Path(td)/"render")
                print("BLOCK8_REVISION_PRODUCTION "+rendered)
            print("BLOCK8_REVIEW_ALREADY_APPLIED_AND_VERIFIED "+result)
            return result
        result=apply_review_request(job_id,storage=storage,repository=repo)
        verified=acknowledge_persisted_review(job_id,storage=storage,repository=repo)
        if result.decision=="change":
            intake,_=derive_canonical_edit_request(job_id,storage=storage,repository=repo)
            print("BLOCK8_EDIT_INTAKE_VERIFIED "+intake)
        if produce and result.decision=="change":
            rendered=produce_revision(job_id,storage=storage,repository=repo,workdir=Path(td)/"render")
            print("BLOCK8_REVISION_PRODUCTION "+rendered)
        print("BLOCK8_REVIEW_CANONICAL_APPLIED_AND_ACKNOWLEDGED "+
              f"job={job_id} request={result.request_id} action={result.decision} "+
              f"application={result.result} ack={verified}")
        return verified


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--job-id",required=True,
        help="Opaque canonical dashboard job UUID, never a caller-provided R2 path")
    parser.add_argument("--produce",action="store_true")
    args=parser.parse_args()
    run(args.job_id,produce=args.produce)
