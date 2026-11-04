"""Offline incident regression: R2 NotEntitled and all-60-before-first-five."""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml
import generate_ideas as ideas
import motogp_content_agency_v2 as agency
import racing_run_controller as rc
from integrations.agent_memory_preflight import prepare_repository_agent_context, require_agent_memory


def repository(root):
    for role in ('01_content_creator', '04_social_media_strategist', '14_memory_curator'):
        path = root / f'agents/{role}.md'
        path.parent.mkdir(exist_ok=True)
        path.write_text(f'Role {role}: use verified sources only.')
    for name in ('USER_PREFERENCES', 'LEARNED_RULES', 'MEMORY_CONTEXT'):
        path = root / f'memory/{name}.md'
        path.parent.mkdir(exist_ok=True)
        path.write_text(f'{name}: human approval required.')


def test_repository_context_is_loaded_and_provenance_kept(tmp_path):
    repository(tmp_path)
    result = require_agent_memory(prepare_repository_agent_context(
        agent_id='01_content_creator', job={'job_id': 'test'}, root=tmp_path))
    assert result['memory_backend'] == 'repository'
    assert result['memory']['personal'][0]['source'] == 'agents/01_content_creator.md'
    assert len(result['memory']['shared']) == 3
    assert 'human approval' in result['memory']['shared'][0]['summary']


@pytest.mark.parametrize('damage', ['missing', 'empty', 'oversized', 'escape'])
def test_repository_context_fails_closed(tmp_path, damage):
    repository(tmp_path)
    path = tmp_path / 'memory/LEARNED_RULES.md'
    role = '01_content_creator'
    if damage == 'missing':
        path.unlink()
    elif damage == 'empty':
        path.write_text(' ')
    elif damage == 'oversized':
        path.write_bytes(b'x' * (128 * 1024 + 1))
    else:
        role = '../private'
    with pytest.raises((ValueError, FileNotFoundError)):
        prepare_repository_agent_context(agent_id=role, job={'job_id': 'test'}, root=tmp_path)


def test_generator_uses_explicit_repository_without_r2(tmp_path, monkeypatch):
    repository(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('DAILY_IDEAS_MEMORY_BACKEND', 'repository')
    with patch.object(ideas, 'quick_chat', return_value='draft') as llm, \
         patch.object(ideas, 'get_context', return_value='memory'), \
         patch('integrations.openmontage.r2_client.from_environment') as r2:
        assert ideas.generate_content_plan() == 'draft'
    r2.assert_not_called()
    assert 'REPOSITORY' in llm.call_args.args[0]
    assert 'human approval required' in llm.call_args.args[0]
    assert llm.call_args.kwargs['response_validator'] is ideas.validate_content_plan


def test_r2_not_entitled_is_not_silently_ignored(monkeypatch):
    class Unavailable:
        def get_object(self, **kwargs):
            error = RuntimeError('NotEntitled')
            error.response = {'Error': {'Code': 'NotEntitled'}}
            raise error
    with patch.object(ideas, 'quick_chat') as llm, patch.object(ideas, 'get_context', return_value='memory'):
        with pytest.raises(RuntimeError, match='NotEntitled'):
            ideas.generate_content_plan(memory_storage=Unavailable())
    llm.assert_not_called()


def rows(count):
    return [dict(title=f'News {i}', url=f'https://example.test/{i}',
                 caption=f'Caption {i}', series='MotoGP', source_series='MotoGP') for i in range(count)]


def test_first_five_stop_editor_without_touching_other_55():
    candidates = rows(60)
    with patch.object(agency, 'ordered_pool', side_effect=lambda items, names: items), \
         patch.object(agency, 'qualify_parallel', side_effect=lambda items, workers: items) as qualify, \
         patch.object(agency, 'known_story_keys', return_value=set()), \
         patch.object(agency, 'review_batch', return_value=[(True, [])]), \
         patch.object(agency, 'finish_item', return_value=True) as finish, \
         patch.object(agency, 'yesterday_raw') as yesterday:
        current, fallback, picks = agency.qualify_daily_picks(candidates, [], datetime.now(timezone.utc))
    assert picks == candidates[:5]
    assert current == candidates[:5] and fallback == []
    qualify.assert_called_once_with(candidates[:5], 3)
    assert finish.call_count == 5
    yesterday.assert_not_called()


def test_rejected_copy_batch_and_media_continue_without_bypass():
    candidates = rows(15)
    def qualify(items, workers):
        return items[1:]  # First item in each chunk fails copy QM.
    with patch.object(agency, 'ordered_pool', side_effect=lambda items, names: items), \
         patch.object(agency, 'qualify_parallel', side_effect=qualify), \
         patch.object(agency, 'known_story_keys', return_value=set()), \
         patch.object(agency, 'review_batch', side_effect=lambda items: [(items[0] != candidates[2], [])]), \
         patch.object(agency, 'finish_item', side_effect=lambda item, i: item != candidates[3]) as finish:
        _, _, picks = agency.qualify_daily_picks(candidates, [], datetime.now(timezone.utc))
    assert picks == [candidates[i] for i in (1, 4, 6, 7, 8)]
    assert len({call.args[0]['url'] for call in finish.call_args_list}) == finish.call_count


def test_fallback_only_when_current_final_packages_insufficient():
    candidates = rows(6)
    with patch.object(agency, 'ordered_pool', side_effect=lambda items, names: items), \
         patch.object(agency, 'qualify_parallel', side_effect=lambda items, workers: items), \
         patch.object(agency, 'known_story_keys', return_value=set()), \
         patch.object(agency, 'review_batch', return_value=[(True, [])]), \
         patch.object(agency, 'finish_item', return_value=True), \
         patch.object(agency, 'yesterday_raw', return_value=candidates[2:]) as yesterday:
        current, fallback, picks = agency.qualify_daily_picks(candidates[:2], [], datetime.now(timezone.utc))
    assert len(picks) == 5 and len(current) == 2 and len(fallback) == 4
    yesterday.assert_called_once()


def test_cross_chunk_duplicate_does_not_pass():
    candidates = rows(6)
    duplicate = dict(candidates[0], title='renamed')
    with patch.object(agency, 'ordered_pool', side_effect=lambda items, names: items), \
         patch.object(agency, 'known_story_keys', return_value=set()), \
         patch.object(agency, 'review_batch', return_value=[(True, [])]), \
         patch.object(agency, 'finish_item', return_value=True) as finish:
        picks = agency.select_and_finish([duplicate, candidates[4]], [], existing=candidates[:4])
    assert picks == candidates[:5]
    finish.assert_called_once_with(candidates[4], 5)


def test_exhaustion_preserves_60_current_20_fallback_caps():
    candidates = rows(120)
    with patch.object(agency, 'ordered_pool', side_effect=lambda items, names: items), \
         patch.object(agency, 'qualify_parallel', return_value=[]) as qualify, \
         patch.object(agency, 'yesterday_raw', return_value=candidates[90:]), \
         patch.object(agency, 'finish_item') as finish:
        current, fallback, picks = agency.qualify_daily_picks(candidates[:90], [], datetime.now(timezone.utc))
    assert current == fallback == picks == []
    attempted = [item for call in qualify.call_args_list for item in call.args[0]]
    assert attempted == candidates[:60] + candidates[90:110]
    finish.assert_not_called()


def test_timeout_recovery_and_completed_day_dedupe(tmp_path, monkeypatch):
    monkeypatch.setattr(rc, 'STATE', tmp_path / 'state.json')
    monkeypatch.setenv('GITHUB_EVENT_NAME', 'schedule')
    now = datetime(2026, 11, 4, 7, tzinfo=timezone.utc)
    ok, bid, _ = rc.begin(now)
    assert ok
    assert not rc.morning_due(now + timedelta(minutes=17))
    assert not rc.begin(now + timedelta(minutes=17))[0]
    assert rc.morning_due(now + timedelta(minutes=90))
    assert rc.begin(now + timedelta(minutes=90))[0]
    rc.transition(bid, 'READY_FOR_APPROVAL')
    assert not rc.morning_due(now + timedelta(hours=3))
    assert not rc.begin(now + timedelta(hours=3))[0]


def test_workflow_memory_and_persistence_contract():
    daily = yaml.load(Path('.github/workflows/daily-ideas.yml').read_text(), Loader=yaml.BaseLoader)
    step = next(x for x in daily['jobs']['generate']['steps'] if x.get('name') == 'Run idea generator')
    assert step['env']['DAILY_IDEAS_MEMORY_BACKEND'] == 'repository'
    assert not any(key.startswith('R2_') for key in step['env'])
    racing = yaml.load(Path('.github/workflows/motogp-content-agency.yml').read_text(), Loader=yaml.BaseLoader)
    assert racing['concurrency']['cancel-in-progress'] == 'false'
    steps = racing['jobs']['collect']['steps']
    persist = next(i for i, x in enumerate(steps) if x.get('run') == 'bash scripts/persist_racing_state.sh')
    flush = next(i for i, x in enumerate(steps) if x.get('run') == 'python racing_flush_notifications.py')
    assert persist < flush and 'success()' in steps[flush]['if']
