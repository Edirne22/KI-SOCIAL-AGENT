"""Guarded development and Agent-21 repair contracts.

Task text is data, never shell. Repository writes are permitted only after a
bounded path/branch/size validation and remain outside this validation module.
"""
from __future__ import annotations
import argparse
import json
import re
import shlex
from pathlib import Path

ALLOWED = {369: {"title":"Private Telegram album project intake","paths":["scripts/telegram_private_media.py","scripts/r2_media_warehouse.py","telegram_router.py","tests/test_telegram_private_media.py","tests/test_r2_media_warehouse.py"],"checks":["python -m unittest discover -s tests -p test_telegram_private_media.py -v","python -m unittest discover -s tests -p test_r2_media_warehouse.py -v"],"constraints":["Do not forward private album items to legacy vision or social pipelines","R2 immutable originals, readback SHA256 and compare-and-swap manifests","Album correlation by chat and media_group_id, never timestamp alone","No private files or secrets in GitHub artifacts or model prompts","No production deployment or automatic merge"]}}
AGENT21_ID="agent-21-instandhaltungsagent"
MAX_PATCH_BYTES=96*1024
FORBIDDEN_EXACT={"PROJECT_GUARDRAILS.md","MASTER-SNAPSHOT.md","CLAUDE.md","agents/11_system_restart_agent.md","agents/21_instandhaltungsagent.md","agents/AGENTS_INDEX.md","scripts/guarded_development_agent.py","infra/ai-central-tools/claude-only/opencode.jsonc","infra/ai-central-tools/claude-only/opencode-agent21-writer.jsonc"}
FORBIDDEN_PREFIXES=(".github/workflows/",".git/",".opencode/","secrets/",".env")
ALLOWED_PREFIXES=("agents/","scripts/","tests/","docs/","Claude-Instandhaltung/","infra/ai-central-dashboard/","infra/ai-central-tools/")
REPAIR_ID_RE=re.compile(r"^[A-Z0-9][A-Z0-9_-]{2,63}$")

def plan(issue:int)->dict:
    if issue not in ALLOWED: raise ValueError("Development issue is not allowlisted")
    spec=ALLOWED[issue]; basics=Path("docs/GUARDED_DEVELOPMENT_AGENT_BASICS.md")
    if not basics.is_file() or "Auftrag #369" not in basics.read_text(encoding="utf-8"): raise ValueError("Missing mandatory development-agent basics")
    missing=[path for path in spec["paths"] if not Path(path).is_file()]
    return {"schema":"GUARDED-DEVELOPMENT-PLAN-V1","issue":issue,**spec,"status":"BLOCKED_MISSING_SOURCE" if missing else "PLAN_ONLY_AWAITING_CODE_REVIEW","missing_prerequisites":missing,"mandatory_briefing":str(basics),"automatic_commit":False,"automatic_merge":False,"automatic_deploy":False}

def _safe_path(path:str)->bool:
    normalized=path.replace("\\","/").lstrip("/")
    return ".." not in normalized.split("/") and normalized not in FORBIDDEN_EXACT and not normalized.startswith(FORBIDDEN_PREFIXES) and normalized.startswith(ALLOWED_PREFIXES)

def validate_agent21_write_contract(contract:dict)->dict:
    if contract.get("schema")!="AGENT21-REPAIR-PATCH-V1": raise ValueError("Invalid Agent 21 repair schema")
    if contract.get("agent")!=AGENT21_ID: raise ValueError("Wrong repair agent")
    branch=str(contract.get("branch") or "")
    if not branch.startswith("repair/agent21-") or branch in {"main","master"}: raise ValueError("Agent 21 writes require a dedicated repair branch")
    machine=contract.get("machine"); stage=contract.get("stage")
    if not isinstance(machine,str) or not machine.strip(): raise ValueError("Machine is required")
    if not isinstance(stage,str) or not stage.strip(): raise ValueError("Stage is required")
    changes=contract.get("changes")
    if not isinstance(changes,list) or not changes: raise ValueError("At least one bounded change is required")
    total=0; checked=[]
    for change in changes:
        path=str(change.get("path") or ""); content=change.get("content")
        if not _safe_path(path): raise ValueError("Forbidden repair path: "+path)
        if not isinstance(content,str): raise ValueError("Repair content must be UTF-8 text")
        total+=len(content.encode("utf-8")); checked.append(path)
    if total>MAX_PATCH_BYTES: raise ValueError("Repair patch exceeds size limit")
    tests=contract.get("tests")
    if not isinstance(tests,list) or not tests: raise ValueError("At least one targeted test is required")
    forbidden_meta=set(";|&><$`\n\r"); test_argv=[]
    for command in tests:
        if not isinstance(command,str) or any(ch in command for ch in forbidden_meta): raise ValueError("Agent 21 test contains forbidden shell syntax")
        try: argv=shlex.split(command)
        except ValueError as exc: raise ValueError("Invalid Agent 21 test command") from exc
        if len(argv)<4 or argv[:3]!=["python","-m","unittest"]: raise ValueError("Agent 21 tests must use the unittest allowlist")
        test_argv.append(argv)
    return {"schema":"AGENT21-WRITE-AUTHORIZATION-V1","agent":AGENT21_ID,"branch":branch,"machine":machine.strip(),"stage":stage.strip(),"paths":checked,"bytes":total,"tests":tests,"test_argv":test_argv,"automatic_merge":False,"automatic_deploy":False,"status":"WRITE_CONTRACT_VALIDATED"}

def build_repair_record(repair:dict, existing_paths=())->dict:
    """Build an append-only repair report descriptor; never overwrites an old report."""
    rid=str(repair.get("repair_id") or "")
    if not REPAIR_ID_RE.fullmatch(rid): raise ValueError("Invalid Repair-ID")
    machine=str(repair.get("machine") or "").strip(); stage=str(repair.get("stage") or "").strip()
    if not machine or not stage: raise ValueError("Machine and stage are required")
    date=str(repair.get("date") or "")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}",date): raise ValueError("ISO date is required")
    path=f"Claude-Instandhaltung/{date}_REPAIR-{rid}.md"
    if path in set(existing_paths): raise FileExistsError("Repair report is immutable and already exists")
    root=str(repair.get("root_cause") or "").strip(); evidence=str(repair.get("evidence") or "").strip()
    if not root or not evidence: raise ValueError("Root cause and evidence are required")
    body=(f"# Repair {rid}\n\n- Agent: {AGENT21_ID}\n- Datum: {date}\n- Maschine / Tool: {machine}\n- Stage: {stage}\n- Root Cause: {root}\n- Nachweis: {evidence}\n- Endzustand: {repair.get('end_state','UNVERIFIED')}\n")
    return {"schema":"AGENT21-REPAIR-RECORD-V1","path":path,"content":body,"append_only":True,"status":"REPAIR_RECORD_READY"}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--issue",required=True,type=int); parser.add_argument("--output",default="guarded-development-plan.json"); args=parser.parse_args()
    result=plan(args.issue); Path(args.output).write_text(json.dumps(result,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"GUARDED_PLAN_PASS issue={args.issue} status={result['status']}")
if __name__=="__main__": main()
