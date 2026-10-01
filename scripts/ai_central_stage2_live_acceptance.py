"""One-shot synthetic, cost-gated, private Worker → R2 → GitHub → NVIDIA acceptance.

Runs only from an explicitly authorized deployment workflow, never from normal
PR/cron, no GitHub read/write permissions, no user-provided data or retries.
"""
from __future__ import annotations
import json
import os
import re
import time
import requests

BASE="https://edirne22-ai-central-dashboard.butupeli.workers.dev"
TOKEN=os.getenv("AI_DASHBOARD_TOKEN","")
GATEWAY=BASE+"/api"
TASK="Public synthetic QA only: In one sentence explain why an HTTP 000 cannot prove whether a Cloudflare container application has started. Label every hypothesis unverified."
def main():
    if len(TOKEN)<24: raise RuntimeError("DASHBOARD_SECRET_MISSING")
    auth={"Authorization":"Bearer "+TOKEN}
    # Positive and negative auth controls: never print response text.
    unauth=requests.get(GATEWAY+"/inbox",timeout=15)
    if unauth.status_code!=401:raise RuntimeError("UNAUTHENTICATED_ACCESS_NOT_BLOCKED")
    health=requests.get(GATEWAY+"/health",headers=auth,timeout=15)
    if health.status_code!=200 or health.json().get("truth")!="WORKER_AND_R2_BINDING_PRESENT":
        raise RuntimeError("WORKER_R2_HEALTH_NOT_VERIFIED")
    public=requests.get(BASE,timeout=15)
    if public.status_code!=200 or "NVIDIA-Team starten" not in public.text:
        raise RuntimeError("NEW_DASHBOARD_UI_NOT_DEPLOYED")
    print("LIVE_WORKER_AUTH_R2_AND_NEW_UI_VERIFIED",flush=True)
    inbox=requests.post(GATEWAY+"/inbox",headers={**auth,"Origin":BASE},
        json={"message":TASK},timeout=20)
    if inbox.status_code!=202:raise RuntimeError("R2_SYNTHETIC_DRAFT_REJECTED_HTTP_"+str(inbox.status_code))
    item=inbox.json()
    ident=item.get("id","")
    if not re.fullmatch(r"[A-Za-z0-9_-]{10,64}",ident):
        raise RuntimeError("INVALID_DRAFT_ID")
    day=item.get("created_at","")[:10]
    if not re.fullmatch(r"20[0-9]{2}-[0-9]{2}-[0-9]{2}",day):
        raise RuntimeError("INVALID_DRAFT_DATE")
    # Exactly one explicit team dispatch. NEVER retry ambiguous HTTP/network failure.
    print("SYNTHETIC_TASK_ID="+ident,flush=True)
    try:
        dispatch=requests.post(GATEWAY+"/dispatch",headers={**auth,"Origin":BASE},
            json={"id":ident,"date":day,"mode":"free-team"},timeout=25)
    except requests.RequestException:
        raise RuntimeError("DISPATCH_OUTCOME_UNCERTAIN_NO_RETRY")
    if dispatch.status_code!=202:
        raise RuntimeError("TEAM_DISPATCH_REJECTED_HTTP_"+str(dispatch.status_code))
    print("GITHUB_TEAM_DISPATCH_ACCEPTED_NOT_INFERENCE_PROOF",flush=True)
    deadline=time.monotonic()+270
    last=""
    while time.monotonic()<deadline:
        response=requests.get(GATEWAY+"/task",headers=auth,params={"id":ident},timeout=20)
        if response.status_code==200:
            result=response.json()
            if result.get("id")!=ident:raise RuntimeError("CROSS_TASK_STATUS")
            status=result.get("status","")
            if status!=last:
                print("REAL_TASK_STATE="+str(status)[:48],flush=True);last=status
            if status in ("FAILED","BLOCKED_FREE_TIER"):
                raise RuntimeError("REAL_TEAM_LIFECYCLE_"+status)
            if result.get("truth")=="R2_ARCHIVED_REPORT" and status=="PENDING_REVIEW":
                roles=result.get("roles",[])
                statuses={x.get("role"):x.get("status") for x in roles if isinstance(x,dict)}
                print("LIVE_MODEL_ROLES="+json.dumps(statuses,sort_keys=True),flush=True)
                if statuses.get("research")!="ANSWER" or statuses.get("diagnosis")!="ANSWER":
                    raise RuntimeError("NVIDIA_PRIMARY_ROLES_NOT_PROVEN")
                if statuses.get("challenge") not in ("ANSWER","UNAVAILABLE"):
                    raise RuntimeError("CHALLENGE_STATUS_MISSING_OR_INVALID")
                if statuses["challenge"]=="UNAVAILABLE":
                    print("LIVE_TEAM_PARTIAL: NVIDIA_2_OF_2; CHALLENGE_UNAVAILABLE",flush=True)
                else:
                    print("LIVE_TEAM_ALL_THREE_ROLES_ANSWERED",flush=True)
                notify_telegram(ident,statuses)
                print("LIVE_R2_REPORT_VERIFIED_RUN="+str(result.get("run_id",""))[:18],flush=True)
                return
        time.sleep(10)
    raise RuntimeError("LIVE_ACCEPTANCE_TIMEOUT_NO_DOUBLE_DISPATCH")

def notify_telegram(ident,statuses):
    token=os.getenv("TELEGRAM_BOT_TOKEN","")
    chat=os.getenv("TELEGRAM_CHAT_ID","")
    if not token or not chat:
        print("TELEGRAM_OUTBOUND_NOT_TESTED_MISSING_SECRETS",flush=True)
        return
    message=("KI-Zentrale LIVE-Abnahme: Nemotron und Kimi haben geantwortet. "
             "Gegenprüfung: "+str(statuses.get("challenge"))+". "
             "Telegram-Eingang jetzt mit /zentrale ergebnis "+ident+" prüfbar.")
    # Send only public synthetic result ID and role states; never private response text.
    response=requests.post("https://api.telegram.org/bot"+token+"/sendMessage",
        data={"chat_id":chat,"text":message},timeout=15)
    if response.status_code!=200 or response.json().get("ok") is not True:
        print("TELEGRAM_OUTBOUND_NOT_VERIFIED_HTTP_"+str(response.status_code),flush=True)
        return
    print("TELEGRAM_OUTBOUND_DELIVERY_ACCEPTED",flush=True)

if __name__=="__main__":
    main()
