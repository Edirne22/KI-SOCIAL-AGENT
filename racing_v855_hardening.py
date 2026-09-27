"""V8.5.5 runtime hardening for the Racing chain.
Keeps source facts immutable across feedback loops, constrains editor facts, and separates provider failures from editorial rejects.
"""
import re,time,json
from racing_final_guard import expected_series
from racing_language_rules import prompt_contract as racing_lexicon_contract, deterministic_errors as racing_lexicon_errors

VALID=('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300')
UNSUPPORTED=('WorldWCR','WorldSPB','Moto4')

def install(a):
    original_prompt=a._editor_prompt

    def transfer(x):
        s=a.fold(' '.join((x.get('title',''),x.get('summary',''))))
        if 'motogp' in s and any(p in s for p in ('join motogp','joins motogp','to motogp','motogp switch','moves to motogp','move to motogp','switch to motogp','motogp debut','new motogp star')): return 'MotoGP'
        if ('worldsbk' in s or 'world superbike' in s) and any(p in s for p in ('join worldsbk','joins worldsbk','to worldsbk','worldsbk switch','moves to worldsbk','move to worldsbk','switch to worldsbk')): return 'WorldSBK'
        return ''

    def lock(x,declared=None):
        frozen=str(x.get('trusted_series','')).strip()
        dest=transfer(x)
        inferred=expected_series(x)
        # Current explicit source facts outrank a stale trusted lock. A candidate
        # can enter through an umbrella/misclassified feed and later gain a WSSP/
        # WorldSBK/Moto* headline during source re-analysis.
        if frozen in VALID and not dest and inferred not in VALID and inferred not in UNSUPPORTED:
            x.update(series=frozen,source_series=frozen,series_locked=True)
            return x
        supplied=str(declared or x.get('source_series') or x.get('series') or '').strip()
        if inferred in UNSUPPORTED:
            # Preserve the real source class instead of collapsing an unsupported
            # championship into the umbrella feed (e.g. WorldSPB -> WorldSBK).
            x['series']=inferred;x['source_series']=inferred;x['series_locked']=True
            x['series_origin']='source-fact-unsupported'
            x.pop('trusted_series',None)
            return x
        chosen=dest or (inferred if inferred in VALID else '') or (supplied if supplied in VALID else '')
        if chosen:
            x['trusted_series']=chosen;x['series']=chosen;x['source_series']=chosen;x['series_locked']=True
            x['series_origin']='explicit-transfer' if dest else ('source-fact-lock' if inferred in VALID else 'official-feed')
        return x

    def series_for(x):
        inferred=expected_series(x)
        if inferred in UNSUPPORTED:
            lock(x)
            return inferred
        frozen=str(x.get('trusted_series','')).strip()
        if frozen in VALID:return frozen
        lock(x)
        return str(x.get('trusted_series') or x.get('series') or 'MotoGP')

    def fact_packet(x):
        source=' '.join((str(x.get('title','')),str(x.get('summary',''))))
        return {'series':series_for(x),'title':' '.join(str(x.get('title','')).split()),'summary':' '.join(str(x.get('summary','')).split()),'riders':a.riders_in(source),'numbers':sorted(set(re.findall(r'(?<![A-Za-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',source)))}

    def whitelist_errors(x,caption):
        f=fact_packet(x);errs=list(racing_lexicon_errors(caption));src=a.fold(f['title']+' '+f['summary']);cap=a.fold(re.sub(r'#[^\s]+','',caption or ''))
        cfo=f['series']
        series_tokens={
            'MotoGP': ('motogp',),
            'Moto2': ('moto2',),
            'Moto3': ('moto3',),
            'WorldSBK': ('worldsbk','world superbike'),
            'WorldSSP': ('worldssp','world supersport','wssp','supersport'),
            'WorldSSP300': ('worldssp300','worldssp 300','wssp300','supersport 300'),
        }
        for other,tokens in series_tokens.items():
            if other==cfo:continue
            if any(re.search(r'(?<![a-z0-9])'+re.escape(token)+r'(?![a-z0-9])',cap) for token in tokens) and not any(re.search(r'(?<![a-z0-9])'+re.escape(token)+r'(?![a-z0-9])',src) for token in tokens):
                errs.append(f'Source-Fact-Whitelist: Falsche Serie {other} im Text obwohl CFO {cfo} ist')
        allowed={a.fold(n) for n in f['riders']};allowed_last={n.split()[-1] for n in allowed}
        # Shared Turkish surnames (Öncü, Sofuoğlu) cannot be resolved by riders_in()
        # from surname alone. Human-selected turkish_rider is safe only when that
        # same folded surname is explicitly present in the source packet.
        selected=a.fold(str(x.get('turkish_rider','')).strip())
        selected_last=selected.split()[-1] if selected else ''
        if selected_last and len(selected_last)>=4 and re.search(r'(?<![a-z])'+re.escape(selected_last)+r'(?![a-z])',src):
            allowed.add(selected);allowed_last.add(selected_last)
        for n in a.RIDERS_V2:
            fn=a.fold(n);last=fn.split()[-1]
            present=fn in cap or (len(last)>=5 and re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',cap))
            if present and fn not in allowed and last not in allowed_last:errs.append('Source-Fact-Whitelist: Fahrer nicht in Quelle: '+n)
        normalize_number=lambda n:re.sub(r'(?:s|km|mph|kph)
        for n in sorted(capnums-srcnums):errs.append('Source-Fact-Whitelist: Zahl nicht in Quelle: '+n)
        return errs

    def prompt(x,reasons=None,structure_variant=None):
        lock(x);base=original_prompt(x,reasons,structure_variant);facts=json.dumps(fact_packet(x),ensure_ascii=False)
        return base+'\n\n'+racing_lexicon_contract('V8.5.5-HARDENING')+'\n\nSOURCE-FACT-WHITELIST (GESCHLOSSEN): '+facts+'\nJede konkrete Person und jede Zahl im Post muss darin bzw. in TITEL/ZUSAMMENFASSUNG vorkommen. Orte, Teams und Hersteller nur nennen, wenn sie in TITEL/ZUSAMMENFASSUNG stehen. Nicht belegte Details weglassen, niemals aus Vorwissen ergaenzen.'

    def semantic_technical_retry(x,caption):
        # Provider/backoff retries are centralized in llm_client. Semantic QM gets
        # exactly one provider transaction so technical failures cannot multiply
        # with editor/priority repair loops.
        r=a.semantic_review_detailed(x,caption)
        if r.get('technical_error'):
            print('SEMANTIC-QM TECHNICAL DEFER:',x.get('title','')[:90],'|',str(r.get('technical_reason','provider'))[:180])
        return r

    def qualify(x,initial_reasons=None):
        if not a.racing_relevant(x):return False
        lock(x);repair=initial_reasons
        max_attempts=5 if x.get('priority_repair') else 3
        attempts=range(1,max_attempts+1)
        if x.get('priority_repair'):print('PRIORITY-REPAIR START max=5:',x.get('title','')[:90],'|',','.join(x.get('priority_reasons',[])))
        for attempt in attempts:
            lock(x);x['caption']=a.german_editor(x,repair);lock(x)
            if not x['caption']:
                if x.pop('editor_technical_error',None):
                    x['editor_qm']='TECHNICAL-DEFER';x['rewrite_count']=attempt-1
                    print('EDITOR TECHNICAL DEFER – no editorial retry consumed:',x.get('title','')[:90])
                    return False
                repair=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REPAIR attempt={attempt}:',x.get('title','')[:90]);continue
            w=whitelist_errors(x,x['caption'])
            if w:
                if attempt<max_attempts:repair=w;a.reanalyse_source(x,repair);lock(x);continue
                print('SOURCE-FACT-WHITELIST REJECT:',x.get('title','')[:90],'|','; '.join(w)[:600]);break
            r_ok,r_err=a.racing_review(x,x['caption']);x['qm_errors']=r_err
            if not r_ok:
                if attempt<max_attempts:repair=['Racing-QM: '+e for e in r_err];a.reanalyse_source(x,repair);lock(x);continue
                print('RACING-QM HARD REJECT after feedback loop:',x.get('title','')[:90],'|','; '.join(r_err)[:600]);break
            sem=semantic_technical_retry(x,x['caption'])
            if sem.get('technical_error'):
                # A provider/JSON outage is not a factual rejection. The candidate
                # has already passed deterministic source whitelist + Racing-QM.
                # Keep it eligible, but mark the semantic gate as degraded so the
                # final Chief/domain gates still run and the audit trail is explicit.
                x['technical_qm_deferred']=True
                x['semantic_qm']='DEGRADED-PASS'
                x['racing_qm']='PASS'
                x['rewrite_count']=attempt-1
                print('SEMANTIC-QM DEGRADED PASS – deterministic fact gates passed; provider unavailable:',x.get('title','')[:90])
                return True
            x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
            if not sem['hard_ok']:
                if attempt<max_attempts:repair=['Fakten-QM: '+e for e in sem['hard_reasons']];a.reanalyse_source(x,repair);lock(x);continue
                print(f'SEMANTIC HARD-FACT REJECT after feedback loop attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['hard_reasons'])[:700]);break
            if not sem['language_ok']:
                if attempt<max_attempts:repair=['Sprach-QM: '+e for e in sem['repair_reasons']];print(f'LANGUAGE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
                break
            if not a.language_sane(x['caption']):
                if attempt<max_attempts:repair=['Deutsch/PR-/KI-Sprech deterministisch bereinigen'];continue
                break
            # V8.5.5 replaces agency.qualify_copy at install time, so the same
            # pre-media Human Writing gate must live in this runtime chain too.
            # Keep this text-only: media/source/domain/final-truth stay in finish_item.
            from chief_quality_manager import human_text_review
            human_ok,human_err=human_text_review('Motorcycle Racing',x,x['caption'])
            if not human_ok:
                if attempt<max_attempts:repair=['Finales Human-Writing-Gate: '+e for e in human_err];print(f'HUMAN-GATE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
                print('HUMAN-GATE FINAL REJECT:',x.get('title','')[:90],'|','; '.join(human_err)[:600]);break
            x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
        x['semantic_qm']='TECHNICAL-DEFER' if x.get('technical_qm_deferred') else 'FAIL';x['rewrite_count']=min(max_attempts-1,attempt-1)
        if x.get('priority_repair'):print('PRIORITY BLOCKED after repair lane:',x.get('title','')[:90])
        return False

    a.lock_source_series=lock;a.series_for_raw=series_for;a.series_for=series_for
    a._editor_prompt=prompt;a.fact_whitelist_errors=whitelist_errors;a.qualify_copy=qualify
    a.VERSION='V8.5.5'
    return a
,'',n.replace(',','.'))
        # Source/provenance URLs are metadata, not editorial claims.  Their slug/ID
        # numbers must never enter the closed fact-number comparison.
        cap_facts=re.sub(r'https?://\\S+',' ',cap)
        srcnums={normalize_number(n) for n in re.findall(r'(?<![a-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',src)};capnums={normalize_number(n) for n in re.findall(r'(?<![a-z])\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?',cap_facts)}
        for n in sorted(capnums-srcnums):errs.append('Source-Fact-Whitelist: Zahl nicht in Quelle: '+n)
        return errs

    def prompt(x,reasons=None,structure_variant=None):
        lock(x);base=original_prompt(x,reasons,structure_variant);facts=json.dumps(fact_packet(x),ensure_ascii=False)
        return base+'\n\n'+racing_lexicon_contract('V8.5.5-HARDENING')+'\n\nSOURCE-FACT-WHITELIST (GESCHLOSSEN): '+facts+'\nJede konkrete Person und jede Zahl im Post muss darin bzw. in TITEL/ZUSAMMENFASSUNG vorkommen. Orte, Teams und Hersteller nur nennen, wenn sie in TITEL/ZUSAMMENFASSUNG stehen. Nicht belegte Details weglassen, niemals aus Vorwissen ergaenzen.'

    def semantic_technical_retry(x,caption):
        # Provider/backoff retries are centralized in llm_client. Semantic QM gets
        # exactly one provider transaction so technical failures cannot multiply
        # with editor/priority repair loops.
        r=a.semantic_review_detailed(x,caption)
        if r.get('technical_error'):
            print('SEMANTIC-QM TECHNICAL DEFER:',x.get('title','')[:90],'|',str(r.get('technical_reason','provider'))[:180])
        return r

    def qualify(x,initial_reasons=None):
        if not a.racing_relevant(x):return False
        lock(x);repair=initial_reasons
        max_attempts=5 if x.get('priority_repair') else 3
        attempts=range(1,max_attempts+1)
        if x.get('priority_repair'):print('PRIORITY-REPAIR START max=5:',x.get('title','')[:90],'|',','.join(x.get('priority_reasons',[])))
        for attempt in attempts:
            lock(x);x['caption']=a.german_editor(x,repair);lock(x)
            if not x['caption']:
                if x.pop('editor_technical_error',None):
                    x['editor_qm']='TECHNICAL-DEFER';x['rewrite_count']=attempt-1
                    print('EDITOR TECHNICAL DEFER – no editorial retry consumed:',x.get('title','')[:90])
                    return False
                repair=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REPAIR attempt={attempt}:',x.get('title','')[:90]);continue
            w=whitelist_errors(x,x['caption'])
            if w:
                if attempt<max_attempts:repair=w;a.reanalyse_source(x,repair);lock(x);continue
                print('SOURCE-FACT-WHITELIST REJECT:',x.get('title','')[:90],'|','; '.join(w)[:600]);break
            r_ok,r_err=a.racing_review(x,x['caption']);x['qm_errors']=r_err
            if not r_ok:
                if attempt<max_attempts:repair=['Racing-QM: '+e for e in r_err];a.reanalyse_source(x,repair);lock(x);continue
                print('RACING-QM HARD REJECT after feedback loop:',x.get('title','')[:90],'|','; '.join(r_err)[:600]);break
            sem=semantic_technical_retry(x,x['caption'])
            if sem.get('technical_error'):
                # A provider/JSON outage is not a factual rejection. The candidate
                # has already passed deterministic source whitelist + Racing-QM.
                # Keep it eligible, but mark the semantic gate as degraded so the
                # final Chief/domain gates still run and the audit trail is explicit.
                x['technical_qm_deferred']=True
                x['semantic_qm']='DEGRADED-PASS'
                x['racing_qm']='PASS'
                x['rewrite_count']=attempt-1
                print('SEMANTIC-QM DEGRADED PASS – deterministic fact gates passed; provider unavailable:',x.get('title','')[:90])
                return True
            x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
            if not sem['hard_ok']:
                if attempt<max_attempts:repair=['Fakten-QM: '+e for e in sem['hard_reasons']];a.reanalyse_source(x,repair);lock(x);continue
                print(f'SEMANTIC HARD-FACT REJECT after feedback loop attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['hard_reasons'])[:700]);break
            if not sem['language_ok']:
                if attempt<max_attempts:repair=['Sprach-QM: '+e for e in sem['repair_reasons']];print(f'LANGUAGE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
                break
            if not a.language_sane(x['caption']):
                if attempt<max_attempts:repair=['Deutsch/PR-/KI-Sprech deterministisch bereinigen'];continue
                break
            # V8.5.5 replaces agency.qualify_copy at install time, so the same
            # pre-media Human Writing gate must live in this runtime chain too.
            # Keep this text-only: media/source/domain/final-truth stay in finish_item.
            from chief_quality_manager import human_text_review
            human_ok,human_err=human_text_review('Motorcycle Racing',x,x['caption'])
            if not human_ok:
                if attempt<max_attempts:repair=['Finales Human-Writing-Gate: '+e for e in human_err];print(f'HUMAN-GATE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
                print('HUMAN-GATE FINAL REJECT:',x.get('title','')[:90],'|','; '.join(human_err)[:600]);break
            x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
        x['semantic_qm']='TECHNICAL-DEFER' if x.get('technical_qm_deferred') else 'FAIL';x['rewrite_count']=min(max_attempts-1,attempt-1)
        if x.get('priority_repair'):print('PRIORITY BLOCKED after repair lane:',x.get('title','')[:90])
        return False

    a.lock_source_series=lock;a.series_for_raw=series_for;a.series_for=series_for
    a._editor_prompt=prompt;a.fact_whitelist_errors=whitelist_errors;a.qualify_copy=qualify
    a.VERSION='V8.5.5'
    return a
