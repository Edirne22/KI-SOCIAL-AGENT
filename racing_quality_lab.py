"""Deterministic evaluation + evidence-map foundation for Racing quality releases."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable, Iterable
import json, time

@dataclass(frozen=True)
class EvalCase:
    id: str
    category: str
    source: dict
    caption: str
    expect_pass: bool

@dataclass
class EvalResult:
    id: str
    category: str
    expected: bool
    actual: bool
    passed: bool
    duration_ms: int
    errors: list[str]

def run_cases(cases: Iterable[EvalCase], gate: Callable[[dict,str], list[str]]) -> list[EvalResult]:
    out=[]
    for case in cases:
        started=time.perf_counter()
        errors=list(gate(case.source, case.caption) or [])
        actual=not errors
        out.append(EvalResult(case.id,case.category,case.expect_pass,actual,
                              actual==case.expect_pass,
                              round((time.perf_counter()-started)*1000),errors))
    return out

def summarize(results: Iterable[EvalResult]) -> dict:
    rows=list(results); total=len(rows); passed=sum(r.passed for r in rows)
    protected=[r for r in rows if not r.expected]
    controls=[r for r in rows if r.expected]
    return {
        "schema":"RACING-EVAL-V1","total":total,"passed":passed,"failed":total-passed,
        "attack_block_rate": (sum(r.passed for r in protected)/len(protected) if protected else 1.0),
        "positive_control_rate": (sum(r.passed for r in controls)/len(controls) if controls else 1.0),
        "results":[asdict(r) for r in rows],
    }

def evidence_map(summary: dict, required: Iterable[str]) -> dict:
    by_cat={}
    for r in summary["results"]:
        by_cat.setdefault(r["category"],[]).append(r)
    clauses=[]
    for category in required:
        rows=by_cat.get(category,[])
        clauses.append({"requirement":category,
                        "status":"PASS" if rows and all(r["passed"] for r in rows) else "FAIL",
                        "evidence":[r["id"] for r in rows]})
    return {"schema":"RACING-EVIDENCE-MAP-V1","clauses":clauses,
            "release_ready":bool(clauses) and all(c["status"]=="PASS" for c in clauses)}

def dump_report(summary: dict, evidence: dict, path: str) -> None:
    with open(path,"w",encoding="utf-8") as fh:
        json.dump({"evaluation":summary,"evidence_map":evidence},fh,ensure_ascii=False,indent=2)
