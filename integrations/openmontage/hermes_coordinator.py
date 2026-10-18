"""Fail-closed Hermes-compatible coordination boundary for research-only jobs.

No runtime installation, external execution, production or publication here.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Callable

ROLES = ("research_discovery", "source_reader", "nemotron_analyst", "fact_checker", "handoff")
REQUIRED = {
    "research_discovery": ("candidates",),
    "source_reader": ("documents",),
    "nemotron_analyst": ("claims",),
    "fact_checker": ("verified_claims",),
    "handoff": ("report",),
}

@dataclass(frozen=True)
class Result:
    role: str
    verdict: str
    data: dict
    reason: str = ""

def run_research(topic: str, workers: dict[str, Callable], *, max_retries: int = 1) -> dict:
    """Dispatch strict dependency chain, stop at first unfulfilled contract."""
    if max_retries < 0 or max_retries > 2:
        raise ValueError("max_retries must be 0..2")
    if not topic.strip():
        raise ValueError("topic required")
    state = {"topic": topic, "research_only": True, "production_started": False,
             "publication_authorized": False, "history": [], "status": "BLOCKED"}
    for role in ROLES:
        worker = workers.get(role)
        if worker is None:
            state["history"].append(asdict(Result(role, "BLOCK", {}, "WORKER_MISSING")))
            return state
        for attempt in range(max_retries + 1):
            try:
                output = worker(dict(state))
                if not isinstance(output, dict):
                    raise ValueError("INVALID_WORKER_OUTPUT")
                missing = [field for field in REQUIRED[role] if not output.get(field)]
                if role == "source_reader":
                    documents = output.get("documents") or []
                    if not all(isinstance(d, dict) and d.get("url") and d.get("text") for d in documents):
                        missing.append("DOCUMENT_PROVENANCE")
                if role == "nemotron_analyst":
                    claims = output.get("claims") or []
                    if not all(isinstance(c, dict) and c.get("source_url") and c.get("claim") for c in claims):
                        missing.append("CLAIM_PROVENANCE")
                if role == "fact_checker":
                    verified = output.get("verified_claims") or []
                    if not all(isinstance(c, dict) and c.get("source_url") and
                               c.get("evidence_excerpt") for c in verified):
                        missing.append("CLAIM_EVIDENCE")
                if missing:
                    raise ValueError("MISSING_" + "_".join(missing))
                state[role] = output
                state["history"].append(asdict(Result(role, "PASS", {"count": len(output)}, "")))
                break
            except Exception as exc:
                verdict = "RETRY" if attempt < max_retries else "BLOCK"
                state["history"].append(asdict(Result(role, verdict, {}, type(exc).__name__ + ": " + str(exc)[:160])))
                if verdict == "BLOCK":
                    return state
    state["status"] = "RESEARCH_READY"
    return state
