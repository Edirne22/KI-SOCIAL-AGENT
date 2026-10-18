from pathlib import Path
import unittest

class ActionsRenderWiringTests(unittest.TestCase):
    def test_production_mode_wires_secure_research_render_preview(self):
        workflow = Path(".github/workflows/openmontage.yml").read_text(encoding="utf-8")
        self.assertIn("scripts.openmontage_load_verified_research", workflow)
        self.assertIn("scripts.openmontage_render_verified", workflow)
        self.assertIn("scripts.openmontage_publish_preview", workflow)
        self.assertIn("rendered/creative-demo.mp4", workflow)
        self.assertNotIn("            integrations/openmontage/.runtime/rendered/creative-demo.mp4\\n", workflow.split("path: |")[-1])

    def test_private_research_loader_is_fail_closed(self):
        loader = Path("scripts/openmontage_load_verified_research.py").read_text(encoding="utf-8")
        self.assertIn("verify_research_payload", loader)
        self.assertIn("owner_chat_sha256", loader)
        self.assertIn('openmontage/research/{request_id}.json', loader)
