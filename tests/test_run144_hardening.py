from types import SimpleNamespace
import chief_quality_manager as chief
import racing_v855_hardening as hard

def _fake_agency():
    def fold(s):
        return str(s or "").casefold().replace("ı","i").replace("ğ","g").replace("ü","u").replace("ö","o").replace("ş","s").replace("ç","c")
    return SimpleNamespace(_editor_prompt=lambda *a,**k:"",fold=fold,RIDERS_V2=[],riders_in=lambda t:[],semantic_review_detailed=lambda i,c:{"hard_ok":True,"language_ok":True,"hard_reasons":[],"repair_reasons":[],"technical_error":False},racing_relevant=lambda x:True,german_editor=lambda *a,**k:"",racing_review=lambda *a,**k:(True,[]),_format_only_hashtag_errors=lambda e:False,_deterministic_hashtag_repair=lambda x:None,reanalyse_source=lambda x,r:x,language_sane=lambda c:True)

def test_run144_unicode_apostrophes_are_equivalent_names():
    item={"title":"Gigi Dall’Igna und Agius’u","summary":""}
    assert chief._name_spelling_errors(item,"Gigi Dall'Igna und Agius'u. Zwei Sätze sind hier.\n\n#MotoGP #Racing #Test")==[]

def test_run144_explicit_wsbk_overrides_stale_motogp_lock():
    a=_fake_agency();hard.install(a)
    item={"title":"WSBK Cremona 1. yarış: Lecuona lider","summary":"","series":"MotoGP","source_series":"MotoGP","trusted_series":"MotoGP"}
    assert a.series_for(item)=="WorldSBK"
    assert item["trusted_series"]=="WorldSBK" and item["source_series"]=="WorldSBK"

def test_semantic_breaker_recovers_on_bounded_probe():
    a=_fake_agency();calls={"n":0}
    def semantic(item,caption):
        calls["n"]+=1
        if calls["n"]<=3:return {"hard_ok":False,"language_ok":False,"hard_reasons":[],"repair_reasons":[],"technical_error":True,"technical_reason":"HTTP429"}
        return {"hard_ok":True,"language_ok":True,"hard_reasons":[],"repair_reasons":[],"technical_error":False}
    a.semantic_review_detailed=semantic;hard.install(a);item={"title":"MotoGP test","summary":"","series":"MotoGP"}
    for _ in range(3):a.semantic_technical_retry(item,"x")
    assert a.semantic_runtime_summary()["breaker_open"] is True
    for _ in range(5):a.semantic_technical_retry(item,"x")
    recovered=a.semantic_technical_retry(item,"x");stats=a.semantic_runtime_summary()
    assert recovered["technical_error"] is False and stats["breaker_open"] is False and stats["success"]==1

def test_semantic_breaker_stays_fail_closed_when_probe_fails():
    a=_fake_agency();a.semantic_review_detailed=lambda i,c:{"hard_ok":False,"language_ok":False,"hard_reasons":[],"repair_reasons":[],"technical_error":True,"technical_reason":"HTTP429"}
    hard.install(a);item={"title":"MotoGP test","summary":"","series":"MotoGP"}
    for _ in range(12):a.semantic_technical_retry(item,"x")
    stats=a.semantic_runtime_summary()
    assert stats["breaker_open"] is True and stats["success"]==0
