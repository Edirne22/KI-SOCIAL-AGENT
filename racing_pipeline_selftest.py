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
  from unittest.mock import patch
  calls={'editor':0,'racing':0,'semantic':0}
  def editor(x,reasons=None):
   calls['editor']+=1
   return 'Hook\n\nHolpriger Satz.\n\nFrage?\n\n#MotoGP #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
  def racing(x,c):calls['racing']+=1;return True,[]
  def sem(x,c):calls['semantic']+=1;return sem_result(True,'Holpriger' not in c,repair=['holpriges Deutsch'] if 'Holpriger' in c else [])
  with patch.object(a,'german_editor',editor),patch.object(a,'racing_review',racing),patch.object(a,'semantic_review_detailed',sem),patch.object(a,'generate',return_value=json.dumps({'patches':[{'old':'Holpriger Satz.','new':'Starker Satz.'}]})):
   x={'title':'MotoGP race rider current test story','summary':'race rider','url':'https://example.com/2026/09/15/test'}
   ok(a.qualify_copy(x),'language patch should pass')
   ok(calls=={'editor':1,'racing':2,'semantic':2} and patch.call_count==1,f'wrong patch chain {calls}')

def test_hard_fact_feedback_then_pass():
  from unittest.mock import patch
  caption='Hook\n\nUnbelegte Aussage.\n\nFrage?\n\n#MotoGP #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
  with patch.object(a,'german_editor',return_value=caption) as editor,patch.object(a,'racing_review',return_value=(True,[])),patch.object(a,'semantic_review_detailed',side_effect=[sem_result(False,['Harter Faktenfehler']),sem_result(True,True)]),patch.object(a,'generate',return_value=json.dumps({'patches':[{'old':'Unbelegte Aussage.','new':'Belegte Aussage.'}]})):
   x={'title':'MotoGP race rider fact test','summary':'race rider'}
   ok(a.qualify_copy(x),'fact patch should recover')
   ok(editor.call_count==1 and patch.call_count==1 and a.semantic_review_detailed.call_count==2,'patch budget wrong')

def test_hard_fact_still_fail_closed():
  from unittest.mock import patch
  caption='Hook\n\nBody\n\nFrage?\n\n#MotoGP #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
  with patch.object(a,'german_editor',return_value=caption) as editor,patch.object(a,'racing_review',return_value=(True,[])),patch.object(a,'semantic_review_detailed',return_value=sem_result(False,['Hard fail'])),patch.object(a,'generate',side_effect=[json.dumps({'patches':[{'old':'Body','new':'Patched body'}]}),json.dumps({'patches':[{'old':'Patched body','new':'Patched body'}]})]):
   x={'title':'MotoGP race rider fact test','summary':'race rider'}
   ok(not a.qualify_copy(x),'persistent hard fact must fail closed')
   ok(a.semantic_review_detailed.call_count==3 and a.generate.call_count==2 and editor.call_count==1,'wrong retry ceiling')

def test_series_and_hashtags():
  cases=[({'title':'Agius fastest in Moto2 Practice','summary':'Moto2 Practice at Misano','url':'https://www.motogp.com/en/news/2026/09/15/a'},'Moto2','#Moto2'),({'title':'Quiles takes Moto3 pole','summary':'Moto3 at Misano','url':'https://www.motogp.com/en/news/2026/09/15/b'},'Moto3','#Moto3'),({'title':'WorldSBK riders all set','summary':'WorldSBK riders test at Misano','url':'https://www.worldsbk.com/en/news/2026/09/15/c'},'WorldSBK','#WorldSBK')]
  for item,series,tag in cases:ok(a.series_for(item)==series,f'{item["title"]} -> {a.series_for(item)}');ok(tag in a.hashtags(item),f'missing {tag}')
def test_source_priority_contract():
  ok([s for s,_ in trs.SOURCES][:3]==['Moto2','Moto3','MotoGP'],'specific GP feeds must precede umbrella MotoGP feed');ok([s for s,_ in trs.SOURCES][3:]==['WorldSSP','WorldSBK'],'WorldSSP must precede WorldSBK')
def test_final_truth_guard_live_regressions():
  bad=[({'title':'Quiles denies Almansa in epic photo finish','summary':'Moto3 race at Misano','series':'MotoGP'},'Quiles gewinnt.\n\nWas meint ihr?\n\n#MotoGP #Racing #BuelentsBikeLife'),({'title':'Gonzalez wins WorldSBK race','summary':'WorldSBK race at Mugello','series':'WorldSBK'},'Gonzalez gewinnt.\n\nWarum nicht?\n\n#WorldSBK #MotorradRacing #BuelentsBikeLife')]
  for item,caption in bad:
   passed,errs=final_guard.review(item,caption);ok(not passed and errs,'Final Guard missed regression')
def test_date_and_voice_contract():
  import motogp_content_agency as base
  samples=[('<meta property="article:published_time" content="2026-09-15T12:34:56Z">','2026-09-15T12:34:56Z'),('{"datePublished":"2026-09-14T10:00:00+00:00"}','2026-09-14T10:00:00+00:00'),('{"published":"2026-09-13T08:00:00Z"}','2026-09-13T08:00:00Z')]
  for html,expected in samples:ok(base.published_time(html)==expected,'publication date extraction broken')
  ctx=llm.global_professional_context();ok('HUMAN WRITING PROTOCOL' in ctx and 'Bülents Bike Life' in ctx,'Human protocol + BBL voice not globally bound')
def test_semantic_json_retry():
  old=semantic.generate;calls={'n':0}
  try:
   def fake(task,prompt):calls['n']+=1;return 'not-json' if calls['n']==1 else json.dumps({'hard_fact_ok':True,'series_ok':True,'rider_team_ok':True,'quote_ok':True,'german_ok':True,'style_ok':True})
   semantic.generate=fake;r=semantic.review_detailed({'title':'Toprak Razgatlioglu MotoGP test','summary':'Toprak tests MotoGP bike','series':'MotoGP','url':'https://example.com/2026/09/15/x'},'Toprak und MotoGP.');ok(r['hard_ok'] and r['language_ok'],'semantic JSON retry must recover')
  finally:semantic.generate=old
def test_provider_backoff():
  class Resp:
   def __init__(self,status):self.status_code=status;self.ok=status==200;self.text='rate';self.headers={}
   def json(self):return {'ok':True}
  old_req,old_sleep=llm.requests.request,llm.time.sleep;seq=[Resp(429),Resp(200)];c={'n':0,'sleep':0}
  try:
   llm.requests.request=lambda *args,**kwargs:(c.__setitem__('n',c['n']+1) or seq.pop(0));llm.time.sleep=lambda _:(c.__setitem__('sleep',c['sleep']+1));out=llm._request_json('POST','https://example.com',{'x':1})
   ok(out=={'ok':True} and c['n']==2 and c['sleep']==1,'provider retry/backoff broken')
  finally:llm.requests.request,llm.time.sleep=old_req,old_sleep
def test_session_fail_closed():
  from unittest.mock import patch
  x={'title':'MotoGP race current story','summary':'race rider','semantic_qm':'PASS','racing_qm':'PASS','technical_qm_deferred':True}
  with patch.object(a,'german_editor',return_value=''),patch.object(a,'racing_relevant',return_value=True):
   ok(not a.qualify_copy(x),'empty editor must reject')
   ok(x['semantic_qm']=='FAIL' and x['racing_qm']=='FAIL' and not x['technical_qm_deferred'],'stale qualification status survived')

def test_static_contracts():
  receiver=Path('motogp_telegram_receive_v85.py').read_text(encoding='utf-8')
  workflow=Path('.github/workflows/motogp-content-agency.yml').read_text(encoding='utf-8')
  ok(a.VERSION=='V8.6','runtime version mismatch')
  ok('MIN_SESSION_VERSION=18' in receiver,'approval compatibility changed')
  ok('racing_pipeline_selftest.py' in workflow and 'racing_v85_selftest.py' in workflow,'workflow preflight incomplete')
  before=a._editor_prompt
  install(a)
  ok(a._editor_prompt is before,'installation must be idempotent')
  item={'title':'Agius takes Moto2 pole','summary':'Agius fastest'}
  prompt=a._editor_prompt(item)
  ok('CANONICAL FACT OBJECT' in prompt and 'Senna' not in prompt,'editor facts expanded from roster')

def test_noop_repair_rejected_before_repeat_qm():
  from unittest.mock import patch
  caption='Hook\n\nBody\n\nFrage?\n\n#MotoGP #MotorradRacing #RacingDeutschland #BuelentsBikeLife'
  with patch.object(a,'german_editor',return_value=caption),patch.object(a,'racing_review',return_value=(False,['Racing-QM: style issue'])),patch.object(a,'generate',return_value='```json\n{"patches":[{"old":"Body","new":"Body"}]}\n```'),patch.object(a,'semantic_review_detailed',return_value=sem_result(True,True)) as sem:
   x={'title':'MotoGP race rider noop patch test','summary':'race rider','url':'https://example.com/2026/09/15/noop'}
   ok(not a.qualify_copy(x),'noop patch must be rejected without re-evaluating the same caption')
   ok(sem.call_count == 0 or sem.call_count == 1,'same text must not re-enter semantic QM after no-op repair')

def main():
  test_language_repair_chain();test_hard_fact_feedback_then_pass();test_hard_fact_still_fail_closed();test_series_and_hashtags();test_source_priority_contract();test_final_truth_guard_live_regressi[...]
  test_noop_repair_rejected_before_repeat_qm();
 if __name__=='__main__':main()

