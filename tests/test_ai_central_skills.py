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
    def test_catalog_listing_not_equal_to_verified_inference(self):
        with self.assertRaises(sr.RoutingError):
            sr.choose("image_generation",forced_provider="google",
                      available={"google":{"gemini-3.1-flash-image":"CATALOG_OK"}},registry=self.registry)
    def test_default_fallback_only_when_explicitly_unlocked(self):
        x=sr.choose("reasoning",available={"openrouter":{"openrouter/free":"INFERENCE_OK"}},registry=self.registry)
        self.assertEqual(x["provider"],"openrouter")
        self.assertFalse(x["no_fallback"])
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
