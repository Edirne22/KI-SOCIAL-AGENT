"""Racing Agency V8.5 run controller.

Deterministic orchestration state. Prevents accidental duplicate research/Telegram cycles,
keeps human approval separate from QA, and gives every run a persistent batch identity.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, time

STATE=Path('memory/RACING_RUN_STATE.json')
ARCH_VERSION='V8.5.0'
TERMINAL={'BLOCKED','READY_FOR_APPROVAL','APPROVED','PUBLISHED','CLOSED'}
DUPLICATE_WINDOW_SECONDS=30*60

def _now(): return datetime.now(timezone.utc)
def _load():
    try:return json.loads(STATE.read_text(encoding='utf-8'))
    except Exception:return {'version':1,'runs':{},'last_notification_at':0,'last_notification_fingerprint':''}
def _save(data):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    tmp=STATE.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');tmp.replace(STATE)
def event_name():return os.getenv('GITHUB_EVENT_NAME','local')
def github_run_id():return os.getenv('GITHUB_RUN_ID','local')
def force_new():return os.getenv('INPUT_FORCE_NEW_RUN','').strip().lower() in {'1','true','yes','on'}
def batch_id(now=None):
    now=now or _now();event=event_name()
    if event=='schedule':return f'racing-{now.date().isoformat()}-daily'
    if event=='workflow_dispatch':return f'racing-{now.date().isoformat()}-manual-{github_run_id()}'
    return f'racing-{now.date().isoformat()}-{event}-{github_run_id()}'
def begin(now=None):
    now=now or _now();data=_load();bid=batch_id(now);ts=int(now.timestamp());runs=data.setdefault('runs',{})
    # A scheduled daily batch is idempotent for the whole UTC day.
    if event_name()=='schedule':
        old=runs.get(bid,{})
        if old.get('status') in TERMINAL and not force_new():return False,bid,f'daily batch already {old.get("status")}'
    # Protect Telegram/user from accidental immediate duplicate workflow_dispatch runs.
    recent=[r for r in runs.values() if ts-int(r.get('started_at',0)) < DUPLICATE_WINDOW_SECONDS and r.get('status') in {'RUNNING','BLOCKED','READY_FOR_APPROVAL'}]
    if recent and not force_new():
        newest=max(recent,key=lambda r:int(r.get('started_at',0)))
        return False,bid,f'duplicate window active after {newest.get("batch_id","previous run")} ({newest.get("status")})'
    runs[bid]={'batch_id':bid,'architecture':ARCH_VERSION,'event':event_name(),'github_run_id':github_run_id(),'started_at':ts,'updated_at':ts,'status':'RUNNING'}
    # bounded history
    if len(runs)>40:
        for k,_ in sorted(runs.items(),key=lambda kv:int(kv[1].get('started_at',0)))[:-40]:runs.pop(k,None)
    data['active_batch_id']=bid;_save(data);return True,bid,''
def transition(bid,status,**fields):
    if status not in {'RUNNING','RESEARCHED','EDITED','QM_CHECKED','BLOCKED','READY_FOR_APPROVAL','APPROVED','PUBLISHED','CLOSED'}:raise ValueError(status)
    data=_load();run=data.setdefault('runs',{}).setdefault(bid,{'batch_id':bid});run.update(fields);run['status']=status;run['updated_at']=int(time.time());data['active_batch_id']=bid;_save(data)
def notification_allowed(kind,message,now=None):
    now=now or _now();data=_load();fp=hashlib.sha256((kind+'\n'+message).encode()).hexdigest();last=int(data.get('last_notification_at',0))
    # Exact duplicate is suppressed for 24h; any Racing status notification is rate-limited for 30m.
    if data.get('last_notification_fingerprint')==fp and int(now.timestamp())-last<86400:return False
    if int(now.timestamp())-last<DUPLICATE_WINDOW_SECONDS:return False
    data['last_notification_at']=int(now.timestamp());data['last_notification_fingerprint']=fp;_save(data);return True

def get_run(bid):return _load().get('runs',{}).get(bid,{})
