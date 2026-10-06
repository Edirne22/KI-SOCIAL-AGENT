"""One-shot exact start for the already authorized private Dünya production.

This module is intentionally bound to one task id. It never publishes and never
blindly retries a FAILED production; failures must go through Agent 21 -> Agent 11.
"""
from __future__ import annotations
import json, os, time
from datetime import datetime, timezone
import requests
from scripts.ai_central_shared_inbox import PREFIX, _is_private_video_request, client_from_env

TASK_ID="f6f50c9f4c2690e4eb1fe978"
RUNTIME_URL="https://edirne22-private-asr.butupeli.workers.dev/private-video/jobs"
ACTIVE={"ACCEPTED","RUNNING","COMPLETED"}

def _code(exc):
    return str(getattr(exc,"response",{}).get("Error",{}).get("Code",""))

def _status(client,bucket):
    key=f"ai-central/v1/private-video/{TASK_ID}/status.json"
    try:
        value=json.loads(client.get_object(Bucket=bucket,Key=key)["Body"].read(12000))
    except Exception as exc:
        if _code(exc) in ("404","NoSuchKey","NotFound"): return None
        raise
    if value.get("schema")!="PRIVATE-VIDEO-STATUS-V1" or value.get("task_id")!=TASK_ID:
        raise RuntimeError("EXACT_PRIVATE_VIDEO_STATUS_INVALID")
    return value

def start_exact(client,bucket,token,post=requests.post,sleeper=time.sleep):
    if not token: raise RuntimeError("EXACT_PRIVATE_VIDEO_TOKEN_MISSING")
    matches=[]
    paginator=client.get_paginator("list_objects_v2")
    scanned=0
    for page in paginator.paginate(Bucket=bucket,Prefix=PREFIX):
        for item in page.get("Contents",[]):
            scanned+=1
            if scanned>5000: raise RuntimeError("EXACT_PRIVATE_VIDEO_SCAN_LIMIT")
            key=item.get("Key","")
            if not key.endswith(".json"): continue
            obj=client.get_object(Bucket=bucket,Key=key)
            value=json.loads(obj["Body"].read(12000))
            if value.get("id")==TASK_ID: matches.append((key,value,obj.get("ETag")))
    if len(matches)!=1: raise RuntimeError("EXACT_PRIVATE_VIDEO_TASK_MATCH_"+str(len(matches)))
    key,task,etag=matches[0]
    if (task.get("schema")!="AI-INBOX-V1" or task.get("kind")!="message"
        or task.get("auto_dispatch") is not False or not _is_private_video_request(task.get("message",""))):
        raise RuntimeError("EXACT_PRIVATE_VIDEO_TASK_NOT_AUTHORIZED")
    if task.get("status") not in ("DRAFT_REQUIRES_REVIEW","QUEUED_FREE_REVIEW","QUEUED_PRIVATE_VIDEO"):
        raise RuntimeError("EXACT_PRIVATE_VIDEO_TASK_STATE_"+str(task.get("status")))
    current=_status(client,bucket)
    if current:
        state=current.get("status")
        if state in ACTIVE:
            return {"result":"ALREADY_"+state,"stage":current.get("stage")}
        if state=="FAILED":
            raise RuntimeError("EXACT_PRIVATE_VIDEO_FAILED_NEEDS_AGENT21:"+str(current.get("stage") or "unknown")+":"+str(current.get("error_code") or "unknown"))
        raise RuntimeError("EXACT_PRIVATE_VIDEO_UNKNOWN_RUNTIME_STATE_"+str(state))
    if task.get("status")!="QUEUED_PRIVATE_VIDEO":
        if not isinstance(etag,str) or not etag: raise RuntimeError("EXACT_PRIVATE_VIDEO_ETAG_MISSING")
        queued={**task,"status":"QUEUED_PRIVATE_VIDEO","dispatch_target":"private-media-container",
                "inference_scope":"none-private-ffmpeg","approved_at":datetime.now(timezone.utc).isoformat(),
                "approval_source":"blockrun-chat-handover-2026-10-06"}
        claimed=client.put_object(Bucket=bucket,Key=key,Body=json.dumps(queued,ensure_ascii=False).encode(),
            ContentType="application/json",IfMatch=etag)
        if not claimed.get("ETag"): raise RuntimeError("EXACT_PRIVATE_VIDEO_CLAIM_UNCERTAIN")
    try:
        response=post(RUNTIME_URL,headers={"Authorization":"Bearer "+token},
                      json={"task_id":TASK_ID},timeout=30)
    except requests.RequestException as exc:
        raise RuntimeError("EXACT_PRIVATE_VIDEO_DISPATCH_UNCERTAIN") from exc
    if response.status_code not in (200,202):
        raise RuntimeError("EXACT_PRIVATE_VIDEO_RUNTIME_HTTP_"+str(response.status_code))
    for attempt in range(12):
        if attempt: sleeper(10)
        current=_status(client,bucket)
        if current and current.get("status") in ACTIVE:
            return {"result":"START_"+current["status"],"stage":current.get("stage")}
        if current and current.get("status")=="FAILED":
            raise RuntimeError("EXACT_PRIVATE_VIDEO_FAILED_NEEDS_AGENT21:"+str(current.get("stage") or "unknown")+":"+str(current.get("error_code") or "unknown"))
    raise RuntimeError("EXACT_PRIVATE_VIDEO_START_NOT_PROVEN")

def main():
    client,bucket=client_from_env()
    result=start_exact(client,bucket,os.environ.get("PRIVATE_ASR_INTERNAL_TOKEN",""))
    print("PRIVATE_VIDEO_EXACT_TASK_"+result["result"]+" task="+TASK_ID+" stage="+str(result.get("stage") or "unknown"))
    return 0

if __name__=="__main__": raise SystemExit(main())
