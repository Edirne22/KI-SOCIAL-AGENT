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




def test_turkish_human_final_is_directly_instagram_publishable(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    test_published = tmp_path / "PUBLISHED.md"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(approval, "PUBLISHED", test_published)

    asset = tmp_path / "assets" / "images" / "2026-09" / "turkish-human.jpg"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"jpeg")
    posts = {
        1: {
            "title": "Oğuz Test",
            "source": "https://example.com/oguz",
            "image": asset.as_posix(),
            "text": "Exakt freigegebener Text",
            "caption_final": True,
            "human_final": True,
        }
    }
    monkeypatch.setattr(approval, "download_og_image_for_instagram", lambda source, target: target)
    send_photo = MagicMock()
    monkeypatch.setattr(approval, "send_photo", send_photo)

    count = approval.publish(posts, [1], uid=2001, batch="turkish-human-test")
    assert count == 2
    content = test_published.read_text(encoding="utf-8")
    instagram = content.split("## Instagram", 1)[1].split("## Facebook", 1)[0]
    assert "Status: FREIGEGEBEN" in instagram
    assert "Status: BILD_GENERIERT" not in instagram
    assert f"Bild: {asset.as_posix()}" in instagram
    assert pi.load_pending() == []
    send_photo.assert_not_called()


def test_motogp_approval_falls_back_to_agnes_without_og_image(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    test_published = tmp_path / "PUBLISHED.md"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(approval, "PUBLISHED", test_published)

    test_img = tmp_path / "fallback.jpg"
    test_img.write_bytes(b"old")
    posts = {
        1: {
            "title": "Fallback Test",
            "source": "https://example.com/no-og",
            "image": str(test_img),
            "text": "Facebook Basistext",
        }
    }

    mock_agnes = MagicMock(return_value=b"agnes bytes")
    mock_save = MagicMock()
    monkeypatch.setattr(approval, "download_og_image_for_instagram", lambda source, target: None)
    monkeypatch.setattr(approval, "generate_buelent_caption", lambda text: text)
    monkeypatch.setattr(approval, "agnes_generate_image", mock_agnes)
    monkeypatch.setattr(approval, "save_bytes", mock_save)
    monkeypatch.setattr(approval, "send_photo", MagicMock())

    approval.publish(posts, [1], uid=1002, batch="batch-fallback")
    mock_agnes.assert_called_once()
    mock_save.assert_called_once()
    published_content = test_published.read_text(encoding="utf-8")
    assert "Medienstatus: EIGENE_KI_EDITORIALGRAFIK" in published_content


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
        "Telegram-Update-ID: 999\n"
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

    # 1. Only explicitly image-bound commands may mutate an image approval.
    reject_synonyms = ["bild ❌", "bild neu", "bild ablehnen"]
    for syn in reject_synonyms:
        mock_send_photo.reset_mock()
        assert tr._get_bild_command_action(syn) == "❌"
        handled = tr._handle_bild_command(syn)
        assert handled is True
        assert len(pi.load_pending()) == 1  # Still pending
        mock_send_photo.assert_called_once()

    # 2. Bare human words are intentionally ambiguous and must never publish.
    approve_synonyms = ["bild ✅", "bild posten", "bild freigeben"]
    for syn in approve_synonyms:
        assert tr._get_bild_command_action(syn) == "✅"

    # Execute approve with "freigeben zum posten" on a successful Meta publish.
    # The success-path test must provide a real media ID; failed publishes are
    # covered separately and must remain pending.
    monkeypatch.setenv("INSTAGRAM_USER_ID", "123")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "token")
    test_image = tmp_path / "quiles.jpg"
    test_image.write_bytes(b"fake")
    pending = pi.get_first_pending()
    pending["bild_pfad"] = str(test_image)
    pi.save_pending([pending])
    monkeypatch.setattr(tr, "process_image_for_instagram", lambda p: p)
    monkeypatch.setattr(tr, "asset_url", lambda *args: "https://example.com/image.jpg")
    monkeypatch.setattr(tr, "create_container", lambda *args: "creation-1")
    monkeypatch.setattr(tr, "ig_wait", lambda *args: True)
    monkeypatch.setattr(tr, "ig_publish_container", lambda *args: "media-123")

    mock_send_message.reset_mock()
    handled_accept = tr._handle_bild_command("bild posten")
    assert handled_accept is True
    assert pi.load_pending() == []

    published_content = test_published.read_text(encoding="utf-8")
    assert "Status: GEPOSTET" in published_content
    assert "Status: BILD_GENERIERT" not in published_content
    assert "ID: media-123" in published_content
    assert '"platform": "instagram"' in published_content
    assert '"creation_id": "creation-1"' in published_content
    assert '"published_media_id": "media-123"' in published_content
    mock_send_message.assert_called_with(
        "✅ Instagram gepostet: Quiles Victory\nMeta-Media-ID: media-123"
    )


def test_instagram_publish_failure_never_reports_success_or_removes_pending(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    test_published = tmp_path / "PUBLISHED.md"
    test_img = tmp_path / "quiles.jpg"
    test_img.write_bytes(b"fake")
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(tr, "Path", lambda p: test_published if p == "content/PUBLISHED.md" else Path(p))
    test_published.write_text(
        "## Instagram\nStatus: BILD_GENERIERT\nRacing-Batch-ID: batch-fail\n"
        "MotoGP-Auswahl: 1\nTitel: Fail Test\nText:\nCaption\n",
        encoding="utf-8",
    )
    pi.add_pending(
        batch_id="batch-fail", auswahl=1, titel="Fail Test", text="Caption",
        bild_pfad=str(test_img), prompt_fuer_agnes="Prompt",
    )
    monkeypatch.setenv("INSTAGRAM_USER_ID", "123")
    monkeypatch.setenv("INSTAGRAM_ACCESS_TOKEN", "token")
    monkeypatch.setattr(tr, "process_image_for_instagram", lambda p: p)
    monkeypatch.setattr(tr, "asset_url", lambda *args: "https://example.com/image.jpg")
    monkeypatch.setattr(tr, "create_container", lambda *args: "creation-1")
    monkeypatch.setattr(tr, "ig_wait", lambda *args: True)
    monkeypatch.setattr(tr, "ig_publish_container", lambda *args: None)
    mock_send = MagicMock()
    monkeypatch.setattr(tr, "send_message", mock_send)

    result = tr._publish_instagram_pending(pi.get_first_pending())

    assert result is False
    assert len(pi.load_pending()) == 1
    published = test_published.read_text(encoding="utf-8")
    assert "Status: BILD_GENERIERT" in published
    assert "Status: GEPOSTET" not in published
    assert "APPROVAL_SIMULATED_" not in published
    assert not any("✅ Instagram gepostet" in str(call) for call in mock_send.call_args_list)
    assert any("❌ Instagram NICHT gepostet" in str(call) for call in mock_send.call_args_list)


def test_telegram_router_synonyms_without_pending(tmp_path, monkeypatch):
    test_json = tmp_path / "PENDING_INSTAGRAM.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)

    # Ensure pending queue is empty
    assert pi.get_first_pending() is None

    # Bare actions are not publication authority for any pending image.
    for command in ("posten","ok","✅","freigeben","ja","neu","nein","❌","ändern"):
        assert tr._get_bild_command_action(command) is None
    assert tr._get_bild_command_action("bild posten") == "✅"
    assert tr._get_bild_command_action("bild 3 posten") == "✅"
    assert tr._get_bild_command_action("bild neu") == "❌"
    assert tr._get_bild_command_action("bild 3 neu") == "❌"
    assert tr._get_bild_command_action("random command") is None


def test_stale_deniz_pending_plus_bare_posten_never_publishes(monkeypatch, tmp_path):
    """Regression for 2026-10-04: T1 Toprak preview + bare Posten published stale Deniz."""
    from datetime import datetime, timedelta, timezone
    test_json = tmp_path / "pending.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    stale = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pi.add_pending(
        "racing-2026-10-03-daily", 3,
        "Deniz Öncü Japonya’da daha fazlasını istiyor: Hedef ilk 10’un ötesi",
        "old", "old.jpg", "old prompt", erstellt=stale,
    )
    sent=[]; acked=[]
    monkeypatch.setattr(tr, "get_chat_id", lambda: 42)
    monkeypatch.setattr(tr, "_read_last_update_id", lambda: 10)
    monkeypatch.setattr(tr, "get_updates", lambda **kw: [
        {"update_id":11,"message":{"chat":{"id":42},"text":"Posten"}}
    ] if kw.get("offset")==11 else [])
    monkeypatch.setattr(tr, "_ack", lambda uid: acked.append(uid))
    monkeypatch.setattr(tr, "send_message", lambda msg: sent.append(msg))
    monkeypatch.setattr(tr, "_publish_instagram_pending",
                        lambda item: (_ for _ in ()).throw(AssertionError("wrong item published")))
    monkeypatch.setattr(tr.subprocess, "run",
                        lambda *a,**kw: (_ for _ in ()).throw(AssertionError("ambiguous command dispatched")))
    tr.main()
    assert acked == [11]
    assert any("Nicht eindeutig" in msg for msg in sent)
    assert len(pi.load_pending()) == 1


def test_explicit_t1_posten_routes_turkish_not_stale_image(monkeypatch, tmp_path):
    from datetime import datetime, timedelta, timezone
    test_json = tmp_path / "pending.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    stale = (datetime.now(timezone.utc) - timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
    pi.add_pending("old-batch",3,"Deniz stale","old","old.jpg","old",erstellt=stale)
    acked=[]; calls=[]
    monkeypatch.setattr(tr, "get_chat_id", lambda: 42)
    monkeypatch.setattr(tr, "_read_last_update_id", lambda: 20)
    monkeypatch.setattr(tr, "get_updates", lambda **kw: [
        {"update_id":21,"message":{"chat":{"id":42},"text":"T1 posten"}}
    ] if kw.get("offset")==21 else [])
    monkeypatch.setattr(tr, "_ack", lambda uid: acked.append(uid))
    monkeypatch.setattr(tr, "send_message", lambda msg: None)
    monkeypatch.setattr(tr, "_publish_instagram_pending",
                        lambda item: (_ for _ in ()).throw(AssertionError("stale image published")))
    class Result:
        returncode=0
    monkeypatch.setattr(tr.subprocess, "run", lambda args,check=False: calls.append(args) or Result())
    tr.main()
    assert acked == [21]
    assert calls and calls[0][1].endswith("motogp_telegram_receive.py")
    assert calls[0][-1] == "T1 posten"


def test_image_publish_requires_recent_unique_context(monkeypatch, tmp_path):
    from datetime import datetime, timedelta, timezone
    test_json = tmp_path / "pending.json"
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    stale=(datetime.now(timezone.utc)-timedelta(hours=25)).strftime("%Y-%m-%dT%H:%M:%SZ")
    now=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pi.add_pending("old",3,"Old Deniz","old","old.jpg","old",erstellt=stale)
    published=[]; sent=[]
    monkeypatch.setattr(tr, "_publish_instagram_pending", lambda item: published.append(item) or True)
    monkeypatch.setattr(tr, "send_message", lambda msg: sent.append(msg))
    assert tr._handle_bild_command("bild posten") is True
    assert published == []
    assert any("Alte Pending-Einträge" in msg for msg in sent)

    pi.add_pending("new",1,"Fresh Toprak","new","one.jpg","p",erstellt=now)
    sent.clear()
    assert tr._handle_bild_command("bild posten") is True
    assert [x["titel"] for x in published] == ["Fresh Toprak"]

    pi.add_pending("new",3,"Fresh Other","new","three.jpg","p",erstellt=now)
    published.clear(); sent.clear()
    assert tr._handle_bild_command("bild posten") is True
    assert published == []
    assert any("Mehrere aktuelle" in msg for msg in sent)
    assert tr._handle_bild_command("bild 3 posten") is True
    assert [x["titel"] for x in published] == ["Fresh Other"]


def test_recent_pending_excludes_stale_records(monkeypatch, tmp_path):
    from datetime import datetime, timedelta, timezone
    monkeypatch.setattr(pi, "PENDING_FILE", tmp_path / "pending.json")
    now=datetime(2026,10,4,9,30,tzinfo=timezone.utc)
    pi.add_pending("old",1,"Old","x","x.jpg","p",
                   erstellt=(now-timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    pi.add_pending("fresh",2,"Fresh","x","y.jpg","p",
                   erstellt=(now-timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ"))
    recent=pi.get_recent_pending(max_age_seconds=7200,now=now)
    assert [x["titel"] for x in recent] == ["Fresh"]


def test_latest_pending_targets_current_batch(monkeypatch, tmp_path):
    import pending_instagram as pi
    monkeypatch.setattr(pi, "PENDING_FILE", tmp_path / "pending.json")
    pi.add_pending("old-batch", 1, "Old", "old text", "old.jpg", "old prompt")
    pi.add_pending("current-batch", 1, "Current", "current text", "current.jpg", "current prompt")
    chosen = pi.get_latest_pending()
    assert chosen["batch_id"] == "current-batch"
    assert chosen["titel"] == "Current"


def test_turkish_human_legacy_block_is_migrated_not_deduped(tmp_path, monkeypatch):
    test_published = tmp_path / "PUBLISHED.md"
    test_json = tmp_path / "pending.json"
    monkeypatch.setattr(approval, "PUBLISHED", test_published)
    monkeypatch.setattr(pi, "PENDING_FILE", test_json)
    monkeypatch.setattr(approval, "get_existing_published_texts", lambda: {"exakt bereits freigegebener turkish-human-text"})
    text = "Exakt bereits freigegebener Turkish-Human-Text"
    test_published.write_text(
        "# Freigegebene Beiträge\n\n"
        "## Instagram\nStatus: BILD_GENERIERT\nFreigabe: Telegram Racing\n"
        "Racing-Batch-ID: old-TR-HUMAN\nTelegram-Update-ID: 1\nMotoGP-Auswahl: 1\n"
        "Titel: Oğuz Test\nText:\n" + text + "\nQuelle: https://example.com/oguz\n"
        "Medienstatus: QUELLE_BESTÄTIGT\nBild: memory/turkish-human-T1.jpg\n\n"
        "## Facebook\nStatus: FREIGEGEBEN\nRacing-Batch-ID: old-TR-HUMAN\n"
        "MotoGP-Auswahl: 1\nTitel: Oğuz Test\nText:\n" + text + "\n",
        encoding="utf-8",
    )
    asset = tmp_path / "assets" / "images" / "2026-09" / "oguz.jpg"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"jpeg")
    posts = {1: {"title":"Oğuz Test","source":"https://example.com/oguz",
                 "image":asset.as_posix(),"text":text,"caption_final":True,"human_final":True}}
    monkeypatch.setattr(approval, "download_og_image_for_instagram", lambda source, target: target)
    monkeypatch.setattr(approval, "send_photo", MagicMock())

    count = approval.publish(posts,[1],uid=222,batch="new-TR-HUMAN")
    assert count == 0
    content = test_published.read_text(encoding="utf-8")
    ig = content.split("## Instagram",1)[1].split("## Facebook",1)[0]
    assert "Status: FREIGEGEBEN" in ig
    assert "Status: BILD_GENERIERT" not in ig
    assert f"Bild: {asset.as_posix()}" in ig
    assert "Telegram-Update-ID: 222" in ig
    assert content.count("## Facebook") == 1
    assert content.count("## Instagram") == 1
    assert pi.load_pending() == []
