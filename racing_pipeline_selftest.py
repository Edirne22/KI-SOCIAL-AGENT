"""Offline regression tests for the Racing editorial/QM chain. No provider calls."""
from pathlib import Path
import motogp_content_agency_v2 as a

def assert_true(v,msg):
    if not v: raise AssertionError(msg)

def test_racing_fail_gets_exactly_one_rewrite():
    calls={'editor':0,'racing':0,'semantic':0}
    old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        def editor(x,reasons=None):
            calls['editor']+=1
            if calls['editor']==2: assert_true(reasons and reasons[0].startswith('Racing-QM:'),'Racing-QM reasons not returned to editor')
            return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
        def racing(x,c):
            calls['racing']+=1
            return (False,['Testfehler']) if calls['racing']==1 else (True,[])
        def semantic(x,c): calls['semantic']+=1;return True,[]
        a.german_editor,a.racing_review,a.semantic_review=editor,racing,semantic
        x={'title':'MotoGP race rider current test story','summary':'race rider','url':'https://example.com/2026/09/15/test'}
        assert_true(a.qualify_copy(x),'candidate should pass after one rewrite')
        assert_true(calls=={'editor':2,'racing':2,'semantic':1},f'wrong chain counts: {calls}')
        assert_true(x.get('rewrite_count')==1,'rewrite count must be exactly one')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_semantic_fail_rechecks_both_gates():
    calls={'editor':0,'racing':0,'semantic':0};old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        def editor(x,reasons=None): calls['editor']+=1;return 'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
        def racing(x,c): calls['racing']+=1;return True,[]
        def semantic(x,c): calls['semantic']+=1;return ((False,['Faktenfehler']) if calls['semantic']==1 else (True,[]))
        a.german_editor,a.racing_review,a.semantic_review=editor,racing,semantic
        x={'title':'MotoGP race rider semantic test story','summary':'race rider','url':'https://example.com/2026/09/15/test2'}
        assert_true(a.qualify_copy(x),'semantic repair should pass')
        assert_true(calls=={'editor':2,'racing':2,'semantic':2},f'all gates not re-run: {calls}')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_second_failure_is_fail_closed():
    old=(a.german_editor,a.racing_review,a.semantic_review)
    try:
        a.german_editor=lambda x,reasons=None:'Hook\n\nBody\n\nFrage?\n\n#MotoGP #Test #Racing #BuelentsBikeLife'
        a.racing_review=lambda x,c:(False,['immer falsch'])
        a.semantic_review=lambda x,c:(True,[])
        x={'title':'MotoGP race rider fail closed test','summary':'race rider','url':'https://example.com/2026/09/15/test3'}
        assert_true(not a.qualify_copy(x),'second failure must be blocked')
        assert_true(x.get('rewrite_count')==1,'more than one rewrite must never occur')
    finally:a.german_editor,a.racing_review,a.semantic_review=old

def test_contracts():
    src=Path('motogp_content_agency_v2.py').read_text(encoding='utf-8')
    assert_true("VERSION='V8.4.6.2'" in src,'version mismatch')
    assert_true('Professional Agent Standard: V1.0' in src,'professional standard missing')
    assert_true('semantic_review' in src and 'chief_review' in src,'QM layers missing')
    assert_true('fetch_article_details' not in src,'obsolete undefined research function returned')
    assert_true(Path('config/PROFESSIONAL_AGENT_STANDARD.md').is_file(),'professional standard file missing')
    assert_true(Path('config/HUMAN_WRITING_PROTOCOL.md').is_file(),'human protocol missing')

def main():
    test_racing_fail_gets_exactly_one_rewrite();test_semantic_fail_rechecks_both_gates();test_second_failure_is_fail_closed();test_contracts();print('RACING PIPELINE SELFTEST: PASS')
if __name__=='__main__':main()
