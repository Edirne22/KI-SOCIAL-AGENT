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
_stub("pending_instagram", get_latest_pending=lambda: None)
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


    def test_turkish_human_post_command_routes_to_racing_receiver(self):
        update = {"update_id": 43, "message": {"chat": {"id": "1"}, "text": "T1,T3,T5 posten"}}
        with tempfile.TemporaryDirectory() as tmp:
            offset_file = Path(tmp) / "TELEGRAM_LAST_UPDATE_ID"
            offset_file.write_text("42\n", encoding="utf-8")
            def fake_get_updates(offset=None):
                return [update] if offset == 43 else []
            completed = types.SimpleNamespace(returncode=0)
            with patch.object(tr, "TELEGRAM_LAST_UPDATE_FILE", offset_file), \
                 patch.object(tr, "get_chat_id", return_value="1"), \
                 patch.object(tr, "get_updates", side_effect=fake_get_updates), \
                 patch.object(tr.subprocess, "run", return_value=completed) as run:
                tr.main()
            args = run.call_args.args[0]
            self.assertEqual(args[1], "-u")
            self.assertEqual(args[2], "motogp_telegram_receive.py")
            self.assertEqual(args[-1], "T1,T3,T5 posten")
            self.assertEqual(offset_file.read_text(encoding="utf-8").strip(), "43")


    def test_skipped_foreign_update_does_not_drop_following_owner_update(self):
        updates = [
            {"update_id": 43, "message": {"chat": {"id": "999"}, "text": "posten"}},
            {"update_id": 44, "message": {"chat": {"id": "1"}, "text": "T1,T3,T5 posten"}},
        ]
        with tempfile.TemporaryDirectory() as tmp:
            offset_file = Path(tmp) / "TELEGRAM_LAST_UPDATE_ID"
            offset_file.write_text("42\n", encoding="utf-8")
            def fake_get_updates(offset=None):
                return updates if offset == 43 else []
            completed = types.SimpleNamespace(returncode=0)
            with patch.object(tr, "TELEGRAM_LAST_UPDATE_FILE", offset_file), \
                 patch.object(tr, "get_chat_id", return_value="1"), \
                 patch.object(tr, "get_updates", side_effect=fake_get_updates), \
                 patch.object(tr.subprocess, "run", return_value=completed) as run:
                tr.main()
            self.assertTrue(run.called, "following owner update must still be routed")
            self.assertEqual(run.call_args.args[0][-1], "T1,T3,T5 posten")
            self.assertEqual(offset_file.read_text(encoding="utf-8").strip(), "44")



if __name__ == "__main__":
    unittest.main()
