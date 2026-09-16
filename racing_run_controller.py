"""Racing Agency V8.5.4 run controller.
Deterministic orchestration state: duplicate protection, persistent batch identity and human approval boundary.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,time
STATE=Path('memory/RACING_RUN_STATE.json');ARCH_VERSION='V8.5.4';TERMINAL={'BLOCKED','READY_FOR_APPROVAL','APPROVED','PUBLISHED','CLOSED'};DUPLICATE_WINDOW_SECONDS=30*60
def _now():return datetime.now(timezone.utc)
def _load():
 try:return json.loads(STATE.read_text(encoding='utf-8'))
 except Exception:return {'version':1,'runs':{},'last_notification_at':0,'last_notification_fingerprint':''}
def _save(data):
 STATE.parent.mkdir(parents=True,exist_ok=True);tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(STATE)
def event_name():return os.getenv('GITHUB_EVENT_NAME','local')
def github_run_id():return os.getenv('GITHUB_RUN_ID','local')
def force_new():return os.getenv('INPUT_FORCE_NEW_RUN','').strip().lower() in {'1','true','yes','on'}
def batch_id(now=None):
 now=now or _now();event=event_name()
 if event=='schedule':return f'racing-{now.date().isoformat()}-daily'
 if event=='workflow_dispatch':return f'racing-{now.date().isoformat()}-manual-{github_run_id()}'
 return f'racing-{now.date().isoformat()}-{event}-{github_run_id()}'
def begin():
 data=_load();bid=batch_id();existing=data['runs'].get(bid)
 if existing and existing.get('status') not in {'FAILED','BLOCKED'} and not force_new():return False,bid,'duplicate batch'
 data['runs'][bid]={'status':'STARTED','started_at':_now().isoformat(),'updated_at':_now().isoformat(),'event':event_name(),'github_run_id':github_run_id(),'arch_version':ARCH_VERSION};data['active_batch_id']=bid;_save(data);return True,bid,'started'
def transition(bid,status,error=''):
 data=_load();run=data['runs'].setdefault(bid,{});run['status']=status;run['updated_at']=_now().isoformat()
 if error:run['error']=error
 if status in TERMINAL and data.get('active_batch_id')==bid:data['active_batch_id']=''
 _save(data)
def active_batch_id():return _load().get('active_batch_id','')
def run_state(bid):return _load().get('runs',{}).get(bid,{})
def notification_allowed(kind,payload,min_interval=120):
 data=_load();now=time.time();fp=hashlib.sha256((kind+'|'+payload).encode()).hexdigest()
 if fp==data.get('last_notification_fingerprint') and now-float(data.get('last_notification_at',0))<min_interval:return False
 data['last_notification_fingerprint']=fp;data['last_notification_at']=now;_save(data);return True
