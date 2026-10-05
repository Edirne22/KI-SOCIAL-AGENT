"""Validated recovery handoff shared by Agent 21 and Agent 11.

This module describes *intent and state only*. It never accepts arbitrary shell
commands, URLs, secrets or executable code from a repair agent.
"""
from __future__ import annotations
import re

ID=re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{5,95}$")
MACHINES={"private-media-container","private-asr-container","dashboard-worker","opencode-container"}
ACTIONS={"RESUME","RESTART_STAGE","RESTART_JOB"}
TERMINAL={"COMPLETED","CANCELLED"}
ACTIVE={"ACCEPTED","RUNNING"}

def validate_handoff(value:dict)->dict:
    required={"schema","repair_id","job_id","stage_id","machine","checkpoint","restart_required","requested_action"}
    if not isinstance(value,dict) or set(value)!=required:
        raise ValueError("RECOVERY_HANDOFF_SCHEMA_INVALID")
    if value["schema"]!="AGENT21-TO-AGENT11-RECOVERY-V1":
        raise ValueError("RECOVERY_HANDOFF_VERSION_INVALID")
    for key in ("repair_id","job_id","stage_id","checkpoint"):
        if not isinstance(value[key],str) or not ID.fullmatch(value[key]):
            raise ValueError("RECOVERY_HANDOFF_ID_INVALID:"+key)
    if value["machine"] not in MACHINES:
        raise ValueError("RECOVERY_MACHINE_NOT_ALLOWED")
    if value["restart_required"] is not True:
        raise ValueError("RECOVERY_RESTART_NOT_AUTHORIZED")
    if value["requested_action"] not in ACTIONS:
        raise ValueError("RECOVERY_ACTION_NOT_ALLOWED")
    return dict(value)

def recovery_decision(handoff:dict,current:dict)->dict:
    h=validate_handoff(handoff)
    if not isinstance(current,dict) or set(current)!={"job_id","stage_id","checkpoint","status"}:
        raise ValueError("RECOVERY_CURRENT_STATE_INVALID")
    if current["job_id"]!=h["job_id"] or current["stage_id"]!=h["stage_id"]:
        raise ValueError("RECOVERY_JOB_STAGE_MISMATCH")
    status=current["status"]
    if status in TERMINAL:
        return {"decision":"NO_RESTART","reason":"TERMINAL_JOB"}
    if status in ACTIVE:
        return {"decision":"OBSERVE_ONLY","reason":"JOB_ALREADY_ACTIVE"}
    if current["checkpoint"]!=h["checkpoint"]:
        raise ValueError("RECOVERY_CHECKPOINT_MISMATCH")
    return {"decision":h["requested_action"],"reason":"VALIDATED_RECOVERY"}

def healthy_after_restart(samples:list[dict],minimum_heartbeats:int=2)->bool:
    """Require readiness plus consecutive matching RUNNING heartbeats."""
    if not isinstance(samples,list) or minimum_heartbeats<2:
        return False
    good=0
    for sample in samples:
        if not isinstance(sample,dict):
            good=0; continue
        if sample.get("container_ready") is True and sample.get("machine_ready") is True and sample.get("job_status")=="RUNNING":
            good+=1
            if good>=minimum_heartbeats:return True
        else:good=0
    return False
