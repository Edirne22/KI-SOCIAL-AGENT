"""Agent 21 reconciliation for the exact stalled Dünya Level 12 render.

This is intentionally one-task, fail-closed repair logic. It validates the watcher
incident plus stale PRIVATE-VIDEO-STATUS-V1 before converting the orphaned RUNNING
record into FAILED so Agent 11 can execute the existing guarded RESUME contract.
"""
from __future__ import annotations

import json, os
from datetime import datetime, timezone

from scripts.ai_central_shared_inbox import client_from_env

TASK_ID="f6f50c9f4c2690e4eb1fe978"
STAGE="video_editor_ffmpeg"
REPAIR_ID="R21-DUENYA-FFMPEG-SLEEP-20261007-V4"
PRODUCTION_REVISION=os.environ.get("DUENYA_PRODUCTION_REVISION","v4")
if PRODUCTION_REVISION not in {"v4","v4-creative1"}:
    raise RuntimeError("AGENT21_DUENYA_REVISION_INVALID")
STATUS_KEY=f"ai-central/v1/private-video/{TASK_ID}/revisions/{PRODUCTION_REVISION}/status.json"
INCIDENT_ID=f"WD-{TASK_ID}-{STAGE}-{PRODUCTION_REVISION}"
INCIDENT_KEY=f"ai-central/v1/maintenance/incidents/{INCIDENT_ID}.json"
STALE_AFTER_SECONDS=75


def _read_json(client,bucket,key,limit=16384):
    return json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(limit))


def reconcile(client,bucket,*,now=None):
    now=now or datetime.now(timezone.utc)
    incident=_read_json(client,bucket,INCIDENT_KEY)
    if (
        incident.get("schema")!="MACHINE-WATCHDOG-INCIDENT-V1"
        or incident.get("incident_id")!=INCIDENT_ID
        or incident.get("job_id")!=TASK_ID
        or incident.get("stage_id")!=STAGE
        or incident.get("machine")!="private-media-container"
        or incident.get("route_to")!="agent21"
        or incident.get("requested_action")!="DIAGNOSE_ONLY"
        or incident.get("reason")!="MACHINE_REPORTED_STALLED"
    ):
        raise RuntimeError("AGENT21_DUENYA_INCIDENT_INVALID")

    state=_read_json(client,bucket,STATUS_KEY)
    if (state.get("schema")!="PRIVATE-VIDEO-STATUS-V1" or state.get("task_id")!=TASK_ID
        or state.get("production_revision")!=PRODUCTION_REVISION
        or state.get("runtime_revision")!="duenya-creative-chain-v3"):
        raise RuntimeError("AGENT21_DUENYA_STATUS_INVALID")
    if state.get("status")=="COMPLETED":
        return {"action":"NO_RECOVERY","reason":"ALREADY_COMPLETED","repair_id":REPAIR_ID}
    if state.get("status")=="FAILED":
        if state.get("stage")!=STAGE:
            raise RuntimeError("AGENT21_DUENYA_FAILED_STAGE_MISMATCH")
        return {"action":"HANDOFF_AGENT11","reason":"ALREADY_FAILED","repair_id":REPAIR_ID}
    if state.get("status")!="RUNNING" or state.get("stage")!=STAGE:
        raise RuntimeError("AGENT21_DUENYA_STATE_NOT_RECONCILABLE")

    try:
        heartbeat=datetime.fromisoformat(str(state.get("updated_at")).replace("Z","+00:00"))
    except Exception as exc:
        raise RuntimeError("AGENT21_DUENYA_HEARTBEAT_INVALID") from exc
    if heartbeat.tzinfo is None:
        raise RuntimeError("AGENT21_DUENYA_HEARTBEAT_INVALID")
    age=(now-heartbeat).total_seconds()
    if age<=STALE_AFTER_SECONDS:
        return {"action":"NO_RECOVERY","reason":"HEARTBEAT_FRESH","repair_id":REPAIR_ID}

    payload={
        "schema":"PRIVATE-VIDEO-STATUS-V1",
        "task_id":TASK_ID,
        "status":"FAILED",
        "stage":STAGE,
        "production_revision":PRODUCTION_REVISION,
        "runtime_revision":"duenya-creative-chain-v3",
        "updated_at":now.isoformat(),
        "error_code":"AGENT21_CONFIRMED_STALLED",
        "detail":"Stale FFmpeg heartbeat reconciled after container background-lifecycle repair.",
    }
    client.put_object(
        Bucket=bucket,Key=STATUS_KEY,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",CacheControl="private, no-store",
    )
    return {
        "action":"HANDOFF_AGENT11",
        "reason":"STALE_RUNNING_RECONCILED",
        "repair_id":REPAIR_ID,
        "stale_seconds":int(age),
    }


def main():
    client,bucket=client_from_env()
    result=reconcile(client,bucket)
    print(json.dumps(result,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
