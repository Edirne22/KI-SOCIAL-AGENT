"""Dedicated Turkish-Rider editorial lane after explicit human T1-T5 selection.

Human selection decides relevance. This lane still enforces source truth, series, numbers,
semantic hard facts and Chief-QM. The selected Turkish rider is a hard editorial target:
the final Turkish-Rider post must stay centered on that rider.
"""
import json,re
from llm_router import quick_chat
from racing_final_guard import review as final_guard_review, fold
from chief_quality_manager import review as chief_review

GENERIC_TAGS=("#BuelentsBikeLife","#MotorradRacing","#RacingDeutschland")

def _source_text(x):
    return " ".join((str(x.get("title","")),str(x.get("summary","")),str(x.get("video_transcript",""))))

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
Schreibe auf Deutsch: direkt, sympathisch, locker, frech wenn es passt, gern mit trockenem Humor und Energie.\nLOKALISIERUNGS-VERTRAG: Tuerkische Quellen niemals Satz fuer Satz uebersetzen. Zuerst Bedeutung und belegte Fakten erfassen, danach Titel/Hook/Body/CTA in natuerlichem idiomatischem Deutsch neu schreiben. Kein tuerkischer Quelltitel und kein tuerkischer Satzbau darf im finalen Post stehen. Tuerkische Eigennamen und korrekte Zeichen wie Öncü, Sofuoğlu und Razgatlıoğlu bleiben erhalten.
Der Text soll Lust machen weiterzulesen und zu kommentieren. Nutze 2 bis 5 passende Emojis natuerlich, nicht als Spam.
Keine steife Nachrichtenagentur-Sprache, kein KI-Sprech, kein kuenstliches Marketing-Gebruell.\nSchreibe wie Buelent selbst nach dem Lesen der Quelle: spontan, menschlich, mitfiebernd und als echter Fan.
EMOTION NACH SITUATION: Sieg, Podium, Punkte oder klar starkes Ergebnis duerfen echte Freude/Jubel tragen; bei Rueckschlag passend enttaeuscht oder angespannt; bei neutraler Meldung keine kuenstliche Jubelstimmung.\nKeine Standard-KI-Floskeln, kein immer gleiches Hook-Body-Frage-Muster. Variiere Einstieg, Satzlaenge und Rhythmus.\nEine Community-Frage ist erlaubt, aber nicht Pflicht. Emojis passend und unregelmaessig einsetzen.\nBuelent darf als Fan hoffen, sich freuen, genervt oder stolz sein; Meinung muss als Fanreaktion erkennbar bleiben.\nKeine erfundenen persoenlichen Erlebnisse, Gespraeche mit Fahrern oder Insiderinformationen.
WICHTIG: Coolness darf NIEMALS neue Fakten erzeugen.

Der Mensch hat {rider} ausdruecklich als Turkish-Rider-Thema ausgewaehlt. Relevanz ist damit entschieden.
TURKISH-RIDER TARGET-LOCK: Der fertige Post handelt ausschliesslich von {rider}. Andere Rennfahrer duerfen im finalen redaktionellen Text NICHT namentlich erzaehlt, gefeiert oder zum Hauptthema gemacht werden. Wenn die Quelle nicht genug belegte Fakten ueber {rider} fuer einen eigenstaendigen Post enthaelt, erfinde oder fuelle NICHT mit anderen Fahrern auf.
Die Originalmeldung darf hauptsaechlich von jemand anderem handeln. Ziehe ausschliesslich den belegten Blickwinkel auf {rider} heraus,
aber behaupte niemals, er habe Pole, Sieg, Rekord, Vertrag, Platzierung oder Aussage erzielt, wenn TITEL/ZUSAMMENFASSUNG das nicht belegen.
Nur Fakten aus TITEL/ZUSAMMENFASSUNG. Keine Fakten aus Vorwissen. Keine erfundenen Zitate, Zahlen, Orte, Teams, Nationalitaeten oder Beziehungen. Nationalitaeten nur nennen, wenn sie in TITEL/ZUSAMMENFASSUNG ausdruecklich belegt sind.
Wenn VIDEO_TRANSKRIPT vorhanden ist: nutze dessen belegten Inhalt als Quellenmaterial, aber formuliere vollstaendig neu.
Keine laengeren Originalformulierungen aus Titel, Beschreibung oder Transkript uebernehmen.
Serie unveraendert: {series}. Keine Hashtags – die setzt das System deterministisch.
Wenn es natuerlich passt, darfst du mit einer kurzen Community-Frage enden. Erzwinge sie nicht.
{repair}
TITEL: {x.get('title','')}
ZUSAMMENFASSUNG: {x.get('summary','')}\nVIDEO_TRANSKRIPT: {x.get('video_transcript','')[:12000]}
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
    source=str(x.get("url","")).strip()
    source_line=("\n\nQuelle / weitere Infos: "+source) if source else ""
    x["caption"]=caption+"\n\n"+_hashtags(x,agency)+source_line
    return x["caption"]

def _copied_source_phrase(x,caption,min_words=9):
    def words(s):return re.findall(r"[A-Za-zÀ-ž0-9]+",fold(str(s)))
    out=words(caption)
    if len(out)<min_words:return False
    src=words(" ".join((str(x.get("title","")),str(x.get("summary","")),str(x.get("video_transcript","")))))
    grams={" ".join(src[i:i+min_words]) for i in range(max(0,len(src)-min_words+1))}
    return any(" ".join(out[i:i+min_words]) in grams for i in range(max(0,len(out)-min_words+1)))

def _editorial_text(caption):
    """Strip deterministic hashtags/source provenance before language/copy review."""
    text=str(caption or "").split("\n\nQuelle / weitere Infos:",1)[0]
    text=re.sub(r"(?m)^\s*#[^\n]*$","",text)
    return text.strip()

def _target_focus_errors(x,caption,agency):
    rider=str(x.get("turkish_rider","")).strip()
    if not rider:return ["Turkish-Final-QM: Turkish-Rider Target-Lock ohne Ziel-Fahrer"]
    target=fold(rider); target_last=target.split()[-1] if target else ""
    others=[]
    for name in agency.riders_in(_editorial_text(caption)):
        fn=fold(name); last=fn.split()[-1] if fn else ""
        if fn==target or (target_last and last==target_last):continue
        if name not in others:others.append(name)
    return ["Turkish-Final-QM: Target-Lock verletzt – anderer Fahrer im Turkish-Rider-Post: "+n for n in others]

def final_review(x,caption,agency):
    errors=[]
    editorial=_editorial_text(caption)
    if _copied_source_phrase(x,editorial):errors.append("Turkish-Final-QM: Originalformulierung aus Quellenmaterial uebernommen")
    if not agency.language_sane(editorial):errors.append("Turkish-Final-QM: finaler Text ist nicht vollstaendig idiomatisches Deutsch / enthaelt tuerkischen Sprachrest")
    if not _target_supported(x):errors.append("Turkish-Final-QM: ausgewaehlter Fahrer ist in den Quellenfakten nicht belegt")
    errors.extend(_target_focus_errors(x,editorial,agency))
    errors.extend(agency.fact_whitelist_errors(x,caption))
    ok,guard_errors=final_guard_review(x,caption)
    if not ok:errors.extend(guard_errors)
    # Human selection owns relevance. Do not call normal Racing-QM here: it assumes
    # the selected rider must be one of the first/main source riders.
    return not errors,list(dict.fromkeys(errors))


def process_manual_selection(x,i,agency,max_attempts=3):
    """Bounded repair chain for an explicit Buelent T-selection.

    Human selection owns topic/relevance. Deterministic/semantic/Chief findings
    reject the current caption, never the selected topic. After bounded repair
    the latest caption is escalated for an explicit human decision; escalation
    is never recorded as a QM PASS.
    """
    agency.lock_source_series(x,x.get("source_series"));agency.enrich_turkish(x)
    agency.mark_priority(x,"TURKISH_SELECTED")
    x["manual_turkish_selection"]=True
    if not _target_supported(x):
        reasons=["FACT/SOURCE: ausgewaehlter Fahrer ist in den Quellenfakten nicht belegt"]
        x["manual_decision_status"]="ESCALATE";x["manual_decision_reasons"]=reasons
        return {"status":"ESCALATE","reasons":reasons,"item":x}

    reasons=None
    latest_errors=[]
    for attempt in range(1,max_attempts+1):
        print(f"TURKISH MANUAL REPAIR attempt={attempt}:",x.get("title","")[:90])
        if not edit(x,agency,reasons):
            latest_errors=["TECHNICAL: Turkish Editor lieferte kein gueltiges JSON"]
            reasons=latest_errors
            continue

        ok,errors=final_review(x,x["caption"],agency)
        latest_errors=list(errors)
        if not ok:
            reasons=latest_errors
            print(f"TURKISH MANUAL FINAL-QM REPAIR attempt={attempt}:","; ".join(reasons)[:1000])
            continue

        sem=agency.semantic_review_detailed(x,x["caption"])
        hard=list(sem.get("hard_reasons") or []);repair=list(sem.get("repair_reasons") or [])
        joined=" ".join(hard).casefold()
        technical=any(k in joined for k in ("technisch ungueltig","http 429","rate limit","provider-anfrage","timeout"))
        if hard and not technical:
            latest_errors=["FACT/SOURCE: "+e for e in hard]
            reasons=latest_errors
            print(f"TURKISH MANUAL SEMANTIC REPAIR attempt={attempt}:","; ".join(reasons)[:1000])
            continue
        if not sem.get("language_ok",True):
            latest_errors=["Sprach-QM: "+e for e in repair] or ["Sprach-QM: Text ist nicht vollstaendig idiomatisches Deutsch; keine Detailgruende vom Semantic-QM geliefert"]
            reasons=latest_errors
            print(f"TURKISH MANUAL LANGUAGE REPAIR attempt={attempt}:","; ".join(reasons)[:1000])
            continue

        x["instagram_media"]=agency.prepare_media(x,i)
        if not x["instagram_media"]:
            x["manual_decision_status"]="TECHNICAL"
            x["manual_decision_reasons"]=["TECHNICAL: prepare_media lieferte kein Medium"]
            return {"status":"TECHNICAL","reasons":x["manual_decision_reasons"],"item":x}
        x["story_key"]=agency.story_key(x["title"],x["url"])
        reviewer=lambda item,caption:final_review(item,caption,agency)
        chief_ok,chief_errors=chief_review("Motorcycle Racing",x,x["caption"],x["instagram_media"],x["url"],reviewer)
        if chief_ok:
            x["racing_qm"]="PASS";x["semantic_qm"]="DEGRADED-PASS" if technical else "PASS"
            x["turkish_final_qm"]="PASS";x["chief_qm"]="PASS"
            x["rewrite_count"]=attempt-1;x["caption_final"]=True
            x["manual_decision_status"]="PASS"
            return {"status":"PASS","reasons":[],"item":x}
        latest_errors=list(chief_errors)
        reasons=["Chief-QM: "+e for e in latest_errors]
        print(f"TURKISH MANUAL CHIEF REPAIR attempt={attempt}:","; ".join(reasons)[:1000])

    x["manual_decision_status"]="ESCALATE"
    x["manual_decision_reasons"]=latest_errors or ["Editor/QM konnte innerhalb der Reparaturgrenze keinen PASS erzeugen"]
    # Deliberately do not set turkish_final_qm/chief_qm to PASS here.
    return {"status":"ESCALATE","reasons":x["manual_decision_reasons"],"item":x}


def qualify(x,agency,max_attempts=3):
    agency.lock_source_series(x,x.get("source_series"));agency.enrich_turkish(x)
    if not _target_supported(x):
        x["turkish_qm_errors"]=["Turkish-Final-QM: ausgewaehlter Fahrer ist in den Quellenfakten nicht belegt"]
        print("TURKISH FINAL-QM BLOCK precheck:",x.get("title","")[:90],"|","; ".join(x["turkish_qm_errors"]))
        return False
    reasons=None
    for attempt in range(1,max_attempts+1):
        print(f"TURKISH EDITOR attempt={attempt}:",x.get("title","")[:90])
        if not edit(x,agency,reasons):
            reasons=["Turkish Editor lieferte kein gueltiges JSON"]
            print(f"TURKISH EDITOR INVALID attempt={attempt}:","; ".join(reasons))
            continue
        ok,errors=final_review(x,x["caption"],agency);x["turkish_qm_errors"]=errors
        if not ok:
            reasons=errors
            print(f"TURKISH FINAL-QM BLOCK attempt={attempt}:",x.get("title","")[:90],"|","; ".join(errors)[:1000])
            if attempt<max_attempts:continue
            print("TURKISH FINAL-QM HARD REJECT:",x.get("title","")[:90],"|","; ".join(errors)[:1000])
            return False
        sem=agency.semantic_review_detailed(x,x["caption"])
        hard=list(sem.get("hard_reasons") or []);repair=list(sem.get("repair_reasons") or [])
        joined=" ".join(hard).casefold()
        technical=any(k in joined for k in ("technisch ungueltig","http 429","rate limit","provider-anfrage","timeout"))
        if hard and not technical:
            x["turkish_qm_errors"]=hard
            reasons=["Fakten-QM: "+e for e in hard]
            print(f"TURKISH SEMANTIC-QM BLOCK attempt={attempt}:","; ".join(hard)[:1000])
            if attempt<max_attempts:continue
            print("TURKISH SEMANTIC-QM HARD REJECT:","; ".join(hard)[:1000])
            return False
        if not sem.get("language_ok",True):
            reasons=["Sprach-QM: "+e for e in repair]
            print(f"TURKISH LANGUAGE-QM BLOCK attempt={attempt}:","; ".join(repair)[:1000])
            if attempt<max_attempts:continue
            print("TURKISH LANGUAGE-QM HARD REJECT:","; ".join(repair)[:1000])
            return False
        x["racing_qm"]="PASS";x["semantic_qm"]="DEGRADED-PASS" if technical else "PASS"
        x["turkish_final_qm"]="PASS";x["rewrite_count"]=attempt-1
        print(f"TURKISH FINAL-QM PASS attempt={attempt}:",x.get("title","")[:90])
        return True
    return False

def finish(x,i,agency):
    if x.get("turkish_final_qm")!="PASS":return False
    x["instagram_media"]=agency.prepare_media(x,i)
    if not x["instagram_media"]:
        print("TURKISH MEDIA BLOCK:",x.get("title","")[:90],"| prepare_media lieferte kein Medium")
        return False
    x["story_key"]=agency.story_key(x["title"],x["url"])
    reviewer=lambda item,caption:final_review(item,caption,agency)
    ok,errors=chief_review("Motorcycle Racing",x,x["caption"],x["instagram_media"],x["url"],reviewer)
    x["chief_errors"]=errors
    if not ok:print("TURKISH CHIEF-QM REJECT:",x.get("title","")[:90],"|","; ".join(errors)[:600])
    return ok
