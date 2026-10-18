import ast
import unittest
from pathlib import Path


class RouterFeedbackWiringTests(unittest.TestCase):
    def test_router_injects_feedback_storage_only_for_editorial_commands(self):
        source = Path("telegram_router.py").read_text(encoding="utf-8")
        ast.parse(source)
        self.assertIn('parsed_montage.startswith(("approve:", "reject:"))', source)
        self.assertIn('feedback_storage=feedback_storage', source)
        self.assertIn('request_storage=private_storage', source)


if __name__ == "__main__":
    unittest.main()
