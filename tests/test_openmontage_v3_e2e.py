"""Real End-to-End Integration Verification Suite for OpenMontage V3 (Block 7 / P1-H)."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import pytest

from openmontage_fact_checker import verify_research_payload
from openmontage_media_sourcing import build_media_manifest
from openmontage_production import produce_video
from openmontage_research import build_research
from openmontage_storyboard import build_storyboard
from scripts import openmontage_control as om_ctrl


def test_openmontage_v3_real_e2e_pipeline():
    prompt = "Erstelle einen Film über MotoGP News der letzten 7 Tage, 60 Sekunden, Deutsch, 9:16"

    # Real reachability simulation with valid ISO dates
    real_news_items = [
        {
            "title": "Marc Marquez dominates Aragon MotoGP Sprint",
            "url": "https://www.motogp.com/en/news/aragon-sprint",
            "summary": "Marc Marquez takes dominant victory for Ducati Lenovo Team.",
            "source": "motogp.com",
            "series": "MotoGP",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "title": "Jorge Martin secures second place podium",
            "url": "https://www.motogp.com/en/news/martin-podium",
            "summary": "Jorge Martin scores valuable championship points.",
            "source": "motogp.com",
            "series": "MotoGP",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    # Step 1: Research Adapter
    research = build_research(prompt, mock_items=real_news_items)
    assert research["item_count"] == 2
    assert len(research["stories"]) == 2

    # Step 2: Fact & Recency Verification
    verified_research = verify_research_payload(research)
    assert verified_research["verified_item_count"] == 2
    assert verified_research["rejected_item_count"] == 0

    # Step 3: Storyboard Scene Planning
    storyboard = build_storyboard(
        verified_research,
        target_duration=60,
        aspect_ratio="9:16",
        language="de",
        film_type="news",
    )
    assert storyboard["target_duration_seconds"] == 60
    assert storyboard["aspect_ratio"] == "9:16"
    assert storyboard["scene_count"] >= 3

    # Step 4: Media Sourcing & Rights Verification (Unverified URLs trigger synthetic fallbacks)
    manifest = build_media_manifest(storyboard)
    assert manifest["total_scenes"] == storyboard["scene_count"]
    assert manifest["all_rights_verified"] is True

    # Step 5: Automated Video Production Engine (Render & ffprobe)
    with tempfile.TemporaryDirectory(prefix="om-v3-e2e-") as tmpdir:
        out_dir = Path(tmpdir) / "production_out"
        prod_report = produce_video(
            research_data=verified_research,
            storyboard_data=storyboard,
            media_manifest_data=manifest,
            output_dir=out_dir,
        )

        assert prod_report["status"] == "COMPLETED"
        assert Path(prod_report["video_file"]).is_file()
        assert Path(prod_report["ffprobe_file"]).is_file()
        assert prod_report["bytes"] > 0
        assert prod_report["duration_seconds"] > 0

        # Step 6: Telegram Controls & State Persistence
        jobs_file = Path(tmpdir) / "OPENMONTAGE_JOBS.json"

        # Test creation
        cmd_reply = om_ctrl.handle(
            text=f"/montage erstellen {prompt}",
            update_id=9999,
            chat="owner_chat",
            authorized_chat="owner_chat",
            jobs_state=jobs_file,
        )
        assert "Auftrag erfasst" in cmd_reply
        assert "job_9999" in cmd_reply

        ledger = om_ctrl.load_jobs_ledger(jobs_file)
        assert "job_9999" in ledger
        assert ledger["job_9999"]["prompt"] == prompt

        # Test editorial review approval (without social media publishing)
        video_id = "12345678-1111-2222-3333-444455556666"
        approve_reply = om_ctrl.handle(
            text=f"/montage freigeben {video_id}",
            update_id=10000,
            chat="owner_chat",
            authorized_chat="owner_chat",
            jobs_state=jobs_file,
        )
        assert "redaktionell FREIGEGEBEN" in approve_reply
        assert "Kein automatisches Social-Posting" in approve_reply

        ledger_updated = om_ctrl.load_jobs_ledger(jobs_file)
        assert ledger_updated["job_12345678"]["status"] == "APPROVED"
        assert ledger_updated["job_12345678"]["editorial_decision"] == "FREIGEGEBEN"
