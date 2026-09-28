"""Red-team mutations routed through real production Racing truth gates."""
from racing_mutation_engine import Mutation,apply_mutation
from racing_quality_lab_production_adapter import production_truth_errors

def item(title,summary,series="WorldSBK"):
    return {"title":title,"summary":summary,"series":series,"source_series":series,"trusted_series":series,"series_locked":True,"url":"https://synthetic.invalid/redteam"}

def blocked(src,caption):
    return bool(production_truth_errors(src,caption))

passed=0
def ok(cond,label):
    global passed
    assert cond,label
    passed+=1

# Controlled base with source-backed facts.
src=item("WorldSBK Superpole Race in Cremona: Iker Lecuona wins for Ducati",
         "Iker Lecuona wins the Superpole Race in Cremona for Ducati.")
base="Iker Lecuona gewinnt das Superpole Race in Cremona für Ducati.\n\nEin starkes Ergebnis im WorldSBK-Wochenende.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife"

attacks=(
 Mutation("session","session","Superpole Race","Superpole"),
 Mutation("place","place","Cremona","Barcelona"),
 Mutation("team","team","Ducati","Phoenix-Werksteam"),
)
for m in attacks:
    ok(blocked(src,apply_mutation(base,m)),"production missed "+m.id)

# Multi-fact attack: session + place + team are all falsified at once.
multi=base
for m in attacks:
    multi=apply_mutation(multi,m)
errs=production_truth_errors(src,multi)
ok(bool(errs),"multi-fact attack passed")
ok(any("Session widerspricht Quelle" in e for e in errs),"multi session not identified")
ok(any("Ort nicht in Quelle" in e for e in errs),"multi place not identified")
ok(any("Team/Hersteller nicht in Quelle" in e for e in errs),"multi team not identified")

# Claim-strength attack.
rumor=item("Strong signal about Morbidelli 2027 WorldSBK future",
           "A move is possible but not officially confirmed.")
ok(blocked(rumor,"Morbidelli wechselt 2027 in die WorldSBK.\n\nDer Wechsel steht fest.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife"),"rumor upgrade passed")

# Human-writing attack.
ok(blocked(src,"Iker Lecuona gewinnt.\n\nSo kurz vor dem Renne war das stark.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife"),"bad German passed")

# Positive controls: exact supported facts and preserved uncertainty.
ok(not blocked(src,base),"supported source facts overblocked")
ok(not blocked(rumor,"Morbidelli könnte 2027 in die WorldSBK wechseln.\n\nDer Wechsel ist noch nicht bestätigt.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife"),"uncertainty overblocked")

# Rider/name attacks through the full production whitelist (same truth basis used by Racing).
import importlib
import motogp_content_agency_v2 as agency
import racing_v855_hardening as hard
importlib.reload(agency); importlib.reload(hard).install(agency)

rider_src=item("WorldSSP: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP.","WorldSSP")
rider_good="Can Öncü wird Sechster.\n\nEin starkes Ergebnis.\n\nWie seht ihr das?\n\n#WorldSSP #MotorradRacing #BuelentsBikeLife"
rider_fake="Can Öncü wird Sechster.\n\nToprak Razgatlıoğlu fährt direkt hinter ihm ins Ziel.\n\nWie seht ihr das?\n\n#WorldSSP #MotorradRacing #BuelentsBikeLife"
good_errs=agency.fact_whitelist_errors(rider_src,rider_good)
fake_errs=agency.fact_whitelist_errors(rider_src,rider_fake)
ok(not any("Fahrer nicht in Quelle" in e for e in good_errs),"Can Oncu -> Can Öncü alias overblocked")
ok(any("Fahrer nicht in Quelle" in e for e in fake_errs),"invented Toprak rider passed")

print(f"PRODUCTION-GATE RED TEAM: {passed}/12 PASS")
