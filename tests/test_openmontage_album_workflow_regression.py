"""B77: prevent regression to synthetic rendering for explicit owner albums."""
from pathlib import Path
import unittest


class AlbumWorkflowRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = Path(".github/workflows/openmontage.yml").read_text(encoding="utf-8")

    def test_album_input_is_explicit_and_opt_in(self):
        self.assertIn("      album_job_id:", self.workflow)
        self.assertIn("        default: ''", self.workflow)
        self.assertIn("inputs.album_job_id != ''", self.workflow)

    def test_album_selection_and_owner_renderer_are_wired(self):
        self.assertIn("scripts.openmontage_load_album_selection", self.workflow)
        self.assertIn("scripts.openmontage_render_owner_album", self.workflow)
        self.assertIn("--selections integrations/openmontage/.runtime/album_selection.json",
                      self.workflow)
        self.assertIn("--research integrations/openmontage/.runtime/verified_research.json",
                      self.workflow)

    def test_synthetic_render_only_without_album(self):
        marker = "      - name: Freigegebene Recherche als synthetisches MP4 rendern"
        section = self.workflow.split(marker, 1)[1].split("      - name:", 1)[0]
        self.assertIn("inputs.album_job_id == ''", section)
        self.assertIn("scripts.openmontage_render_verified", section)

    def test_no_automatic_social_publish(self):
        self.assertNotIn("python -m facebook_publish", self.workflow)
        self.assertNotIn("python -m instagram_publish", self.workflow)


if __name__ == "__main__":
    unittest.main()
