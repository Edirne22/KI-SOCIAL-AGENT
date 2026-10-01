"""Versioned read-only dashboard view from private cloud AI Central task reports.

Both Telegram and future authenticated web dashboard share the same task and run
IDs. This module does not expose credentials, model raw payloads or approval APIs.
"""
from __future__ import annotations
import re

SCHEMA="AI-CENTRAL-DASHBOARD-V1"
GOOD_STATUSES=frozenset({"PENDING_REVIEW","APPROVED","REJECTED"})
def view_report(report:dict):
    if not isinstance(report,dict) or report.get("schema")!="CLOUD-AI-CENTRAL-V1":
        raise ValueError("unexpected report schema")
    run=str(report.get("run_id",""))
    task=str(report.get("task_id",""))
    if not re.fullmatch(r"[0-9]{1,18}",run) or not re.fullmatch(r"[a-f0-9]{32}",task):
        raise ValueError("unsafe report identity")
    status=report.get("status")
    if status not in GOOD_STATUSES:
        raise ValueError("unknown status")
    roles=[]
    for role in report.get("results",[]):
        if not isinstance(role,dict):raise ValueError("malformed role")
        roles.append({"role":str(role.get("role",""))[:48],
            "status":str(role.get("status",""))[:32],
            "provider_count":len(role.get("attempts",[]))})
    if len(roles)>10:raise ValueError("excessive roles")
    return {"schema":SCHEMA,"task_id":task,"run_id":run,
        "status":status,"title":str(report.get("task",{}).get("title",""))[:120],
        "roles":roles,"github_url":"https://github.com/Edirne22/KI-SOCIAL-AGENT/actions/runs/"+run,
        "approval_required":bool(report.get("requires_human_approval",True))}
