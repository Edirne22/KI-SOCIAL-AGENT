"""Offline V8.5 orchestration and official-source regressions."""
import os,tempfile
from pathlib import Path
from datetime import datetime,timezone
import racing_run_controller as rc
import motogp_telegram_receive_v85 as approval
import turkish_riders_scout as scout

def check(v,msg):
    if not v:raise AssertionError(msg)
def main():
    old_state=rc.STATE;old_env={k:os.environ.get(k) for k in ('GITHUB_EVENT_NAME','GITHUB_RUN_ID','INPUT_FORCE_NEW_RUN')}
    try:
        with tempfile.TemporaryDirectory() as td:
            rc.STATE=Path(td)/'state.json';os.environ['GITHUB_EVENT_NAME']='workflow_dispatch';os.environ['GITHUB_RUN_ID']='100';os.environ.pop('INPUT_FORCE_NEW_RUN',None)
            ok,bid,_=rc.begin(datetime(2026,9,16,4,0,tzinfo=timezone.utc));check(ok and bid.endswith('-100'),'first manual run rejected');rc.transition(bid,'BLOCKED')
            os.environ['GITHUB_RUN_ID']='101';ok2,_,reason=rc.begin(datetime(2026,9,16,4,1,tzinfo=timezone.utc));check(not ok2 and 'duplicate window' in reason,'immediate duplicate run was not suppressed')
            os.environ['INPUT_FORCE_NEW_RUN']='true';ok3,bid3,_=rc.begin(datetime(2026,9,16,4,2,tzinfo=timezone.utc));check(ok3 and bid3.endswith('-101'),'explicit force did not bypass duplicate window')
            rc.transition(bid3,'READY_FOR_APPROVAL');check(rc.get_run(bid3)['status']=='READY_FOR_APPROVAL','state transition lost')
            check(rc.notification_allowed('x','same',datetime(2026,9,16,5,0,tzinfo=timezone.utc)),'first notification rejected');check(not rc.notification_allowed('x','same',datetime(2026,9,16,5,1,tzinfo=timezone.utc)),'duplicate notification not suppressed')
            rc.STATE=Path(td)/'scheduled.json';os.environ['GITHUB_EVENT_NAME']='schedule';os.environ['GITHUB_RUN_ID']='200';os.environ.pop('INPUT_FORCE_NEW_RUN',None)
            ok4,daily,_=rc.begin(datetime(2026,9,16,6,0,tzinfo=timezone.utc));check(ok4 and daily=='racing-2026-09-16-daily','daily batch id not deterministic');rc.transition(daily,'READY_FOR_APPROVAL');ok5,_,_=rc.begin(datetime(2026,9,16,7,0,tzinfo=timezone.utc));check(not ok5,'terminal daily batch reran')
        check(approval.MIN_SESSION_VERSION==18,'approval session minimum must be 18');check(approval.MAX_SESSION_AGE_SECONDS==86400,'approval session age contract changed')
        # Reserve-source contract: each GP class has its own official feed, while all feeds remain official.
        src=dict(scout.SOURCES)
        check(src.get('MotoGP')=='https://www.motogp.com/en/news','MotoGP official source missing')
        check(src.get('Moto2')=='https://www.motogp.com/en/news/Moto2','Moto2 reserve source missing')
        check(src.get('Moto3')=='https://www.motogp.com/en/news/Moto3','Moto3 reserve source missing')
        check(src.get('WorldSBK')=='https://www.worldsbk.com/en/news','WorldSBK official source missing')
        check(src.get('WorldSSP')=='https://www.worldsbk.com/en/news/ssp','WorldSSP official source missing')
        check(scout.classify_series('Moto2','Agius takes pole in Moto2','https://www.motogp.com/en/news/2026/09/12/x')=='Moto2','Moto2 collapsed into another class')
        check(scout.classify_series('Moto3','Quiles wins Moto3 race','https://www.motogp.com/en/news/2026/09/13/y')=='Moto3','Moto3 collapsed into another class')
        check(scout.classify_series('WorldSSP','Oncu wins WorldSSP race','https://www.worldsbk.com/en/news/2026/09/14/z')=='WorldSSP','WorldSSP classification regressed')
        print('RACING V8.5 ORCHESTRATION + SOURCE RESERVE SELFTEST: PASS')
    finally:
        rc.STATE=old_state
        for k,v in old_env.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
if __name__=='__main__':main()
