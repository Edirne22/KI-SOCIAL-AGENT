from racing_quality_lab import EvalCase,run_cases,summarize,evidence_map
from racing_quality_lab_production_adapter import production_truth_errors

def item(title,summary,series="WorldSBK"):
    return {"title":title,"summary":summary,"series":series,"source_series":series,"trusted_series":series,"series_locked":True,"url":"https://synthetic.invalid/eval"}

cases=[
 EvalCase("session-attack","hallucination_attack",item("WorldSBK Superpole Race: Lecuona wins","Lecuona wins Superpole Race"),"Iker Lecuona gewinnt die Superpole.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife",False),
 EvalCase("claim-attack","hallucination_attack",item("Strong signal about 2027 WorldSBK","Move is not officially confirmed"),"Der Wechsel 2027 steht fest.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife",False),
 EvalCase("place-attack","hallucination_attack",item("WorldSBK: Lecuona wins","Lecuona wins the race"),"Iker Lecuona gewinnt in Barcelona.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife",False),
 EvalCase("language-attack","hallucination_attack",item("WorldSBK: Lecuona wins","Lecuona wins the race"),"Iker Lecuona gewinnt.\n\nSo kurz vor dem Renne war das stark.\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife",False),
 EvalCase("place-control","positive_control",item("WorldSBK Barcelona: Lecuona wins","Lecuona wins in Barcelona"),"Iker Lecuona gewinnt in Barcelona.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife",True),
]
s=summarize(run_cases(cases,production_truth_errors))
assert s["failed"]==0,s
assert s["attack_block_rate"]==1.0
assert s["positive_control_rate"]==1.0
ev=evidence_map(s,["hallucination_attack","positive_control"])
assert ev["release_ready"]
print("QUALITY LAB -> PRODUCTION TRUTH GATES: 5/5 PASS")
