"""Offline regression for replying to an Instagram preview after delayed polling."""
import copy
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock
import pytest
import pending_instagram as pi
import telegram_router as tr

@pytest.fixture
def context(tmp_path, monkeypatch):
    monkeypatch.setattr(pi, "PENDING_FILE", tmp_path / "pending.json")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "123456:synthetic-test-token")
    monkeypatch.setattr(tr, "get_chat_id", lambda: "42")
    created = datetime.now(timezone.utc) - timedelta(hours=8)
    stamp = created.strftime("%Y-%m-%dT%H:%M:%SZ")
    pi.add_pending("older-batch", 4, "Wrong item", "old", "old.jpg", "", erstellt=stamp)
    pi.add_pending("target-batch", 4, "Exact preview", "caption", "image.jpg", "", erstellt=stamp)
    reply = {"from": {"id": 123456, "is_bot": True}, "chat": {"id": 42},
             "date": int(created.timestamp()) + 1, "photo": [{"file_id": "synthetic"}],
             "caption": "🖼️ Instagram-Bild bereit für: Exact preview\nAuswahl: 4 (Batch: target-batch)\n\nAntworte mit:\n- bild ✅"}
    message = {"chat": {"id": 42}, "text": "Posten", "reply_to_message": reply}
    monkeypatch.setattr(tr, "send_message", Mock())
    published = Mock(return_value=True)
    monkeypatch.setattr(tr, "_publish_instagram_pending", published)
    return message, published

@pytest.mark.parametrize("command", ["Posten", "Bild posten", "bild 4 posten", "✅"])
def test_main_reply_selects_exact_old_preview(context, monkeypatch, command):
    message, published = context
    message["text"] = command
    monkeypatch.setattr(tr, "_read_last_update_id", lambda: 10)
    monkeypatch.setattr(tr, "get_updates", lambda **kw: [{"update_id": 11, "message": message}])
    ack = Mock()
    monkeypatch.setattr(tr, "_ack", ack)
    tr.main()
    published.assert_called_once()
    assert published.call_args.args[0]["batch_id"] == "target-batch"
    ack.assert_called_once_with(11)

@pytest.mark.parametrize("mutation", [
    "other_bot", "not_bot", "foreign_reply_chat", "forwarded", "bad_caption",
    "newer_revision", "removed", "number_conflict",
])
def test_untrusted_or_mismatched_reply_never_falls_back(context, mutation):
    message, published = context
    reply = message["reply_to_message"]
    command = "bild posten"
    if mutation == "other_bot": reply["from"]["id"] = 999
    if mutation == "not_bot": reply["from"]["is_bot"] = False
    if mutation == "foreign_reply_chat": reply["chat"]["id"] = 999
    if mutation == "forwarded": reply["forward_origin"] = {"type": "user"}
    if mutation == "bad_caption": reply["caption"] = "T1 Preview"
    if mutation == "newer_revision":
        items = pi.load_pending()
        items[-1]["erstellt"] = datetime.now(timezone.utc).isoformat()
        pi.save_pending(items)
    if mutation == "removed": pi.remove_pending("target-batch", 4)
    if mutation == "number_conflict": command = "bild 3 posten"
    assert tr._handle_bild_command(command, message) is True
    published.assert_not_called()

def test_foreign_owner_message_cannot_approve(context, monkeypatch):
    message, published = context
    message["chat"]["id"] = 999
    monkeypatch.setattr(tr, "_read_last_update_id", lambda: 10)
    monkeypatch.setattr(tr, "get_updates", lambda **kw: [{"update_id": 11, "message": message}])
    monkeypatch.setattr(tr, "_ack", Mock())
    tr.main()
    published.assert_not_called()

def test_consumed_reply_is_not_reused(context, monkeypatch):
    message, published = context
    def consume(item):
        pi.remove_pending(item["batch_id"], item["auswahl"])
        return True
    published.side_effect = consume
    tr._handle_bild_command("bild posten", message)
    tr._handle_bild_command("bild posten", message)
    published.assert_called_once()

def test_no_reply_preserves_stale_item_guard(context):
    message, published = context
    tr._handle_bild_command("bild posten")
    published.assert_not_called()

def test_poller_covers_night():
    from pathlib import Path
    import re
    cron = re.search(r'cron:\s*"([^"]+)"', Path(".github/workflows/telegram-receive.yml").read_text()).group(1).split()
    assert cron[1:] == ["*", "*", "*", "*"]  # all hours, including night
    match = re.fullmatch(r'(?:\*|(\d+)-(\d+))/(\d+)', cron[0])
    assert match is not None
    start, end, step = match.groups()
    minutes = list(range(int(start or 0), int(end or 59) + 1, int(step)))
    assert len(minutes) == 12
    assert all((minutes[(i + 1) % 12] - minutes[i]) % 60 == 5 for i in range(12))
