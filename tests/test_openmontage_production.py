"""Unit tests for OpenMontage V3 Automated Video Production Engine (Block 5)."""
from pathlib import Path
import tempfile
import pytest
from datetime import datetime, timezone

from openmontage_production import produce_video
from openmontage_research import build_research
from openmontage_storyboard import build_storyboard
from openmontage_media_sourcing import build_media_manifest


def test_video_production_pipeline():
    mock_items = [
        {
            "title": "Marc Marquez wins thrilling MotoGP Sprint",
            "url": "https://www.motogp.com/en/news/sprint",
            "summary": "Marc Marquez victory in Aragon.",
            "source": "motogp.com",
            "series": "MotoGP",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "title": "Jorge Martin takes second place",
            "url": "https://www.motogp.com/en/news/martin",
            "summary": "Jorge Martin strong result.",
            "source": "motogp.com",
            "series": "MotoGP",
            "published_at": datetime.now(timezone.utc).isoformat(),
        },
    ]

    research = build_research("MotoGP News", mock_items=mock_items)
    storyboard = build_storyboard(research, target_duration=30, aspect_ratio="9:16", language="de")
    manifest = build_media_manifest(storyboard)

    with tempfile.TemporaryDirectory(prefix="om-test-prod-") as tmpdir:
        out_dir = Path(tmpdir) / "render_out"
        report = produce_video(
            research_data=research,
            storyboard_data=storyboard,
            media_manifest_data=manifest,
            output_dir=out_dir,
        )

        assert report["status"] == "COMPLETED"
        assert report["scene_count"] >= 3
        assert Path(report["video_file"]).is_file()
        assert Path(report["ffprobe_file"]).is_file()
        assert report["bytes"] > 0
        assert report["duration_seconds"] > 0
