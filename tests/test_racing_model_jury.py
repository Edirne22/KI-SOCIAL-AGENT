from racing_model_jury import evaluate_jury, combine_with_truth_gate

src={"title":"Can Öncü P6","summary":"0,365 Sekunden"}
supported={p:(lambda s,c:"SUPPORTED") for p in ("agnes","gemini","nvidia")}
j=evaluate_jury(src,"Can Öncü P6",supported)
assert j["consensus"]=="SUPPORTED"
assert combine_with_truth_gate([],j)["decision"]=="PASS"

# A unanimous model hallucination must NEVER overrule deterministic source truth.
assert combine_with_truth_gate(["Ort nicht in Quelle"],j)["decision"]=="BLOCK"

mixed={"agnes":lambda s,c:"SUPPORTED","gemini":lambda s,c:"UNSURE","nvidia":lambda s,c:"CONTRADICTED"}
j2=evaluate_jury(src,"claim",mixed)
assert j2["consensus"]=="DISAGREE"
assert combine_with_truth_gate([],j2)["decision"]=="REVIEW"

def boom(s,c): raise RuntimeError("provider down")
j3=evaluate_jury(src,"claim",{"agnes":boom,"gemini":lambda s,c:"SUPPORTED","nvidia":lambda s,c:"SUPPORTED"})
assert j3["consensus"]=="SUPPORTED"
assert any(v["verdict"]=="UNAVAILABLE" for v in j3["votes"])
print("RACING 3-MODEL JURY CONTRACT: PASS")
