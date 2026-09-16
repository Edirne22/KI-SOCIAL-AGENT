"""V8.5.6 runtime hardening for the Racing chain.
Keeps source facts immutable across feedback loops, constrains editor facts, and separates provider failures from editorial rejects.
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
            x.update(series=frozen,source_series=frozen,series_locked=True)
            return x
        dest=transfer(x)
        inferred=expected_series(x)
        supplied=str(declared or x.get('source_series') or x.get('series') or '').strip()
        chosen=dest or (inferred if inferred in VALID else '') or (supplied if supplied in VALID else '')
        if chosen:
            x['trusted_series']=chosen;x['series']=chosen;x['source_series']=chosen;x['series_locked']=True
            x['series_origin']='explicit-transfer' if dest else ('source-fact-lock' if inferred in VALID else 'official-feed')
        return x

    def series_for(x):
        frozen=str(x.get('trusted_series','')).strip()
        if frozen in VALID:return frozen
        lock(x)
        return str(x.get('trusted_series') or x.get('series') or 'MotoGP')

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
        guard=f'''\n\nV8.5.6 FACT-PRESERVATION-GUARD (HART):
- GESPERRTE SERIE = {series}. Schreibe niemals den Namen einer anderen Rennserie in den Post. WorldSBK ist NICHT WorldSSP/Supersport; MotoGP ist NICHT Moto2/Moto3.
- Keine semantische Faktenverschaerfung: Ein allgemeines "championship leader" darf nur als "Meisterschaftsfuehrender" wiedergegeben werden, NICHT eigenmaechtig als Moto2-/Moto3-/MotoGP-Meisterschaftsfuehrender, sofern die Klasse nicht wortwoertlich durch die Quelle belegt ist.
- "fastest", "P1", "top of the timesheets", "fuehrt die Zeitenliste an" oder eine Tages-/Session-Fuehrung niemals in WM-/Meisterschafts-/Gesamtfuehrung umdeuten.
- "targets", "set to", "expected", "aims" und vergleichbare Aussagen nicht in staerkere Motive, feste Zusagen oder sichere Zukunftsaussagen umformulieren. Keine Rueckkehr nach einem genannten Wochenende behaupten, wenn die Quelle sie nicht nennt.
- Keine zeitliche Einordnung wie "diese Woche", "heute", "morgen" oder "aktuell", wenn sie nicht durch die bereitgestellten Quelldaten eindeutig gedeckt ist.
- Keine Team-, Strecken-, Orts-, Nationalitaets-, Verletzungs-, Titel- oder Beziehungsdetails aus Motorsportwissen ergaenzen. "Heimrennen" nur verwenden, wenn die Quelle diesen Bezug explizit herstellt.
- Wenn eine attraktive Formulierung einen Fakt praeziser, staerker oder spezifischer machen wuerde als die Quelle: die neutralere Formulierung waehlen oder das Detail weglassen.
- QM-Rueckgaben sind Korrekturanweisungen, KEINE neue Faktenquelle. Eine Rueckgabe darf niemals zum Erfinden eines Ersatzdetails fuehren.'''
        return base+'\n\nSOURCE-FACT-WHITELIST (GESCHLOSSEN): '+facts+'\nJede konkrete Person und jede Zahl im Post muss darin bzw. in TITEL/ZUSAMMENFASSUNG vorkommen. Orte, Teams und Hersteller nur nennen, wenn sie in TITEL/ZUSAMMENFASSUNG stehen. Nicht belegte Details weglassen, niemals aus Vorwissen ergaenzen.'+guard

    def semantic_technical_retry(x,caption):
        for n in (1,2,3):
            r=a.semantic_review_detailed(x,caption)
            joined=' '.join(r.get('hard_reasons',[])).lower()
            technical=('technisch ungueltig' in joined or 'http 429' in joined or 'rate limit' in joined or 'provider-anfrage' in joined or 'timeout' in joined)
            if not technical:return r
            print(f'SEMANTIC-QM TECHNICAL RETRY {n}/3:',x.get('title','')[:90],'|',joined[:180])
            if n<3:time.sleep(2*n)
        return {'technical_error':True,'technical_reason':'Provider/QM nach technischen Retries nicht verfuegbar','hard_ok':False,'language_ok':False,'hard_reasons':[],'repair_reasons':[]}

    def qualify(x,initial_reasons=None):
        if not a.racing_relevant(x):return False
        lock(x);repair=initial_reasons
        for attempt in (1,2,3):
            lock(x);x['caption']=a.german_editor(x,repair);lock(x)
            if not x['caption']:
                repair=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REPAIR attempt={attempt}:',x.get('title','')[:90]);continue
            w=whitelist_errors(x,x['caption'])
            if w:
                if attempt<3:repair=w;a.reanalyse_source(x,repair);lock(x);continue
                print('SOURCE-FACT-WHITELIST REJECT:',x.get('title','')[:90],'|','; '.join(w)[:600]);break
            r_ok,r_err=a.racing_review(x,x['caption']);x['qm_errors']=r_err
            if not r_ok:
                if attempt<3:repair=['Racing-QM: '+e for e in r_err];a.reanalyse_source(x,repair);lock(x);continue
                print('RACING-QM HARD REJECT after feedback loop:',x.get('title','')[:90],'|','; '.join(r_err)[:600]);break
            sem=semantic_technical_retry(x,x['caption'])
            if sem.get('technical_error'):
                x['technical_qm_deferred']=True;print('SEMANTIC-QM TECHNICAL DEFER – candidate not factually rejected:',x.get('title','')[:90]);break
            x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
            if not sem['hard_ok']:
                if attempt<3:repair=['Fakten-QM: '+e for e in sem['hard_reasons']];a.reanalyse_source(x,repair);lock(x);continue
                print(f'SEMANTIC HARD-FACT REJECT after feedback loop attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['hard_reasons'])[:700]);break
            if not sem['language_ok']:
                if attempt<3:repair=['Sprach-QM: '+e for e in sem['repair_reasons']];print(f'LANGUAGE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
                break
            if not a.language_sane(x['caption']):
                if attempt<3:repair=['Deutsch/PR-/KI-Sprech deterministisch bereinigen'];continue
                break
            x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
        x['semantic_qm']='TECHNICAL-DEFER' if x.get('technical_qm_deferred') else 'FAIL';x['rewrite_count']=min(2,attempt-1);return False

    a.lock_source_series=lock;a.series_for_raw=series_for;a.series_for=series_for
    a._editor_prompt=prompt;a.fact_whitelist_errors=whitelist_errors;a.qualify_copy=qualify
    a.VERSION='V8.5.6'
    return a
