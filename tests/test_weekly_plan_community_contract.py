"""Regression tests for weekly community planning and provider failures."""
from unittest.mock import patch, Mock
import os
import llm_router
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import weekly_plan


def test_weekly_prompt_reads_community_and_requires_a_group_post():
    def fake_read(path, max_chars=10000):
        return {
            "content/TURKISH_BIKER_COMMUNITY.md": "Turkbirler public club profile",
            "config/followed_accounts.md": "bike_society_hagen",
            "memory/COMMUNITY_ROTATION.json": '"last_community": "bike_society_bergisches_land"',
        }.get(path, "repo context")

    response = "\n".join(
        f"{day}: Motorradthema. Community-Beitrag über Turkbirler."
        for day in ((datetime.now(ZoneInfo("Europe/Berlin")).date() + timedelta(days=i)).isoformat() for i in range(7))
    )
    with patch.object(weekly_plan, "calendar_context", return_value="calendar fixture"), \
         patch.object(weekly_plan, "read", side_effect=fake_read), \
         patch.object(weekly_plan, "get_context", return_value="memory"), \
         patch.object(weekly_plan, "global_professional_context", return_value="standard"), \
         patch.object(weekly_plan, "quick_chat", return_value=response) as chat:
        result = weekly_plan.generate_weekly_plan()

    assert chat.call_args.kwargs["task_type"] == "weekly_plan"
    prompt = chat.call_args.args[0]
    assert "Turkbirler public club profile" in prompt
    assert "bike_society_hagen" in prompt
    assert "LETZTE COMMUNITY-ROTATION" in prompt
    assert "Turkbirler" in result


def test_provider_failure_is_not_saved_as_a_successful_plan():
    with patch.object(weekly_plan, "calendar_context", return_value="calendar fixture"), \
         patch.object(weekly_plan, "read", return_value="repo context"), \
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
    assert post.call_args.kwargs["json"]["model"] == router.config["providers"]["groq"]["models"]["reasoning"]


def test_weekly_route_is_bounded_and_preserves_other_routes():
    router = llm_router.LLMRouter()
    assert router.config["task_routing"]["reasoning"] == ["openrouter", "google", "nvidia"]
    assert router.config["task_routing"]["weekly_plan"] == ["groq", "openrouter", "google", "nvidia"]
    for name in router.config["task_routing"]["weekly_plan"]:
        models = router.config["providers"][name]["models"]
        assert models["weekly_plan"] == models.get("reasoning", models["default"])
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

if __name__ == "__main__":
    test_weekly_prompt_reads_community_and_requires_a_group_post()
    test_provider_failure_is_not_saved_as_a_successful_plan()
    test_weekly_route_uses_existing_groq_model_first()
    test_weekly_route_is_bounded_and_preserves_other_routes()
    print("Weekly community-plan tests: PASS")
