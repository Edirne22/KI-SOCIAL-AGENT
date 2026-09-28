"""Regression for source-wording claim strength, based on Run #137 Morbidelli."""
from racing_source_claim_guard import claim_strength_errors,source_has_uncertainty,source_has_definitive_confirmation
import motogp_quality_manager as racing_qm
import racing_final_guard as final_guard
import racing_semantic_qm as semantic

def check(c,m):
    if not c: raise AssertionError(m)

def uncertain():
    return {"title":"Franco Morbidelli'den 2027 WorldSBK Geleceğine Dair Güçlü Sinyal",
            "summary":"Morbidelli 2027 WorldSBK geleceği hakkında güçlü sinyal verdi. Ducati fabrika sözleşmesi resmi olarak henüz doğrulanmadı.",
            "series":"WorldSBK","source_series":"WorldSBK"}

def blocks(body):
    return body+" 🏁\n\nDie Zukunft bleibt damit ein Thema.\n\nWie seht ihr das?\n\n#WorldSBK #FrancoMorbidelli #MotorradRacing #BuelentsBikeLife"

def test_run137_definitive_upgrade_fails():
    x=uncertain()
    bad=blocks("Morbidelli sagt's klar: 2027 WorldSBK. Ab 2027 geht er in der WorldSBK an den Start. Der Ducati-Werkvertrag ist noch nicht offiziell bestätigt.")
    errs=claim_strength_errors(x,bad);check(errs,errs)
    ok,re=racing_qm.review(x,bad);check(not ok and any("nicht gedeckt" in e for e in re),re)
    ok,fe=final_guard.review(x,bad);check(not ok and any("nicht gedeckt" in e for e in fe),fe)
    sr=semantic.review_detailed(x,bad);check(not sr["hard_ok"] and not sr["technical_error"],sr)

def test_uncertain_wording_is_preserved():
    x=uncertain()
    good=blocks("Morbidelli hat ein starkes Signal in Richtung WorldSBK 2027 gegeben. Ein Wechsel könnte kommen, ist aber noch nicht offiziell bestätigt.")
    check(not claim_strength_errors(x,good),claim_strength_errors(x,good))

def test_official_confirmation_allows_definitive_wording():
    x={"title":"Bulega's future confirmed: secures MotoGP seat for 2027",
       "summary":"The rider will join the team in 2027.","series":"MotoGP","source_series":"MotoGP"}
    check(source_has_definitive_confirmation(x),x)
    good=blocks("Bulega wechselt 2027 in die MotoGP.")
    check(not claim_strength_errors(x,good),claim_strength_errors(x,good))

def test_not_confirmed_is_not_confirmation():
    x={"title":"Move not officially confirmed","summary":"Strong signal for a 2027 WorldSBK move.","series":"WorldSBK"}
    check(source_has_uncertainty(x),x)
    check(not source_has_definitive_confirmation(x),x)
    check(claim_strength_errors(x,blocks("Er wechselt 2027 in die WorldSBK.")),x)

def test_plain_race_result_untouched():
    x={"title":"Lecuona wins Superpole Race","summary":"Bulega finishes second.","series":"WorldSBK"}
    check(not claim_strength_errors(x,blocks("Lecuona gewinnt das Superpole Race.")),x)

if __name__=="__main__":
    test_run137_definitive_upgrade_fails()
    test_uncertain_wording_is_preserved()
    test_official_confirmation_allows_definitive_wording()
    test_not_confirmed_is_not_confirmation()
    test_plain_race_result_untouched()
    print("RACING SOURCE CLAIM STRENGTH REGRESSION: PASS")
