"""Regression tests for deterministic Racing event/session contract."""
from racing_event_contract import detect_session,source_event_contract,session_errors
import motogp_quality_manager as racing_qm
import racing_final_guard as final_guard
import racing_semantic_qm as semantic

def check(cond,msg):
    if not cond: raise AssertionError(msg)

def item():
    return {
      "title":"WorldSBK EICMA Italian Round Superpole Yarışı: Lecuona Kazandı, Bulega İkinci",
      "summary":"Cremona: Iker Lecuona Superpole Race'i kazandı. Bulega 2,005 saniye geride ikinci oldu.",
      "url":"https://motoetkinlik.com/worldsbk-eicma-italian-round-superpole-yarisi-lecuona-kazandi-bulega-ikinci",
      "series":"WorldSBK","source_series":"WorldSBK","trusted_series":"WorldSBK"
    }

def caption(session):
    return (f"Iker Lecuona gewinnt das {session} in Cremona. 🏁\n\n"
            "Bulega wird mit 2,005 Sekunden Rückstand Zweiter.\n\n"
            "Was erwartet ihr vom zweiten Rennen?\n\n"
            "#WorldSBK #IkerLecuona #NicoloBulega #MotorradRacing #BuelentsBikeLife")

def test_detection():
    check(detect_session("Superpole Yarışı: Lecuona kazandı")=="Superpole Race","Turkish Superpole race")
    check(detect_session("Superpole Race: Lecuona wins")=="Superpole Race","English Superpole race")
    check(detect_session("Lecuona takes Superpole at Cremona")=="Superpole","bare Superpole")
    check(detect_session("Race 1 results")=="Race 1","Race 1")
    check(detect_session("2. Yarış sonucu")=="Race 2","Turkish Race 2")
    check(detect_session("MotoGP Sprint: Martin wins")=="Sprint","Sprint")
    check(detect_session("FP1 classification")=="FP1","FP1")
    check(detect_session("Qualifying results")=="Qualifying","Qualifying")

def test_source_is_deterministic():
    contract=source_event_contract(item())
    check(contract["session"]=="Superpole Race",contract)
    check(contract["source_field"]=="title",contract)

def test_run137_wrong_session_hard_fails_every_gate():
    x=item();bad=caption("Superpole")
    errs=session_errors(x,bad)
    check(errs,"shared contract must reject")
    ok,re=racing_qm.review(x,bad);check(not ok and any("Session widerspricht" in e for e in re),re)
    ok,fe=final_guard.review(x,bad);check(not ok and any("Session widerspricht" in e for e in fe),fe)
    sr=semantic.review_detailed(x,bad);check(not sr["hard_ok"] and not sr["technical_error"],sr)

def test_correct_session_passes_session_gate():
    x=item();good=caption("Superpole Race")
    check(not session_errors(x,good),session_errors(x,good))
    ok,re=racing_qm.review(x,good);check(ok,re)
    ok,fe=final_guard.review(x,good);check(ok,fe)

def test_omission_is_not_invention():
    x=item()
    neutral=("Iker Lecuona gewinnt in Cremona. Bulega wird mit 2,005 Sekunden Rückstand Zweiter.\n\n"
             "Wie seht ihr das?\n\n#WorldSBK #IkerLecuona #NicoloBulega #MotorradRacing #BuelentsBikeLife")
    check(not session_errors(x,neutral),session_errors(x,neutral))

def test_title_priority_prevents_summary_cross_session_override():
    x={"title":"WorldSBK Superpole Race: Lecuona wins",
       "summary":"After Saturday Superpole qualifying, Sunday Superpole Race went to Lecuona.",
       "url":"https://example.test/superpole-race","series":"WorldSBK"}
    check(source_event_contract(x)["session"]=="Superpole Race",source_event_contract(x))

if __name__=="__main__":
    test_detection()
    test_source_is_deterministic()
    test_run137_wrong_session_hard_fails_every_gate()
    test_correct_session_passes_session_gate()
    test_omission_is_not_invention()
    test_title_priority_prevents_summary_cross_session_override()
    print("RACING EVENT SESSION CONTRACT REGRESSION: PASS")
