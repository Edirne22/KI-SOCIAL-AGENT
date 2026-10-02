"""Static positive and adversarial contracts for the Edirne 22 agency roster.

This is a documentation/handoff consistency test, NOT proof of a live dispatcher.
"""
from __future__ import annotations
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "agents" / "AGENTS_INDEX.md"
ORG = ROOT / "docs" / "AGENCY_ORG_AND_HANDOFF.md"
REQUIRED_ROLES = {
    "01_content_creator.md", "02_instagram_curator.md", "03_tiktok_strategist.md",
    "04_social_media_strategist.md", "05_research_synthesist.md",
    "06_reddit_community_builder.md", "07_video_optimization.md",
    "08_paid_social_strategist.md", "09_quality_agent.md",
    "10_follow_analysis_agent.md", "11_system_restart_agent.md",
    "12_music_agent.md", "14_memory_curator.md", "15_finance_planner.md",
    "17_instagram_engagement_agent.md", "18_tour_ride_story_agent.md",
    "19_ki_integrationsingenieur.md", "20_maschinen_scout.md",
}
ROW_RE = re.compile(r"^\| \[(\d{2}_[a-z0-9_]+\.md)\]\(\1\) \| [^|]+\| [^|]+\|$", re.M)


def inspect_roster(content: str, exists=lambda name: True) -> set[str]:
    # No escaped 'newline' token may conceal adjacent Markdown table rows.
    if r"\n|" in content:
        raise ValueError("literal escaped newline in agent table")
    role_rows = ROW_RE.findall(content)
    if len(role_rows) != len(set(role_rows)):
        raise ValueError("duplicate roster entries")
    roles = set(role_rows)
    if roles != REQUIRED_ROLES:
        raise ValueError(f"missing/foreign role entries: {sorted(REQUIRED_ROLES ^ roles)}")
    if not all(exists(name) for name in roles):
        raise ValueError("roster link points to absent agent description")
    if "Historisch" not in content and "Historische" not in content and "Historisch" not in content.title():
        raise ValueError("legacy ID ambiguity not documented")
    if "Agent 18" not in content and "„18“" not in content:
        raise ValueError("historical Facebook role collision not disclosed")
    if "keine" not in content.lower() or "freigabe" not in content.lower():
        raise ValueError("no explicit authority boundary")
    return roles


def inspect_handoffs(content: str) -> None:
    terms = (
        "Produktionsleiter", "Ressourcenmanager", "Research",
        "Source", "Media", "Security", "Golden", "Publisher",
        "Memory", "Scout", "Integrationsingenieur", "Bülent",
        "Revision", "STATUS", "R2", "Kosten",
    )
    if any(token.lower() not in content.lower() for token in terms):
        raise ValueError("incomplete agency handoff document")
    for required in ("kein", "Freigabe", "OPEN"):
        if required.lower() not in content.lower():
            raise ValueError("missing explicit uncertainty or human approval")


class AgencyRosterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = INDEX.read_text(encoding="utf-8")
        cls.org = ORG.read_text(encoding="utf-8")

    def test_all_role_links_exist_and_are_unique(self):
        self.assertEqual(inspect_roster(self.index, lambda name: (ROOT / "agents" / name).is_file()), REQUIRED_ROLES)

    def test_hierarchy_contains_distinct_authority_and_missing_runtime_disclosure(self):
        inspect_handoffs(self.org)

    def test_malformed_escaped_lines_rejected(self):
        with self.assertRaisesRegex(ValueError, "escaped newline"):
            inspect_roster(self.index.replace("| [20_maschinen_scout.md]", r"\n| [20_maschinen_scout.md]"))

    def test_duplicate_role_rejected(self):
        first = next(line for line in self.index.splitlines() if line.startswith("| [01_content_creator.md]"))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            inspect_roster(self.index + "\n" + first)

    def test_missing_role_rejected(self):
        damaged = "\n".join(line for line in self.index.splitlines() if not line.startswith("| [14_memory_curator.md]"))
        with self.assertRaisesRegex(ValueError, "missing"):
            inspect_roster(damaged)

    def test_missing_agent_file_rejected(self):
        with self.assertRaisesRegex(ValueError, "absent"):
            inspect_roster(self.index, lambda name: name != "20_maschinen_scout.md")

    def test_missing_org_contract_rejected(self):
        with self.assertRaisesRegex(ValueError, "incomplete"):
            inspect_handoffs(self.org.replace("Ressourcenmanager", "other-role"))

    def test_no_marketing_100_percent_claim(self):
        self.assertNotIn("100% efficiency", self.org.lower())
        self.assertIn("nicht", self.org.lower())

    def test_agent_runtime_rules_reference_current_guardrails(self):
        policy = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("PROJECT_GUARDRAILS.md", policy)
        self.assertIn("docs/AGENCY_ORG_AND_HANDOFF.md", policy)
        self.assertIn("OmniRoute", policy)
        self.assertIn("PAUSED", policy)
        self.assertNotIn("OmniRoute auf VPS als zentrales Gateway", policy)
        self.assertNotIn("Bei Testfehlern: nur Analyse + Kommentar", policy)


if __name__ == "__main__":
    unittest.main()
