"""Fail-closed release gate for Racing Quality Lab evidence."""
REQUIRED_CORE=("regression","hallucination_attack","positive_control","ci")

def release_gate(evidence: dict, *, production_behavior_changed: bool, provider_logic_changed: bool=False):
    required=list(REQUIRED_CORE)
    if production_behavior_changed:
        required.append("runtime_e2e")
    if provider_logic_changed:
        required.extend(["provider_outage","jury_advisory"])
    missing=[]; failed=[]
    for key in required:
        status=evidence.get(key)
        if status is None: missing.append(key)
        elif status!="PASS": failed.append(key)
    return {"schema":"RACING-RELEASE-GATE-V1","required":required,"missing":missing,"failed":failed,
            "release_ready":not missing and not failed}
