"""Offline regression tests for the complete Racing editorial/QM chain. No provider calls."""
from pathlib import Path
from datetime import datetime,timezone
import tempfile,json
import motogp_content_agency_v2 as a
import racing_semantic_qm as semantic
import turkish_riders_scout as trs
import llm_client as llm

def ok(v,msg):
 if not v:raise AssertionError(msg)

def test_rewrite_chain():
 calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review)
 try:
  def editor(x,reasons=None):calls['editor']+=1;return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
  def racing(x,c):calls['racing']+=1;return (False,['Testfehler']) if calls['racing']==1 else (True,[])
  def sem(x,c):calls['semantic']+=1;return True,[]
  a.german_editor,a.racing_review,a.semantic_review=editor,racing,sem
  x={'title':'MotoGP race rider current test story','summary':'race rider','url':'https://example.com/2026/09/15/test'}
  ok(a.qualify_copy(x),'candidate should pass after one rewrite');ok(calls=={'editor':2,'racing':2,'semantic':1},f'wrong chain counts {calls}');ok(x['rewrite_count']==1,'rewrite count')
 finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_semantic_rechecks_both_gates():
 calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review)
 try:
  a.german_editor=lambda x,reasons=None:(calls.__setitem__('editor',calls['editor']+1) or 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife')
  def racing(x,c):calls['racing']+=1;return True,[]
  def sem(x,c):calls['semantic']+=1;return ((False,['Faktenfehler']) if calls['semantic']==1 else (True,[]))
  a.racing_review,a.semantic_review=racing,sem;x={'title':'MotoGP race rider semantic test story','summary':'race rider','url':'https://example.com/2026/09/15/test2'}
  ok(a.qualify_copy(x),'semantic repair should pass');ok(calls=={'editor':2,'racing':2,'semantic':2},f'gates not rerun {calls}')
 finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_second_failure_fail_closed():
 old=(a.german_editor,a.racing_review,a.semantic_review)
 try:
  a.german_editor=lambda x,reasons=None:'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife';a.racing_review=lambda x,c:(False,['immer falsch']);a.semantic_review=lambda x,c:(True,[])
  x={'title':'MotoGP race rider fail closed test','summary':'race rider','url':'https://example.com/2026/09/15/test3'};ok(not a.qualify_copy(x),'second failure must block');ok(x['rewrite_count']==1,'more than one rewrite')
 finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_series_and_hashtags():
 cases=[
 ({'title':'Agius fastest in Moto2 Practice','summary':'Moto2 Practice at Misano','url':'https://www.motogp.com/en/news/2026/09/15/a'},'Moto2','#Moto2'),
 ({'title':'Quiles takes Moto3 pole','summary':'Moto3 qualifying','url':'https://www.motogp.com/en/news/2026/09/15/b'},'Moto3','#Moto3'),
 ({'title':'Brad Binder MotoGP update','summary':'Binder in MotoGP','url':'https://example.com/2026/09/15/c'},'MotoGP','#MotoGP'),
 ({'title':'Bulega makes MotoGP switch for 2027','summary':'Bulega moves from WorldSBK to MotoGP','url':'https://www.worldsbk.com/en/news/2026/09/15/d'},'MotoGP','#MotoGP'),
 ({'title':'Miller joins WorldSBK for 2027','summary':'Miller moves from MotoGP to WorldSBK','url':'https://www.motogp.com/en/news/2026/09/15/e'},'WorldSBK','#WorldSBK')]
 for item,series,tag in cases:ok(a.series_for(item)==series,f'{item["title"]} -> {a.series_for(item)}');ok(tag in a.hashtags(item),f'missing {tag}')
 ok(a.is_gp_family(cases[0][0]) and a.is_gp_family(cases[1][0]),'Moto2/Moto3 must remain GP family')

def test_editor_json_technical_retry():
 old_generate,old_sleep=a.generate,a.time.sleep;calls={'n':0}
 try:
  def fake(task,prompt):
   calls['n']+=1
   return 'not-json' if calls['n']==1 else json.dumps({'hook':'Hook','body':'Body','question':'Was meint ihr?'})
  a.generate=fake;a.time.sleep=lambda _:None
  item={'title':'Brad Binder MotoGP current racing story','summary':'Binder in MotoGP','url':'https://example.com/2026/09/15/x'}
  text=a.german_editor(item);ok(text and calls['n']==2,'editor JSON technical retry broken')
 finally:a.generate,a.time.sleep=old_generate,old_sleep

def test_turkish_aliases():
 cases={'Toprak Razgatlıoğlu takes MotoGP pole':'Toprak Razgatlıoğlu','Toprak Razgatlioglu takes MotoGP pole':'Toprak Razgatlıoğlu','Can Öncü wins WorldSSP':'Can Öncü','Can Oncu wins WorldSSP':'Can Öncü','Deniz Öncü claims Moto2 podium':'Deniz Öncü','Deniz Oncu claims Moto2 podium':'Deniz Öncü','Bahattin Sofuoğlu scores in WorldSBK':'Bahattin Sofuoğlu','Bahattin Sofuoglu scores in WorldSBK':'Bahattin Sofuoğlu','Zayn Sofuoğlu continues testing':'Zayn Sofuoğlu','Zayn Sofuoglu continues testing':'Zayn Sofuoğlu'}
 for text,expected in cases.items():ok(trs.rider_for(text)==expected,f'alias failed {text}')
 ok(trs.rider_for('Öncü takes another podium')=='','ambiguous surname guessed');ok(trs.fold('Razgatlıoğlu')==trs.fold('Razgatlioglu'),'Toprak fold mismatch')

def test_semantic_retry_and_provider_backoff():
 cleaned=semantic._caption_for_fact_review('Text #MotoGP #BuelentsBikeLife #ToprakRazgatlioglu');ok('#BuelentsBikeLife' not in cleaned,'brand hashtag fact-reviewed')
 old=semantic.generate;calls={'n':0}
 try:
  def fake(task,prompt):calls['n']+=1;return 'not-json' if calls['n']==1 else json.dumps({'pass':True,'reasons':[],'unsupported_claims':[],'series_ok':True,'rider_team_ok':True,'german_ok':True,'quote_ok':True})
  semantic.generate=fake;passed,reasons=semantic.review({'title':'Toprak Razgatlioglu MotoGP test','summary':'Toprak tests MotoGP bike','series':'MotoGP','url':'https://example.com/2026/09/15/x'},'Toprak testet.\n\nWas meint ihr?\n\n#MotoGP #ToprakRazgatlioglu #BuelentsBikeLife');ok(passed and calls['n']==2 and not reasons,'semantic JSON retry broken')
 finally:semantic.generate=old
 class Resp:
  def __init__(self,status):self.status_code=status;self.ok=status==200;self.text='rate';self.headers={}
  def json(self):return {'ok':True}
 old_req,old_sleep=llm.requests.request,llm.time.sleep;seq=[Resp(429),Resp(200)];c={'n':0,'sleep':0}
 try:
  def req(*args,**kwargs):c['n']+=1;return seq.pop(0)
  llm.requests.request=req;llm.time.sleep=lambda _:(c.__setitem__('sleep',c['sleep']+1));out=llm._request_json('POST','https://example.com',{}, {},1,max_retries=2);ok(out=={'ok':True} and c=={'n':2,'sleep':1},f'provider retry {c}')
 finally:llm.requests.request,llm.time.sleep=old_req,old_sleep

def test_session_fail_closed():
 old=a.SESSION
 try:
  with tempfile.TemporaryDirectory() as td:
   a.SESSION=Path(td)/'session.md';a.SESSION.write_text('Approval-Status: READY\nQM: PASS\n## Beitrag 1\nALT',encoding='utf-8');a.invalidate_session(datetime(2026,9,16,tzinfo=timezone.utc),'nur 3/5',3);text=a.SESSION.read_text(encoding='utf-8');ok('QM: FAIL' in text and 'Approval-Status: BLOCKED' in text,'stale PASS not blocked');ok('Bestandene-Pakete: 3/5' in text and '## Beitrag' not in text,'old posts survived')
 finally:a.SESSION=old

def test_static_contracts():
 src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8');workflow=Path('.github/workflows/motogp-content-agency.yml').read_text(encoding='utf-8');receiver=Path('motogp_telegram_receive_v85.py').read_text(encoding='utf-8');scout=Path('turkish_riders_scout.py').read_text(encoding='utf-8');sem=Path('racing_semantic_qm.py').read_text(encoding='utf-8');client=Path('llm_client.py').read_text(encoding='utf-8')
 ok(a.VERSION=='V8.5.2' and "VERSION='V8.5.2'" in src,'version mismatch');ok('Session-Version: 18' in src and 'Approval-Status: READY' in src and 'invalidate_session' in src,'session contract incomplete');ok('MIN_SESSION_VERSION=18' in receiver,'receiver must require v18');ok('MAX_SESSION_AGE_SECONDS=24*3600' in receiver,'session age gate missing');ok('unicodedata' in scout and 'Razgatlıoğlu' in scout and 'Can Öncü' in scout,'Turkish Unicode contract missing');ok('BRAND_HASHTAGS' in sem and 'technical_attempt in range(2)' in sem,'semantic protections missing');ok('429,500,502,503,504' in client and 'max_retries=2' in client,'provider retry missing');ok('racing_pipeline_selftest.py' in workflow and 'racing_v85_selftest.py' in workflow,'workflow preflight incomplete');ok('article_info(t,u)' in src,'research signature regressed');ok('remember_offered(picks,now)' in src,'memory handoff regressed');ok('send_message' in src,'Telegram handoff regressed');ok('review_batch([x])' in src,'batch QM missing');ok('qualify_parallel(fresh[:30],2)' in src,'Agnes throttling missing');ok(Path('config/PROFESSIONAL_AGENT_STANDARD.md').is_file() and Path('config/HUMAN_WRITING_PROTOCOL.md').is_file(),'global standards missing')

def main():
 test_rewrite_chain();test_semantic_rechecks_both_gates();test_second_failure_fail_closed();test_series_and_hashtags();test_editor_json_technical_retry();test_turkish_aliases();test_semantic_retry_and_provider_backoff();test_session_fail_closed();test_static_contracts();print('RACING PIPELINE SELFTEST: PASS')
if __name__=='__main__':main()
