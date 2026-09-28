"""Controlled synthetic drill for the production Racing QM chain."""
import motogp_quality_manager as racing_qm
import racing_final_guard as final_guard
import racing_semantic_qm as semantic
from chief_quality_manager import human_text_review
from racing_event_contract import session_errors
from racing_source_claim_guard import claim_strength_errors
def check(c,m):
    if not c: raise AssertionError(m)
def base(t,s,series="WorldSBK"):
    return {"title":t,"summary":s,"series":series,"source_series":series,"trusted_series":series,"series_locked":True,"url":"https://synthetic.invalid/drill"}
def test_wrong_session():
    x=base("WorldSBK Superpole Race: Test Rider wins","Test Rider wins the Superpole Race. Rival is second.")
    c="Test Rider holt sich die Superpole. Rival wird Zweiter. Wie seht ihr das?\n\n#WorldSBK #TestRider #MotorradRacing #BuelentsBikeLife"
    check(session_errors(x,c),"session contract missed mismatch")
    check(not racing_qm.review(x,c)[0],"Racing-QM let mismatch pass")
    check(not final_guard.review(x,c)[0],"Final guard let mismatch pass")
    s=semantic.review_detailed(x,c);check(not s["hard_ok"] and not s["technical_error"],s)
def test_claim_upgrade():
    x=base("Strong signal for Test Rider WorldSBK move in 2027","The move is not officially confirmed.")
    c="Test Rider wechselt 2027 in die WorldSBK. Der Wechsel steht fest. Wie seht ihr das?\n\n#WorldSBK #TestRider #MotorradRacing #BuelentsBikeLife"
    check(claim_strength_errors(x,c),"claim guard missed certainty upgrade")
    check(not racing_qm.review(x,c)[0],"Racing-QM let upgrade pass")
    check(not final_guard.review(x,c)[0],"Final guard let upgrade pass")
    s=semantic.review_detailed(x,c);check(not s["hard_ok"] and not s["technical_error"],s)
def test_bad_german():
    x=base("Test Rider has surgery before Japan round","Test Rider had surgery before Japan round.","MotoGP")
    c="Test Rider musste kurz vor Japan operiert werden. So kurz vor dem Renne auf den OP-Tisch – wie seht ihr das?\n\n#MotoGP #TestRider #MotorradRacing #BuelentsBikeLife"
    ok,e=human_text_review("Motorcycle Racing",x,c);check(not ok and any("vor dem Renne" in z for z in e),e)
def test_clean_control():
    x=base("WorldSBK Superpole Race: Test Rider wins","Test Rider wins the Superpole Race. Rival finishes second.")
    c="Test Rider gewinnt das Superpole Race. Rival wird Zweiter. Wie seht ihr das?\n\n#WorldSBK #TestRider #MotorradRacing #BuelentsBikeLife"
    check(not session_errors(x,c),session_errors(x,c));check(not claim_strength_errors(x,c),claim_strength_errors(x,c))
    check(human_text_review("Motorcycle Racing",x,c)[0],human_text_review("Motorcycle Racing",x,c)[1])
    check(racing_qm.review(x,c)[0],racing_qm.review(x,c)[1]);check(final_guard.review(x,c)[0],final_guard.review(x,c)[1])
if __name__=="__main__":
    for t in [test_wrong_session,test_claim_upgrade,test_bad_german,test_clean_control]:
        t();print("CONTROLLED DRILL PASS:",t.__name__)
    print("CONTROLLED RACING GATE DRILL: 4/4 PASS")
