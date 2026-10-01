"""Task-specific, fail-closed model and skill routing.

A requested provider/model lock is a contract: never silently fall back.
Catalog entries represent candidates until real requests and cost checks pass.
"""
from __future__ import annotations
import json
from pathlib import Path

REGISTRY = Path(__file__).resolve().parents[1] / "config/ai_central_capabilities.json"
class RoutingError(ValueError): pass

def load_registry(path=REGISTRY):
    result=json.loads(Path(path).read_text(encoding="utf8"))
    if result.get("schema")!="AI-CENTRAL-CAPABILITIES-V1":
        raise RoutingError("unsupported registry")
    return result

def choose(task_type, *, forced_provider=None, forced_model=None, available=None, registry=None):
    registry=registry or load_registry()
    available=available or {}
    tasks=registry["tasks"]
    if task_type not in tasks:raise RoutingError("unsupported task")
    task=tasks[task_type]
    if forced_provider:
        # "Claude" locks the MODEL FAMILY: direct Anthropic and the exact
        # Anthropic Claude route via OpenRouter are both permitted transports.
        # No non-Claude substitution, including Gemini, is allowed.
        names=["claude","claude_openrouter"] if forced_provider.lower()=="claude" else [forced_provider.lower()]
        if not set(names).intersection(task["providers"]):
            raise RoutingError("requested provider not permitted for task; no fallback")
    else:names=task["providers"]
    for provider in names:
        candidate=registry["providers"].get(provider)
        if not candidate:continue
        if provider not in task["providers"]:continue
        if forced_model:
            if not forced_provider:
                raise RoutingError("forced model requires forced provider")
            if forced_model not in candidate.get("models",[]):
                raise RoutingError("model not allowlisted; no fallback")
            model=forced_model
        else:
            model=(task.get("model_by_provider") or {}).get(provider)
            if not model:continue
        # This must be a measured probe result, not just a catalog listing.
        if available.get(provider,{}).get(model)!="INFERENCE_OK":
            # Continue only within the locked Claude family, never into Gemini.
            continue
        if candidate["secret"]=="":
            raise RoutingError("invalid provider secret binding")
        return {"task":task_type,"provider":provider,"model":model,"secret_name":candidate["secret"],
                "no_fallback":bool(forced_provider),"requires_user_approval":task.get("approval",True)}
    if forced_provider:raise RoutingError("requested provider/model not live-verified; no fallback")
    raise RoutingError("no live-verified permitted provider; do not pretend task completed")

def document_skill(output_format, requested_provider=None):
    registry=load_registry()
    kind=output_format.lower().lstrip(".")
    skill=registry["document_skills"].get(kind)
    if not skill:raise RoutingError("unsupported document format")
    if requested_provider and requested_provider.lower()=="claude":
        # Formatting library does not secretly invoke another AI model.
        # Separate Claude review/edit must pass choose('document_edit',forced_provider='claude',...).
        return {"skill":skill,"ai_provider":"claude","requires_verified_anthropic_key":True}
    return {"skill":skill,"ai_provider":requested_provider,"requires_verified_anthropic_key":False}
