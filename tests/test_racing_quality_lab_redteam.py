"""Adversarial attack against the Quality Lab itself."""
from racing_blind_validator import BehaviorClause, validate_behavior
from racing_mutation_engine import DEFAULT_MUTATIONS, apply_mutation
from racing_model_jury import evaluate_jury, combine_with_truth_gate
from racing_release_gate import release_gate

passed=0
def ok(cond,name):
    global passed
    assert cond, name
    passed+=1

# 1-6 mutation attacks must actually alter protected facts.
base="WorldSSP Superpole Race in Cremona für Ducati: 0,365 Sekunden, vor dem Rennen."
for m in DEFAULT_MUTATIONS:
    attacked=apply_mutation(base,m)
    ok(attacked != base and m.replacement in attacked,"mutation:"+m.id)

# 7 chained attack: several lies in one caption.
attacked=base
for m in (DEFAULT_MUTATIONS[0],DEFAULT_MUTATIONS[1],DEFAULT_MUTATIONS[2],DEFAULT_MUTATIONS[3]):
    attacked=apply_mutation(attacked,m)
ok("Superpole Race" not in attacked and "Barcelona" in attacked and "Phoenix-Werksteam" in attacked and "9,999" in attacked,
   "multi-fact mutation")

# 8 mutation must fail closed if fixture drift makes the attack impossible.
try:
    apply_mutation("unrelated fixture",DEFAULT_MUTATIONS[0])
    ok(False,"missing mutation needle")
except ValueError:
    ok(True,"missing mutation needle")

# 9-11 blind validator: no evidence, false PASS and clean control.
clauses=[BehaviorClause("fake","BLOCK"),BehaviorClause("clean","PASS")]
ok(not validate_behavior(clauses,{"clean":"PASS"})["passed"],"blind missing evidence")
ok(not validate_behavior(clauses,{"fake":"PASS","clean":"PASS"})["passed"],"blind false pass")
ok(validate_behavior(clauses,{"fake":"BLOCK","clean":"PASS"})["passed"],"blind positive control")

# 12 unanimous hallucinating jury cannot erase deterministic truth failure.
yes={p:(lambda s,c:"SUPPORTED") for p in ("agnes","gemini","nvidia")}
jury=evaluate_jury({"title":"Cremona"},"Barcelona",yes)
ok(combine_with_truth_gate(["Ort nicht in Quelle"],jury)["decision"]=="BLOCK","jury cannot override truth")

# 13 split jury requires review.
mixed={"agnes":lambda s,c:"SUPPORTED","gemini":lambda s,c:"UNSURE","nvidia":lambda s,c:"CONTRADICTED"}
ok(combine_with_truth_gate([],evaluate_jury({}, "x", mixed))["decision"]=="REVIEW","jury disagreement")

# 14 provider outage is visible, not silently converted to a vote.
def down(s,c): raise RuntimeError("down")
j=evaluate_jury({}, "x", {"agnes":down,"gemini":lambda s,c:"SUPPORTED","nvidia":lambda s,c:"SUPPORTED"})
ok(any(v["verdict"]=="UNAVAILABLE" for v in j["votes"]),"provider outage visible")

# 15-17 release gate fail-closed and positive control.
core={"regression":"PASS","hallucination_attack":"PASS","positive_control":"PASS","ci":"PASS"}
ok(not release_gate(core,production_behavior_changed=True)["release_ready"],"runtime evidence mandatory")
ok(not release_gate({**core,"runtime_e2e":"PASS","hallucination_attack":"FAIL"},production_behavior_changed=True)["release_ready"],"red team failure blocks")
ok(release_gate({**core,"runtime_e2e":"PASS"},production_behavior_changed=True)["release_ready"],"release positive control")

print(f"QUALITY LAB RED TEAM: {passed}/17 PASS")
