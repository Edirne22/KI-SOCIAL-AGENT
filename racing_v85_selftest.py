"""Offline V8.5 orchestration, source-lock and freshness regressions."""
import os,tempfile
from pathlib import Path
from datetime import datetime,timezone,timedelta
import racing_run_controller as rc
import motogp_telegram_receive_v85 as approval
import turkish_riders_scout as scout
import motogp_content_agency_v2 as agency
import racing_telegram_commands as racing_cmds
from racing_v855_hardening import install as install_v855_hardening

# Production installs V8.5.5 hardening in racing_v85 before executing the agency.
# This selftest must exercise the same runtime chain instead of the un-hardened module.
install_v855_hardening(agency)

def check(v,msg):
    if not v:raise AssertionError(msg)
def main():
    old_state=rc.STATE;old_env={k:os.environ.get(k) for k in ('GITHUB_EVENT_NAME','GITHUB_RUN_ID','INPUT_FORCE_NEW_RUN','GITHUB_EVENT_PATH')}
    try:
        with tempfile.TemporaryDirectory() as td:
            rc.STATE=Path(td)/'state.json';os.environ['GITHUB_EVENT_NAME']='workflow_dispatch';os.environ['GITHUB_RUN_ID']='100';os.environ.pop('INPUT_FORCE_NEW_RUN',None);os.environ.pop('GITHUB_EVENT_PATH',None)
            ok,bid,_=rc.begin(datetime(2026,9,16,4,0,tzinfo=timezone.utc));check(ok and bid.endswith('-100'),'first manual run rejected');rc.transition(bid,'BLOCKED')
            os.environ['GITHUB_RUN_ID']='101';ok2,bid2,_=rc.begin(datetime(2026,9,16,4,1,tzinfo=timezone.utc));check(ok2 and bid2.endswith('-101'),'intentional manual rerun was suppressed')
            ok_duplicate,_,reason=rc.begin(datetime(2026,9,16,4,1,tzinfo=timezone.utc));check(not ok_duplicate and reason=='duplicate batch','identical manual batch was not suppressed')
            os.environ['INPUT_FORCE_NEW_RUN']='true';ok3,bid3,_=rc.begin(datetime(2026,9,16,4,2,tzinfo=timezone.utc));check(ok3 and bid3.endswith('-101'),'explicit force did not bypass identical-batch protection');rc.transition(bid3,'READY_FOR_APPROVAL');check(rc.get_run(bid3)['status']=='READY_FOR_APPROVAL','state transition lost')
            # Regression: checked workflow_dispatch checkbox must survive even if
            # the workflow env mapping accidentally resolves to "false".
            event_file=Path(td)/'event.json';event_file.write_text('{"inputs":{"force_new_run":"true"}}',encoding='utf-8')
            os.environ['INPUT_FORCE_NEW_RUN']='false';os.environ['GITHUB_EVENT_PATH']=str(event_file);os.environ['GITHUB_RUN_ID']='102'
            check(rc.force_new(),'checked dispatch input was lost when env mapping was false')
            ok_event,bid_event,_=rc.begin(datetime(2026,9,16,4,3,tzinfo=timezone.utc));check(ok_event and bid_event.endswith('-102'),'event-payload force did not bypass duplicate window')
            os.environ.pop('GITHUB_EVENT_PATH',None)
            check(rc.notification_allowed('x','same',datetime(2026,9,16,5,0,tzinfo=timezone.utc)),'first notification rejected');check(not rc.notification_allowed('x','same',datetime(2026,9,16,5,1,tzinfo=timezone.utc)),'duplicate notification not suppressed')
            rc.STATE=Path(td)/'scheduled.json';os.environ['GITHUB_EVENT_NAME']='schedule';os.environ['GITHUB_RUN_ID']='200';os.environ.pop('INPUT_FORCE_NEW_RUN',None)
            ok4,daily,_=rc.begin(datetime(2026,9,16,6,0,tzinfo=timezone.utc));check(ok4 and daily=='racing-2026-09-16-daily','daily batch id not deterministic');rc.transition(daily,'READY_FOR_APPROVAL');ok5,_,_=rc.begin(datetime(2026,9,16,7,0,tzinfo=timezone.utc));check(not ok5,'terminal daily batch reran')
        check(approval.MIN_SESSION_VERSION==18,'approval session minimum must be 18');check(approval.MAX_SESSION_AGE_SECONDS==86400,'approval session age contract changed')
        check(approval.selection('motogp 4, motogp 3,')==[3,4],'repeated MotoGP dictation prefix was rejected')
        check(approval.selection('motogp 4,9') is None,'invalid MotoGP choice accepted')
        check(approval.turkish_selection('T1,T3')==[1,3],'compact T1,T3 selection was rejected')
        check(approval.turkish_selection('turkish 1-3')==[1,2,3],'Turkish rider range was rejected')
        check(racing_cmds.is_turkish_approval('T1'),'T1 did not route to Turkish approval')
        check(racing_cmds.is_turkish_approval('T1,T3'),'T1,T3 did not route to Turkish approval')
        check(racing_cmds.is_turkish_approval('turkish 1-3'),'Turkish range did not route to approval')
        check(not racing_cmds.is_archive_select('T1'),'T1 was incorrectly sent to racing archive')
        check(racing_cmds.is_archive_select('poste 2'),'explicit archive selection was lost')
        check(racing_cmds.is_turkish_human_action('T1 posten'),'Turkish post action was not routed')
        check(not racing_cmds.is_turkish_human_action('T1'),'plain Turkish selection was misclassified as an action')
        fresh={'title':'Can Oncu Estoril fresh report','url':'https://motoetkinlik.com/estoril-fresh','published_at':'2026-10-14T09:00:00Z','turkish_rider':'Can Öncü','kind':'news'}
        offered={'title':'Can Oncu Estoril already offered','url':'https://motoetkinlik.com/estoril-offered','published_at':'2026-10-13T09:00:00Z','turkish_rider':'Can Öncü','kind':'news'}
        stale={'title':'Can Oncu old report','url':'https://motoetkinlik.com/estoril-old','published_at':'2026-10-10T09:00:00Z','turkish_rider':'Can Öncü','kind':'news'}
        not_repeated,_=agency.turkish_offer_candidates([fresh,offered,stale],datetime(2026,10,14,12,0,tzinfo=timezone.utc),3,offered_keys={agency.story_key(offered['title'],offered['url'])})
        check([x['title'] for x in not_repeated]==[fresh['title']],'Turkish offers repeated a prior story or admitted a stale story')
        src=dict(scout.SOURCES);check(src.get('MotoGP')=='https://www.motogp.com/en/news','MotoGP official source missing');check(src.get('Moto2')=='https://www.motogp.com/en/news/Moto2','Moto2 reserve source missing');check(src.get('Moto3')=='https://www.motogp.com/en/news/Moto3','Moto3 reserve source missing');check(src.get('WorldSBK')=='https://www.worldsbk.com/en/news','WorldSBK official source missing');check(src.get('WorldSSP')=='https://www.worldsbk.com/en/news/ssp','WorldSSP official source missing')
        check(scout.classify_series('Moto2','Agius takes pole in Moto2','https://www.motogp.com/en/news/2026/09/12/x')=='Moto2','Moto2 collapsed');check(scout.classify_series('Moto3','Quiles wins Moto3 race','https://www.motogp.com/en/news/2026/09/13/y')=='Moto3','Moto3 collapsed');check(scout.classify_series('WorldSSP','Oncu wins WorldSSP race','https://www.worldsbk.com/en/news/2026/09/14/z')=='WorldSSP','WorldSSP classification regressed')
        # Exact live regression: generic MotoGP page metadata must never override a dedicated feed class.
        q={'title':'Quiles denies Almansa in epic photo finish','summary':'The Official Home of MotoGP race report','url':'https://www.motogp.com/en/news/2026/09/13/q','series':'Moto3','source_series':'Moto3','series_locked':True};check(agency.series_for(q)=='Moto3','locked Moto3 was overwritten by generic MotoGP metadata');check('#Moto3' in agency.hashtags(q) and '#MotoGP' not in agency.hashtags(q),'locked Moto3 hashtag wrong')
        g={'title':'Agius storms to stunning Misano pole','summary':'The Official Home of MotoGP qualifying report','url':'https://www.motogp.com/en/news/2026/09/13/g','series':'Moto2','source_series':'Moto2','series_locked':True};check(agency.series_for(g)=='Moto2','locked Moto2 was overwritten by generic MotoGP metadata');check('#Moto2' in agency.hashtags(g) and '#MotoGP' not in agency.hashtags(g),'locked Moto2 hashtag wrong')
        transfer={'title':'Bulega makes MotoGP switch for 2027','summary':'moves from WorldSBK to MotoGP','series':'WorldSBK','source_series':'WorldSBK','series_locked':True};check(agency.series_for(transfer)=='MotoGP','explicit transfer destination must override source feed')
        now=datetime(2026,9,16,12,0,tzinfo=timezone.utc);items=[{'title':'Moto2 race result','summary':'Moto2 race','url':'https://x/2026/09/15/a','series':'Moto2','source_series':'Moto2','series_locked':True},{'title':'MotoGP race','summary':'MotoGP race','url':'https://x/no-date','series':'MotoGP','source_series':'MotoGP','series_locked':True},{'title':'Moto3 old race','summary':'Moto3 race','url':'https://x/2026/08/01/c','series':'Moto3','source_series':'Moto3','series_locked':True}];reasons,_=agency.freshness_diagnostics(items,now);check(reasons['fresh']==1 and reasons['missing-date']==1 and reasons['older-than-7d']==1,'freshness diagnostics contract broken')
        print('RACING V8.5 ORCHESTRATION + SERIES LOCK + FRESHNESS SELFTEST: PASS')
    finally:
        rc.STATE=old_state
        for k,v in old_env.items():
            if v is None:os.environ.pop(k,None)
            else:os.environ[k]=v
if __name__=='__main__':main()
