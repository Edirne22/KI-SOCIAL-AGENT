"""Advisory three-model jury contract. Never overrides deterministic truth gates."""
from dataclasses import dataclass
from typing import Callable

@dataclass(frozen=True)
class JuryVote:
    provider: str
    verdict: str  # SUPPORTED / UNSURE / CONTRADICTED / UNAVAILABLE
    detail: str=""

def evaluate_jury(source_packet: dict, claim: str, voters: dict[str,Callable]) -> dict:
    votes=[]
    for provider in ("agnes","gemini","nvidia"):
        fn=voters.get(provider)
        if fn is None:
            votes.append(JuryVote(provider,"UNAVAILABLE","no voter"))
            continue
        try:
            verdict=str(fn(source_packet,claim)).upper()
        except Exception as exc:
            votes.append(JuryVote(provider,"UNAVAILABLE",type(exc).__name__))
            continue
        if verdict not in {"SUPPORTED","UNSURE","CONTRADICTED"}:
            verdict="UNSURE"
        votes.append(JuryVote(provider,verdict))
    available=[v for v in votes if v.verdict!="UNAVAILABLE"]
    verdicts={v.verdict for v in available}
    consensus=(available[0].verdict if len(available)>=2 and len(verdicts)==1 else "DISAGREE")
    return {"schema":"RACING-JURY-V1","advisory":True,"consensus":consensus,
            "needs_human_or_semantic_review": consensus!="SUPPORTED",
            "votes":[v.__dict__ for v in votes]}

def combine_with_truth_gate(deterministic_errors: list[str], jury: dict) -> dict:
    # Non-negotiable: model votes can add caution, never erase deterministic evidence.
    if deterministic_errors:
        return {"decision":"BLOCK","reason":"DETERMINISTIC_TRUTH_GATE","jury":jury}
    return {"decision":"PASS" if jury.get("consensus")=="SUPPORTED" else "REVIEW",
            "reason":"JURY_ADVISORY","jury":jury}
