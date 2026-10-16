"""Regression tests for weekly community planning and provider failures."""
from unittest.mock import patch, Mock
import os
import json
import pytest
import llm_router
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import weekly_plan


def test_weekly_prompt_reads_community_and_requires_a_group_post():
    def fake_read(path, max_chars=10000):
        return {
            "content/TURKISH_BIKER_COMMUNITY.md": "## Seriöse Clubs & Gruppen\n### Turkbirler\npublic club profile\n## Wichtig: Nicht verwenden\n### Forbidden Club",
            "config/followed_accounts.md": "bike_society_hagen",
            "memory/COMMUNITY_ROTATION.json": '"last_community": "bike_society_bergisches_land"',
        }.get(path, "repo context")

    response = selection()
    with patch.object(weekly_plan, "calendar_context", return_value='{"events": []}'), \
         patch.object(weekly_plan, "read", side_effect=fake_read), \
         patch.object(weekly_plan, "get_context", return_value="memory"), \
         patch.object(weekly_plan, "global_professional_context", return_value="standard"), \
         patch.object(weekly_plan, "quick_chat", return_value=response) as chat:
        result = weekly_plan.generate_weekly_plan()

    assert chat.call_args.kwargs["task_type"] == "weekly_plan"
    prompt = chat.call_args.args[0]
    assert "## Seriöse Clubs & Gruppen\n### Turkbirler\npublic club profile\n## Wichtig: Nicht verwenden\n### Forbidden Club" in prompt
    assert "bike_society_hagen" in prompt
    assert "LETZTE COMMUNITY-ROTATION" in prompt
    assert "Turkbirler" in result


def test_provider_failure_is_not_saved_as_a_successful_plan():
    with patch.object(weekly_plan, "calendar_context", return_value='{"events": []}'), \
         patch.object(weekly_plan, "read", return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(weekly_plan, "get_context", return_value="memory"), \
         patch.object(weekly_plan, "global_professional_context", return_value="standard"), \
         patch.object(weekly_plan, "quick_chat", side_effect=RuntimeError("provider down")):
        try:
            weekly_plan.generate_weekly_plan()
        except RuntimeError as error:
            assert str(error) == "provider down"
        else:
            raise AssertionError("provider failure must fail the weekly planner")



def test_weekly_route_uses_existing_groq_model_first():
    router = llm_router.LLMRouter()
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "synthetic weekly plan"}}]}
    with patch.dict(os.environ, {"GROQ_API_KEY": "fixture"}, clear=True), \
         patch.object(llm_router.requests, "post", return_value=response) as post:
        assert router.chat([{"role": "user", "content": "fixture"}], task_type="weekly_plan") == "synthetic weekly plan"
    post.assert_called_once()
    assert post.call_args.args[0] == "https://api.groq.com/openai/v1/chat/completions"
    assert post.call_args.kwargs["json"]["model"] == "openai/gpt-oss-120b"
    assert post.call_args.kwargs["json"]["reasoning_effort"] == "low"
    assert post.call_args.kwargs["json"]["include_reasoning"] is False
    assert post.call_args.kwargs["json"]["max_tokens"] == 2000


def test_weekly_route_is_bounded_and_preserves_other_routes():
    router = llm_router.LLMRouter()
    assert router.config["task_routing"]["reasoning"] == ["openrouter", "google", "nvidia"]
    assert router.config["task_routing"]["weekly_plan"] == ["groq", "openrouter", "google", "nvidia"]
    for name in router.config["task_routing"]["weekly_plan"]:
        models = router.config["providers"][name]["models"]
        assert models["weekly_plan"] == (models["default"] if name == "groq" else models.get("reasoning", models["default"]))
    keys = {router.config["providers"][name]["api_key_env"]: "fixture"
            for name in router.config["task_routing"]["weekly_plan"]}
    response = Mock(status_code=503)
    with patch.dict(os.environ, keys, clear=True), \
         patch.object(llm_router.requests, "post", return_value=response) as post:
        try:
            router.chat([{"role": "user", "content": "fixture"}], task_type="weekly_plan")
        except RuntimeError:
            pass
        else:
            raise AssertionError("Outage must not produce a successful plan")
    assert post.call_count == 4

def complete_plan():
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    return "\n".join(f"{today + timedelta(days=i)}: Community Club-Porträt." for i in range(7))


def test_weekly_truncated_response_is_rejected_without_exposing_text(capsys):
    router = llm_router.LLMRouter()
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"finish_reason": "length", "message": {"content": "PRIVATE_RESPONSE"}}]}
    cfg = router.config["providers"]["groq"]
    with patch.dict(os.environ, {"GROQ_API_KEY": "fixture"}, clear=True), \
         patch.object(llm_router.requests, "post", return_value=response):
        assert router._call_provider("groq", cfg, [], "weekly_plan") is None
    logs = capsys.readouterr().out
    assert "Tokenlimit" in logs and "PRIVATE_RESPONSE" not in logs


def test_other_routes_keep_existing_payload():
    router = llm_router.LLMRouter()
    response = Mock(status_code=200)
    response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    with patch.dict(os.environ, {"GROQ_API_KEY": "fixture"}, clear=True), \
         patch.object(llm_router.requests, "post", return_value=response) as post:
        assert router.chat([], task_type="default") == "ok"
    assert "reasoning_effort" not in post.call_args.kwargs["json"]
    assert "include_reasoning" not in post.call_args.kwargs["json"]


def test_large_history_is_bounded_but_calendar_and_standards_survive():
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    calendar = json.dumps({"events": [{"series": "MotoGP", "track": "Fixture Track",
        "date_start": today.isoformat(), "date_end": today.isoformat(),
        "sessions": [], "source": "https://www.motogp.com/en/calendar",
        "source_excerpt": "exact source evidence"}]})
    standard = weekly_plan.global_professional_context()
    with patch.object(weekly_plan, "calendar_context", return_value=calendar), \
         patch.object(weekly_plan, "read", side_effect=lambda path, max_chars=10000: ("## Seriöse Clubs & Gruppen\n### Turkbirler" if path.endswith("TURKISH_BIKER_COMMUNITY.md") else ("history " * 10000)[-max_chars:])), \
         patch.object(weekly_plan, "get_context", side_effect=lambda size: ("memory " * 10000)[-size:]), \
         patch.object(weekly_plan, "quick_chat", return_value=selection()) as chat:
        weekly_plan.generate_weekly_plan()
    prompt = chat.call_args.args[0]
    assert len(prompt.encode("utf-8")) <= weekly_plan.MAX_PROMPT_BYTES
    assert calendar in prompt and standard in prompt
    chat.assert_called_once()


def test_oversized_required_context_stops_before_network():
    with patch.object(weekly_plan, "calendar_context", return_value='{"events": []}'), \
         patch.object(weekly_plan, "read", return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(weekly_plan, "get_context", return_value=""), \
         patch.object(weekly_plan, "global_professional_context", return_value="X" * 21000), \
         patch.object(weekly_plan, "quick_chat") as chat, \
         pytest.raises(RuntimeError, match="Kontext zu groß"):
        weekly_plan.generate_weekly_plan()
    chat.assert_not_called()


@pytest.mark.parametrize("claim", [" Rennen 2099-12-31", " Rennen 31.12.2099", " Sprint 14:00", " Start 14 Uhr"])
def test_unproven_calendar_claims_block_save(claim):
    with patch.object(weekly_plan, "calendar_context", return_value='{"events": []}'), \
         patch.object(weekly_plan, "read", return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(weekly_plan, "get_context", return_value=""), \
         patch.object(weekly_plan, "global_professional_context", return_value=""), \
         patch.object(weekly_plan, "quick_chat", return_value=complete_plan() + claim), \
         patch.object(weekly_plan, "save_weekly_plan") as save, \
         pytest.raises(RuntimeError):
        weekly_plan.save_weekly_plan(weekly_plan.generate_weekly_plan())
    save.assert_not_called()


def test_calendar_dates_and_missing_session_notice_are_accepted():
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    calendar = json.dumps({"events": [{"date_start": today.isoformat(), "date_end": (today + timedelta(days=8)).isoformat()}]})
    weekly_plan.validate_calendar_claims(complete_plan() + f" Rennen bis {today + timedelta(days=8)}; Sessionzeiten fehlen.", calendar, today)




def selection():
    return json.dumps(["community_0", "tour", "pause", "kalender", "ausruestung", "gemeinschaft", "technik"])


@pytest.mark.parametrize("response", [
    "Bagnaia holt in Sepang Pole; Moto2 Barcelona: Álex Río und Kaito Matsumoto.",
    json.dumps(["community_0", "tour", "pause", "kalender", "ausruestung", "gemeinschaft", "Bagnaia Pole"]),
    json.dumps({"days": json.loads(selection()), "result": "Bagnaia holt Pole"}),
    json.dumps(["community_0", "tour", "pause", "kalender", "ausruestung", "gemeinschaft", {"technik": "14:00"}]),
    json.dumps(["community_0", "tour", "pause", "kalender", "ausruestung", "gemeinschaft", "tour"]),
    json.dumps(["community_0", "tour", "pause", "erinnerung", "ausruestung", "gemeinschaft", "technik"]),
    selection() + " Startaufstellung steht fest.",
    "null", "[]", "{}",
])
def test_free_facts_and_invalid_selection_never_reach_save(response):
    with patch.object(weekly_plan, "calendar_context", return_value='{"events": []}'), \
         patch.object(weekly_plan, "read", return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(weekly_plan, "get_context", return_value=""), \
         patch.object(weekly_plan, "global_professional_context", return_value=""), \
         patch.object(weekly_plan, "quick_chat", return_value=response), \
         patch.object(weekly_plan, "save_weekly_plan") as save, \
         pytest.raises(RuntimeError):
        weekly_plan.save_weekly_plan(weekly_plan.generate_weekly_plan())
    save.assert_not_called()


def test_sourced_calendar_reaches_saved_plan_without_generated_results(tmp_path, monkeypatch):
    today = datetime.now(ZoneInfo("Europe/Berlin")).date()
    calendar = json.dumps({"events": [{"series": "MotoGP", "track": "Phillip Island",
        "date_start": today.isoformat(), "date_end": (today + timedelta(days=3)).isoformat(),
        "source": "https://www.motogp.com/en/calendar", "source_excerpt": "Australia source excerpt", "sessions": []}]})
    monkeypatch.chdir(tmp_path)
    with patch.object(weekly_plan, "calendar_context", return_value=calendar), \
         patch.object(weekly_plan, "read", return_value="## Seriöse Clubs & Gruppen\n### Turkbirler"), \
         patch.object(weekly_plan, "get_context", return_value="Bagnaia holt Pole in Sepang"), \
         patch.object(weekly_plan, "global_professional_context", return_value=""), \
         patch.object(weekly_plan, "quick_chat", return_value=selection()):
        weekly_plan.save_weekly_plan(weekly_plan.generate_weekly_plan())
    saved = (tmp_path / "content/WOCHENPLAN.md").read_text()
    assert "Phillip Island" in saved and "Australia source excerpt" in saved
    assert str(today + timedelta(days=3)) in saved
    assert "Bagnaia" not in saved and "Sepang" not in saved and "14:00" not in saved
    assert saved.count("\n## 20") == 7 and "ENTWURF" in saved
    assert "Sessionzeiten" in saved and "nicht rennfrei" in saved


def test_unapproved_or_missing_clubs_cannot_be_selected():
    with pytest.raises(RuntimeError):
        weekly_plan.editorial_catalog("## Wichtig: Nicht verwenden\n### Forbidden Club")
    catalog = weekly_plan.editorial_catalog("## Seriöse Clubs & Gruppen\n### Turkbirler\n## Wichtig: Nicht verwenden\n### Forbidden Club")
    assert len([key for key in catalog if key.startswith("community_")]) == 1
    assert "Forbidden" not in str(catalog)


if __name__ == "__main__":
    test_weekly_prompt_reads_community_and_requires_a_group_post()
    test_provider_failure_is_not_saved_as_a_successful_plan()
    test_weekly_route_uses_existing_groq_model_first()
    test_weekly_route_is_bounded_and_preserves_other_routes()
    print("Weekly community-plan tests: PASS")
