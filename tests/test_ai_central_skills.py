import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from scripts import ai_central_skill_router as sr
from scripts import ai_central_document_export as ex

class Router(unittest.TestCase):
    def setUp(self):
        self.registry=sr.load_registry()
    def test_forced_claude_never_changes_to_other_models(self):
        with self.assertRaisesRegex(sr.RoutingError,"not live-verified"):
            sr.choose("document_edit",forced_provider="claude",available={
                "google":{"gemini-3.6-flash":"INFERENCE_OK"}
            },registry=self.registry)
        x=sr.choose("document_edit",forced_provider="claude",available={
            "claude":{"claude-sonnet-4-5":"INFERENCE_OK"}
        },registry=self.registry)
        self.assertEqual(x["provider"],"claude")
        self.assertTrue(x["no_fallback"])
        self.assertEqual(x["secret_name"],"ANTHROPIC_API_KEY")
    def test_claude_only_can_use_verified_anthropic_openrouter_transport(self):
        x=sr.choose("document_edit",forced_provider="claude",available={
            "google":{"gemini-3.6-flash":"INFERENCE_OK"},
            "claude_openrouter":{"anthropic/claude-sonnet-4.5":"INFERENCE_OK"}},registry=self.registry)
        self.assertEqual(x["provider"],"claude_openrouter")
        self.assertEqual(x["secret_name"],"OPENROUTER_API_KEY")
        self.assertTrue(x["model"].startswith("anthropic/claude-"))
        self.assertTrue(x["no_fallback"])
    def test_catalog_listing_not_equal_to_verified_inference(self):
        with self.assertRaises(sr.RoutingError):
            sr.choose("image_generation",forced_provider="google",
                      available={"google":{"gemini-3.1-flash-image":"CATALOG_OK"}},registry=self.registry)
    def test_default_fallback_only_when_explicitly_unlocked(self):
        x=sr.choose("reasoning",available={"openrouter":{"openrouter/free":"INFERENCE_OK"}},registry=self.registry)
        self.assertEqual(x["provider"],"openrouter")
        self.assertFalse(x["no_fallback"])
    def test_research_agents_are_allowlisted_and_others_fail_closed(self):
        for agent in ("05_research_synthesist","13_motogp_content_agency","16_turkish_riders_scout","18_tour_ride_story_agent","19_ki_integrationsingenieur","20_maschinen_scout","21_instandhaltungsagent"):
            self.assertTrue(sr.agent_can(agent,"web_research",self.registry),agent)
        self.assertFalse(sr.agent_can("17_instagram_engagement_agent","web_research",self.registry))
        with self.assertRaisesRegex(sr.RoutingError,"not authorized"):
            sr.choose_for_agent("17_instagram_engagement_agent","web_research",available={},registry=self.registry)
    def test_web_research_still_requires_live_verified_model(self):
        with self.assertRaisesRegex(sr.RoutingError,"no live-verified"):
            sr.choose_for_agent("05_research_synthesist","web_research",available={},registry=self.registry)
        x=sr.choose_for_agent("05_research_synthesist","web_research",available={
            "nvidia":{"nvidia/nemotron-3.5-lightning-30b-a3b":"INFERENCE_OK"}},registry=self.registry)
        self.assertEqual(x["provider"],"nvidia")
        self.assertEqual(x["task"],"web_research")
    def test_exporter_validation_and_formula_escape(self):
        data={"title":"Rezeptur Analyse","paragraphs":["Daten wurden geprüft"],
              "table":[["Rezept","Anteil"],["Mischung",50],["=HYPERLINK(\"http://bad\")","Ne"]]}
        ex.validate(data)
        self.assertTrue(ex.spreadsheet_cell(data["table"][-1][0]).startswith("'="))
        with self.assertRaises(ValueError):
            ex.validate({**data,"table":[["a"],["a","b"]]})
        self.assertEqual(sr.document_skill(".xlsx","claude")["requires_verified_anthropic_key"],True)
    def test_pdf_docx_files_are_real(self):
        data={"title":"Bülent KI-Zentrale","paragraphs":["Testbericht zu Tabelle"],
              "table":[["Modell","Status"],["Gemini","getestet"]]}
        with tempfile.TemporaryDirectory() as temp:
            for fmt,signature in [("pdf",b"%PDF"),("docx",b"PK")]:
                path=pathlib.Path(temp)/("report."+fmt)
                result=ex.export(data,path)
                self.assertEqual(result["format"],fmt)
                self.assertTrue(path.read_bytes().startswith(signature))

if __name__=="__main__":unittest.main()
