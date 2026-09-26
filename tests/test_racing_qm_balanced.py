"""Regression tests for balanced Racing fact gates."""
import racing_semantic_qm as sem
import motogp_content_agency_v2 as agency
from racing_v855_hardening import install

def test_opinion_question_not_hard_fail():
    item={"series":"MotoGP","title":"MotoGP confirms Valencia as 2027 season finale","summary":"Valencia will host the 2027 season finale."}
    obj={"contract_version":"SOURCE-FACT-CONTRACT-V1","coverage_complete":True,"claims":[
      {"claim":"Valencia ist 2027 Saisonfinale.","claim_type":"FACT","status":"SUPPORTED","source_evidence":[{"source_field":"title","quote":"Valencia as 2027 season finale"}]},
      {"claim":"Wie seht ihr Valencia als Saisonfinale?","claim_type":"OPINION_QUESTION","status":"UNSUPPORTED","source_evidence":[]}
    ]}
    hard,reasons,_=sem._validate_contract(item,obj)
    assert hard and not reasons,(hard,reasons)

def test_unsupported_fact_still_fails():
    item={"series":"MotoGP","title":"MotoGP calendar revealed","summary":"Calendar published."}
    obj={"contract_version":"SOURCE-FACT-CONTRACT-V1","coverage_complete":True,"claims":[
      {"claim":"Bulega fährt MotoGP.","claim_type":"FACT","status":"UNSUPPORTED","source_evidence":[]}
    ]}
    hard,reasons,_=sem._validate_contract(item,obj)
    assert not hard and reasons

def test_decimal_separator_equivalence():
    install(agency)
    item={"series":"WorldSBK","source_series":"WorldSBK","trusted_series":"WorldSBK","series_locked":True,
          "title":"Lecuona beats Bulega by 0.119s in FP1 at Cremona","summary":"Lecuona led Bulega by 0.119s."}
    errs=agency.fact_whitelist_errors(item,"Lecuona liegt 0,119s vor Bulega.\n\n#WorldSBK #BuelentsBikeLife")
    assert not any("Zahl nicht in Quelle" in e for e in errs),errs
    errs_unitless=agency.fact_whitelist_errors(item,"Lecuona liegt 0.119 vor Bulega.\n\n#WorldSBK #BuelentsBikeLife")
    assert not any("Zahl nicht in Quelle" in e for e in errs_unitless),errs_unitless
    errs2=agency.fact_whitelist_errors(item,"Lecuona liegt 0,118s vor Bulega.\n\n#WorldSBK #BuelentsBikeLife")
    assert any("Zahl nicht in Quelle" in e for e in errs2),errs2

def test_semantic_provider_failure_degraded_pass():
    install(agency)
    old_editor,old_review,old_sem,old_sane=agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.language_sane
    try:
      agency.german_editor=lambda x,r=None:"Brad Binder wechselt zu BMW.\n\nWas haltet ihr davon?\n\n#WorldSBK #BradBinder #BuelentsBikeLife #Racing"
      agency.racing_review=lambda x,c:(True,[])
      agency.semantic_review_detailed=lambda x,c:{"hard_ok":False,"language_ok":False,"hard_reasons":["Semantischer Fakten-QM technisch ungueltig nach 3 Versuchen: RuntimeError: ReadTimeout"],"repair_reasons":[]}
      agency.language_sane=lambda c:True
      item={"series":"WorldSBK","source_series":"WorldSBK","trusted_series":"WorldSBK","series_locked":True,
            "title":"Brad Binder joins BMW in WorldSBK","summary":"Brad Binder joins BMW in WorldSBK."}
      assert agency.qualify_copy(item) is True,item
      assert item.get("semantic_qm")=="DEGRADED-PASS",item
    finally:
      agency.german_editor,agency.racing_review,agency.semantic_review_detailed,agency.language_sane=old_editor,old_review,old_sem,old_sane

if __name__=="__main__":
 test_opinion_question_not_hard_fail();test_unsupported_fact_still_fails();test_decimal_separator_equivalence();test_semantic_provider_failure_degraded_pass()
 print("BALANCED RACING QM REGRESSION: PASS")
