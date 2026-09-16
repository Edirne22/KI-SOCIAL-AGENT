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
  ok(not a.qualify_copy(x),'persistent hard fact must still fail closed');ok(calls=={'semantic':3,'research':2},f'wrong retry ceiling {calls}')
 finally:a.german_editor,a.racing_review,a.semantic_review_detailed,a.reanalyse_source=old
def test_series_and_hashtags():
 cases=[({'title':'Agius fastest in Moto2 Practice','summary':'Moto2 Practice at Misano','url':'https://www.motogp.com/en/news/2026/09/15/a'},'Moto2','#Moto2'),({'title':'Quiles takes Moto3 pole','summary':'Moto3 qualifying','url':'https://www.motogp.com/en/news/2026/09/15/b'},'Moto3','#Moto3'),({'title':'Brad Binder MotoGP update','summary':'Binder in MotoGP','url':'https://example.com/2026/09/15/c'},'MotoGP','#MotoGP')]
 for item,series,tag in cases:ok(a.series_for(item)==series,f'{item["title"]} -> {a.series_for(item)}');ok(tag in a.hashtags(item),f'missing {tag}')
def test_source_priority_contract():
 ok([s for s,_ in trs.SOURCES][:3]==['Moto2','Moto3','MotoGP'],'specific GP feeds must precede umbrella MotoGP feed');ok([s for s,_ in trs.SOURCES][3:]==['WorldSSP','WorldSBK'],'WorldSSP must precede umbrella WorldSBK feed')
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
  def __init__(self,status):self.status_code=status;self.ok=status==200;self.text='rate';self.headers={}
  def json(self):return {'ok':True}
 old_req,old_sleep=llm.requests.request,llm.time.sleep;seq=[Resp(429),Resp(200)];c={'n':0,'sleep':0}
 try:
  llm.requests.request=lambda *args,**kwargs:(c.__setitem__('n',c['n']+1) or seq.pop(0));llm.time.sleep=lambda _:(c.__setitem__('sleep',c['sleep']+1));out=llm._request_json('POST','https://example.com',{}, {},1,max_retries=2);ok(out=={'ok':True} and c=={'n':2,'sleep':1},f'provider retry {c}')
 finally:llm.requests.request,llm.time.sleep=old_req,old_sleep
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
 test_language_repair_chain();test_hard_fact_feedback_then_pass();test_hard_fact_still_fail_closed();test_series_and_hashtags();test_source_priority_contract();test_final_truth_guard_live_regressions();test_date_and_voice_contract();test_semantic_json_retry();test_provider_backoff();test_session_fail_closed();test_static_contracts();print('RACING PIPELINE SELFTEST V8.5.5 + FEEDBACK LOOP + BBL VOICE: PASS')
if __name__=='__main__':main()
