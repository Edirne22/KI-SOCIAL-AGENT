"""Trusted executor for validated Agent-21 repair contracts."""
from __future__ import annotations
import subprocess
from pathlib import Path
from scripts.guarded_development_agent import build_repair_record, validate_agent21_write_contract

def _target(root:Path, rel:str)->Path:
    root=root.resolve()
    target=root.joinpath(rel)
    cur=root
    for part in Path(rel).parts[:-1]:
        cur=cur/part
        if cur.exists() and cur.is_symlink(): raise ValueError("Symlink parent is forbidden")
    if target.exists() and target.is_symlink(): raise ValueError("Symlink target is forbidden")
    resolved_parent=target.parent.resolve()
    if root!=resolved_parent and root not in resolved_parent.parents: raise ValueError("Repair path escapes workspace")
    return target

def apply_changes(root:Path, contract:dict)->dict:
    auth=validate_agent21_write_contract(contract)
    written=[]
    for change in contract["changes"]:
        target=_target(root,change["path"])
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(change["content"],encoding="utf-8")
        written.append(change["path"])
    return {"status":"PATCHED","authorization":auth,"written":written}

def run_tests(root:Path, authorization:dict, timeout:int=120)->dict:
    results=[]
    for argv in authorization["test_argv"]:
        cp=subprocess.run(argv,cwd=root,shell=False,capture_output=True,text=True,timeout=timeout)
        results.append({"argv":argv,"returncode":cp.returncode,"stdout":cp.stdout[-4000:],"stderr":cp.stderr[-4000:]})
        if cp.returncode!=0: raise RuntimeError("Targeted Agent 21 test failed")
    return {"status":"TESTED","results":results}

def write_repair_log(root:Path, repair:dict)->dict:
    existing=[str(p.relative_to(root)).replace("\\","/") for p in root.joinpath("Claude-Instandhaltung").glob("*") if p.is_file()] if root.joinpath("Claude-Instandhaltung").exists() else []
    record=build_repair_record(repair,existing)
    target=_target(root,record["path"])
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open("x",encoding="utf-8") as fh: fh.write(record["content"])
    return {"status":"REPAIR_LOGGED","path":record["path"]}
