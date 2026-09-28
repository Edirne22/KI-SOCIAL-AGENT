"""Diagnostic-only parity audit for the Racing truth/QM chain.

This test intentionally does NOT change production behaviour.  It documents which
source projection each gate consumes and reproduces the Run #137 blind spots so a
later contract PR can fix them without guessing.
"""
import inspect
import motogp_content_agency_v2 as agency
import racing_semantic_qm as semantic
import racing_final_guard as final_guard
import motogp_quality_manager as racing_qm
import chief_quality_manager as chief
import racing_v855_hardening as hardening

def check(cond,msg):
    if not cond:
        raise AssertionError(msg)

def _worldsbk_superpole_race():
    return {
        "title":"WorldSBK EICMA Italian Round Superpole Yarışı: Lecuona Kazandı, Bulega İkinci",
        "summary":"Iker Lecuona Superpole Race'i kazandı. Bulega 2,005 saniye geride ikinci oldu. Şampiyona kararı ikinci yarışa kaldı.",
        "url":"https://motoetkinlik.com/worldsbk-eicma-italian-round-superpole-yarisi-lecuona-kazandi-bulega-ikinci",
        "series":"WorldSBK","source_series":"WorldSBK","trusted_series":"WorldSBK","series_locked":True,
    }

def _morbidelli_signal():
    return {
        "title":"Franco Morbidelli'den 2027 WorldSBK Geleceğine Dair Güçlü Sinyal",
        "summary":"Morbidelli 2027 WorldSBK geleceği hakkında güçlü sinyal verdi. Ducati fabrika sözleşmesi resmi olarak doğrulanmadı.",
        "url":"https://motoetkinlik.com/franco-morbidelliden-2027-worldsbk-gelecegine-dair-guclu-sinyal",
        "series":"WorldSBK","source_series":"WorldSBK","trusted_series":"WorldSBK","series_locked":True,
    }

def audit_projection_split():
    # These assertions are diagnostic architecture guards: changing one of these
    # functions later must be deliberate because today they create independent
    # truth projections from the same item.
    sem_src=inspect.getsource(semantic._source_fields)
    hard_src=inspect.getsource(hardening.install)
    final_src=inspect.getsource(final_guard.review)
    check("infer_story_series" in sem_src and "locked_metadata" in sem_src,
          "Semantic projection unexpectedly changed")
    check("def fact_packet" in hard_src and "'numbers'" in hard_src and "'riders'" in hard_src,
          "Whitelist projection unexpectedly changed")
    check("expected_series(item)" in final_src and "source_text(item)" in final_src,
          "Final-Guard projection unexpectedly changed")
    print("GATE-PARITY DIAG: independent truth projections confirmed")
    print("  whitelist = series,title,summary,riders,numbers")
    print("  semantic  = inferred series,title,summary,locked_metadata")
    print("  final     = independently inferred series/transfer from title+summary")

def reproduce_run137_session_blind_spot():
    item=_worldsbk_superpole_race()
    bad=("Iker Lecuona holt sich die Superpole in Cremona – dahinter wird Bulega "
         "mit 2,005 Sekunden Rückstand Zweiter.\\n\\n"\n         "Damit ist es schon Lecuonas zweiter "
         "Sieg an diesem Wochenende, und die Titelentscheidung rutscht ins zweite Rennen.\n\n"
         "Was erwartet ihr von der Titelentscheidung im zweiten Rennen?\n\n"
         "#WorldSBK #IkerLecuona #NicoloBulega #MotorradRacing #RacingDeutschland #BuelentsBikeLife")
    # Install exposes the production whitelist without changing repository code.
    hardening.install(agency)
    whitelist=agency.fact_whitelist_errors(item,bad)
    racing_ok,racing_err=racing_qm.review(item,bad)
    final_ok,final_err=final_guard.review(item,bad)
    check(not whitelist and racing_ok and final_ok,
          f"Run #137 session blind spot no longer reproduces: whitelist={whitelist}, racing={racing_err}, final={final_err}")
    print("RUN137 REPRO: Superpole Race -> Superpole is NOT rejected by deterministic gates")

def reproduce_run137_claim_strength_blind_spot():
    item=_morbidelli_signal()
    bad=("Morbidelli sagt's klar: 2027 WorldSBK.\n\n"
         "In Cremona hat er's deutlich gemacht – ab 2027 geht er in der WorldSBK an den Start. "
         "Der Ducati-Werkvertrag ist bis jetzt noch nicht offiziell bestätigt worden.\n\n"
         "Wie seht ihr den Wechsel, und wie sicher ist eurer Meinung nach der Ducati-Vertrag?\n\n"
         "#WorldSBK #FrancoMorbidelli #MotorradRacing #RacingDeutschland #BuelentsBikeLife")
    hardening.install(agency)
    whitelist=agency.fact_whitelist_errors(item,bad)
    racing_ok,racing_err=racing_qm.review(item,bad)
    final_ok,final_err=final_guard.review(item,bad)
    check(not whitelist and racing_ok and final_ok,
          f"Run #137 claim-strength blind spot no longer reproduces: whitelist={whitelist}, racing={racing_err}, final={final_err}")
    print("RUN137 REPRO: source signal -> definitive move is NOT rejected by deterministic gates")

def reproduce_run137_language_blind_spot():
    item={"title":"Fermin Aldeguer Japonya MotoGP Öncesi Ameliyat Oldu",
          "summary":"Aldeguer Japonya yarışı öncesinde sol bacağındaki vida nedeniyle ameliyat oldu.",
          "series":"MotoGP","source_series":"MotoGP"}
    bad=("Fermin Aldeguer hat sich kurz vor der Japan-Runde operieren lassen. Schmerzen im linken Bein, "
         "eine Schraube, die raus musste – beim Gresini-Rider wurde das erledigt, bevor es weitergeht.\n\n"
         "So kurz vor dem Renne auf den OP-Tisch – wie seht ihr das?\n\n"
         "#MotoGP #FerminAldeguer #MotorradRacing #RacingDeutschland #BuelentsBikeLife")
    ok,errs=chief.human_text_review("Motorcycle Racing",item,bad)
    check(ok,f"Run #137 language blind spot no longer reproduces: {errs}")
    print("RUN137 REPRO: 'vor dem Renne' is NOT rejected by Human-Writing gate")

def audit_semantic_degraded_contract():
    src=inspect.getsource(hardening.install)
    check("deterministic fact gates remain mandatory" in src and "DEGRADED-PASS" in src,
          "DEGRADED-PASS contract unexpectedly changed")
    check("if not sem['hard_ok']" in src,
          "real Semantic hard FAIL must remain blocking/repairing")
    print("CONFLICT DIAG: deterministic FAIL blocks; Semantic hard FAIL blocks; technical Semantic outage may DEGRADED-PASS only after current deterministic gates")

def main():
    audit_projection_split()
    reproduce_run137_session_blind_spot()
    reproduce_run137_claim_strength_blind_spot()
    reproduce_run137_language_blind_spot()
    audit_semantic_degraded_contract()
    print("RACING GATE PARITY DIAGNOSTIC: PASS (blind spots reproduced; no production fix applied)")

if __name__=="__main__":
    main()
