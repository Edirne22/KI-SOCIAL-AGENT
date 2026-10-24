import importlib.util
import pathlib
import unittest
from unittest.mock import patch
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("inventory", ROOT/"scripts/cloud_model_inventory.py")
inv=importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)
CFG={"api_key_env":"TEST_MODEL_KEY","base_url":"https://provider.example/v1"}
class FakeResponse:
    status_code=200
    def json(self):
        return {"data":[{"id":"qwen/qwen-coder"},{"id":"nvidia/nemotron"},{"id":"unrelated/model"},
                        {"id":"qwen/qwen-coder"}]}
class InventoryTests(unittest.TestCase):
    def test_absent_key_no_network(self):
        with patch.dict("os.environ",{},clear=True):
            self.assertEqual(inv.scan_one("nvidia",CFG)["state"],"SKIPPED_NO_KEY")
    def test_selected_models_only_no_key_leak(self):
        seen=[]
        def get(url,**kwargs):
            seen.append((url,kwargs))
            return FakeResponse()
        with patch.dict("os.environ",{"TEST_MODEL_KEY":"mock-secret"}):
            result=inv.scan_one("nvidia",CFG,transport=get)
        self.assertEqual(result["state"],"CATALOG_OK")
        self.assertEqual(result["matched_count"],2)
        self.assertEqual(len(result["models"]),2)
        self.assertNotIn("mock-secret",str(result))
        self.assertEqual(seen[0][1]["timeout"],12)
    def test_http_404_not_marked_available(self):
        class Missing:
            status_code=404
        with patch.dict("os.environ",{"TEST_MODEL_KEY":"mock-secret"}):
            result=inv.scan_one("groq",CFG,transport=lambda *a,**kw:Missing())
        self.assertEqual(result["state"],"HTTP_ERROR")
        self.assertFalse(result["models"])
if __name__=="__main__":unittest.main()
