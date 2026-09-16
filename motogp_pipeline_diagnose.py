"""Read-only Racing pipeline diagnostic runner.
Mirrors collection/freshness/relevance counts without Telegram, publisher or memory writes.
"""
from datetime import datetime,timezone
from collections import Counter
import motogp_content_agency_v2 as a
from racing_v855_hardening import install
from motogp_pipeline_audit import new_run_id,stage,rejection,write_summary
install(a)

def main():
 run_id=new_run_id();st=[];names=a.roster_names();known=a.known_story_keys();raw=[];seen=set();meta={}
 scout=list(a.racing_scout(140));st.append(stage(run_id,'research_scout',len(scout),len(scout)))
 for t,u,s,r in scout:
  u=a.canonical_url(u);key=a.story_key(t,u)
  if u in seen:
   rejection(run_id,'story_deduplicate',{'title':t,'url':u,'story_key':key},'DUPLICATE','URL bereits im aktuellen Recherchepool','excluded');continue
  if key in known:
   rejection(run_id,'story_deduplicate',{'title':t,'url':u,'story_key':key},'DUPLICATE','Story bereits angeboten/veroeffentlicht','excluded');continue
  seen.add(u);raw.append((t,u));meta[u]={'source_series':s,'series':s,'series_locked':True,**({'turkish_rider':r} if r else {})}
 st.append(stage(run_id,'story_deduplicate',len(scout),len(raw),deduplicated_count=len(raw),rejected_count=len(scout)-len(raw)))
 details=[]
 for i,(t,u) in enumerate(raw):
  try:
   x=a.article_info(t,u);x.update(meta.get(u,{}));a.lock_source_series(x,meta.get(u,{}).get('source_series'));x=a.enrich_turkish(x);x['original_record_id']=a.story_key(t,u);details.append(x)
  except Exception as e:rejection(run_id,'article_extract',{'title':t,'url':u},'PARSER_ERROR',f'{type(e).__name__}: {e}','excluded')
 st.append(stage(run_id,'article_extract',len(raw),len(details),normalized_count=len(details),rejected_count=len(raw)-len(details)))
 now=datetime.now(timezone.utc);fresh=[];reason_counts=Counter()
 for x in details:
  reason=a.freshness_reason(x,now);reason_counts[reason]+=1
  if reason=='fresh':fresh.append(x);continue
  code={'missing-date':'MISSING_DATE','not-racing-or-promo':'QUALITY_FILTER','profile':'QUALITY_FILTER','older-than-7d':'QUALITY_FILTER','future-date':'QUALITY_FILTER'}.get(reason,'UNKNOWN')
  rejection(run_id,'freshness',x,code,reason,'excluded_from_current_news')
 st.append(stage(run_id,'freshness',len(details),len(fresh),rejected_count=len(details)-len(fresh),warning_count=reason_counts.get('missing-date',0)))
 relevant=[]
 for x in fresh:
  if a.racing_relevant(x):relevant.append(x)
  else:rejection(run_id,'racing_relevance',x,'QUALITY_FILTER','not-racing-or-promo','excluded')
 st.append(stage(run_id,'racing_relevance',len(fresh),len(relevant),rejected_count=len(fresh)-len(relevant)))
 # Important boundary: do NOT call editor/QM here. This diagnostic proves the pre-QM loss independently.
 st.append(stage(run_id,'pre_qm_boundary',len(relevant),len(relevant),roster_checked_count=len(names)))
 summary=write_summary(run_id,st);summary['freshness_reasons']=dict(reason_counts);write_summary(run_id,st+[{'freshness_reasons':dict(reason_counts)}])
 print('DIAG RUN',run_id,'raw',len(raw),'details',len(details),'fresh',len(fresh),'relevant',len(relevant),'roster',len(names))
if __name__=='__main__':main()
