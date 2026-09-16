"""V8.6 runtime hardening, retaining the existing CFO architecture."""
import copy
import json
import re
import time
from racing_cfo import (SERIES, build_cfo, validate_cfo, select_series,
                        guard_errors as cfo_guard_errors, apply_patch, tags)
from racing_semantic_qm import reset_caption_cache
from hashtag_database import contextual_hashtags

VALID = tuple(SERIES)
NATIONALITY_GROUPS = {"australien": ("australier", "australische", "australien", "australian", "australia"), "japan": ("japaner", "japanische", "japan", "japanese"), "spanien": ("spanier", "spanische", "spanien", "spanish", "spaniard"), "türkei": ("türke", "türkische", "türkei", "turkish", "turk"), "brasilien": ("brasilianer", "brasilianische", "brasilien", "brazilian", "brazil"), "italien": ("italiener", "italienische", "italien", "italian", "italy"), "england": ("brite", "briten", "britische", "british", "britain", "england")}

def _parse_patch_payload(raw):
    if not isinstance(raw, str) or not raw.strip(): raise ValueError('patch payload is empty')
    text = raw.strip(); text = re.sub(r'```(?:json)?\s*', '', text, flags=re.I); text = re.sub(r'\s*```\s*$', '', text, flags=re.I | re.S)
    decoder = json.JSONDecoder()
    for i, ch in enumerate(text):
        if ch != '{': continue
        try: value, _ = decoder.raw_decode(text[i:])
        except json.JSONDecodeError: continue
        if isinstance(value, dict) and set(value) == {'patches'}: return value
    raise ValueError('patch response is not a JSON object with patches only')

def _relax_language_guard(errors, cfo, caption):
    source = json.dumps(cfo.get('source', {}), ensure_ascii=False).casefold()
    out = []
    for error in errors:
        lower = error.lower()
        if 'unsupported subject' not in lower and 'changed source spelling' not in lower:
            out.append(error)
            continue
        subject = error.rsplit(' ', 1)[-1].casefold().strip('.,:;!?"')
        allowed = False
        for variants in NATIONALITY_GROUPS.values():
            if subject in variants:
                if any(v in source for v in variants):
                    allowed = True
                    break
        if not allowed:
            out.append(error)
    return out

def _contextual_guard(cfo, caption, rider_catalog=()):
    errors = _relax_language_guard(
        cfo_guard_errors(cfo, caption, rider_catalog), cfo, caption
    )
    riders = [str(r.get('value', '')) for r in cfo.get('riders', [])]
    numbers = {
        str(n.get('value', '')).lower().lstrip('p q fp')
        for n in cfo.get('numbers', [])
    }
    rider_present = any(
        re.search(r'(?i)(?<!\w)' + re.escape(r) + r'(?!\w)', str(caption))
        for r in riders
    )
    for error in list(errors):
        m = re.search(r'unsupported hashtag #([A-Za-z]*\d+)$', error)
        if m and rider_present:
            digit_match = re.search(r'\d+', m.group(1))
            if digit_match and digit_match.group().lower() in numbers:
                errors.remove(error)
    return sorted(set(errors))

def install(a):
    if getattr(a,'_cfo_v86_installed',False): return a
    catalog=tuple(a.RIDERS_V2)+('Senna Agius','Manuel Gonzalez','David Almansa','Takaaki Nakagami','Libero Liberati','Valentino Rossi')
    def lock(x,declared=None):
        if declared and not x.get('source_series'): x['source_series']=declared
        series,origin=select_series(x); x.update(series=series,trusted_series=series,series_locked=bool(series),series_origin=origin); return x
    def series_for(x): lock(x); return x['series']
    def fact_packet(x): return x.get('canonical_fact_object') or build_cfo(x,catalog)
    def whitelist_errors(x,caption): f=fact_packet(x); return validate_cfo(f,x,catalog)+_contextual_guard(f,caption,catalog)
    def repair_caption(x,caption,reasons):
        p=f'''Repariere nur beanstandete Stellen des bestehenden deutschen Posts.\nKeine neue Story, keine Recherche, keine Fakten aus Vorwissen.\nNamen und Zahlen nur aus dem CFO. Keine komplette Neufassung.\nCFO: {json.dumps(fact_packet(x),ensure_ascii=False)}\nQM-FEHLER: {json.dumps((reasons or [])[:8],ensure_ascii=False)}\nBESTEHENDER POST: {json.dumps(caption,ensure_ascii=False)}\nAntworte ausschliesslich JSON: {{"patches":[{{"old":"exakter vorhandener Text","new":"Ersatz"}}]}}'''
        audit={'before_sha256':__import__('hashlib').sha256(caption.encode()).hexdigest()}
        try:
            payload=_parse_patch_payload(a.generate('final_captions',p)); repaired=apply_patch(caption,json.dumps(payload,ensure_ascii=False))
            if repaired==caption: raise ValueError('repair produced no text change')
            audit.update(applied=True,patches=payload['patches']); return repaired
        except Exception as exc:
            audit.update(applied=False,error=f'{type(exc).__name__}: {str(exc)[:200]}')
            print('EDITOR PATCH REJECT:',audit['error'])
            return caption
        finally:
            x.setdefault('repair_history',[]).append(audit)
    def prompt(x,reasons=None): return f'''Du schreibst einen deutschen Racing-Post fuer Buelents Bike Life.\n{a.global_professional_context()}\nV8.6: Das Canonical Fact Object ist die einzige Faktenbasis. Keine Ergaenzung aus Vorwissen.\nNamen exakt uebernehmen, keine Vornamen/Nationalitaeten/Teams/Orte ergaenzen.\nKeine Serienverwechslung, P1 ist weder Q1 noch Meisterschaftsfuehrung.\nModalitaet erhalten. Keine direkten oder frei uebersetzten Zitate.\nNatuerliches Deutsch, Hook, 2-4 informative Saetze und eine Community-Frage.\nKeine Hashtags erzeugen.\nCANONICAL FACT OBJECT: {json.dumps(fact_packet(x),ensure_ascii=False)}\nAntworte nur JSON: {{"hook":"...","body":"...","question":"..."}}'''
    def evaluate(x,caption,frozen):
        w=([] if x.get('canonical_fact_object')==frozen else ['CFO: object mutated'])+validate_cfo(frozen,x,catalog)+_contextual_guard(frozen,caption,catalog); x['guard_errors']=w
        if w:return False,w,'whitelist'
        r_ok,r_err=a.racing_review(x,caption); x['qm_errors']=r_err; current=x.get('caption',caption); w=validate_cfo(frozen,x,catalog)+_contextual_guard(frozen,current,catalog)
        if x.get('canonical_fact_object')!=frozen:w.append('CFO: object mutated')
        x['guard_errors']=w
        if w:return False,w,'whitelist'
        if not r_ok:return False,['Racing-QM: '+e for e in r_err],'racing'
        sem=a.semantic_review_detailed(x,current)
        if sem.get('technical_error'):return None,[],'technical'
        x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
        if not sem['hard_ok']:return False,['Fakten-QM: '+e for e in sem['hard_reasons']],'facts'
        if not sem['language_ok']:return False,['Sprach-QM: '+e for e in sem['repair_reasons']],'language'
        if x.get('caption')!=current or x.get('canonical_fact_object')!=frozen or validate_cfo(frozen,x,catalog):return False,['CFO: source/caption changed during QM'],'whitelist'
        if not a.language_sane(current):return False,['Deutsch/PR-/KI-Sprech bereinigen'],'language'
        return True,[],'pass'
    def qualify(x,initial_reasons=None):
        if not a.racing_relevant(x): return False
        lock(x); reset_caption_cache(); x.update(canonical_fact_object=build_cfo(x,catalog),guard_history=[],repair_history=[],guard_errors=[],qm_errors=[],semantic_errors=[],technical_qm_deferred=False,rewrite_count=0); frozen=copy.deepcopy(x['canonical_fact_object'])
        if not frozen['series'] or frozen['series']=='WorldWCR': x['guard_errors']=['CFO: source series unknown or unsupported']; return False
        x['caption']=a.german_editor(x,initial_reasons)
        if not x['caption']: x['qm_errors']=['Editor: no structured text']; return False
        for attempt in (1,2,3):
            ok,reasons,kind=evaluate(x,x['caption'],frozen); x['guard_history'].append({'attempt':attempt,'stage':kind,'errors':list(reasons),'guard_errors':list(x['guard_errors'])}); x['rewrite_count']=attempt-1
            if ok is None: x.update(technical_qm_deferred=True,semantic_qm='TECHNICAL-DEFER'); return False
            if ok: x.update(semantic_qm='PASS',racing_qm='PASS'); print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]); return True
            if attempt<3:
                previous=x['caption']; repaired=repair_caption(x,previous,reasons)
                if repaired==previous: x.update(semantic_qm='FAIL',racing_qm='FAIL',technical_qm_deferred=False); x['guard_errors']=['CFO: repair returned unchanged text; no repeat QM without a factual change']; x['guard_history'][-1]['errors']=list(x['guard_errors']); print('COPY-QM HARD REJECT: unchanged caption; no repeat QM:',x.get('title','')[:90]); return False
                x['caption']=repaired
        x['semantic_qm']='FAIL'; print('COPY-QM HARD REJECT after bounded patch repair:',x.get('title','')[:90]); return False
    a.lock_source_series=lock; a.series_for_raw=a.series_for=series_for; a._editor_prompt=prompt; a.fact_whitelist_errors=whitelist_errors; a.fact_packet=fact_packet; a.hashtags=lambda x:' '.join(contextual_hashtags(fact_packet(x))); a.qualify_copy=qualify; a.final_series_guard=lambda x:not whitelist_errors(x,x.get('caption','')) and a.racing_review(x,x.get('caption',''))[0]; a.VERSION='V8.6'; a._cfo_v86_installed=True; return a
