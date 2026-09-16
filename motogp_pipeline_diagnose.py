"""Read-only Racing pipeline diagnostic runner.
Mirrors collection/freshness/relevance, copy-QM and ranking without Telegram, publisher or memory writes.
"""
from datetime import datetime,timezone
from collections import Counter
from pathlib import Path
import json
import motogp_content_agency_v2 as a
from racing_v855_hardening import install
from motogp_date_recovery_patch import install as install_date_recovery
from motogp_pipeline_audit import new_run_id,stage,rejection,write_summary
install_date_recovery(a)
install(a)
ARTIFACT_DIR=Path('artifacts');TOP10_ARTIFACT=ARTIFACT_DIR/'motogp-top10.json';QM_ARTIFACT=ARTIFACT_DIR/'motogp-qm-results.json'

def write_top10_artifact(run_id,items,names):
 ranked=sorted(items,key=lambda x:a.editorial_score(x,names),reverse=True);top=ranked[:10];rows=[]
 for rank,x in enumerate(top,1):
  rows.append({'rank':rank,'score':a.editorial_score(x,names),'title':x.get('title',''),'url':x.get('url',''),'series':a.series_for(x),'turkish_rider':x.get('turkish_rider',''),'published_at':x.get('published_at') or x.get('published') or x.get('date') or x.get('pub_date'),'original_record_id':x.get('original_record_id',''),'semantic_qm':x.get('semantic_qm'),'racing_qm':x.get('racing_qm'),'rewrite_count':x.get('rewrite_count',0)})
 ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
 TOP10_ARTIFACT.write_text(json.dumps({'run_id':run_id,'input_count':len(items),'top10_count':len(rows),'items':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return top

def run_copy_qm(run_id,items):
 qualified=[];rows=[];technical_defer=0
 for x in items:
  try:ok=a.qualify_copy(x)
  except Exception as e:
   ok=False;x['semantic_qm']='TECHNICAL-DEFER';x['technical_qm_deferred']=True;x['diagnostic_qm_exception']=f'{type(e).__name__}: {e}'
  status='PASS' if ok else ('TECHNICAL-DEFER' if x.get('technical_qm_deferred') or x.get('semantic_qm')=='TECHNICAL-DEFER' else 'REJECT')
  if ok:qualified.append(x)
  elif status=='TECHNICAL-DEFER':technical_defer+=1;rejection(run_id,'copy_qm',x,'LOW_CONFIDENCE',x.get('diagnostic_qm_exception') or 'Semantic-QM provider technisch nicht verfuegbar','technical_defer')
  else:rejection(run_id,'copy_qm',x,'QUALITY_FILTER','; '.join((x.get('qm_errors') or [])+(x.get('semantic_errors') or [])+(x.get('guard_errors') or [])) or 'Copy-QM nicht bestanden','excluded')
  rows.append({'status':status,'title':x.get('title',''),'url':x.get('url',''),'series':a.series_for(x),'semantic_qm':x.get('semantic_qm'),'racing_qm':x.get('racing_qm'),'rewrite_count':x.get('rewrite_count',0),'qm_errors':x.get('qm_errors',[]),'semantic_errors':x.get('semantic_errors',[]),'technical_error':x.get('diagnostic_qm_exception'),'pipeline_version':x.get('pipeline_version'),'canonical_fact_object':x.get('canonical_fact_object'),'guard_errors':x.get('guard_errors',[]),'guard_history':x.get('guard_history',[]),'repair_history':x.get('repair_history',[])})
 ARTIFACT_DIR.mkdir(parents=True,exist_ok=True)
 QM_ARTIFACT.write_text(json.dumps({'run_id':run_id,'input_count':len(items),'pass_count':len(qualified),'technical_defer_count':technical_defer,'reject_count':len(items)-len(qualified)-technical_defer,'items':rows},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 return qualified,technical_defer

def main():
 run_id=new_run_id();st=[];names=a.roster_names();known=a.known_story_keys();raw=[];seen=set();meta={}
 scout=list(a.racing_scout(140));st.append(stage(run_id,'research_scout',len(scout),len(scout)))
 for t,u,s,r in scout:
  u=a.canonical_url(u);key=a.story_key(t,u)
  if u in seen:rejection(run_id,'story_deduplicate',{'title':t,'url':u,'story_key':key},'DUPLICATE','URL bereits im aktuellen Recherchepool','excluded');continue
  if key in known:rejection(run_id,'story_deduplicate',{'title':t,'url':u,'story_key':key},'DUPLICATE','Story bereits angeboten/veroeffentlicht','excluded');continue
  seen.add(u);raw.append((t,u));meta[u]={'source_series':s,'series':s,'series_locked':True,**({'turkish_rider':r} if r else {})}
 st.append(stage(run_id,'story_deduplicate',len(scout),len(raw),deduplicated_count=len(raw),rejected_count=len(scout)-len(raw)))
 details=[]
 for t,u in raw:
  try:x=a.article_info(t,u);x.update(meta.get(u,{}));a.lock_source_series(x,meta.get(u,{}).get('source_series'));x=a.enrich_turkish(x);x['original_record_id']=a.story_key(t,u);details.append(x)
  except Exception as e:rejection(run_id,'article_extract',{'title':t,'url':u},'PARSER_ERROR',f'{type(e).__name__}: {e}','excluded')
 st.append(stage(run_id,'article_extract',len(raw),len(details),normalized_count=len(details),rejected_count=len(raw)-len(details)))
 now=datetime.now(timezone.utc);fresh=[];reason_counts=Counter()
 for x in details:
  reason=a.freshness_reason(x,now);reason_counts[reason]+=1
  if reason=='fresh':fresh.append(x);continue
  code={'missing-date':'MISSING_DATE','not-racing-or-promo':'QUALITY_FILTER','profile':'QUALITY_FILTER','older-than-7d':'QUALITY_FILTER','future-date':'QUALITY_FILTER'}.get(reason,'UNKNOWN');rejection(run_id,'freshness',x,code,reason,'excluded_from_current_news')
 st.append(stage(run_id,'freshness',len(details),len(fresh),rejected_count=len(details)-len(fresh),warning_count=reason_counts.get('missing-date',0)))
 relevant=[]
 for x in fresh:
  if a.racing_relevant(x):relevant.append(x)
  else:rejection(run_id,'racing_relevance',x,'QUALITY_FILTER','not-racing-or-promo','excluded')
 st.append(stage(run_id,'racing_relevance',len(fresh),len(relevant),rejected_count=len(fresh)-len(relevant)))
 st.append(stage(run_id,'pre_qm_boundary',len(relevant),len(relevant),roster_checked_count=len(names)))
 qualified,technical_defer=run_copy_qm(run_id,relevant)
 st.append(stage(run_id,'copy_qm',len(relevant),len(qualified),rejected_count=max(0,len(relevant)-len(qualified)-technical_defer),warning_count=technical_defer))
 top10=write_top10_artifact(run_id,qualified,names)
 st.append(stage(run_id,'post_qm_ranking_top10',len(qualified),len(top10),rejected_count=max(0,len(qualified)-len(top10))))
 write_summary(run_id,st+[{'freshness_reasons':dict(reason_counts)}])
 print('DIAG RUN',run_id,'raw',len(raw),'details',len(details),'fresh',len(fresh),'relevant',len(relevant),'qm_pass',len(qualified),'qm_defer',technical_defer,'top10',len(top10),'roster',len(names))
if __name__=='__main__':main()
