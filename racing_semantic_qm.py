"""Semantic source-to-caption QM for Motorcycle Racing.
Fail closed: every factual caption claim must be supported by the supplied source facts.
"""
import json, re
from llm_client import generate


def _clean_json(raw):
    raw=(raw or '').strip()
    raw=re.sub(r'^```(?:json)?\s*|\s*```$', '', raw, flags=re.I|re.S)
    return json.loads(raw)


def review(item, caption):
    source_title=str(item.get('title','')).strip()
    source_summary=str(item.get('summary','')).strip()
    source_series=str(item.get('series','')).strip()
    source_url=str(item.get('url','')).strip()
    prompt=f'''Du bist der unabhaengige semantische Fakten-QM einer Motorrad-Racing-Redaktion.
Pruefe den fertigen deutschen Social-Post SATZ FUER SATZ ausschliesslich gegen die gelieferten QUELLFAKTEN.

QUELLFAKTEN:
SERIE/METADATEN: {source_series or 'nicht angegeben'}
TITEL: {source_title}
ZUSAMMENFASSUNG: {source_summary}
URL (nur Kontext, nicht erfinden): {source_url}

FERTIGER POST:
{caption}

HARTE REGELN:
1. Jede Tatsachenbehauptung muss durch Titel/Zusammenfassung/Metadaten eindeutig gedeckt sein.
2. Erfunden/vertauscht/falsch zugeordnet: Fahrer, Team, Hersteller, Rennserie, Klasse, Jahr, Ort, Ergebnis, Rekord, Zahl, Titel/Champion-Status oder Beziehung => FAIL.
3. Keine Schlussfolgerung als Tatsache ausgeben, wenn die Quelle sie nicht sagt.
4. Direkte Zitate oder angebliche Zitate => FAIL. Paraphrasen sind erlaubt, wenn inhaltlich gedeckt.
5. Natuerliches korrektes Deutsch ist Pflicht. Wortsalat, falsche Faelle/Pluralformen, englische Lehnuebersetzungen, PR-Sprech oder unnatuerliche Formulierungen => FAIL.
6. Die Community-Frage darf Meinung erfragen, aber keine unbelegte Tatsache voraussetzen.
7. Hashtags werden nur auf falsche Fahrer/Serie geprueft; generische Racing-Hashtags sind erlaubt.
8. Sei streng. Bei Unsicherheit => FAIL.

Antworte NUR als JSON:
{{"pass":true|false,"reasons":["..."],"unsupported_claims":["..."],"series_ok":true|false,"rider_team_ok":true|false,"german_ok":true|false,"quote_ok":true|false}}'''
    try:
        obj=_clean_json(generate('racing_semantic_qm', prompt))
        ok=bool(obj.get('pass')) and bool(obj.get('series_ok')) and bool(obj.get('rider_team_ok')) and bool(obj.get('german_ok')) and bool(obj.get('quote_ok'))
        reasons=[str(x) for x in obj.get('reasons',[]) if str(x).strip()]
        unsupported=[str(x) for x in obj.get('unsupported_claims',[]) if str(x).strip()]
        if unsupported: reasons += ['Nicht belegt: '+x for x in unsupported]
        if not ok and not reasons: reasons=['Semantischer Fakten-QM: nicht alle Pflichtfelder PASS']
        return ok, reasons
    except Exception as e:
        return False, [f'Semantischer Fakten-QM nicht verfuegbar/ungueltig: {type(e).__name__}: {str(e)[:140]}']
