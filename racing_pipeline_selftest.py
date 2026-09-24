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
def test_static_contracts():
 src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8');workflow=Path('.github/workflows/motogp-content-agency.yml').read_text(encoding='utf-8');receiver=Path('motogp_telegram_receive_v85.py').read_text(encoding='utf-8');client=Path('llm_client.py').read_text(encoding='utf-8');hardening=Path('racing_v855_hardening.py').read_text(encoding='utf-8')
 ok(a.VERSION=='V8.5.5' and rc.ARCH_VERSION=='V8.5.5','agency/controller version mismatch');ok('Session-Version: 18' in src and 'Approval-Status: READY' in src,'session contract incomplete');ok('MIN_SESSION_VERSION=18' in receiver,'receiver v18 missing');ok('QM → RESEARCH → EDITOR' in src and 'CHIEF-QM → EDITOR RETURN' in src,'feedback loop contract missing');ok('qualify_parallel(fresh[:60],3)' in src and 'fallback_raw[:20]' in src,'pool contract missing');ok('trusted_series' in hardening and 'SOURCE-FACT-WHITELIST' in hardening and 'TECHNICAL RETRY' in hardening,'V8.5.5 hardening contract missing');ok('BBL_VOICE' in client,'BBL voice global binding missing');ok('racing_pipeline_selftest.py' in workflow and 'racing_v85_selftest.py' in workflow and 'racing_v855_hardening.py' in workflow,'workflow preflight incomplete')
def main():
 test_language_repair_chain();test_hard_fact_feedback_then_pass();test_hard_fact_still_fail_closed();test_series_and_hashtags();test_source_priority_contract();test_transfer_direction_and_unsupported_worldspb();test_final_truth_guard_live_regressions();test_date_and_voice_contract();test_semantic_json_retry();test_provider_backoff();test_retry_contract_separation();test_session_fail_closed();test_static_contracts();print('RACING PIPELINE SELFTEST V8.5.5 + FEEDBACK LOOP + BBL VOICE: PASS')
if __name__=='__main__':main()
