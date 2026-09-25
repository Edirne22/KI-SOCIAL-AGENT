"""Tests for Instagram two-stage approval functionality."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock

import pending_instagram as pi
import telegram_router as tr
import motogp_telegram_receive_v85 as approval


def test_pending_instagram_manager(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)

    assert pi.load_pending() == []

    # Add item
    item = pi.add_pending(
        batch_id="racing-2026-09-21-daily",
        auswahl=3,
        titel="Test Titel",
        text="Test Text",
        bild_pfad="assets/images/test.jpg",
        prompt_fuer_agnes="Test Prompt",
    )

    assert item["batch_id"] == "racing-2026-09-21-daily"
    assert item["auswahl"] == 3

    loaded = pi.load_pending()
    assert len(loaded) == 1
    assert loaded[0]["titel"] == "Test Titel"

    # Get first
    first = pi.get_first_pending()
    assert first["auswahl"] == 3

    # Update image
    updated = pi.update_pending_image("racing-2026-09-21-daily", 3, "assets/images/new.jpg")
    assert updated["bild_pfad"] == "assets/images/new.jpg"
    assert pi.get_first_pending()["bild_pfad"] == "assets/images/new.jpg"

    # Remove item
    removed = pi.remove_pending("racing-2026-09-21-daily", 3)
    assert removed["batch_id"] == "racing-2026-09-21-daily"
    assert pi.load_pending() == []


def test_motogp_approval_publish_two_stage(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    test_published = tmp_path / "PUBLISHED.md"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(approval, "PUBLISHED", test_published)

    # Dummy image file
    test_img = tmp_path / "dummy.jpg"
    test_img.write_bytes(b"fake image data")

    posts = {
        3: {
            "title": "Quiles Cruises To Victory",
            "source": "https://motogp.com/news/1",
            "image": str(test_img),
            "text": "Great race in Austria!",
        }
    }

    mock_agnes = MagicMock(return_value=b"new agnes image bytes")
    mock_send_photo = MagicMock()

    monkeypatch.setattr(approval, "agnes_generate_image", mock_agnes)
    monkeypatch.setattr(approval, "download_og_image_for_instagram", lambda source, target: str(test_img))
    monkeypatch.setattr(approval, "generate_buelent_caption", lambda text: "Bülent: " + text)
    monkeypatch.setattr(approval, "send_photo", mock_send_photo)

    count = approval.publish(posts, [3], uid=1001, batch="batch-123")
    assert count == 2  # 1 Instagram + 1 Facebook block

    published_content = test_published.read_text(encoding="utf-8")
    assert "## Instagram" in published_content
    assert "Status: BILD_GENERIERT" in published_content
    assert "## Facebook" in published_content
    assert "Status: FREIGEGEBEN" in published_content
    assert "Medienstatus: QUELLE_BESTÄTIGT" in published_content
    assert "Bülent: Great race in Austria!" in published_content

    pending = pi.load_pending()
    assert len(pending) == 1
    assert pending[0]["batch_id"] == "batch-123"
    assert pending[0]["auswahl"] == 3

    mock_agnes.assert_not_called()
    mock_send_photo.assert_called_once()
    self_photo_path = mock_send_photo.call_args.args[0]
    assert self_photo_path == str(test_img)
    caption = mock_send_photo.call_args[1].get("caption", "")
    assert "🖼️ Instagram-Bild bereit für: Quiles Cruises To Victory" in caption
    assert "bild ✅" in caption


def test_telegram_router_bild_commands(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    test_published = tmp_path / "PUBLISHED.md"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(tr, "Path", lambda p: test_published if p == "content/PUBLISHED.md" else Path(p))

    # Initial setup
    test_published.write_text(
        "## Instagram\n"
        "Status: BILD_GENERIERT\n"
        "Racing-Batch-ID: batch-123\n"
        "MotoGP-Auswahl: 3\n"
        "Titel: Quiles Victory\n"
        "Text:\nGreat race\n",
        encoding="utf-8",
    )

    pi.add_pending(
        batch_id="batch-123",
        auswahl=3,
        titel="Quiles Victory",
        text="Great race",
        bild_pfad="assets/images/quiles.jpg",
        prompt_fuer_agnes="Prompt 123",
    )

    mock_send_message = MagicMock()
    mock_send_photo = MagicMock()
    mock_agnes = MagicMock(return_value=b"regenerated image bytes")

    monkeypatch.setattr(tr, "send_message", mock_send_message)
    monkeypatch.setattr(tr, "send_photo", mock_send_photo)
    monkeypatch.setattr(tr, "agnes_generate_image", mock_agnes)

    # 1. Test reject synonyms ("bild ❌", "❌", "ablehnen", "neu", "neu generieren", "nein")
    reject_synonyms = ["bild ❌", "❌", "ablehnen", "neu", "neu generieren", "nein"]
    for syn in reject_synonyms:
        mock_send_photo.reset_mock()
        assert tr._get_bild_command_action(syn) == "❌"
        handled = tr._handle_bild_command(syn)
        assert handled is True
        assert len(pi.load_pending()) == 1  # Still pending
        mock_send_photo.assert_called_once()

    # 2. Test approve synonyms ("bild ✅", "✅", "bild posten", "posten", "ok", "freigegeben", "freigeben zum posten", "freigeben", "ja")
    approve_synonyms = ["bild ✅", "✅", "bild posten", "posten", "ok", "freigegeben", "freigeben zum posten", "freigeben", "ja"]
    for syn in approve_synonyms:
        assert tr._get_bild_command_action(syn) == "✅"

    # Execute approve with "freigeben zum posten"
    mock_send_message.reset_mock()
    handled_accept = tr._handle_bild_command("freigeben zum posten")
    assert handled_accept is True
    assert pi.load_pending() == []  # Removed from pending

    published_content = test_published.read_text(encoding="utf-8")
    assert "Status: GEPOSTET" in published_content
    assert "Status: BILD_GENERIERT" not in published_content
    mock_send_message.assert_called_with("✅ Instagram gepostet: Quiles Victory")


def test_telegram_router_synonyms_without_pending(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)

    # Ensure pending queue is empty
    assert pi.get_first_pending() is None

    # Even though action parser returns action for "ok" or "✅",
    # the pending check in main ensures it's not intercepted as Instagram approval.
    assert tr._get_bild_command_action("ok") == "✅"
    assert tr._get_bild_command_action("✅") == "✅"
    assert tr._get_bild_command_action("nein") == "❌"
    assert tr._get_bild_command_action("random command") is None
