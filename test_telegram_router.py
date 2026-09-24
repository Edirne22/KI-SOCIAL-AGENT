import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import patch

# Router-Abhängigkeiten stubben: Dieser Unit-Test prüft ausschließlich Offset-Persistenz.
def _stub(name, **attrs):
    module = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(module, key, value)
    sys.modules[name] = module

_stub("vision_router", VisionRouter=object)
_stub("pending_instagram")
_stub("facebook_engagement")
_stub("generate_agnes_media", agnes_generate_image=lambda *_: None, save_bytes=lambda *_: None)
_stub("instagram_publish", process_image_for_instagram=lambda x: x, create_container=lambda *_: None, publish=lambda *_: None, wait=lambda *_: False)
_stub("asset_paths", asset_url=lambda *_: "", RAW_BASE="")

import telegram_router as tr


class TelegramOffsetTests(unittest.TestCase):
    def test_first_run_baselines_and_second_run_uses_persistent_offset(self):
        update = {"update_id": 42, "message": {"chat": {"id": "1"}, "text": "info IG-12345678"}}
        calls = []

        def fake_get_updates(offset=None):
            calls.append(offset)
            if offset is None:
                return [update]
            return []

        with tempfile.TemporaryDirectory() as tmp:
            offset_file = Path(tmp) / "TELEGRAM_LAST_UPDATE_ID"
            with patch.object(tr, "TELEGRAM_LAST_UPDATE_FILE", offset_file), \
                 patch.object(tr, "get_chat_id", return_value="1"), \
                 patch.object(tr, "get_updates", side_effect=fake_get_updates), \
                 patch.object(tr, "send_message") as send:
                tr.main()
                self.assertEqual(offset_file.read_text(encoding="utf-8").strip(), "42")
                send.assert_not_called()
                tr.main()
                send.assert_not_called()

        self.assertEqual(calls, [None, 43, 43])


if __name__ == "__main__":
    unittest.main()
