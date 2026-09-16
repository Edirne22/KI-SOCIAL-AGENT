"""V8.5.7 runtime hardening for the Racing chain.
Source facts stay immutable. One fresh source regeneration is allowed; subsequent QM
feedback repairs the existing caption instead of repeatedly re-researching/recreating it.
"""
import re,time,json
from racing_final_guard import expected_series

VALID=('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300')

def install(a):
    original_prompt=a._editor_prompt

    def transfer(x):
        s=a.fold(' '.join((x.get('title',''),x.get('summary',''))))
        if 'motogp' in s and any(p in s for p in ('join motogp','joins motogp','to motogp','motogp switch','moves to motogp','move to motogp','switch to motogp','motogp debut','new motogp star')): return 'MotoGP'
        if ('worldsbk' in s or 'world superbike' in s) and any(p in s for p in ('join worldsbk','joins worldsbk','to worldsbk','worldsbk switch','moves to worldsbk','move to worldsbk','switch to worldsbk')): return 'WorldSBK'
        return ''

    def lock(x,declared=None):
        frozen=str(x.get('trusted_series','')).strip()
        if frozen in VALID:
            x.update(series=frozen,source_series=frozen,series_locked=True);return x
        dest=transfer(x);inferred=expected_series(x);supplied=str(declared or x.get('source_series') or x.get('series') or '').strip()
        chosen=dest or (inferred if inferred in VALID else '') or (supplied if supplied in VALID else '')
        if chosen:
            x['trusted_series']=chosen;x['series']=chosen;x['source_series']=chosen;x['series_locked']=True
            x['series_origin']='explicit-transfer' if dest else ('source-fact-lock' if inferred in VALID else 'official-feed')
        return x

    def series_for(x):
        frozen=str(x.get('trusted_series','')).strip()
        if frozen in VALID:return frozen
        lock(x);return str(x.get('trusted_series') or x.get('series') or 'MotoGP')

    def fact_packet(x):
        source=' '.join((str(x.get('title','')),str(x.get('summary',''))))
        return {'series':series_for(x),'title':' '.join(str(x.get('title','')).split()),'summary':' '.join(str(x.get('summary','')).split()),'riders':a.riders_in(source),'numbers':sorted(set(re.findall(r'(?<![A-Za-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',source)))}

    def whitelist_errors(x,caption):
        f=fact_packet(x);src=a.fold(f['title']+' '+f['summary']);cap=a.fold(re.sub(r'#[^\s]+','',caption or ''));errs=[]
        allowed={a.fold(n) for n in f['riders']};allowed_last={n.split()[-1] for n in allowed}
        for n in a.RIDERS_V2:
            fn=a.fold(n);last=fn.split()[-1]
            present=fn in cap or (len(last)>=5 and re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',cap))
            if present and fn not in allowed and last not in allowed_last:errs.append('Source-Fact-Whitelist: Fahrer nicht in Quelle: '+n)
        srcnums=set(re.findall(r'(?<![a-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',src));capnums=set(re.findall(r'(?<![a-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',cap))
        for n in sorted(capnums-srcnums):errs.append('Source-Fact-Whitelist: Zahl nicht in Quelle: '+n)
        return errs

    def prompt(x,reasons=None):
        lock(x);base=original_prompt(x,reasons);facts=json.dumps(fact_packet(x),ensure_ascii=False);series=series_for(x)
        guard=f'''\n\nV8.5.7 SOURCE-BOUND GUARD:
GESPERRTE SERIE: {series}. Keine andere Rennserie nennen. Keine Fakten praezisieren oder verschaerfen. P1/fastest/timesheets ist keine WM-Fuehrung. Allgemeines championship leader nicht eigenmaechtig einer Klasse zuordnen. targets/set to/expected/aims nicht staerker formulieren. Keine Personen-Vornamen, Nationalitaeten, Teams, Hersteller, Orte, Strecken, Verletzungen, Titel, Verwandtschaften oder Zeitbezuege ergaenzen, die nicht in TITEL/ZUSAMMENFASSUNG stehen. Schreibweisen von Namen exakt aus der Quelle uebernehmen. Bei Unsicherheit Detail weglassen.'''
        return base+'\nSOURCE-FACT-WHITELIST: '+facts+guard

    def repair_caption(x,caption,reasons):
        """Repair the current copy in place; QM feedback is not a source of new facts."""
        facts=json.dumps(fact_packet(x),ensure_ascii=False);reason='; '.join((reasons or [])[:8])
        p=f'''Du reparierst einen bestehenden deutschen Racing-Post. Erzeuge KEINE neue Story und recherchiere NICHT aus Vorwissen.
QUELLFAKTEN: {facts}
GESPERRTE SERIE: {series_for(x)}
QM-FEHLER: {reason}
BESTEHENDER POST:\n{caption}

Aendere nur Textstellen, die fuer die genannten QM-Fehler noetig sind. Unbelegte Details entfernen statt ersetzen. Keine neuen Namen, Vornamen, Nationalitaeten, Serien, Teams, Hersteller, Orte, Strecken, Zahlen, Ergebnisse, Titel oder Beziehungen. Namen exakt wie in den Quellfakten schreiben. Behalte Struktur, Ton und Community-Frage. Antworte nur mit dem vollstaendig reparierten Post, ohne Erklaerung.'''
        try:
            out=(a.generate('final_captions',p) or '').strip()
            return out if out else caption
        except Exception as e:
            print('EDITOR REPAIR EXCEPTION:',type(e).__name__,str(e)[:160]);return caption

    def semantic_technical_retry(x,caption):
        for n in (1,2):
            r=a.semantic_review_detailed(x,caption);joined=' '.join(r.get('hard_reasons',[])).lower()
            technical=any(k in joined for k in ('technisch ungueltig','http 429','rate limit','provider-anfrage','timeout'))
            if not technical:return r
            print(f'SEMANTIC-QM TECHNICAL RETRY {n}/2:',x.get('title','')[:90],'|',joined[:180])
            if n<2:time.sleep(2)
        return {'technical_error':True,'hard_ok':False,'language_ok':False,'hard_reasons':[],'repair_reasons':[]}

    def evaluate(x,caption):
        w=whitelist_errors(x,caption)
        if w:return False,w,'whitelist'
        r_ok,r_err=a.racing_review(x,caption);x['qm_errors']=r_err
        if not r_ok:return False,['Racing-QM: '+e for e in r_err],'racing'
        sem=semantic_technical_retry(x,caption)
        if sem.get('technical_error'):return None,[],'technical'
        x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
        if not sem['hard_ok']:return False,['Fakten-QM: '+e for e in sem['hard_reasons']],'facts'
        if not sem['language_ok']:return False,['Sprach-QM: '+e for e in sem['repair_reasons']],'language'
        if not a.language_sane(caption):return False,['Deutsch/PR-/KI-Sprech deterministisch bereinigen'],'language'
        return True,[],'pass'

    def qualify(x,initial_reasons=None):
        if not a.racing_relevant(x):return False
        lock(x);x['caption']=a.german_editor(x,initial_reasons);lock(x)
        if not x['caption']:
            x['semantic_qm']='FAIL';x['rewrite_count']=0;print('EDITOR HARD REJECT: no structured text:',x.get('title','')[:90]);return False
        # At most two targeted in-place repairs. No repeated source fetch and no full regeneration.
        for attempt in (1,2,3):
            ok,reasons,kind=evaluate(x,x['caption'])
            if ok is None:
                x['technical_qm_deferred']=True;x['semantic_qm']='TECHNICAL-DEFER';x['rewrite_count']=attempt-1
                print('SEMANTIC-QM TECHNICAL DEFER:',x.get('title','')[:90]);return False
            if ok:
                x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1
                print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
            if attempt==3:
                print('COPY-QM HARD REJECT after bounded repair:',x.get('title','')[:90],'|','; '.join(reasons)[:700]);break
            print(f'COPY-QM → TARGETED REPAIR {attempt}/2 [{kind}]:',x.get('title','')[:90])
            x['caption']=repair_caption(x,x['caption'],reasons);lock(x)
        x['semantic_qm']='FAIL';x['rewrite_count']=2;return False

    a.lock_source_series=lock;a.series_for_raw=series_for;a.series_for=series_for
    a._editor_prompt=prompt;a.fact_whitelist_errors=whitelist_errors;a.qualify_copy=qualify
    a.VERSION='V8.5.7'
    return a
