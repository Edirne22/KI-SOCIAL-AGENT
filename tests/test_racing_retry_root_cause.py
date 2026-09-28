"""Regression: technical provider failures do not multiply inside Semantic-QM."""
import json
import racing_semantic_qm as sem
import motogp_content_agency_v2 as agency
from racing_v855_hardening import install
from router import get_task_config

def item():
 return {'title':'Toprak Razgatlıoğlu test haberi','summary':'Toprak Razgatlıoğlu yarış hakkında konuştu.','url':'https://example.invalid/story','series':'MotoGP','source_series':'MotoGP'}

def run():
 old=sem.generate
 try:
  calls=[]
  def timeout(task,prompt):
   calls.append(task);raise RuntimeError('Provider-Anfrage nach 2 Versuchen fehlgeschlagen: ReadTimeout')
  sem.generate=timeout
  r=sem.review_detailed(item(),'Toprak Razgatlıoğlu yarış hakkında konuştu.')
  assert r.get('technical_error') is True,r
  assert len(calls)==1,calls

  sem.generate=lambda task,prompt:'{broken json'
  r=sem.review_detailed(item(),'Toprak Razgatlıoğlu yarış hakkında konuştu.')
  assert r.get('technical_error') is True,r
  assert r.get('technical_reason')=='JSONDecodeError',r

  good={'contract_version':'SOURCE-FACT-CONTRACT-V1','coverage_complete':True,'claims':[{'claim':'Toprak Razgatlıoğlu yarış hakkında konuştu.','claim_type':'FACT','status':'SUPPORTED','source_evidence':[{'source_field':'summary','quote':'Toprak Razgatlıoğlu yarış hakkında konuştu.'}]}],'german_ok':True,'style_ok':True,'repair_reasons':[]}
  sem.generate=lambda task,prompt:json.dumps(good,ensure_ascii=False)
  r=sem.review_detailed(item(),'Toprak Razgatlıoğlu yarış hakkında konuştu.')
  assert r['hard_ok'] and not r.get('technical_error'),r

  bad=dict(good);bad['claims']=[{'claim':'Toprak kazandı.','claim_type':'FACT','status':'UNSUPPORTED','source_evidence':[]}]
  sem.generate=lambda task,prompt:json.dumps(bad,ensure_ascii=False)
  r=sem.review_detailed(item(),'Toprak kazandı.')
  assert r['hard_ok'] is False and r.get('technical_error') is False,r
  assert any('UNSUPPORTED' in x for x in r['hard_reasons']),r

  cfg=get_task_config('racing_semantic_qm')
  assert cfg['timeout_seconds']==12,cfg
  assert cfg['request_max_retries']==0,cfg
  assert cfg['text_model_limit']==1,cfg

  # Three consecutive technical failures open the per-run circuit. The fourth
  # candidate must not call the provider again; it is still surfaced as a
  # technical defer so the existing DEGRADED-PASS path remains authoritative.
  original_semantic=agency.semantic_review_detailed
  calls=[]
  try:
   def provider_down(x,caption):
    calls.append(x.get('title'))
    return {'hard_ok':False,'language_ok':False,'hard_reasons':['provider down'],'repair_reasons':[],'technical_error':True,'technical_reason':'ProviderUnavailableError'}
   agency.semantic_review_detailed=provider_down
   install(agency)
   for n in range(4):
    result=agency.semantic_technical_retry({'title':f'candidate-{n}'},'caption')
    assert result['technical_error'] is True,result
   assert len(calls)==3,calls
   stats=agency.semantic_runtime_summary()
   assert stats['total']==4 and stats['technical_defer']==4,stats
   assert stats['breaker_open'] is True,stats
  finally:
   agency.semantic_review_detailed=original_semantic
 finally:sem.generate=old
 print('RACING RETRY ROOT-CAUSE REGRESSION: PASS')

if __name__=='__main__':run()
