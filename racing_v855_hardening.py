"""V8.6 runtime hardening, retaining the existing CFO architecture."""
import copy
import json
import re
import time

from racing_cfo import (SERIES, build_cfo, validate_cfo, select_series,
                        guard_errors, apply_patch, tags)
from racing_semantic_qm import reset_caption_cache

VALID = tuple(SERIES)


def _parse_patch_payload(raw):
    """Parse a provider patch response into a strict {'patches': [...]} object."""
    if not isinstance(raw, str):
        raise ValueError('patch payload must be a string')
    text = raw.strip()
    if not text:
        raise ValueError('patch payload is empty')
    text = re.sub(r'```(?:json)?\s*', '', text, flags=re.I)
    text = re.sub(r'\s*```\s*$', '', text, flags=re.I | re.S)
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != '{':
            continue
        try:
            value, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict) and set(value.keys()) == {'patches'}:
            return value
    raise ValueError('patch response is not a JSON object with patches only')


def install(a):
    if getattr(a, '_cfo_v86_installed', False):
        return a
    catalog = tuple(a.RIDERS_V2)
    catalog += ('Senna Agius', 'Manuel Gonzalez', 'David Almansa', 'Takaaki Nakagami',
                'Libero Liberati', 'Valentino Rossi')

    def lock(x, declared=None):
        if declared and not x.get('source_series'):
            x['source_series'] = declared
        series, origin = select_series(x)
        x.update(series=series, trusted_series=series, series_locked=bool(series), series_origin=origin)
        return x

    def series_for(x):
        lock(x)
        return x['series']

    def fact_packet(x):
        return x.get('canonical_fact_object') or build_cfo(x, catalog)

    def whitelist_errors(x, caption):
        f = fact_packet(x)
        return validate_cfo(f, x, catalog) + guard_errors(f, caption, catalog)

    def prompt(x, reasons=None):
        facts = json.dumps(fact_packet(x), ensure_ascii=False)
        return f'''Du schreibst einen deutschen Racing-Post fuer Buelents Bike Life.
{a.global_professional_context()}
V8.6: Das Canonical Fact Object ist die einzige Faktenbasis. Keine Ergaenzung aus Vorwissen.
Namen exakt uebernehmen, keine Vornamen/Nationalitaeten/Teams/Orte ergaenzen.
Keine Serienverwechslung, P1 ist weder Q1 noch Meisterschaftsfuehrung.
Modalitaet erhalten. Keine direkten oder frei uebersetzten Zitate.
Natuerliches Deutsch, Hook, 2-4 informative Saetze und eine Community-Frage.
Keine Hashtags erzeugen.
CANONICAL FACT OBJECT: {facts}
Antworte nur JSON: {{"hook":"...","body":"...","question":"..."}}'''

    def repair_caption(x, caption, reasons):
        p = f'''Repariere nur beanstandete Stellen des bestehenden deutschen Posts.
Keine neue Story, keine Recherche, keine Fakten aus Vorwissen.
Namen und Zahlen nur aus dem CFO. Keine komplette Neufassung.
CFO: {json.dumps(fact_packet(x), ensure_ascii=False)}
QM-FEHLER: {json.dumps((reasons or [])[:8], ensure_ascii=False)}
BESTEHENDER POST: {json.dumps(caption, ensure_ascii=False)}
Antworte ausschliesslich JSON: {{"patches":[{{"old":"exakter vorhandener Text","new":"Ersatz"}}]}}'''
        audit = {'before_sha256': __import__('hashlib').sha256(caption.encode()).hexdigest()}
        try:
            raw = a.generate('final_captions', p)
            payload = _parse_patch_payload(raw)
            patches = payload['patches']
            if not isinstance(patches, list) or not 1 <= len(patches) <= 8:
                raise ValueError('patches must be a list with 1..8 items')
            repaired = apply_patch(caption, json.dumps(payload, ensure_ascii=False))
            if repaired == caption:
                raise ValueError('repair produced no text change')
            audit.update(applied=True, patches=patches)
            return repaired
        except Exception as exc:
            audit.update(applied=False, error=f'{type(exc).__name__}: {str(exc)[:200]}')
            print('EDITOR PATCH REJECT:', audit['error'])
            return caption
        finally:
            x.setdefault('repair_history', []).append(audit)

    def semantic_technical_retry(x, caption):
        for n in (1, 2):
            result = a.semantic_review_detailed(x, caption)
            joined = ' '.join(result.get('hard_reasons', [])).lower()
            technical = result.get('technical_error') or any(k in joined for k in ('technisch ungueltig', 'http 429', 'rate limit', 'provider-anfrage', 'timeout'))
            if not technical:
                return result
            if n < 2:
                time.sleep(2)
        return {'technical_error': True, 'hard_ok': False, 'language_ok': False, 'hard_reasons': [], 'repair_reasons': []}

    def evaluate(x, caption, frozen):
        w = ([] if x.get('canonical_fact_object') == frozen else ['CFO: object mutated'])
        w += validate_cfo(frozen, x, catalog) + guard_errors(frozen, caption, catalog)
        x['guard_errors'] = w
        if w:
            return False, w, 'whitelist'
        r_ok, r_err = a.racing_review(x, caption)
        x['qm_errors'] = r_err
        current = x.get('caption', caption)
        w = validate_cfo(frozen, x, catalog) + guard_errors(frozen, current, catalog)
        if x.get('canonical_fact_object') != frozen:
            w.append('CFO: object mutated')
        x['guard_errors'] = w
        if w:
            return False, w, 'whitelist'
        if not r_ok:
            return False, ['Racing-QM: ' + e for e in r_err], 'racing'
        sem = semantic_technical_retry(x, current)
        if sem.get('technical_error'):
            return None, [], 'technical'
        x['semantic_errors'] = sem['hard_reasons'] + sem['repair_reasons']
        if not sem['hard_ok']:
            return False, ['Fakten-QM: ' + e for e in sem['hard_reasons']], 'facts'
        if not sem['language_ok']:
            return False, ['Sprach-QM: ' + e for e in sem['repair_reasons']], 'language'
        if x.get('caption') != current or x.get('canonical_fact_object') != frozen or validate_cfo(frozen, x, catalog):
            return False, ['CFO: source/caption changed during QM'], 'whitelist'
        if not a.language_sane(current):
            return False, ['Deutsch/PR-/KI-Sprech bereinigen'], 'language'
        return True, [], 'pass'

    def qualify(x, initial_reasons=None):
        if not a.racing_relevant(x):
            return False
        lock(x)
        reset_caption_cache()
        x.update(canonical_fact_object=build_cfo(x, catalog), guard_history=[], repair_history=[], guard_errors=[], qm_errors=[], semantic_errors=[], technical_qm_deferred=False, rewrite_count=0, semantic_qm='FAIL', racing_qm='FAIL', pipeline_version='V8.6')
        frozen = copy.deepcopy(x['canonical_fact_object'])
        if not frozen['series'] or frozen['series'] == 'WorldWCR':
            x['guard_errors'] = ['CFO: source series unknown or unsupported']
            return False
        x['caption'] = a.german_editor(x, initial_reasons)
        if not x['caption']:
            x['qm_errors'] = ['Editor: no structured text']
            return False
        for attempt in (1, 2, 3):
            ok, reasons, kind = evaluate(x, x['caption'], frozen)
            x['guard_history'].append({'attempt': attempt, 'stage': kind, 'errors': list(reasons), 'guard_errors': list(x['guard_errors'])})
            x['rewrite_count'] = attempt - 1
            if ok is None:
                x.update(technical_qm_deferred=True, semantic_qm='TECHNICAL-DEFER')
                return False
            if ok:
                x.update(semantic_qm='PASS', racing_qm='PASS')
                print(f'FULL COPY-QM PASS attempt={attempt}:', x.get('title', '')[:90])
                return True
            if attempt < 3:
                previous = x['caption']
                repaired = repair_caption(x, previous, reasons)
                if repaired == previous:
                    x.update(semantic_qm='FAIL', racing_qm='FAIL', technical_qm_deferred=False)
                    x['guard_errors'] = ['CFO: repair returned unchanged text; no repeat QM without a factual change']
                    x['guard_history'][-1]['errors'] = list(x['guard_errors'])
                    print('COPY-QM HARD REJECT: unchanged caption; no repeat QM:', x.get('title', '')[:90])
                    return False
                x['caption'] = repaired
        x['semantic_qm'] = 'FAIL'
        print('COPY-QM HARD REJECT after bounded patch repair:', x.get('title', '')[:90])
        return False

    a.lock_source_series = lock
    a.series_for_raw = a.series_for = series_for
    a._editor_prompt = prompt
    a.fact_whitelist_errors = whitelist_errors
    a.fact_packet = fact_packet
    a.hashtags = lambda x: tags(fact_packet(x))
    a.qualify_copy = qualify
    a.final_series_guard = lambda x: not whitelist_errors(x, x.get('caption', '')) and a.racing_review(x, x.get('caption', ''))[0]
    a.VERSION = 'V8.6'
    a._cfo_v86_installed = True
    return a
