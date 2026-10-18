"""B74: prove OpenMontage editorial approval never invokes social publishers."""
import ast
from pathlib import Path
import unittest

from scripts.openmontage_control import handle


class PublishingBoundaryTests(unittest.TestCase):
    def test_telegram_editorial_handler_has_no_publisher_import_or_call(self):
        source = Path("scripts/openmontage_control.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        banned = {"facebook_publish", "instagram_publish", "publish_to_facebook",
                  "publish_to_instagram", "publish_facebook", "publish_instagram"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(any(alias.name.split(".")[0] in banned for alias in node.names))
            elif isinstance(node, ast.ImportFrom):
                self.assertNotIn((node.module or "").split(".")[0], banned)
            elif isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else (
                    node.func.attr if isinstance(node.func, ast.Attribute) else "")
                self.assertNotIn(name, banned)

    def test_unknown_video_never_approves_social(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            response = handle("/montage freigeben 12345678-1234-1234-1234-123456789abc",
                              1, "123", "123", jobs_state=Path(tmp) / "jobs.json")
            self.assertIn("Keine Freigabe", response)


if __name__ == "__main__":
    unittest.main()
