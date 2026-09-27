"""Regression: exhausted editor providers are technical defers, not editorial repairs."""
import importlib
import motogp_content_agency_v2 as agency
import racing_v855_hardening

agency=importlib.reload(agency)
racing_v855_hardening.install(agency)

item={
 "title":"Toprak Razgatlıoğlu prepares for a racing test",
 "summary":"Toprak Razgatlıoğlu prepares for a racing test in WorldSBK.",
 "series":"WorldSBK","source_series":"WorldSBK","series_locked":True,
}
calls={"editor":0,"reanalyse":0}

def provider_down(x,reasons=None):
 calls["editor"]+=1
 x["editor_technical_error"]="Alle konfigurierten Provider nicht verfuegbar: HTTP 429"
 return ""

def no_reanalyse(x,reasons):
 calls["reanalyse"]+=1
 return x

agency.german_editor=provider_down
agency.reanalyse_source=no_reanalyse
agency.racing_relevant=lambda x: True

assert agency.qualify_copy(item) is False
assert calls["editor"]==1, calls
assert calls["reanalyse"]==0, calls
assert item["editor_qm"]=="TECHNICAL-DEFER"
assert item["rewrite_count"]==0
print("PASS editor provider outage defers once without editorial repair")
