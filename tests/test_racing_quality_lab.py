from racing_quality_lab import EvalCase, run_cases, summarize, evidence_map

def gate(source, caption):
    errors=[]
    allowed=set(source.get("allowed",[]))
    for token in source.get("protected_tokens",[]):
        if token in caption and token not in allowed:
            errors.append("unsupported:"+token)
    return errors

cases=[
 EvalCase("attack-fake-place","hallucination_block",{"allowed":[],"protected_tokens":["Barcelona"]},"Sieg in Barcelona",False),
 EvalCase("control-place","positive_control",{"allowed":["Barcelona"],"protected_tokens":["Barcelona"]},"Sieg in Barcelona",True),
 EvalCase("attack-fake-team","hallucination_block",{"allowed":[],"protected_tokens":["Phoenix-Werksteam"]},"für Phoenix-Werksteam",False),
 EvalCase("control-clean","positive_control",{"allowed":[],"protected_tokens":[]},"Sauberer belegter Post",True),
]
results=run_cases(cases,gate)
summary=summarize(results)
assert summary["failed"] == 0
assert summary["attack_block_rate"] == 1.0
assert summary["positive_control_rate"] == 1.0
ev=evidence_map(summary,["hallucination_block","positive_control"])
assert ev["release_ready"] is True
bad=evidence_map(summary,["hallucination_block","positive_control","runtime_e2e"])
assert bad["release_ready"] is False
print("RACING QUALITY LAB FOUNDATION: PASS")
