"""Dedicated Turkish-Rider editorial lane after explicit human T1-T5 selection.

Human selection decides relevance. This lane still enforces source truth, series, numbers,
semantic hard facts and Chief-QM, but it does not require the selected Turkish rider to be
the primary subject of the source article.
"""
import json,re
from llm_router import quick_chat
from racing_final_guard import review as final_guard_review, fold
from chief_quality_manager import review as chief_review

GENERIC_TAGS=("#BuelentsBikeLife","#MotorradRacing","#RacingDeutschland")

def _source_text(x):
    return " ".join((str(x.get("title","")),str(x.get("summary",""))))

def _target_supported(x):
    rider=str(x.get("turkish_rider","")).strip()
    if not rider:return False
    src=fold(_source_text(x));name=fold(rider);last=name.split()[-1] if name else ""
    return name in src or (len(last)>=4 and re.search(r"(?<![a-z])"+re.escape(last)+r"(?![a-z])",src) is not None)

def _hashtags(x,agency):
    rider=str(x.get("turkish_rider","")).strip()
    rider_tag="#"+re.sub(r"[^A-Za-z0-9]","",fold(rider).title().replace(" ",""))
    series=agency.series_for(x)
    series_tag={"MotoGP":"#MotoGP","Moto2":"#Moto2","Moto3":"#Moto3","WorldSBK":"#WorldSBK","WorldSSP":"#WorldSSP","WorldSSP300":"#WorldSSP300"}.get(series,"")
    return " ".join(t for t in (series_tag,rider_tag,*GENERIC_TAGS) if t)

def _prompt(x,agency,reasons=None):
    rider=str(x.get("turkish_rider","")).strip();series=agency.series_for(x)
    repair=""
    if reasons:repair="\nQM-RUECKGABE – behebe nur diese Punkte:\n- "+"\n- ".join(reasons[:8])
    return f"""Du bist der TURKISH EDITOR von Buelents Bike Life – eine coole Socke mit echter Motorrad-Leidenschaft.
Schreibe auf Deutsch: direkt, sympathisch, locker, frech wenn es passt, gern mit trockenem Humor und Energie.
Der Text soll Lust machen weiterzulesen und zu kommentieren. Nutze 2 bis 5 passende Emojis natuerlich, nicht als Spam.
Keine steife Nachrichtenagentur-Sprache, kein KI-Sprech, kein kuenstliches Marketing-Gebruell.
WICHTIG: Coolness darf NIEMALS neue Fakten erzeugen.

Der Mensch hat {rider} ausdruecklich als Turkish-Rider-Thema ausgewaehlt. Relevanz ist damit entschieden.
Die Originalmeldung darf hauptsaechlich von jemand anderem handeln. Ziehe den belegten Blickwinkel auf {rider} heraus,
aber behaupte niemals, er habe Pole, Sieg, Rekord, Vertrag, Platzierung oder Aussage erzielt, wenn TITEL/ZUSAMMENFASSUNG das nicht belegen.
Nur Fakten aus TITEL/ZUSAMMENFASSUNG. Keine Fakten aus Vorwissen. Keine erfundenen Zitate, Zahlen, Orte, Teams oder Beziehungen.
Serie unveraendert: {series}. Keine Hashtags – die setzt das System deterministisch.
Beende mit einer kurzen, natuerlichen Community-Frage, die nur auf den belegten Fakten beruht.
{repair}
TITEL: {x.get('title','')}
ZUSAMMENFASSUNG: {x.get('summary','')}
TURKISH_RIDER: {rider}

Antworte nur als JSON: {{"caption":"..."}}"""

def edit(x,agency,reasons=None):
    raw=quick_chat(_prompt(x,agency,reasons),task_type="final_captions").strip()
    raw=re.sub(r"^\x60\x60\x60(?:json)?\s*|\s*\x60\x60\x60$","",raw,flags=re.I|re.S)
    try:caption=str(json.loads(raw).get("caption","")).strip()
    except Exception:return ""
    if not caption:return ""
    caption=re.sub(r"(?m)^\s*#[^\n]*$","",caption).strip()
    x["structure_variant"]=None
    x["caption"]=caption+"\n\n"+_hashtags(x,agency)
    return x["caption"]

def final_review(x,caption,agency):
    errors=[]
    if not _target_supported(x):errors.append("Turkish-Final-QM: ausgewaehlter Fahrer ist in den Quellenfakten nicht belegt")
    errors.extend(agency.fact_whitelist_errors(x,caption))
    ok,guard_errors=final_guard_review(x,caption)
    if not ok:errors.extend(guard_errors)
    # Human selection owns relevance. Do not call normal Racing-QM here: it assumes
    # the selected rider must be one of the first/main source riders.
    return not errors,list(dict.fromkeys(errors))

def qualify(x,agency,max_attempts=3):
    agency.lock_source_series(x,x.get("source_series"));agency.enrich_turkish(x)
    if not _target_supported(x):
        x["turkish_qm_errors"]=["Turkish-Final-QM: ausgewaehlter Fahrer ist in den Quellenfakten nicht belegt"]
        return False
    reasons=None
    for attempt in range(1,max_attempts+1):
        if not edit(x,agency,reasons):
            reasons=["Turkish Editor lieferte kein gueltiges JSON"];continue
        ok,errors=final_review(x,x["caption"],agency);x["turkish_qm_errors"]=errors
        if not ok:
            reasons=errors
            if attempt<max_attempts:continue
            return False
        sem=agency.semantic_review_detailed(x,x["caption"])
        hard=list(sem.get("hard_reasons") or []);repair=list(sem.get("repair_reasons") or [])
        joined=" ".join(hard).casefold()
        technical=any(k in joined for k in ("technisch ungueltig","http 429","rate limit","provider-anfrage","timeout"))
        if hard and not technical:
            x["turkish_qm_errors"]=hard
            reasons=["Fakten-QM: "+e for e in hard]
            if attempt<max_attempts:continue
            return False
        if not sem.get("language_ok",True):
            reasons=["Sprach-QM: "+e for e in repair]
            if attempt<max_attempts:continue
            return False
        x["racing_qm"]="PASS";x["semantic_qm"]="DEGRADED-PASS" if technical else "PASS"
        x["turkish_final_qm"]="PASS";x["rewrite_count"]=attempt-1
        print(f"TURKISH FINAL-QM PASS attempt={attempt}:",x.get("title","")[:90])
        return True
    return False

def finish(x,i,agency):
    if x.get("turkish_final_qm")!="PASS":return False
    x["instagram_media"]=agency.prepare_media(x,i)
    if not x["instagram_media"]:return False
    x["story_key"]=agency.story_key(x["title"],x["url"])
    reviewer=lambda item,caption:final_review(item,caption,agency)
    ok,errors=chief_review("Motorcycle Racing",x,x["caption"],x["instagram_media"],x["url"],reviewer)
    x["chief_errors"]=errors
    if not ok:print("TURKISH CHIEF-QM REJECT:",x.get("title","")[:90],"|","; ".join(errors)[:600])
    return ok
