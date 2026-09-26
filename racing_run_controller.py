"""Racing Agency V8.5.5 run controller.
Deterministic orchestration state: duplicate protection, persistent batch identity and human approval boundary.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,os,time
STATE=Path('memory/RACING_RUN_STATE.json');ARCH_VERSION='V8.5.5';TERMINAL={'BLOCKED','READY_FOR_APPROVAL','FREIGEGEBEN','APPROVED','PUBLISHED','CLOSED'};DUPLICATE_WINDOW_SECONDS=30*60
def _now():return datetime.now(timezone.utc)
def _load():
 try:return json.loads(STATE.read_text(encoding='utf-8'))
 except Exception:return {'version':1,'runs':{},'last_notification_at':0,'last_notification_fingerprint':''}
def _save(data):
 STATE.parent.mkdir(parents=True,exist_ok=True);tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(STATE)
def event_name():return os.getenv('GITHUB_EVENT_NAME','local')
def github_run_id():return os.getenv('GITHUB_RUN_ID','local')
def _truthy(value):return str(value or '').strip().lower() in {'1','true','yes','on'}
def force_new():
 # Primary path: workflow resolves the dispatch checkbox into this env var.
 if _truthy(os.getenv('INPUT_FORCE_NEW_RUN','')):return True
 # Defensive path: GitHub always exposes the original workflow_dispatch payload
 # via GITHUB_EVENT_PATH. This prevents an env-mapping regression from silently
 # turning an explicitly checked force_new_run into False.
 if event_name()=='workflow_dispatch':
  path=os.getenv('GITHUB_EVENT_PATH','').strip()
  if path:
   try:
    payload=json.loads(Path(path).read_text(encoding='utf-8'))
    return _truthy((payload.get('inputs') or {}).get('force_new_run'))
   except (OSError,ValueError,TypeError):
    pass
 return False
def batch_id(now=None):
 now=now or _now();event=event_name()
 if event=='schedule':return f'racing-{now.date().isoformat()}-daily'
 if event=='workflow_dispatch':return f'racing-{now.date().isoformat()}-manual-{github_run_id()}'
 return f'racing-{now.date().isoformat()}-{event}-{github_run_id()}'
def begin(now=None):
 now=now or _now();data=_load();bid=batch_id(now);existing=data['runs'].get(bid)
 # Every workflow_dispatch has its own GitHub run id and is an intentional manual E2E run.
 # Do not suppress it merely because another Racing run happened within 30 minutes.
 # Scheduled runs keep their stable daily batch id and are still protected below.
 if existing and existing.get('status') not in {'FAILED','BLOCKED'} and not force_new():return False,bid,'duplicate batch'
 stamp=now.isoformat();data['runs'][bid]={'status':'STARTED','started_at':stamp,'updated_at':stamp,'event':event_name(),'github_run_id':github_run_id(),'arch_version':ARCH_VERSION};data['active_batch_id']=bid;_save(data);return True,bid,'started'
def transition(bid,status,error='',**kwargs):
 data=_load();run=data['runs'].setdefault(bid,{});run['status']=status;run['updated_at']=_now().isoformat()
 if error:run['error']=error
 for k,v in kwargs.items():run[k]=v
 if status in ('READY_FOR_APPROVAL', 'FREIGEGEBEN'):data['active_batch_id']=bid
 elif status in ('PUBLISHED','CLOSED','APPROVED','REJECTED'):data['active_batch_id']=''
 _save(data)
def active_batch_id():return _load().get('active_batch_id','')
def run_state(bid):return _load().get('runs',{}).get(bid,{})
def get_run(bid):return run_state(bid)
def notification_allowed(kind,payload,now=None,min_interval=120):
 data=_load();epoch=(now.timestamp() if isinstance(now,datetime) else time.time());fp=hashlib.sha256((kind+'|'+payload).encode()).hexdigest()
 if fp==data.get('last_notification_fingerprint') and epoch-float(data.get('last_notification_at',0))<min_interval:return False
 data['last_notification_fingerprint']=fp;data['last_notification_at']=epoch;_save(data);return True
