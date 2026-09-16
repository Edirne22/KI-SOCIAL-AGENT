"""Non-invasive diagnostic audit for the Racing/MotoGP pipeline.
Does not approve, publish, mutate memory, or change filtering decisions.
"""
from __future__ import annotations
from pathlib import Path
from datetime import datetime, timezone
import json, re, uuid

ART=Path('artifacts')
AUDIT=ART/'motogp-pipeline-audit.jsonl'
SUMMARY=ART/'motogp-stage-summary.json'
REJECTIONS=ART/'motogp-rejections.jsonl'
TOP10=ART/'motogp-top10.json'
REASON_CODES={
'MISSING_RIDER','INVALID_POSITION','MISSING_POSITION','WRONG_CLASS','NOT_IN_ACTIVE_ROSTER','DUPLICATE',
'MISSING_DATE','MISSING_SOURCE','MISSING_TEAM','MISSING_TIME','MISSING_POINTS','LOW_CONFIDENCE',
'ROTATION_FILTER','MEMORY_FILTER','QUALITY_FILTER','RIGHTS_FILTER','PARSER_ERROR','SCHEMA_ERROR','UNKNOWN'}

def new_run_id(prefix='motogp'):
 return f'{prefix}-{datetime.now(timezone.utc):%Y-%m-%d}-{uuid.uuid4().hex[:10]}'

def _write_jsonl(path,obj):
 ART.mkdir(parents=True,exist_ok=True)
 with path.open('a',encoding='utf-8') as f:f.write(json.dumps(obj,ensure_ascii=False,sort_keys=True)+'\n')

def rejection(run_id,stage,record,reason_code,reason,action='excluded'):
 code=reason_code if reason_code in REASON_CODES else 'UNKNOWN'
 obj={'run_id':run_id,'timestamp':datetime.now(timezone.utc).isoformat(),'rider':record.get('rider') or record.get('title') or None,'source_url':record.get('source_url') or record.get('url') or None,'stage':stage,'reason_code':code,'reason':str(reason),'action':action,'original_record_id':record.get('original_record_id') or record.get('story_key') or None}
 _write_jsonl(REJECTIONS,obj);return obj

def stage(run_id,stage_name,input_count,output_count,normalized_count=None,deduplicated_count=None,roster_checked_count=None,valid_position_count=None,rejected_count=0,warning_count=0,rejections=None):
 obj={'run_id':run_id,'timestamp':datetime.now(timezone.utc).isoformat(),'stage':stage_name,'input_count':int(input_count),'output_count':int(output_count),'normalized_count':normalized_count,'deduplicated_count':deduplicated_count,'roster_checked_count':roster_checked_count,'valid_position_count':valid_position_count,'rejected_count':int(rejected_count),'warning_count':int(warning_count),'rejections':rejections or []}
 _write_jsonl(AUDIT,obj);return obj

def write_summary(run_id,stages):
 ART.mkdir(parents=True,exist_ok=True);obj={'run_id':run_id,'timestamp':datetime.now(timezone.utc).isoformat(),'stages':stages};SUMMARY.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');return obj

def normalize_position(value):
 if isinstance(value,bool):return None
 if isinstance(value,int):return value if value>0 else None
 if isinstance(value,float):return int(value) if value>0 and value.is_integer() else None
 s=str(value or '').strip().upper();m=re.search(r'(?<!\d)(?:P|POS(?:ITION)?\.?\s*)?(\d{1,3})(?!\d)',s)
 if not m:return None
 n=int(m.group(1));return n if n>0 else None

def normalize_rider(value):return re.sub(r'\s+',' ',str(value or '')).strip()

def deterministic_top10(records,run_id=None,expected_class='MotoGP',active_roster=None):
 """Pure diagnostic selector. Optional fields never remove a rider.
 Only unusable rider/position or unequivocally wrong class excludes a row.
 """
 run_id=run_id or new_run_id();active={normalize_rider(x).casefold() for x in (active_roster or [])};normalized=[];rejects=[];warnings=[]
 for i,raw in enumerate(records):
  x=dict(raw);x.setdefault('original_record_id',str(i));r=normalize_rider(x.get('rider') or x.get('name'));p=normalize_position(x.get('position'))
  if not r:rejects.append(rejection(run_id,'normalize',x,'MISSING_RIDER','Fahrername fehlt'));continue
  if x.get('position') in (None,''):rejects.append(rejection(run_id,'normalize',x,'MISSING_POSITION','Position fehlt'));continue
  if p is None:rejects.append(rejection(run_id,'normalize',x,'INVALID_POSITION',f'Ungueltige Position: {x.get("position")}'));continue
  cls=normalize_rider(x.get('series') or x.get('class') or expected_class)
  if cls and expected_class and cls.casefold()!=expected_class.casefold():rejects.append(rejection(run_id,'class_check',x,'WRONG_CLASS',f'{cls} != {expected_class}'));continue
  x.update(rider=r,position=p,team=x.get('team') or None,time=x.get('time') or None,points=x.get('points') if x.get('points') not in ('',None) else None,source_url=x.get('source_url') or x.get('url') or None)
  ws=[]
  if not x['team']:ws.append('MISSING_TEAM')
  if not x['time']:ws.append('MISSING_TIME')
  if x['points'] is None:ws.append('MISSING_POINTS')
  if active and r.casefold() not in active:ws.append('NOT_IN_ACTIVE_ROSTER')
  x['warnings']=ws;x['data_quality']='complete' if not ws else 'partial';warnings.extend((r,w) for w in ws);normalized.append(x)
 stage(run_id,'normalize',len(records),len(normalized),normalized_count=len(normalized),valid_position_count=len(normalized),rejected_count=len(rejects),warning_count=len(warnings))
 # Same rider/position duplicate: keep the more complete row, never silently discard.
 by={};dup_rej=[]
 for x in normalized:
  key=(x['rider'].casefold(),x['position'])
  if key not in by:by[key]=x;continue
  old=by[key];score=lambda z:sum(z.get(k) not in (None,'') for k in ('team','time','points','source_url'))
  keep,drop=(x,old) if score(x)>score(old) else (old,x);by[key]=keep;dup_rej.append(rejection(run_id,'deduplicate',drop,'DUPLICATE','Doppelter Fahrer/Positions-Datensatz kontrolliert zusammengefuehrt','merged'))
 dedup=list(by.values());stage(run_id,'deduplicate',len(normalized),len(dedup),normalized_count=len(normalized),deduplicated_count=len(dedup),valid_position_count=len(dedup),rejected_count=len(dup_rej),warning_count=len(warnings))
 # One row per official position. Ambiguities are retained as warnings until deterministic ordering; first stable row wins for diagnostic output.
 dedup.sort(key=lambda z:(z['position'],z['rider'].casefold()));seen_pos=set();ordered=[]
 for x in dedup:
  if x['position'] in seen_pos:
   rejection(run_id,'position_deduplicate',x,'DUPLICATE',f'Position {x["position"]} mehrfach belegt','excluded_from_top10');continue
  seen_pos.add(x['position']);ordered.append(x)
 top=ordered[:10];missing=[p for p in range(1,11) if p not in {x['position'] for x in top}];warning=None if len(top)==10 else f'Nur {len(top)} gueltige Fahrerpositionen gefunden'
 result={'run_id':run_id,'top10_count':len(top),'warning':warning,'missing_positions':missing,'top10':top}
 ART.mkdir(parents=True,exist_ok=True);TOP10.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');stage(run_id,'deterministic_top10',len(dedup),len(top),deduplicated_count=len(dedup),valid_position_count=len(ordered),rejected_count=max(0,len(dedup)-len(ordered)),warning_count=(1 if warning else 0));return result
