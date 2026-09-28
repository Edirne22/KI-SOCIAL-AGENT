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
def _whitelist(item,caption):
    import importlib
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    importlib.reload(agency);importlib.reload(hard).install(agency)
    return agency.fact_whitelist_errors(item,caption)
def test_hallucinated_rider_name():
    x=base("WorldSBK Race 2: Iker Lecuona wins","Iker Lecuona wins Race 2. Nicolo Bulega finishes second.")
    c=post("WorldSBK","Toprak Razgatlioglu gewinnt Race 2.\n\nNicolo Bulega wird Zweiter.")
    e=_whitelist(x,c);check(any("Fahrer nicht in Quelle" in z for z in e),("hallucinated rider passed",e))
    print("E2E EXPECTED BLOCK: hallucinated rider | Whitelist:",e)
def test_hallucinated_second_rider():
    x=base("WorldSSP Race 2: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP Race 2.","WorldSSP")
    c=post("WorldSSP","Can Öncü wird Sechster.\n\nBahattin Sofuoğlu fährt direkt hinter ihm ins Ziel.")
    e=_whitelist(x,c);check(any("Fahrer nicht in Quelle" in z for z in e),("invented second rider passed",e))
    print("E2E EXPECTED BLOCK: invented second rider | Whitelist:",e)
def test_wrong_series_hashtag():
    x=base("WorldSBK Race 2: Iker Lecuona wins","Iker Lecuona wins WorldSBK Race 2.")
    c="Iker Lecuona gewinnt Race 2.\n\nEin sauberer Sieg für Lecuona.\n\nWie seht ihr das?\n\n#MotoGP #IkerLecuona #MotorradRacing #BuelentsBikeLife"
    ok,e=final_guard.review(x,c);check(not ok and any("Serienhashtag" in z for z in e),("wrong hashtag passed",e))
    print("E2E EXPECTED BLOCK: wrong series hashtag | Final:",e)
def test_unsupported_series_metadata():
    x=base("WorldWCR Race: Test Rider wins","Test Rider wins the WorldWCR race.","WorldWCR")
    c="Test Rider gewinnt das Rennen.\n\nEin kontrolliertes Ergebnis.\n\nWie seht ihr das?\n\n#WorldWCR #TestRider #MotorradRacing #BuelentsBikeLife"
    ok,e=final_guard.review(x,c);check(not ok and any("nicht als freigegebene Racing-Serie" in z for z in e),("unsupported series passed",e))
    print("E2E EXPECTED BLOCK: unsupported series | Final:",e)
def test_hallucinated_place_is_semantic_fail_when_available():
    x=base("MotoGP: Fermin Aldeguer has surgery","Fermin Aldeguer had surgery before the Japan MotoGP round.","MotoGP")
    c=post("MotoGP","Fermin Aldeguer wurde in Barcelona operiert.\n\nVor Japan musste er deshalb auf den OP-Tisch.")
    # Place provenance is not a deterministic whitelist field today; Semantic SOURCE-FACT must reject it when available.
    # We assert the deterministic whitelist does NOT pretend to own this fact, documenting the fallback boundary.
    e=_whitelist(x,c);check(any("Ort nicht in Quelle: Barcelona" in z for z in e),("invented place not deterministically rejected",e))
    print("E2E EXPECTED BLOCK: invented place | Entity Guard:",e)
def test_hallucinated_team_boundary():
    x=base("WorldSBK: Iker Lecuona wins","Iker Lecuona wins the WorldSBK race.")
    c=post("WorldSBK","Iker Lecuona gewinnt für das erfundene Phoenix-Werksteam.\n\nDer Sieg fällt deutlich aus.")
    e=_whitelist(x,c)
    # Editor prompt forbids unsupported teams, but deterministic whitelist currently has no team extractor.
    check(any("Team/Hersteller nicht in Quelle" in z for z in e),("invented team not deterministically rejected",e))
    print("E2E EXPECTED BLOCK: invented team | Entity Guard:",e)
def _turkish_final(item,caption):
    import importlib
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    import turkish_editor_qm as tqm
    importlib.reload(agency);importlib.reload(hard).install(agency)
    return tqm.final_review(item,caption,agency)
def test_turkish_secondary_rider_relevance_passes_truth():
    x=base("WorldSSP Superpole: Alcoba takes pole","Jeremy Alcoba takes pole. Can Oncu is P6.","WorldSSP")
    x["turkish_rider"]="Can Öncü"
    c=post("WorldSSP","Jeremy Alcoba holt die Pole.\n\nCan Öncü steht laut Quelle auf P6.")
    ok,e=_turkish_final(x,c);check(ok,("Turkish legitimate secondary-rider perspective blocked",e))
    print("TURKISH E2E EXPECTED PASS: human relevance differs, truth remains supported")
def test_turkish_fake_team_is_blocked():
    x=base("WorldSSP: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP.","WorldSSP");x["turkish_rider"]="Can Öncü"
    c=post("WorldSSP","Can Öncü wird Sechster für das Phoenix-Werksteam.\n\nEin starkes Ergebnis.")
    ok,e=_turkish_final(x,c);check(not ok and any("Team/Hersteller nicht in Quelle" in z for z in e),("Turkish fake team passed",e))
    print("TURKISH E2E EXPECTED BLOCK: invented team:",e)
def test_turkish_wrong_series_is_blocked():
    x=base("WorldSSP: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP.","WorldSSP");x["turkish_rider"]="Can Öncü"
    c=post("WorldSSP","Can Öncü fährt in der MotoGP auf Platz sechs.\n\nEin starkes Ergebnis.")
    ok,e=_turkish_final(x,c);check(not ok and any(("Falsche Serie MotoGP" in z or "widerspricht Quelle" in z) for z in e),("Turkish wrong series passed",e))
    print("TURKISH E2E EXPECTED BLOCK: wrong series:",e)
def test_turkish_invented_rider_is_blocked():
    x=base("WorldSSP: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP.","WorldSSP");x["turkish_rider"]="Can Öncü"
    c=post("WorldSSP","Can Öncü wird Sechster.\n\nToprak Razgatlıoğlu fährt direkt hinter ihm ins Ziel.")
    ok,e=_turkish_final(x,c);check(not ok and any("Fahrer nicht in Quelle" in z for z in e),("Turkish invented rider passed",e))
    print("TURKISH E2E EXPECTED BLOCK: invented second rider:",e)
def test_turkish_fake_place_is_blocked():
    x=base("WorldSSP: Can Oncu finishes sixth","Can Oncu finishes sixth in WorldSSP.","WorldSSP");x["turkish_rider"]="Can Öncü"
    c=post("WorldSSP","Can Öncü wird in Barcelona Sechster.\n\nEin starkes Ergebnis.")
    ok,e=_turkish_final(x,c);check(not ok and any("Ort nicht in Quelle: Barcelona" in z for z in e),("Turkish fake place passed",e))
    print("TURKISH E2E EXPECTED BLOCK: invented place:",e)
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
def _degraded_single_caption_result(item,caption):
    import importlib
    import motogp_content_agency_v2 as agency
    import racing_v855_hardening as hard
    importlib.reload(agency);importlib.reload(hard).install(agency)
    old=(agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source)
    try:
        agency.german_editor=lambda *a,**kw:caption
        agency.racing_review=lambda item,cap:(True,[])
        agency.reanalyse_source=lambda item,*a,**kw:item
        agency.semantic_review_detailed=lambda item,cap:{"hard_ok":False,"language_ok":False,"hard_reasons":["provider unavailable"],"repair_reasons":[],"technical_error":True,"technical_reason":"ProviderUnavailableError"}
        return agency.qualify_copy(item),item
    finally:
        agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.reanalyse_source=old
def test_probe_degraded_invented_place():
    x=base("MotoGP: Fermin Aldeguer has surgery","Fermin Aldeguer had surgery before the Japan MotoGP round.","MotoGP")
    c=post("MotoGP","Fermin Aldeguer wurde in Barcelona operiert.\n\nVor Japan musste er deshalb auf den OP-Tisch.")
    ok,item=_degraded_single_caption_result(x,c)
    check(not ok,("invented place still reached DEGRADED-PASS",item)); print("E2E EXPECTED BLOCK: invented place survives Semantic outage? NO")
def test_probe_degraded_invented_team():
    x=base("WorldSBK: Iker Lecuona wins","Iker Lecuona wins the WorldSBK race.")
    c=post("WorldSBK","Iker Lecuona gewinnt für das Phoenix-Werksteam.\n\nDer Sieg fällt deutlich aus.")
    ok,item=_degraded_single_caption_result(x,c)
    check(not ok,("invented team still reached DEGRADED-PASS",item)); print("E2E EXPECTED BLOCK: invented team survives Semantic outage? NO")
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
    tests=[test_run137_wrong_session,test_turkish_secondary_rider_relevance_passes_truth,test_turkish_fake_team_is_blocked,test_turkish_wrong_series_is_blocked,test_turkish_invented_rider_is_blocked,test_turkish_fake_place_is_blocked,test_hallucinated_rider_name,test_hallucinated_second_rider,test_wrong_series_hashtag,test_unsupported_series_metadata,test_hallucinated_place_is_semantic_fail_when_available,test_hallucinated_team_boundary,test_run137_rumor_upgrade,test_run137_bad_german,test_fake_number_injected,test_wrong_series_injected,test_clean_realistic_control,test_uncertainty_preserved_passes,test_degraded_semantic_outage_still_repairs_human_error,test_probe_degraded_invented_place,test_probe_degraded_invented_team]
    for t in tests:
        t();print("CONTROLLED E2E PASS:",t.__name__)
    print("CONTROLLED RACING E2E REGRESSION: 21/21 PASS")
