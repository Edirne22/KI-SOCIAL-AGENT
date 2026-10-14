"""Regression tests for weekly community planning and provider failures."""
from unittest.mock import patch

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
        for day in ("Montag", "Dienstag", "Mittwoch", "Donnerstag", "Freitag", "Samstag", "Sonntag")
    )
    with patch.object(weekly_plan, "read", side_effect=fake_read), \
         patch.object(weekly_plan, "get_context", return_value="memory"), \
         patch.object(weekly_plan, "global_professional_context", return_value="standard"), \
         patch.object(weekly_plan, "quick_chat", return_value=response) as chat:
        result = weekly_plan.generate_weekly_plan()

    prompt = chat.call_args.args[0]
    assert "Turkbirler public club profile" in prompt
    assert "bike_society_hagen" in prompt
    assert "LETZTE COMMUNITY-ROTATION" in prompt
    assert "Turkbirler" in result


def test_provider_failure_is_not_saved_as_a_successful_plan():
    with patch.object(weekly_plan, "read", return_value="repo context"), \
         patch.object(weekly_plan, "get_context", return_value="memory"), \
         patch.object(weekly_plan, "global_professional_context", return_value="standard"), \
         patch.object(weekly_plan, "quick_chat", side_effect=RuntimeError("provider down")):
        try:
            weekly_plan.generate_weekly_plan()
        except RuntimeError as error:
            assert str(error) == "provider down"
        else:
            raise AssertionError("provider failure must fail the weekly planner")


if __name__ == "__main__":
    test_weekly_prompt_reads_community_and_requires_a_group_post()
    test_provider_failure_is_not_saved_as_a_successful_plan()
    print("Weekly community-plan tests: PASS")
