"""Regression: explicit WSSP source facts must override a stale Moto2 lock."""
import types
import racing_v855_hardening as h

def fold(s):
    return str(s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')

a=types.SimpleNamespace()
a._editor_prompt=lambda x,*args,**kwargs: "prompt"
a.fold=fold
a.riders_in=lambda s: ["Can Öncü"] if "oncu" in fold(s) else []
a.RIDERS_V2=["Can Öncü","Jeremy Alcoba"]
a.racing_relevant=lambda x: True
a.german_editor=lambda x,*args,**kwargs: ""
a.reanalyse_source=lambda x,*args,**kwargs: x
a.racing_review=lambda x,c: (True,[])
a.semantic_review_detailed=lambda x,c: {"hard_ok":True,"language_ok":True,"hard_reasons":[],"repair_reasons":[]}
a.language_sane=lambda c: True
h.install(a)

x={
 "title":"WSSP Superpole İtalya: Alcoba Cremona’da, Kawasaki 2021’den sonra ilk kez zirvede, Can Öncü 6. sırada bitirdi",
 "summary":"World Supersport Superpole at Cremona",
 "series":"Moto2","source_series":"Moto2","trusted_series":"Moto2","series_locked":True,
}
a.lock_source_series(x)
assert a.series_for(x)=="WorldSSP",x
assert x["trusted_series"]=="WorldSSP",x
assert x["source_series"]=="WorldSSP",x
errs=a.fact_whitelist_errors(x,"[Moto2] Can Öncü fuhr in Cremona.")
assert any("Falsche Serie Moto2" in e for e in errs),errs
ok=a.fact_whitelist_errors(x,"Can Öncü fuhr in der WorldSSP in Cremona.")
assert not any("Falsche Serie" in e for e in ok),ok
print("WORLDSSP SERIES LOCK REGRESSION: PASS")
