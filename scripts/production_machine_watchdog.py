"""Generic machine watchdog for production jobs.

Observation only: no shell, provider calls, restarts, deploys or publishing.
It converts bounded machine telemetry into an incident that Agent 21 may inspect.
"""
from __future__ import annotations
from datetime import datetime, timezone
import re

ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,95}$")
MACHINES={"private-media-container","private-asr-container"}
ACTIVE={"WARMING","READY","ACCEPTED","RUNNING"}
TERMINAL={"COMPLETED","CANCELLED"}
FAULT={"FAILED","STALLED","TIMEOUT","UNHEALTHY"}

def inspect(sample:dict)->dict:
    required={"job_id","stage_id","machine","checkpoint","status","heartbeat_at","progress"}
    if not isinstance(sample,dict) or set(sample)!=required:
        raise ValueError("WATCHDOG_SAMPLE_SCHEMA_INVALID")
    for key in ("job_id","stage_id","checkpoint"):
        if not isinstance(sample[key],str) or not ID.fullmatch(sample[key]):
            raise ValueError("WATCHDOG_ID_INVALID:"+key)
    if sample["machine"] not in MACHINES:
        raise ValueError("WATCHDOG_MACHINE_NOT_ALLOWED")
    if sample["status"] not in ACTIVE|TERMINAL|FAULT:
        raise ValueError("WATCHDOG_STATUS_INVALID")
    if not isinstance(sample["progress"],(int,float)) or isinstance(sample["progress"],bool) or not 0<=sample["progress"]<=100:
        raise ValueError("WATCHDOG_PROGRESS_INVALID")
    try:
        heartbeat=datetime.fromisoformat(sample["heartbeat_at"].replace("Z","+00:00"))
    except Exception as exc:
        raise ValueError("WATCHDOG_HEARTBEAT_INVALID") from exc
    if heartbeat.tzinfo is None:
        raise ValueError("WATCHDOG_HEARTBEAT_INVALID")
    if sample["status"] in FAULT:
        return incident(sample,"MACHINE_REPORTED_"+sample["status"])
    return {"decision":"OBSERVE","job_id":sample["job_id"],"stage_id":sample["stage_id"],
            "machine":sample["machine"],"status":sample["status"],"progress":sample["progress"]}

def incident(sample:dict,reason:str)->dict:
    return {
      "schema":"MACHINE-WATCHDOG-INCIDENT-V1",
      "incident_id":"WD-"+sample["job_id"]+"-"+sample["stage_id"],
      "job_id":sample["job_id"],"stage_id":sample["stage_id"],"machine":sample["machine"],
      "checkpoint":sample["checkpoint"],"last_progress":sample["progress"],
      "last_heartbeat_at":sample["heartbeat_at"],"reason":reason,
      "route_to":"agent21","requested_action":"DIAGNOSE_ONLY"
    }


def private_video_status_sample(state:dict,now:datetime|None=None,stall_after_seconds:int=45)->dict:
    """Adapter for existing PRIVATE-VIDEO-STATUS-V1 R2 records."""
    if not isinstance(state,dict) or state.get("schema")!="PRIVATE-VIDEO-STATUS-V1":
        raise ValueError("WATCHDOG_PRIVATE_VIDEO_STATUS_INVALID")
    task=state.get("task_id"); stage=state.get("stage") or "production_lead"
    if not isinstance(task,str) or not ID.fullmatch(task):
        raise ValueError("WATCHDOG_PRIVATE_VIDEO_TASK_INVALID")
    if not isinstance(stage,str) or not ID.fullmatch(stage):
        raise ValueError("WATCHDOG_PRIVATE_VIDEO_STAGE_INVALID")
    stamp=state.get("updated_at")
    try: hb=datetime.fromisoformat(str(stamp).replace("Z","+00:00"))
    except Exception as exc: raise ValueError("WATCHDOG_PRIVATE_VIDEO_HEARTBEAT_INVALID") from exc
    now=now or datetime.now(timezone.utc)
    status=state.get("status")
    if status in ("ACCEPTED","RUNNING") and (now-hb).total_seconds()>stall_after_seconds:
        status="STALLED"
    mapped={"ACCEPTED":"ACCEPTED","RUNNING":"RUNNING","COMPLETED":"COMPLETED","FAILED":"FAILED"}.get(status,status)
    progress=100 if mapped=="COMPLETED" else 0
    return {"job_id":task,"stage_id":stage,"machine":"private-media-container",
            "checkpoint":stage,"status":mapped,"heartbeat_at":hb.isoformat(),"progress":progress}
