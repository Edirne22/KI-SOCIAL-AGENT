"""Morning scheduling, cross-lane dedupe and complete discovery regression."""
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch
import motogp_content_agency as base
import motogp_content_agency_v2 as a
import racing_run_controller as rc

NOW = datetime(2026, 10, 20, 6, tzinfo=timezone.utc)
def item(n, days=0):
    return dict(title=f'Can Öncü WorldSSP report {n}', url=f'https://example.test/news/{n}',
                summary='Can Öncü WorldSSP race', turkish_rider='Can Öncü',
                series='WorldSSP', source_series='WorldSSP',
                published_at=(NOW-timedelta(days=days)).isoformat(), caption=f'copy {n}')

class Repair(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.patches=[patch.object(base,'STORY_MEMORY',root/'stories.md'),
                      patch.object(base,'SESSION',root/'session.md'),
                      patch.object(base,'PUBLISHED',root/'published.md'),
                      patch.object(a,'TURKISH_SESSION',root/'turkish.json'),
                      patch.object(a,'TOP10',root/'pool.json'),
                      patch.object(rc,'STATE',root/'runs.json')]
        for p in self.patches:p.start()
    def tearDown(self):
        for p in reversed(self.patches):p.stop()
        self.tmp.cleanup()
    def test_renamed_source_and_query_string_still_duplicate(self):
        x=item(1);base.remember_offered([x],NOW)
        x.update(title='A completely changed headline',url=x['url']+'?utm_source=test')
        self.assertTrue(a.already_offered(x))
        self.assertFalse(a.already_offered(item(2)))
    def test_yesterday_cannot_reoffer_unpublished_story(self):
        x=item(1);base.remember_offered([x],NOW)
        a.TOP10.write_text(json.dumps({'days':{(NOW-timedelta(days=1)).date().isoformat():[x,item(2)]}}))
        self.assertEqual([x['url'] for x in a.yesterday_raw(NOW,set())],[item(2)['url']])
    def test_final_gate_catches_turkish_reinjection(self):
        x=item(1);base.remember_offered([x],NOW)
        with patch.object(a,'ordered_pool',return_value=[x,item(2)]), patch.object(a,'review_batch',return_value=[(True,[])]), patch.object(a,'finish_item',return_value=True) as finish:
            self.assertEqual(a.select_and_finish([x,item(2)],[]),[item(2)])
        finish.assert_called_once()
    def test_sources_after_320_are_fetched_in_order(self):
        rows=[(str(i),f'https://example.test/{i}') for i in range(400)]
        with patch.object(a,'article_info',side_effect=lambda t,u:dict(title=t,url=u)), patch.object(a,'lock_source_series'), patch.object(a,'enrich_turkish',side_effect=lambda x:x):
            result=a.fetch_details(rows,{rows[-1][1]:{'turkish_rider':'Can Öncü'}})
        self.assertEqual(len(result),400)
        self.assertEqual(result[-1]['title'],'399')
        self.assertEqual(result[-1]['turkish_rider'],'Can Öncü')
    def test_turkish_week_window_no_future_undated_or_stale(self):
        rows=[item(1,4),item(2,8),item(3,-1),item(4)]
        rows[-1]['published_at']=''
        with patch.object(a,'roster_names',return_value=[]):
            result,window=a.turkish_offer_candidates(rows,NOW)
        self.assertEqual(result,[rows[0]])
        self.assertEqual(window,7)
    def test_hidden_turkish_candidates_not_burned(self):
        rows=[item(i) for i in range(10)]
        with patch.object(a,'send_message'), patch.object(a,'_send_turkish_source_photo',return_value=False), patch.object(a,'extract_og_image_url',return_value=''), patch.object(a,'roster_names',return_value=[]):
            visible=a.turkish_five_preview(rows,NOW)
            remaining,_=a.turkish_offer_candidates(rows,NOW)
        self.assertEqual(len(visible),5)
        self.assertEqual(len(remaining),5)
        self.assertFalse({x['url'] for x in visible}&{x['url'] for x in remaining})
    def test_current_racing_pick_not_duplicated_in_turkish(self):
        with patch.object(a,'roster_names',return_value=[]):
            rows,_=a.turkish_offer_candidates([item(1),item(2)],NOW,exclude_items=[item(1)])
        self.assertEqual(rows,[item(2)])
    def test_morning_summer_winter_and_no_midnight_run(self):
        with patch.dict('os.environ',{'GITHUB_EVENT_NAME':'schedule'}):
            for stamp,expected in [('2026-07-01T05:59:00+00:00',False),('2026-07-01T06:00:00+00:00',True),('2026-12-01T06:59:00+00:00',False),('2026-12-01T07:00:00+00:00',True),('2026-12-01T11:00:00+00:00',True)]:
                self.assertEqual(rc.morning_due(datetime.fromisoformat(stamp)),expected,stamp)
    def test_recovery_once_per_day_and_manual_override(self):
        with patch.dict('os.environ',{'GITHUB_EVENT_NAME':'schedule'}):
            self.assertTrue(rc.morning_due(NOW))
            ok,bid,_=rc.begin(NOW);self.assertTrue(ok)
            rc.transition(bid,'READY_FOR_APPROVAL')
            self.assertFalse(rc.morning_due(NOW+timedelta(minutes=20)))
            self.assertFalse(rc.begin(NOW)[0])
            rc.transition(bid,'BLOCKED')
            self.assertTrue(rc.morning_due(NOW))
        with patch.dict('os.environ',{'GITHUB_EVENT_NAME':'workflow_dispatch'}):
            self.assertTrue(rc.morning_due(NOW.replace(hour=22)))
    def test_list_marks_candidates_only_after_successful_send(self):
        import motogp_telegram_receive_v85 as recv
        rows={1:dict(item(1),n=1)}
        with patch.object(recv,'get_chat_id',return_value='owner'), patch.object(recv,'already',return_value=False), patch.object(recv,'parse_turkish_session',return_value=rows), patch.object(recv,'send_message',side_effect=RuntimeError('offline')):
            with self.assertRaises(RuntimeError):recv.handle_turkish_list(1,'owner')
        self.assertFalse(a.already_offered(item(1)))
        with patch.object(recv,'get_chat_id',return_value='owner'), patch.object(recv,'already',return_value=False), patch.object(recv,'parse_turkish_session',return_value=rows), patch.object(recv,'send_message'):
            recv.handle_turkish_list(1,'owner')
        self.assertTrue(a.already_offered(item(1)))
    def test_foreign_chat_cannot_consume_candidates(self):
        import motogp_telegram_receive_v85 as recv
        with patch.object(recv,'get_chat_id',return_value='owner'), patch.object(recv,'parse_turkish_session') as read:
            recv.handle_turkish_list(1,'foreign')
        read.assert_not_called()
    def test_workflow_gates_expensive_steps_and_serializes(self):
        import yaml
        doc=yaml.load(Path('.github/workflows/motogp-content-agency.yml').read_text(),Loader=yaml.BaseLoader)
        self.assertEqual(doc['on']['schedule'],[{'cron':'0 8 * * *','timezone':'Europe/Berlin'}])
        self.assertEqual(doc['concurrency']['cancel-in-progress'],'false')
        steps=doc['jobs']['collect']['steps']
        gate=next(i for i,x in enumerate(steps) if x.get('id')=='morning')
        for step in steps[gate+1:]:self.assertIn("steps.morning.outputs.due == 'true'",step['if'])
    def test_schedule_daily_identity_is_berlin_date(self):
        with patch.dict('os.environ',{'GITHUB_EVENT_NAME':'schedule'}):
            self.assertEqual(rc.batch_id(datetime(2026,10,19,23,tzinfo=timezone.utc)),'racing-2026-10-20-daily')

if __name__=='__main__':unittest.main()
