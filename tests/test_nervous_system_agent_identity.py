"""Regression tests: ambiguous legacy agent numbers must never grant capabilities."""
import unittest
from scripts.ai_central_skill_router import (
    RoutingError, agent_can, choose_for_agent, resolve_agent_role,
)

class CanonicalRoleIdentityTests(unittest.TestCase):
    def test_numeric_15_never_resolves_to_finance_or_chief_qm(self):
        for value in (15, "15"):
            with self.assertRaisesRegex(RoutingError, "numeric"):
                resolve_agent_role(value)
            self.assertFalse(agent_can(value, "web_research"))
            with self.assertRaisesRegex(RoutingError, "not authorized"):
                choose_for_agent(value, "web_research")

    def test_numeric_18_never_resolves_to_tour_or_facebook(self):
        self.assertFalse(agent_can("18", "media_tools"))
        self.assertFalse(agent_can(18, "web_research"))

    def test_unknown_identity_fails_closed(self):
        self.assertFalse(agent_can("15_unknown_agent", "web_research"))
        with self.assertRaisesRegex(RoutingError, "unknown"):
            resolve_agent_role("15_unknown_agent")

    def test_distinct_canonical_15_roles_still_work(self):
        self.assertEqual(resolve_agent_role("15_finance_planner"), "15_finance_planner")
        self.assertEqual(resolve_agent_role("15_chief_quality_manager"), "15_chief_quality_manager")
        self.assertTrue(agent_can("15_finance_planner", "web_research"))
        self.assertTrue(agent_can("15_chief_quality_manager", "web_research"))
        self.assertFalse(agent_can("15_finance_planner", "coding"))

    def test_other_canonical_roles_unchanged(self):
        self.assertTrue(agent_can("21_instandhaltungsagent", "coding"))
        self.assertTrue(agent_can("18_tour_ride_story_agent", "media_tools"))

if __name__ == "__main__":
    unittest.main()
