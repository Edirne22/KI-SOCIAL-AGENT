"""Offline regression for the quality report incident of 2026-10-24."""
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import requests
import quality_agent as quality
from generate_ideas import validate_content_plan, save_content_plan
from llm_router import LLMRouter, quick_chat

FIELDS = ('Titel', 'Plattform', 'Thema', 'Hook', 'Instagram-Caption', 'Facebook-Post',
          'TikTok-Skript', 'Visuelle Idee', 'Medienvorschlag', 'Hashtags Instagram',
          'Hashtags TikTok', 'Trend-Bezug', 'Viral-Score', 'Inspirations-Plattform',
          'Inspirations-Quelle')


def plan():
    return '\n'.join(f'--- BEITRAG {i} ---\n' + '\n'.join(f'{f}: Test' for f in FIELDS)
                     for i in (1, 2, 3))


def router():
    obj = LLMRouter()
    obj.config['task_routing']['daily_ideas'] = ['groq', 'openrouter']
    return obj


def test_invalid_draft_uses_next_provider():
    obj = router()
    with patch.object(obj, '_call_provider', side_effect=['--- BEITRAG 1 ---\nTitel: Test', plan()]) as call:
        assert obj.chat([], 'daily_ideas', response_validator=validate_content_plan) == plan()
        assert call.call_count == 2


def test_all_invalid_drafts_fail_without_writes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path('content').mkdir()
    Path('content/CONTENT_PLAN.md').write_text('existing')
    obj = router()
    with patch.object(obj, '_call_provider', return_value='bad'):
        with pytest.raises(RuntimeError):
            save_content_plan(obj.chat([], 'daily_ideas', response_validator=validate_content_plan))
    assert Path('content/CONTENT_PLAN.md').read_text() == 'existing'
    assert not Path('memory/POST_HISTORY.md').exists()


def test_valid_draft_stops_fallback():
    obj = router()
    with patch.object(obj, '_call_provider', return_value=plan()) as call:
        assert obj.chat([], 'daily_ideas', response_validator=validate_content_plan) == plan()
        assert call.call_count == 1


def test_quick_chat_forwards_validation():
    obj = router()
    with patch('llm_router.get_router', return_value=obj), patch.object(obj, '_call_provider', side_effect=['bad', plan()]):
        assert quick_chat('test', 'daily_ideas', response_validator=validate_content_plan) == plan()


@pytest.mark.parametrize('text', [plan().replace('Hook: Test', 'Hook: ...', 1),
                                 plan().replace('Titel: Test', 'Titel: Test\nTitel: duplicate', 1),
                                 plan().replace('--- BEITRAG 3 ---', '--- BEITRAG 2 ---')])
def test_bad_plans_remain_rejected(text):
    with pytest.raises(RuntimeError):
        validate_content_plan(text)


def source_result(tmp_path, text):
    (tmp_path / 'INSPIRATION_IDEAS.md').write_text(text)
    with patch.object(quality, 'MEMORY', tmp_path):
        return next(r for r in quality.check_source_quality() if r['title'] == 'Inspiration-Duplikate')


def test_citations_are_not_duplicate_sources(tmp_path):
    text = '- Quelle: https://youtube.com/watch?v=Case\n- **Inspirations-Quelle:** https://youtube.com/watch?v=Case\n## Quellenverzeichnis\n1. https://youtube.com/watch?v=Case\n'
    assert source_result(tmp_path, text)['level'] == 'OK'


def test_real_duplicate_source_list_still_warns(tmp_path):
    text = '## Quellen\n1. https://youtube.com/watch?v=Case\n2. https://youtube.com/watch?v=Case\n'
    assert source_result(tmp_path, text)['level'] == 'WARNUNG'


def test_case_sensitive_video_ids_are_distinct(tmp_path):
    text = '## Quellen\n1. https://youtube.com/watch?v=Case\n2. https://youtube.com/watch?v=case\n'
    assert source_result(tmp_path, text)['level'] == 'OK'


@pytest.mark.parametrize('status,conclusion,expected', [('completed','success','OK'), ('completed','failure','KRITISCH'), ('queued',None,'WARNUNG'), ('completed','cancelled','WARNUNG')])
def test_workflow_specific_lookup(status, conclusion, expected, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'test')
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')
    response = Mock()
    response.json.return_value = {'workflow_runs': [{'created_at': quality._now().isoformat(), 'status': status, 'conclusion': conclusion}]}
    with patch.object(quality.requests, 'get', return_value=response) as get:
        results = quality.check_workflows()
    assert len(results) == 5
    assert all(r['level'] == expected for r in results)
    assert all('/actions/workflows/' in c.args[0] for c in get.call_args_list)
    assert all(c.kwargs['params']['branch'] == 'main' for c in get.call_args_list)


def test_one_api_failure_does_not_hide_other_workflows(monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'test')
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')
    response = Mock()
    response.json.return_value = {'workflow_runs': [{'created_at': quality._now().isoformat(), 'status':'completed', 'conclusion':'success'}]}
    with patch.object(quality.requests, 'get', side_effect=[requests.Timeout(),response,response,response,response]):
        results = quality.check_workflows()
    assert [r['level'] for r in results].count('OK') == 4


def test_generator_wires_validator_and_recovers():
    import generate_ideas as ideas
    obj = router()
    with patch.object(ideas, 'read_all', return_value=''), patch.object(ideas, 'read_file', return_value=''), patch.object(ideas, 'get_context', return_value=''), patch.object(ideas, 'get_agent_context', return_value=''), patch.object(ideas, 'prepare_agent_context', return_value={}), patch.object(ideas, 'require_agent_memory', return_value={'memory': {}}), patch('llm_router.get_router', return_value=obj), patch.object(obj, '_call_provider', side_effect=['bad', plan()]):
        assert ideas.generate_content_plan(memory_storage=object()) == plan()


def test_notification_includes_specific_findings():
    import sys
    telegram = Mock()
    report = quality.build_report([{'level':'KRITISCH','title':'Daily','detail':'Fehlgeschlagen.'}, {'level':'WARNUNG','title':'Quelle','detail':'Unbekannt.'}])
    with patch.dict(sys.modules, {'telegram_bot': telegram}):
        quality.notify(report)
    message = telegram.send_message.call_args.args[0]
    assert 'Daily: Fehlgeschlagen.' in message
    assert 'Quelle: Unbekannt.' in message
    assert '**' not in message


@pytest.mark.parametrize('created', ['invalid', '2026-10-01T00:00:00Z', '2026-10-24T00:00:00'])
def test_old_or_malformed_workflow_timestamp_warns(created, monkeypatch):
    monkeypatch.setenv('GITHUB_TOKEN', 'test')
    monkeypatch.setenv('GITHUB_REPOSITORY', 'owner/repo')
    response = Mock()
    response.json.return_value = {'workflow_runs': [{'created_at':created,'status':'completed','conclusion':'success'}]}
    with patch.object(quality.requests, 'get', return_value=response):
        assert all(r['level'] == 'WARNUNG' for r in quality.check_workflows())
