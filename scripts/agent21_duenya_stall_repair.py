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
ALLOWED_STAGES={"production_lead","creative_director","media_story","music_audio","video_editor_ffmpeg","qm","private_preview"}
REPAIR_ID="R21-DUENYA-STAGE-AWARE-20261008-V4"
PRODUCTION_REVISION=os.environ.get("DUENYA_PRODUCTION_REVISION","v4")
if PRODUCTION_REVISION not in {"v4","v4-creative1"}:
    raise RuntimeError("AGENT21_DUENYA_REVISION_INVALID")
STATUS_KEY=f"ai-central/v1/private-video/{TASK_ID}/revisions/{PRODUCTION_REVISION}/status.json"
# Resolve the stage from the authoritative revision status instead of hard-coding FFmpeg.
# The watchdog incident must independently agree with that stage before recovery is allowed.
def _incident_key(stage):
    return f"ai-central/v1/maintenance/incidents/WD-{TASK_ID}-{stage}-{PRODUCTION_REVISION}.json"
STAGE="video_editor_ffmpeg"  # Legacy compatibility for regression imports; runtime remains stage-aware.
INCIDENT_KEY=_incident_key(STAGE)
STALE_AFTER_SECONDS=75


def _read_json(client,bucket,key,limit=16384):
    return json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(limit))


def reconcile(client,bucket,*,now=None):
    now=now or datetime.now(timezone.utc)
    state=_read_json(client,bucket,STATUS_KEY)
    stage=state.get("stage")
    if stage not in ALLOWED_STAGES:
        raise RuntimeError("AGENT21_DUENYA_STAGE_INVALID")
    if (state.get("schema")=="PRIVATE-VIDEO-STATUS-V1" and state.get("task_id")==TASK_ID
        and state.get("production_revision")==PRODUCTION_REVISION
        and state.get("status")=="COMPLETED"):
        return {"action":"NO_RECOVERY","reason":"ALREADY_COMPLETED","repair_id":REPAIR_ID,"stage_id":stage}
    incident_id=f"WD-{TASK_ID}-{stage}-{PRODUCTION_REVISION}"
    incident=_read_json(client,bucket,_incident_key(stage))
    if (
        incident.get("schema")!="MACHINE-WATCHDOG-INCIDENT-V1"
        or incident.get("incident_id")!=incident_id
        or incident.get("job_id")!=TASK_ID
        or incident.get("stage_id")!=stage
        or incident.get("machine")!="private-media-container"
        or incident.get("route_to")!="agent21"
        or incident.get("requested_action")!="DIAGNOSE_ONLY"
        or incident.get("reason") not in {"MACHINE_REPORTED_STALLED","MACHINE_REPORTED_FAILED"}
    ):
        raise RuntimeError("AGENT21_DUENYA_INCIDENT_INVALID")
    if (state.get("schema")!="PRIVATE-VIDEO-STATUS-V1" or state.get("task_id")!=TASK_ID
        or state.get("production_revision")!=PRODUCTION_REVISION
        or state.get("runtime_revision")!="duenya-creative-chain-v3"):
        raise RuntimeError("AGENT21_DUENYA_STATUS_INVALID")
    if state.get("status")=="COMPLETED":
        return {"action":"NO_RECOVERY","reason":"ALREADY_COMPLETED","repair_id":REPAIR_ID}
    if state.get("status")=="FAILED":
        if state.get("stage")!=stage:
            raise RuntimeError("AGENT21_DUENYA_FAILED_STAGE_MISMATCH")
        # Persist the exact bounded diagnostic before any restart.
        error_code = str(state.get("error_code") or "UNKNOWN")[:80]
        detail = str(state.get("detail") or "")[:240]
        diagnostic = {
            "schema": "PRIVATE-VIDEO-MAINTENANCE-HANDOFF-V1",
            "job_id": TASK_ID,
            "production_revision": PRODUCTION_REVISION,
            "stage_id": stage,
            "error_code": error_code,
            "detail": detail,
            "incident_id": incident_id,
            "route_to": "agent21",
            "requested_action": "DIAGNOSE_AND_REPAIR",
            "created_at": now.isoformat(),
        }
        client.put_object(
            Bucket=bucket,
            Key=f"ai-central/v1/maintenance/handoffs/{incident_id}.json",
            Body=json.dumps(diagnostic, ensure_ascii=False).encode("utf-8"),
            ContentType="application/json",
            CacheControl="private, no-store",
        )
        # Narrow, one-time recovery authorization for the independently diagnosed
        # creative-director frame-extraction incident after operator-approved fix.
        # Must be explicitly enabled by the trusted recovery workflow; all other
        # failures continue to require diagnosis.
        if (os.environ.get("DUENYA_FRAME_FIX_VERIFIED") == "true"
            and stage == "creative_director"
            and error_code == "RuntimeError"
            and "PRIVATE_VISION_FRAME_EXTRACTION_FAILED" in detail
            and incident.get("reason") == "MACHINE_REPORTED_FAILED"):
            # A new verified repair revision gets its own one-time authorization.
            # Never reuse the consumed v1 marker; fail closed on duplicate attempts.
            marker=f"ai-central/v1/maintenance/recovery-authorizations/{incident_id}-frame-fix-v2.json"
            try:
                client.put_object(
                    Bucket=bucket, Key=marker, IfNoneMatch="*",
                    Body=json.dumps({"incident_id":incident_id,
                                     "fix":"PRIVATE_VISION_FRAME_EXTRACTION_FAILED",
                                     "repair_revision":"jpeg-still-no-seek-pr518",
                                     "at":now.isoformat()}).encode("utf-8"),
                    ContentType="application/json", CacheControl="private, no-store",
                )
            except Exception:
                return {"action":"DIAGNOSE_REQUIRED","reason":"FRAME_RETRY_NOT_AUTHORIZED",
                        "repair_id":REPAIR_ID,"stage_id":stage,"error_code":error_code}
            return {"action":"HANDOFF_AGENT11","reason":"VERIFIED_FRAME_FIX_ONE_TIME",
                    "repair_id":REPAIR_ID+"-FRAME-FIX-V2","stage_id":stage}
        return {"action":"DIAGNOSE_REQUIRED","reason":"FAILED_NEEDS_ROOT_CAUSE",
                "repair_id":REPAIR_ID,"stage_id":stage,"error_code":error_code}
    if state.get("status")!="RUNNING" or state.get("stage")!=stage:
        raise RuntimeError("AGENT21_DUENYA_STATE_NOT_RECONCILABLE")

    try:
        heartbeat=datetime.fromisoformat(str(state.get("updated_at")).replace("Z","+00:00"))
    except Exception as exc:
        raise RuntimeError("AGENT21_DUENYA_HEARTBEAT_INVALID") from exc
    if heartbeat.tzinfo is None:
        raise RuntimeError("AGENT21_DUENYA_HEARTBEAT_INVALID")
    age=(now-heartbeat).total_seconds()
    if age<=STALE_AFTER_SECONDS:
        return {"action":"NO_RECOVERY","reason":"HEARTBEAT_FRESH","repair_id":REPAIR_ID,"stage_id":stage}

    payload={
        "schema":"PRIVATE-VIDEO-STATUS-V1",
        "task_id":TASK_ID,
        "status":"FAILED",
        "stage":stage,
        "production_revision":PRODUCTION_REVISION,
        "runtime_revision":"duenya-creative-chain-v3",
        "updated_at":now.isoformat(),
        "error_code":"AGENT21_CONFIRMED_STALLED",
        "detail":f"Agent 21 reconciled stale heartbeat at {stage}; original bounded error retained by runtime status.",
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
        "stage_id":stage,
        "stale_seconds":int(age),
    }


def main():
    client,bucket=client_from_env()
    result=reconcile(client,bucket)
    print(json.dumps(result,separators=(",",":")))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
