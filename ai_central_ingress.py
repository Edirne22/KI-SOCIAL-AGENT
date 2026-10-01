"""One allowlisted job intake for Telegram and future authenticated web gateway.

Never interpret arbitrary chat text as workflow/code instructions. The only
currently runnable task is the reviewed OpenChatCut diagnostic in Git.
"""
from __future__ import annotations
import re
from typing import Callable
import requests

REPO="Edirne22/KI-SOCIAL-AGENT"
WORKFLOW="cloud-ai-central.yml"
SCHEMA="AI-CENTRAL-INGRESS-V1"
TASKS={"openchatcut":"openchatcut-stability"}
STATUS_URL="https://api.github.com/repos/"+REPO+"/actions/workflows/"+WORKFLOW+"/runs"
DISPATCH_URL="https://api.github.com/repos/"+REPO+"/actions/workflows/"+WORKFLOW+"/dispatches"
COMMAND=re.compile(r"^/?ki(?:\s+(status|openchatcut))?\s*$",re.I)
def parse(text: str):
    if not isinstance(text,str) or len(text)>128:return None
    m=COMMAND.fullmatch(text.strip())
    if not m:return None
    return {"schema":SCHEMA,"action":(m.group(1) or "help").lower()}
def handle(parsed:dict,*,token:str,transport:Callable=requests.get,dispatch:Callable=requests.post):
    if not isinstance(parsed,dict) or parsed.get("schema")!=SCHEMA:
        raise ValueError("untrusted ingress")
    action=parsed.get("action")
    if action=="help":
        return "KI-Zentrale: /ki status zeigt den letzten GitHub-Lauf; /ki openchatcut startet nur die freigegebene Diagnose."
    if not token:raise RuntimeError("GitHub workflow credential unavailable")
    headers={"Authorization":"Bearer "+token,"Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
    if action=="status":
        r=transport(STATUS_URL,headers=headers,params={"per_page":1,"branch":"main"},timeout=12)
        if r.status_code!=200:raise RuntimeError("GitHub status request failed: HTTP "+str(r.status_code))
        runs=r.json().get("workflow_runs",[])
        if not runs:return "KI-Zentrale: noch kein Lauf auf main."
        run=runs[0]
        if not isinstance(run,dict) or run.get("html_url","").split("/")[2:3]!=["github.com"]:
            raise ValueError("unexpected GitHub status response")
        return "KI-Zentrale: "+str(run.get("status","unknown"))+" / "+str(run.get("conclusion") or "läuft")+"\n"+run["html_url"]
    if action in TASKS:
        r=dispatch(DISPATCH_URL,headers=headers,
            json={"ref":"main","inputs":{"task":TASKS[action]}},timeout=12)
        if r.status_code!=204:
            raise RuntimeError("Workflow dispatch failed: HTTP "+str(r.status_code))
        return "KI-Zentrale: OpenChatCut-Diagnose bei GitHub angefordert. Ergebnis folgt im gemeinsamen R2-Archiv. Status: /ki status"
    raise ValueError("unsupported action")
