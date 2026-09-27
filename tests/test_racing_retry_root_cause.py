"""Regression: technical provider failures do not multiply inside Semantic-QM."""
import json
import racing_semantic_qm as sem

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
 finally:sem.generate=old
 print('RACING RETRY ROOT-CAUSE REGRESSION: PASS')

if __name__=='__main__':run()
