import json
import racing_semantic_qm as qm

valid={
 "contract_version":"SOURCE-FACT-CONTRACT-V1",
 "coverage_complete":True,
 "claims":[{"claim":"Can Öncü wird Sechster","claim_type":"FACT","status":"SUPPORTED","source_evidence":[{"source_field":"summary","quote":"Can Öncü wird Sechster"}]}],
 "german_ok":True,"style_ok":True,"repair_reasons":[]
}
raw=json.dumps(valid,ensure_ascii=False)

assert qm._clean_json(raw)==valid
assert qm._clean_json("~~~".replace("~","`")+"json\n"+raw+"\n"+"~~~".replace("~","`"))==valid
assert qm._clean_json("Hier ist die Prüfung:\n"+raw+"\nEnde.")==valid

for broken in ('kein json','{"contract_version":'):
 try: qm._clean_json(broken)
 except json.JSONDecodeError: pass
 else: raise AssertionError("broken JSON accepted")

item={"series":"WorldSSP","title":"Cremona Superpole","summary":"Can Öncü wird Sechster","url":"https://example.test/story"}
bad=dict(valid);bad["claims"]=[{"claim":"Can Öncü gewinnt","claim_type":"FACT","status":"SUPPORTED","source_evidence":[{"source_field":"summary","quote":"gewinnt"}]}]
try: qm._validate_contract(item,bad)
except ValueError: pass
else: raise AssertionError("unsupported evidence accepted")

print("TEST – Semantic QM JSON Recovery: PASS")
