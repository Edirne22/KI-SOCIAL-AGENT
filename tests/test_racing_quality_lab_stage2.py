from racing_blind_validator import BehaviorClause, validate_behavior
from racing_mutation_engine import DEFAULT_MUTATIONS, apply_mutation

# Source-blind validator sees only the contract and observable PASS/BLOCK result.
clauses=[BehaviorClause("fake-place","BLOCK"),BehaviorClause("clean-control","PASS")]
assert validate_behavior(clauses,{"fake-place":"BLOCK","clean-control":"PASS"})["passed"]
assert not validate_behavior(clauses,{"fake-place":"PASS","clean-control":"PASS"})["passed"]
assert not validate_behavior(clauses,{"clean-control":"PASS"})["passed"]

base="WorldSSP Superpole Race in Cremona für Ducati: 0,365 Sekunden, vor dem Rennen."
seen=set()
for m in DEFAULT_MUTATIONS:
    changed=apply_mutation(base,m)
    assert changed != base
    assert m.replacement in changed
    seen.add(m.kind)
assert seen == {"session","place","team","number","series","language"}

try:
    apply_mutation("clean",DEFAULT_MUTATIONS[0])
    raise AssertionError("missing needle must fail closed")
except ValueError:
    pass
print("RACING BLIND VALIDATOR + MUTATION ENGINE: PASS")
