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
from media_storage import R2Storage


def run(job_id: str):
    with tempfile.TemporaryDirectory(prefix="factory-review-") as td:
        storage=R2Storage.from_env(cache_root=Path(td)/"media")
        repo=R2JobRepository(storage)
        state,_=_read_state(job_id,storage)
        if state.get("state")=="REVIEW_APPLIED":
            result=acknowledge_persisted_review(job_id,storage=storage,repository=repo)
            print("BLOCK8_REVIEW_ALREADY_APPLIED_AND_VERIFIED "+result)
            return result
        result=apply_review_request(job_id,storage=storage,repository=repo)
        verified=acknowledge_persisted_review(job_id,storage=storage,repository=repo)
        print("BLOCK8_REVIEW_CANONICAL_APPLIED_AND_ACKNOWLEDGED "+
              f"job={job_id} request={result.request_id} action={result.decision} "+
              f"application={result.result} ack={verified}")
        return verified


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--job-id",required=True,
        help="Opaque canonical dashboard job UUID, never a caller-provided R2 path")
    args=parser.parse_args()
    run(args.job_id)
