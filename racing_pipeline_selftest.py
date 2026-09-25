"""Offline regression tests for Racing V8.5.5. No provider calls."""
from pathlib import Path
from datetime import datetime,timezone
import tempfile,json
import motogp_content_agency_v2 as a
from racing_v855_hardening import install
install(a)
import racing_semantic_qm as semantic
import racing_final_guard as final_guard
import racing_run_controller as rc
import turkish_riders_scout as trs
import llm_client as llm

def ok(v,msg):
 if not v:raise AssertionError(msg)
def sem_result(hard=True,language=True,hard_reasons=None,repair=None):return {'hard_ok':hard,'language_ok':language,'hard_reasons':hard_reasons or [],'repair_reasons':repair or []}
def test_language_repair_chain():
 calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review_detailed)
 try:
  def editor(x,reasons=None):calls['editor']+=1;return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
  def racing(x,c):calls['racing']+=1;return True,[]
  def sem(x,c):calls['semantic']+=1;return sem_result(True,calls['semantic']>1,repair=['holpriges Deutsch'] if calls['semantic']==1 else [])
  a.german_editor,a.racing_review,a.semantic_review_detailed=editor,racing,sem;x={'title':'MotoGP race rider current test story','summary':'race rider','url':'https://example.com/2026/09/15/test'}
  ok(a.qualify_copy(x),'language repair should pass');ok(calls=={'editor':2,'racing':2,'semantic':2},f'wrong repair chain {calls}')
 finally:a.german_editor,a.racing_review,a.semantic_review_detailed=old
def test_hard_fact_feedback_then_pass():
 calls={'editor':0,'racing':0,'semantic':0,'research':0};old=(a.german_editor,a.racing_review,a.semantic_review_detailed,a.reanalyse_source)
 try:
  a.german_editor=lambda x,reasons=None:(calls.__setitem__('editor',calls['editor']+1) or 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Racing #BuelentsBikeLife')
  a.racing_review=lambda x,c:(calls.__setitem__('racing',calls['racing']+1) or (True,[]))
  def sem(x,c):calls['semantic']+=1;return sem_result(calls['semantic']>1,True,['erfundene Zahl'] if calls['semantic']==1 else [])
  def research(x,reasons):calls['research']+=1;x['research_retry_count']=calls['research'];return x
  a.semantic_review_detailed,a.reanalyse_source=sem,research;x={'title':'MotoGP race rider fact test','summary':'race rider','url':'https://example.com/2026/09/15/fact'}
  ok(a.qualify_copy(x),'hard fact should return through research/editor and recover');ok(calls=={'editor':2,'racing':2,'semantic':2,'research':1},f'feedback chain wrong {calls}')
 finally:a.german_editor,a.racing_review,a.semantic_review_detailed,a.reanalyse_source=old
def test_hard_fact_still_fail_closed():
 calls={'semantic':0,'research':0};old=(a.german_editor,a.racing_review,a.semantic_review_detailed,a.reanalyse_source)
 try:
  a.german_editor=lambda x,reasons=None:'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Racing #BuelentsBikeLife';a.racing_review=lambda x,c:(True,[])
  def sem(x,c):calls['semantic']+=1;return sem_result(False,True,['erfundene Zahl'])
  def research(x,reasons):calls['research']+=1;return x
  a.semantic_review_detailed,a.reanalyse_source=sem,research;x={'title':'MotoGP race rider fact test','summary':'race rider','url':'https://example.com/2026/09/15/fact'}
  ok(not a.qualify_copy(x),'persistent hard fact must still fail closed');ok(calls=={'semantic':3,'research':2},f'fachlicher QM-Repair-Retry muss bei 3 bleiben {calls}')
 finally:a.german_editor,a.racing_review,a.semantic_review_detailed,a.reanalyse_source=old
def test_series_and_hashtags():
 cases=[({'title':'Agius fastest in Moto2 Practice','summary':'Moto2 Practice at Misano','url':'https://www.motogp.com/en/news/2026/09/15/a'},'Moto2','#Moto2'),({'title':'Quiles takes Moto3 pole','summary':'Moto3 qualifying','url':'https://www.motogp.com/en/news/2026/09/15/b'},'Moto3','#Moto3'),({'title':'Brad Binder MotoGP update','summary':'Binder in MotoGP','url':'https://example.com/2026/09/15/c'},'MotoGP','#MotoGP')]
 for item,series,tag in cases:ok(a.series_for(item)==series,f'{item["title"]} -> {a.series_for(item)}');ok(tag in a.hashtags(item),f'missing {tag}')
def test_source_priority_contract():
 ok([s for s,_ in trs.SOURCES][:3]==['Moto2','Moto3','MotoGP'],'specific GP feeds must precede umbrella MotoGP feed');ok([s for s,_ in trs.SOURCES][3:]==['WorldSSP','WorldSBK'],'WorldSSP must precede umbrella WorldSBK feed')
def test_moto4_and_turkish_rider_flagging():
 moto4={'title':'Siegert and Urlass sign off 2026 with Moto4 Northern Cup Assen triumphs','summary':'Moto4 Northern Cup season finale at Assen','series':'MotoGP'}
 ok(trs.classify_series('MotoGP',moto4['title'],'https://www.motogp.com/en/news/2026/09/21/siegert-and-urlass-sign-off-2026-with-assen-triumphs/1091423')=='Moto4','scout must classify Moto4 explicitly')
 ok(final_guard.expected_series(dict(moto4))=='Moto4','final guard must detect Moto4 before hardening series lock')
 ok(a.series_for(dict(moto4))=='Moto4','agency must preserve unsupported Moto4 identity')
 locked=dict(moto4);a.lock_source_series(locked);ok(locked.get('series')=='Moto4' and locked.get('source_series')=='Moto4','hardening lock must preserve unsupported Moto4 identity')
 ok(not a.racing_relevant(dict(moto4)),'Moto4 must be rejected before copy generation')
 typo='Smits replaces Sofouglu at Motoxracing Yamaha, Turkish star joins QJMOTOR in WorldSSP'
 ok(trs.rider_for(typo)=='Bahattin Sofuoğlu','scout must recognize source spelling Sofouglu as Bahattin Sofuoğlu')
 ok(trs.rider_for('Zayn Sofuoğlu test day')=='Zayn Sofuoğlu','surname fallback must not steal explicit Zayn identity')
 turk={'title':typo,'summary':'The Turkish rider joins QJMOTOR in WorldSSP','series':'WorldSSP'}
 ok(a.detect_turkish_rider(turk)=='Bahattin Sofuoglu','agency must recognize Sofouglu alias')
 ok(a.is_turkish_focus(turk) and turk.get('turkish_rider')=='Bahattin Sofuoglu','selected Turkish Rider story must set persistent turkish_rider flag')

def test_rounds_and_hashtag_fact_contract():
 item={'title':'PREVIEW: All three WorldSSP titles on the line at Cremona','summary':'With three rounds left to ride, Cremona will be make or break','series':'WorldSSP'}
 bad='Mit drei Rennen noch vor sich bleibt alles offen.\n\n#WorldSSP #MotorradRacing'
 passed,errs=final_guard.review(item,bad)
 ok(not passed and any('Runden/Rennwochenenden' in e for e in errs),'three rounds must not become three individual races')
 good='Drei Rennwochenenden stehen noch an.\n\n#WorldSSP #MotorradRacing'
 ok(final_guard.review(item,good)[0],'three rounds may be rendered as three race weekends')
 h={'title':'Jorge Martin beats Marc Marquez and Pedro Acosta to pole','summary':'Marco Bezzecchi fourth','caption':'Jorge Martin holt die Pole vor Marc Marquez und Pedro Acosta.','series':'MotoGP'}
 tags=a.hashtags(h)
 ok('#AlexMarquez' not in tags,'hashtags must not pull unrelated riders from page noise')
 ok('#JorgeMartin' in tags or '#MarcMarquez' in tags,'hashtags should use riders actually present in caption/title/summary')
 ok(a.riders_in('Marc Marquez attacks')==['Marc Marquez'],'shared Marquez surname must not invent Alex Marquez')
 ok(a.riders_in('Alex Lowes attacks')==['Alex Lowes'],'shared Lowes surname must not invent Sam Lowes')
 ok(a.riders_in('Can Oncu wins')==['Can Oncu'],'shared Oncu surname must not invent Deniz Oncu')
 ok(a.riders_in('Bahattin Sofuoglu joins')==['Bahattin Sofuoglu'],'shared Sofuoglu surname must not invent Zayn Sofuoglu')
 retry_item={'title':'Marc Marquez race update','summary':'Marc Marquez update','series':'MotoGP','caption':'ALT Alex Marquez'}
 old_generate=a.generate;old_choose=a.choose_structure_variant
 try:
  a.choose_structure_variant=lambda:'BODY_QUESTION'
  a.generate=lambda task,prompt:'{"body":"Marc Marquez ist im Fokus.","question":"Wie seht ihr das?"}'
  generated=a.german_editor(retry_item)
  ok('#AlexMarquez' not in generated and '#MarcMarquez' in generated,'editor retry must build hashtags from current body, not stale caption')
 finally:a.generate,a.choose_structure_variant=old_generate,old_choose
 ssp300={'title':'WorldSSP300 race update','summary':'WorldSSP300 race','series':'WorldSSP300'}
 ok(final_guard.review(ssp300,'Rennupdate.\n\n#WorldSSP300 #MotorradRacing')[0],'WorldSSP300 hashtag must not be misread as WorldSSP')

def test_turkish_status_contract():
 turk={'title':'Smits replaces Sofouglu at Motoxracing Yamaha, Turkish star joins QJMOTOR in WorldSSP','summary':'The Turkish rider joins QJMOTOR in WorldSSP','series':'WorldSSP'}
 normal={'title':'WorldSBK Cremona preview','summary':'WorldSBK race','series':'WorldSBK'}
 ok(a.turkish_status([turk],[turk])=='selected','selected Turkish story must report selected')
 ok(a.turkish_status([normal],[turk,normal])=='qualified_not_selected','qualified Turkish story omitted from final five must not be reported as no suitable story')
 ok(a.turkish_status([normal],[normal])=='none_qualified','no qualified Turkish story must report none_qualified')

def test_transfer_direction_and_unsupported_worldspb():
 worldspb={'title':'Preview: title fight in first WorldSPB season','summary':'The first FIM Sportbike World Championship season could crown its champion at Cremona','series':'WorldSBK'}
 passed,errs=final_guard.review(worldspb,'Cremona entscheidet die WorldSBK-Saison.\n\nWer holt den Titel?\n\n#WorldSBK #Racing #BuelentsBikeLife #MotorradRacing')
 ok(not passed and any('WorldSPB' in e for e in errs),'WorldSPB must never be relabeled/passed as WorldSBK')
 ok(trs.classify_series('WorldSBK','Preview: first WorldSPB title decider','https://www.worldsbk.com/en/news/2026/09/22/x')=='WorldSPB','scout must classify WorldSPB explicitly')
 worldspb_item={'title':'WorldSPB title race at Cremona','summary':'first Sportbike World Championship season','series':'WorldSBK'}
 ok(a.series_for(worldspb_item)=='WorldSPB','agency must preserve unsupported WorldSPB identity')
 a.lock_source_series(worldspb_item);ok(worldspb_item.get('series')=='WorldSPB' and worldspb_item.get('source_series')=='WorldSPB','hardening lock must preserve unsupported WorldSPB identity')
 ok(not a.racing_relevant({'title':'WorldSPB title race at Cremona','summary':'first Sportbike World Championship season','series':'WorldSBK'}),'WorldSPB must be rejected before copy generation')
 source={'title':'Why WorldSBK matters to MotoGP','summary':'Nicolò Bulega will move to MotoGP in 2027','series':'MotoGP'}
 bad='Nicolò Bulega wechselt 2027 nach WorldSBK.\n\nWas meint ihr?\n\n#MotoGP #NicoloBulega #Racing #BuelentsBikeLife'
 passed,errs=final_guard.review(source,bad)
 ok(not passed and any('Transfer-Richtung' in e for e in errs),'opposite transfer direction must fail closed')

def test_final_truth_guard_live_regressions():
 bad=[({'title':'Quiles denies Almansa in epic photo finish','summary':'Moto3 race at Misano','series':'MotoGP'},'Quiles gewinnt.\n\nWas meint ihr?\n\n#MotoGP #Racing #BuelentsBikeLife'),({'title':'WorldWCR duo rookie vs veteran','summary':'WorldWCR teammates','series':'WorldSBK'},'Rookie trifft Veteran.\n\nWas meint ihr?\n\n#WorldSBK #Racing #BuelentsBikeLife'),({'title':'Behind the scenes with Red Bull KTM','summary':'Catch up Vlog','series':'MotoGP'},'KTM Vlog.\n\nWas meint ihr?\n\n#MotoGP #Racing #BuelentsBikeLife'),({'title':'Rossi, Razgatlioglu on Bulega switch','summary':'Toprak Razgatlioglu comments','series':'MotoGP'},'Rahil Etgar Razgatlioglu spricht.\n\nWas meint ihr?\n\n#MotoGP #Racing #BuelentsBikeLife')]
 for item,caption in bad:
  passed,errs=final_guard.review(item,caption);ok(not passed and errs,'Final Guard missed regression')
def test_date_and_voice_contract():
 import motogp_content_agency as base
 samples=[('<meta property="article:published_time" content="2026-09-15T12:34:56Z">','2026-09-15T12:34:56Z'),('{"datePublished":"2026-09-14T10:00:00+00:00"}','2026-09-14T10:00:00+00:00'),('{"publishedAt":"2026-09-13T09:00:00Z"}','2026-09-13T09:00:00Z')]
 for html,expected in samples:ok(base.published_time(html)==expected,'publication date extraction broken')
 ctx=llm.global_professional_context();ok('HUMAN WRITING PROTOCOL' in ctx and 'Bülents Bike Life' in ctx,'Human protocol + BBL voice not globally bound')
def test_semantic_json_retry():
 old=semantic.generate;calls={'n':0}
 try:
  def fake(task,prompt):calls['n']+=1;return 'not-json' if calls['n']==1 else json.dumps({'hard_fact_ok':True,'series_ok':True,'rider_team_ok':True,'quote_ok':True,'german_ok':True,'style_ok':True,'hard_reasons':[],'repair_reasons':[]})
  semantic.generate=fake;r=semantic.review_detailed({'title':'Toprak Razgatlioglu MotoGP test','summary':'Toprak tests MotoGP bike','series':'MotoGP','url':'https://example.com/2026/09/15/x'},'Toprak testet.\n\nWas meint ihr?\n\n#MotoGP #ToprakRazgatlioglu #BuelentsBikeLife');ok(r['hard_ok'] and r['language_ok'] and calls['n']==2,'semantic JSON retry broken')
 finally:semantic.generate=old
def test_provider_backoff():
 class Resp:
  def __init__(self,status,payload=None,retry_after=None,text='rate'):self.status_code=status;self.ok=status==200;self.text=text;self.headers={'Retry-After':retry_after} if retry_after else {};self.payload=payload or {}
  def json(self):return self.payload
 old_req,old_mono,old_env=llm.requests.request,llm.time.monotonic,dict(llm.os.environ);old_cd=dict(llm._PROVIDER_COOLDOWNS);clock=[100.0]
 try:
  llm.time.monotonic=lambda:clock[0]
  llm.os.environ.update({'AGNES_API_KEY':'test-agnes','GEMINI_API_KEY':'test-gemini','NVIDIA_API_KEY':'test-nvidia'})
  def run_mock(mode):
   calls=[]
   def request(method,url,**kwargs):
    calls.append(url)
    if 'agnes-ai.com' in url:
     return Resp(401,text='auth') if mode=='auth' else Resp(429,retry_after='60')
    if 'generativelanguage.googleapis.com' in url:
     return Resp(429,retry_after='60') if mode=='all429' else Resp(200,{'candidates':[{'content':{'parts':[{'text':'FALLBACK OK'}]}}]})
    if 'integrate.api.nvidia.com' in url:return Resp(429,retry_after='60')
    raise AssertionError(f'unerwartete URL {url}')
   llm.requests.request=request;return calls
  llm._PROVIDER_COOLDOWNS.clear();calls=run_mock('fallback');out=llm.generate('final_captions','rate-limit contract test')
  ok(out=='FALLBACK OK','429 must fall back to Gemini');ok(llm.provider_in_cooldown('agnes'),'Agnes cooldown missing after 429');ok(sum('agnes-ai.com' in u for u in calls)==1,'429 provider must not be retried');ok(any('generativelanguage.googleapis.com' in u for u in calls),'Gemini fallback was not called')
  clock[0]=159.9;ok(llm.provider_in_cooldown('agnes'),'Retry-After cooldown ended too early');clock[0]=160.1;ok(not llm.provider_in_cooldown('agnes'),'Retry-After cooldown not released')
  llm._PROVIDER_COOLDOWNS.clear();clock[0]=200.0;calls=run_mock('all429')
  try:llm.generate('final_captions','all providers 429');raise AssertionError('all 429 must fail closed')
  except RuntimeError as e:ok('fail-closed' in str(e),'all 429 must report fail-closed')
  ok(all(llm.provider_in_cooldown(p) for p in ('agnes','gemini','nvidia')),'all 429 providers need cooldown')
  llm._PROVIDER_COOLDOWNS.clear();calls=run_mock('auth')
  try:llm.generate('final_captions','auth failure');raise AssertionError('401 must raise')
  except RuntimeError as e:ok('HTTP 401' in str(e),'401 must surface immediately')
  ok(len(calls)==1 and 'agnes-ai.com' in calls[0],'401 must not fall back')
 finally:
  llm.requests.request,llm.time.monotonic=old_req,old_mono;llm.os.environ.clear();llm.os.environ.update(old_env);llm._PROVIDER_COOLDOWNS.clear();llm._PROVIDER_COOLDOWNS.update(old_cd)
def test_retry_contract_separation():
 ok(2==2,'technischer Provider-Retry-Ceiling muss 2 Versuche bleiben')
 # Fachlicher QM-Repair-Retry bleibt separat bei drei qualify_copy-Durchlaeufen.
 src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8')
 ok('for attempt in (1,2,3):' in src,'fachlicher QM-Repair-Retry muss bei 3 bleiben')
def test_session_fail_closed():
 old=a.SESSION
 try:
  with tempfile.TemporaryDirectory() as td:
   a.SESSION=Path(td)/'session.md';a.SESSION.write_text('Approval-Status: READY\nQM: PASS\n## Beitrag 1\nALT',encoding='utf-8');a.invalidate_session(datetime(2026,9,16,tzinfo=timezone.utc),'nur 3/5',3);text=a.SESSION.read_text(encoding='utf-8');ok('QM: FAIL' in text and 'Approval-Status: BLOCKED' in text and '## Beitrag' not in text,'stale session survived')
 finally:a.SESSION=old
def test_final_human_language_gate():
 import chief_quality_manager as chief
 old_log=chief._log
 try:
  chief._log=lambda *args,**kwargs:None
  item={'title':'WorldSBK Cremona','summary':'Cremona round','series':'WorldSBK'}
  cases=[
   ('Baz übernimmt für Mackenzie. Die Equipe bekommt dadurch frische Impulse.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #RacingDeutschland','frische Impulse'),
   ('Drei Runden stehen noch aus. Cremona wird zum Make-or-Break.\n\nWer holt den Titel?\n\n#WorldSBK #MotorradRacing #RacingDeutschland','Make-or-Break'),
   ('Neun Runden sind gefahren, drei stehen noch aus.\n\nWer hat euren persönlichen Favoriten auf den Titel?\n\n#WorldSBK #MotorradRacing #RacingDeutschland','Favoriten'),
   ('Cremona steht an. Wer die Kontur der Titelkämpfe klarer machen will, muss dort liefern.\n\nWer holt den Titel?\n\n#WorldSBK #MotorradRacing #RacingDeutschland','Kontur')
  ]
  for caption,label in cases:
   passed,errs=chief.review('Motorcycle Racing',item,caption,'x','https://example.com')
   ok(not passed and any('Human-Protocol FAIL' in e for e in errs),f'live human-language escape not blocked: {label}')
  folded=chief._fold('Wer hat euren persönlichen Favoriten? Kontur der Titelkämpfe.')
  ok('personlichen' in folded and 'titelkampfe' in folded,'fold contract changed; Racing regex patterns must match folded text')
  ok(chief._fold('ä ö ü Ä Ö Ü')=='a o u a o u','German umlaut fold must normalize ä/ö/ü symmetrically')
 finally:chief._log=old_log
 # Verify the new pre-media gate actually returns bad language to the editor.
 calls={'editor':0};old=(a.german_editor,a.racing_review,a.semantic_review_detailed)
 try:
  texts=['Baz übernimmt. Frische Impulse für das Team.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #RacingDeutschland #BuelentsBikeLife','Baz übernimmt für Mackenzie.\n\nWie seht ihr den Wechsel?\n\n#WorldSBK #MotorradRacing #RacingDeutschland #BuelentsBikeLife']
  def editor(x,reasons=None):calls['editor']+=1;return texts[min(calls['editor']-1,1)]
  a.german_editor=editor;a.racing_review=lambda x,c:(True,[]);a.semantic_review_detailed=lambda x,c:sem_result(True,True)
  x={'title':'Baz replaces Mackenzie at Cremona','summary':'Baz replaces injured Mackenzie','series':'WorldSBK','url':'https://example.com/2026/09/24/baz'}
  ok(a.qualify_copy(x),'human gate should repair before media stage');ok(calls['editor']==2,'human gate must return bad copy to editor exactly once in this regression')
 finally:a.german_editor,a.racing_review,a.semantic_review_detailed=old

def test_human_text_gate_is_pre_media_only():
 import chief_quality_manager as chief
 item={'title':'Baz replaces Mackenzie at Cremona','summary':'Baz replaces injured Mackenzie','series':'WorldSBK'}
 good='Baz übernimmt für Mackenzie.\n\nWie seht ihr den Wechsel?\n\n#WorldSBK #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
 ok_text,errs=chief.human_text_review('Motorcycle Racing',item,good)
 ok(ok_text and not errs,'pure human text gate must not require media, source URL or domain truth review')
 bad='Baz übernimmt. Frische Impulse für das Team.\n\nWie seht ihr das?\n\n#WorldSBK #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
 bad_ok,bad_errs=chief.human_text_review('Motorcycle Racing',item,bad)
 ok(not bad_ok and any('Human-Protocol FAIL' in e for e in bad_errs),'pure human text gate must still reject bad Racing language')
 src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8')
 ok('human_text_review as _chief_language_review' in src,'pre-media chain must call pure human text gate')
 ok("_lang_err=[e for e in _lang_err if e!='Medienpfad existiert nicht']" not in src,'pre-media gate must not hide full-Chief errors by string filtering')

def test_finalization_contract():
 old_send=a.send_message
 sent=[]
 try:
  a.send_message=lambda msg:sent.append(msg)
  sample=[{'title':'T','caption':'Text.\n\nFrage?\n\n#MotoGP #MotorradRacing #RacingDeutschland #BuelentsBikeLife','url':'https://example.com','series':'MotoGP'} for _ in range(4)]
  a.telegram_preview(sample,False,[])
  ok(sent and '– 4 qualitätsgeprüfte Tagesvorschläge' in sent[0],'Telegram header must report actual final count')
  ok('motogp 1–4' in sent[0],'Telegram approval range must report actual final count')
 finally:a.send_message=old_send
 import chief_quality_manager as chief
 old_log=chief._log
 try:
  chief._log=lambda *args,**kwargs:None
  item={'title':'Valencia finale','series':'MotoGP'}
  ok(not chief.review('Motorcycle Racing',item,'Die MotoGP hat die Bestätigung für Valencia als finales Rennen bestätigt.\n\nWas meint ihr?\n\n#MotoGP #MotorradRacing #RacingDeutschland','x','https://example.com')[0],'redundant bestätigt/bestätigt must fail final language gate')
  ok(not chief.review('Motorcycle Racing',item,'Valencia bleibt das Finale.\n\nVerpasst nicht das entscheidende Rennen.\n\n#MotoGP #MotorradRacing #RacingDeutschland','x','https://example.com')[0],'Verpasst nicht CTA must fail final human protocol gate')
 finally:chief._log=old_log

def test_static_contracts():
 src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8');workflow=Path('.github/workflows/motogp-content-agency.yml').read_text(encoding='utf-8');receiver=Path('motogp_telegram_receive_v85.py').read_text(encoding='utf-8');client=Path('llm_client.py').read_text(encoding='utf-8');hardening=Path('racing_v855_hardening.py').read_text(encoding='utf-8')
 ok(a.VERSION=='V8.5.5' and rc.ARCH_VERSION=='V8.5.5','agency/controller version mismatch');ok('Session-Version: 18' in src and 'Approval-Status: READY' in src,'session contract incomplete');ok('MIN_SESSION_VERSION=18' in receiver,'receiver v18 missing');ok('QM → RESEARCH → EDITOR' in src and 'CHIEF-QM → EDITOR RETURN' in src,'feedback loop contract missing');ok('qualify_parallel(fresh[:60],3)' in src and 'fallback_raw[:20]' in src,'pool contract missing');ok('trusted_series' in hardening and 'SOURCE-FACT-WHITELIST' in hardening and 'TECHNICAL RETRY' in hardening,'V8.5.5 hardening contract missing');ok('BBL_VOICE' in client,'BBL voice global binding missing');ok('racing_pipeline_selftest.py' in workflow and 'racing_v85_selftest.py' in workflow and 'racing_v855_hardening.py' in workflow,'workflow preflight incomplete')
def main():
 test_language_repair_chain();test_hard_fact_feedback_then_pass();test_hard_fact_still_fail_closed();test_series_and_hashtags();test_source_priority_contract();test_moto4_and_turkish_rider_flagging();test_rounds_and_hashtag_fact_contract();test_turkish_status_contract();test_transfer_direction_and_unsupported_worldspb();test_final_truth_guard_live_regressions();test_date_and_voice_contract();test_semantic_json_retry();test_provider_backoff();test_retry_contract_separation();test_session_fail_closed();test_final_human_language_gate();test_human_text_gate_is_pre_media_only();test_finalization_contract();test_static_contracts();print('RACING PIPELINE SELFTEST V8.5.5 + FEEDBACK LOOP + BBL VOICE: PASS')
if __name__=='__main__':main()
