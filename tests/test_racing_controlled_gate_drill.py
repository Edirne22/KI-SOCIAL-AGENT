"""Permanent controlled E2E regression drill for the production Racing QM chain.

All inputs are synthetic/controlled fixtures based on known Racing failure classes.
No network, Telegram, media upload or publishing is performed.
"""
import motogp_quality_manager as racing_qm
import racing_final_guard as final_guard
import racing_semantic_qm as semantic
from chief_quality_manager import human_text_review
from racing_event_contract import session_errors
from racing_source_claim_guard import claim_strength_errors

TAGS={"WorldSBK":"#WorldSBK","WorldSSP":"#WorldSSP","MotoGP":"#MotoGP"}
def check(c,m):
    if not c: raise AssertionError(m)
def base(title,summary,series="WorldSBK",url="https://synthetic.invalid/drill"):
    return {"title":title,"summary":summary,"series":series,"source_series":series,"trusted_series":series,"series_locked":True,"url":url}
def post(series,body,q="Wie seht ihr das?"):
    return body+"\n\n"+q+"\n\n"+TAGS[series]+" #MotorradRacing #RacingDeutschland #BuelentsBikeLife"
def expect_hard_block(item,caption,label):
    rq,rr=racing_qm.review(item,caption)
    fg,fr=final_guard.review(item,caption)
    sr=semantic.review_detailed(item,caption)
    check(not rq,(label,"Racing-QM unexpectedly PASS",rr))
    check(not fg,(label,"Final-Guard unexpectedly PASS",fr))
    check(not sr["hard_ok"] and not sr["technical_error"],(label,"Semantic deterministic precheck did not hard fail",sr))
    print("E2E EXPECTED BLOCK:",label,"| Racing-QM:",rr,"| Final:",fr,"| Semantic:",sr["hard_reasons"])
def test_run137_wrong_session():
    x=base("WorldSBK Superpole Race: Iker Lecuona wins","Iker Lecuona wins the Superpole Race. Nicolo Bulega is second by 2.005 seconds.")
    c=post("WorldSBK","Iker Lecuona holt sich die Superpole.\n\nNicolo Bulega wird mit 2,005 Sekunden Rückstand Zweiter.")
    check(session_errors(x,c),"session contract missed Run137-class mismatch")
    expect_hard_block(x,c,"Run137 Superpole Race -> Superpole")
def test_run137_rumor_upgrade():
    x=base("Strong signal from Franco Morbidelli about 2027 WorldSBK future","Morbidelli gives a strong signal. A Ducati factory contract is not officially confirmed.")
    c=post("WorldSBK","Franco Morbidelli wechselt 2027 in die WorldSBK.\n\nDer Wechsel steht fest, der Ducati-Vertrag ist noch nicht offiziell bestätigt.")
    check(claim_strength_errors(x,c),"claim guard missed rumor/certainty upgrade")
    expect_hard_block(x,c,"Run137 signal -> definitive transfer")
def test_run137_bad_german():
    x=base("Fermin Aldeguer has surgery before Japan MotoGP round","Fermin Aldeguer had surgery before the Japan MotoGP round.","MotoGP")
    c=post("MotoGP","Fermin Aldeguer musste kurz vor Japan operiert werden.\n\nSo kurz vor dem Renne auf den OP-Tisch.")
    ok,e=human_text_review("Motorcycle Racing",x,c)
    check(not ok and any("vor dem Renne" in z for z in e),("Human gate missed Run137 German error",e))
    print("E2E EXPECTED BLOCK: Run137 bad German | Human:",e)
def test_fake_number_injected():
    x=base("WorldSSP Race 2: Can Oncu finishes sixth","Can Oncu finishes sixth in Race 2.","WorldSSP")
    c=post("WorldSSP","Can Öncü wird im Race 2 Sechster.\n\nZur Spitze fehlen ihm angeblich 9,999 Sekunden.")
    # Closed source whitelist owns exact number provenance. Reproduce it through production hardening binding.
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    hard.install(agency)
    errs=agency.fact_whitelist_errors(x,c)
    check(any("Zahl nicht in Quelle" in e for e in errs),("fake number not rejected",errs))
    print("E2E EXPECTED BLOCK: invented number | Whitelist:",errs)
def test_wrong_series_injected():
    x=base("WorldSSP Race 2: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP Race 2.","WorldSSP")
    c=post("WorldSSP","Can Öncü fährt in der MotoGP auf Platz sechs.\n\nEin starkes Rennen von ihm.")
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    hard.install(agency)
    errs=agency.fact_whitelist_errors(x,c)
    check(any("Falsche Serie MotoGP" in e for e in errs),("wrong series not rejected",errs))
    print("E2E EXPECTED BLOCK: injected wrong series | Whitelist:",errs)
def test_clean_realistic_control():
    x=base("WorldSBK Superpole Race: Iker Lecuona wins","Iker Lecuona wins the Superpole Race. Nicolo Bulega finishes second.")
    c=post("WorldSBK","Iker Lecuona gewinnt das Superpole Race.\n\nNicolo Bulega wird Zweiter und komplettiert damit das Ergebnis.")
    check(not session_errors(x,c),session_errors(x,c));check(not claim_strength_errors(x,c),claim_strength_errors(x,c))
    check(human_text_review("Motorcycle Racing",x,c)[0],human_text_review("Motorcycle Racing",x,c)[1])
    check(racing_qm.review(x,c)[0],racing_qm.review(x,c)[1])
    check(final_guard.review(x,c)[0],final_guard.review(x,c)[1])
    print("E2E EXPECTED PASS: supported realistic control")
def test_uncertainty_preserved_passes():
    x=base("Strong signal from Franco Morbidelli about 2027 WorldSBK future","Morbidelli gives a strong signal. A Ducati factory contract is not officially confirmed.")
    c=post("WorldSBK","Franco Morbidelli deutet einen möglichen Wechsel 2027 in die WorldSBK an.\n\nEin Ducati-Werkvertrag ist noch nicht offiziell bestätigt.")
    check(not claim_strength_errors(x,c),claim_strength_errors(x,c))
    check(final_guard.review(x,c)[0],final_guard.review(x,c)[1])
    print("E2E EXPECTED PASS: uncertainty preserved")
def test_degraded_semantic_outage_still_repairs_human_error():
    import importlib
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    importlib.reload(agency);importlib.reload(hard).install(agency)
    x=base("Fermin Aldeguer has surgery before Japan MotoGP round","Fermin Aldeguer had surgery before the Japan MotoGP round.","MotoGP")
    outputs=[post("MotoGP","Fermin Aldeguer musste kurz vor Japan operiert werden.\n\nSo kurz vor dem Renne auf den OP-Tisch."),
             post("MotoGP","Fermin Aldeguer musste kurz vor Japan operiert werden.\n\nSo kurz vor dem Rennen auf den OP-Tisch.")]
    calls={"n":0}
    old=(agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source)
    try:
        def editor(item,reasons=None,*a,**kw):
            i=min(calls["n"],1);calls["n"]+=1;return outputs[i]
        agency.german_editor=editor
        agency.racing_review=lambda item,cap:(True,[])
        agency.reanalyse_source=lambda item,*a,**kw:item
        agency.semantic_review_detailed=lambda item,cap:{"hard_ok":False,"language_ok":False,"hard_reasons":["provider unavailable"],"repair_reasons":[],"technical_error":True,"technical_reason":"ProviderUnavailableError"}
        check(agency.qualify_copy(x) is True,x)
        check(calls["n"]==2,calls)
        check(x.get("semantic_qm")=="DEGRADED-PASS",x)
        check("vor dem Rennen" in x["caption"] and "vor dem Renne " not in x["caption"],x["caption"])
        print("E2E EXPECTED DEGRADED PASS: semantic outage only after deterministic human repair")
    finally:
        agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source=old

if __name__=="__main__":
    tests=[test_run137_wrong_session,test_run137_rumor_upgrade,test_run137_bad_german,test_fake_number_injected,test_wrong_series_injected,test_clean_realistic_control,test_uncertainty_preserved_passes,test_degraded_semantic_outage_still_repairs_human_error]
    for t in tests:
        t();print("CONTROLLED E2E PASS:",t.__name__)
    print("CONTROLLED RACING E2E REGRESSION: 8/8 PASS")
