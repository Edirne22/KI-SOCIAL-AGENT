"""Offline regression tests for the complete Racing editorial/QM chain. No provider calls."""
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import motogp_content_agency_v2 as a
import racing_semantic_qm as semantic
import turkish_riders_scout as trs

def assert_true(v,msg):
    if not v: raise AssertionError(msg)

def test_racing_fail_gets_exactly_one_rewrite():
    calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        def editor(x,reasons=None):
            calls['editor']+=1
            if calls['editor']==2: assert_true(reasons and reasons[0].startswith('Racing-QM:'),'Racing-QM reasons not returned to editor')
            return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
        def racing(x,c): calls['racing']+=1;return (False,['Testfehler']) if calls['racing']==1 else (True,[])
        def sem(x,c): calls['semantic']+=1;return True,[]
        a.german_editor,a.racing_review,a.semantic_review=editor,racing,sem
        x={'title':'MotoGP race rider current test story','summary':'race rider','url':'https://example.com/2026/09/15/test'}
        assert_true(a.qualify_copy(x),'candidate should pass after one rewrite');assert_true(calls=={'editor':2,'racing':2,'semantic':1},f'wrong chain counts: {calls}');assert_true(x.get('rewrite_count')==1,'rewrite count must be exactly one')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_semantic_fail_rechecks_both_gates():
    calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        def editor(x,reasons=None): calls['editor']+=1;return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
        def racing(x,c): calls['racing']+=1;return True,[]
        def sem(x,c): calls['semantic']+=1;return ((False,['Faktenfehler']) if calls['semantic']==1 else (True,[]))
        a.german_editor,a.racing_review,a.semantic_review=editor,racing,sem
        x={'title':'MotoGP race rider semantic test story','summary':'race rider','url':'https://example.com/2026/09/15/test2'}
        assert_true(a.qualify_copy(x),'semantic repair should pass');assert_true(calls=={'editor':2,'racing':2,'semantic':2},f'all gates not re-run: {calls}')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_second_failure_is_fail_closed():
    old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        a.german_editor=lambda x,reasons=None:'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife';a.racing_review=lambda x,c:(False,['immer falsch']);a.semantic_review=lambda x,c:(True,[])
        x={'title':'MotoGP race rider fail closed test','summary':'race rider','url':'https://example.com/2026/09/15/test3'}
        assert_true(not a.qualify_copy(x),'second failure must be blocked');assert_true(x.get('rewrite_count')==1,'more than one rewrite must never occur')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_entity_series_and_hashtag_contracts():
    cases=[
      ({'title':'Jack Miller WorldSBK test','summary':'Miller prepares for WorldSBK','url':'https://example.com/2026/09/15/a'},'WorldSBK','#JackMiller','#WorldSBK'),
      ({'title':'Brad Binder MotoGP update','summary':'Binder in MotoGP','url':'https://example.com/2026/09/15/b'},'MotoGP','#BradBinder','#MotoGP'),
      ({'title':'WorldSSP300 race update','summary':'WorldSSP300 grid','url':'https://example.com/2026/09/15/c'},'WorldSSP300',None,'#WorldSSP300'),
      ({'title':'Bulega makes MotoGP switch for 2027','summary':'Bulega moves from WorldSBK to MotoGP','url':'https://www.worldsbk.com/en/news/2026/09/15/x'},'MotoGP','#NicoloBulega','#MotoGP'),
      ({'title':'Miller joins WorldSBK for 2027','summary':'Miller moves from MotoGP to WorldSBK','url':'https://www.motogp.com/en/news/2026/09/15/y'},'WorldSBK','#JackMiller','#WorldSBK'),]
    for item,series,rider_tag,series_tag in cases:
        assert_true(a.series_for(item)==series,f'series mismatch: {item["title"]}');tags=a.hashtags(item);assert_true(series_tag in tags,f'series hashtag missing: {tags}')
        if rider_tag:assert_true(rider_tag in tags,f'rider hashtag missing: {tags}')

def test_turkish_rider_unicode_ascii_aliases():
    cases={
      'Toprak Razgatlıoğlu takes MotoGP pole':'Toprak Razgatlıoğlu',
      'Toprak Razgatlioglu takes MotoGP pole':'Toprak Razgatlıoğlu',
      'Toprak Razgatlıoglu tests the MotoGP bike':'Toprak Razgatlıoğlu',
      'Can Öncü wins WorldSSP Race 1':'Can Öncü',
      'Can Oncu wins WorldSSP Race 1':'Can Öncü',
      'C. Oncu returns to the WorldSSP podium':'Can Öncü',
      'Deniz Öncü claims Moto2 podium':'Deniz Öncü',
      'Deniz Oncu claims Moto2 podium':'Deniz Öncü',
      'D. Öncü fastest in Moto2 practice':'Deniz Öncü',
      'Bahattin Sofuoğlu scores in WorldSBK':'Bahattin Sofuoğlu',
      'Bahattin Sofuoglu scores in WorldSBK':'Bahattin Sofuoğlu',
      'Zayn Sofuoğlu continues testing':'Zayn Sofuoğlu',
      'Zayn Sofuoglu continues testing':'Zayn Sofuoğlu'}
    for text,expected in cases.items():assert_true(trs.rider_for(text)==expected,f'Turkish alias failed: {text} -> {trs.rider_for(text)!r}')
    assert_true(trs.rider_for('Öncü takes another podium')=='','bare shared surname must not guess Can vs Deniz')
    assert_true(trs.rider_for('Oncu takes another podium')=='','ASCII bare shared surname must not guess Can vs Deniz')
    assert_true(trs.fold('Razgatlıoğlu')==trs.fold('Razgatlioglu'),'Turkish/ASCII normalization mismatch for Toprak')
    assert_true(trs.fold('Öncü')==trs.fold('Oncu'),'Turkish/ASCII normalization mismatch for Öncü')
    assert_true(a.detect_turkish_rider({'title':'Toprak Razgatlıoğlu MotoGP update','summary':'','url':''})=='Toprak Razgatlioglu','agency Toprak Turkish spelling detection failed')
    assert_true(a.detect_turkish_rider({'title':'Can Öncü WorldSSP update','summary':'','url':''})=='Can Oncu','agency Can Turkish spelling detection failed')
    assert_true(a.detect_turkish_rider({'title':'Deniz Oncu Moto2 update','summary':'','url':''})=='Deniz Oncu','agency Deniz ASCII detection failed')

def test_stale_approval_session_is_blocked():
    old=a.SESSION
    try:
        with tempfile.TemporaryDirectory() as td:
            a.SESSION=Path(td)/'session.md';a.SESSION.write_text('QM: PASS\n## Beitrag 1\nALT',encoding='utf-8');a.invalidate_session(datetime(2026,9,16,tzinfo=timezone.utc),'nur 3/5',3);text=a.SESSION.read_text(encoding='utf-8')
            assert_true('QM: FAIL' in text and 'Approval-Status: BLOCKED' in text,'stale PASS session not blocked');assert_true('Bestandene-Pakete: 3/5' in text,'blocked session count missing');assert_true('## Beitrag' not in text,'old approvable posts survived invalidation')
    finally:a.SESSION=old

def test_freshness_and_semantic_fail_closed_contracts():
    now=datetime(2026,9,16,tzinfo=timezone.utc);assert_true(a.current_news({'url':'https://example.com/2026/09/15/story'},now,7),'fresh dated URL rejected');assert_true(not a.current_news({'url':'https://example.com/2026/08/01/story'},now,7),'stale story accepted');assert_true(not a.current_news({'url':'https://example.com/story'},now,7),'undated story must fail closed')
    try:semantic._clean_json('not-json')
    except Exception:pass
    else:raise AssertionError('invalid semantic JSON did not fail closed')
    assert_true(semantic._clean_json('```json\n{"pass": true}\n```')['pass'] is True,'semantic fenced JSON parser broken')

def test_contracts():
    src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8');workflow=Path('.github/workflows/motogp-content-agency.yml').read_text(encoding='utf-8');receiver=Path('motogp_telegram_receive.py').read_text(encoding='utf-8');scout=Path('turkish_riders_scout.py').read_text(encoding='utf-8')
    assert_true(a.VERSION=='V8.4.6.4',f'version mismatch: {a.VERSION}');assert_true("VERSION='V8.4.6.4'" in src,'source version mismatch');assert_true('Session-Version: 18' in src,'session writer version mismatch');assert_true('invalidate_session' in src,'stale approval invalidation missing');assert_true('MIN_SESSION_VERSION=10' in receiver,'receiver minimum session contract changed unexpectedly');assert_true('unicodedata' in scout and 'Razgatlıoğlu' in scout and 'Can Öncü' in scout,'Turkish Unicode scout contract missing');assert_true('racing_pipeline_selftest.py' in workflow and 'racing_semantic_qm.py' in workflow,'workflow preflight incomplete');assert_true('Professional Agent Standard: V1.0' in src,'professional standard missing');assert_true('semantic_review' in src and 'chief_review' in src,'QM layers missing');assert_true('fetch_article_details' not in src,'obsolete undefined research function returned');assert_true(Path('config/PROFESSIONAL_AGENT_STANDARD.md').is_file(),'professional standard file missing');assert_true(Path('config/HUMAN_WRITING_PROTOCOL.md').is_file(),'human protocol missing')

def main():
    test_racing_fail_gets_exactly_one_rewrite();test_semantic_fail_rechecks_both_gates();test_second_failure_is_fail_closed();test_entity_series_and_hashtag_contracts();test_turkish_rider_unicode_ascii_aliases();test_stale_approval_session_is_blocked();test_freshness_and_semantic_fail_closed_contracts();test_contracts();print('RACING PIPELINE SELFTEST: PASS')
if __name__=='__main__':main()
