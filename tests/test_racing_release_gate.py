from racing_release_gate import release_gate

core={"regression":"PASS","hallucination_attack":"PASS","positive_control":"PASS","ci":"PASS"}
assert release_gate(core,production_behavior_changed=False)["release_ready"]
assert not release_gate(core,production_behavior_changed=True)["release_ready"]
prod={**core,"runtime_e2e":"PASS"}
assert release_gate(prod,production_behavior_changed=True)["release_ready"]
jury={**prod,"provider_outage":"PASS","jury_advisory":"PASS"}
assert release_gate(jury,production_behavior_changed=True,provider_logic_changed=True)["release_ready"]
bad={**jury,"hallucination_attack":"FAIL"}
assert not release_gate(bad,production_behavior_changed=True,provider_logic_changed=True)["release_ready"]
print("RACING RELEASE GATE V1: PASS")
