"""Source-blind behavior validation: validator receives contract + observable result, never source internals."""
from dataclasses import dataclass

@dataclass(frozen=True)
class BehaviorClause:
    id: str
    expected: str  # PASS or BLOCK

def validate_behavior(clauses, observations):
    report=[]
    for c in clauses:
        actual=observations.get(c.id)
        status="PASS" if actual==c.expected else ("BLOCKED" if actual is None else "FAIL")
        report.append({"id":c.id,"expected":c.expected,"observed":actual,"status":status})
    return {"schema":"RACING-BEHAVIOR-V1","clauses":report,
            "passed":bool(report) and all(x["status"]=="PASS" for x in report)}
