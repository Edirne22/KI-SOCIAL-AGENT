"""Unit tests for OpenMontage V3 Telegram Controls & Persistence (Block 6)."""
import json
from pathlib import Path
import tempfile
import pytest

from scripts import openmontage_control as om_ctrl


def test_command_parsing():
    assert om_ctrl.is_command("/montage erstellen MotoGP News, 90s, Deutsch") is True
    assert om_ctrl.is_command("/montage status") is True
    assert om_ctrl.is_command("/montage freigeben 12345678-1234-1234-1234-123456789abc") is True

    parsed_create = om_ctrl.parse_command("/montage erstellen MotoGP News")
    assert isinstance(parsed_create, dict)
    assert parsed_create["action"] == "erstellen"
    assert parsed_create["prompt"] == "MotoGP News"

    parsed_plan = om_ctrl.parse_command("/montage planen Toprak WorldSBK")
    assert isinstance(parsed_plan, dict)
    assert parsed_plan["action"] == "planen"
    assert parsed_plan["prompt"] == "Toprak WorldSBK"


def test_telegram_handle_workflow_and_persistence():
    with tempfile.TemporaryDirectory(prefix="om-test-tg-") as tmpdir:
        jobs_file = Path(tmpdir) / "OPENMONTAGE_JOBS.json"

        # Test command execution
        res_create = om_ctrl.handle(
            text="/montage erstellen MotoGP News 2026, 60s",
            update_id=1001,
            chat="12345",
            authorized_chat="12345",
            jobs_state=jobs_file,
        )

        assert "Auftrag erfasst" in res_create
        assert "job_1001" in res_create

        # Verify state written to file
        ledger = om_ctrl.load_jobs_ledger(jobs_file)
        assert "job_1001" in ledger
        assert ledger["job_1001"]["prompt"] == "MotoGP News 2026, 60s"
        assert ledger["job_1001"]["status"] == "QUEUED"

        # Test approval command
        res_approve = om_ctrl.handle(
            text="/montage freigeben 12345678-1234-1234-1234-123456789abc",
            update_id=1002,
            chat="12345",
            authorized_chat="12345",
            jobs_state=jobs_file,
        )

        assert "redaktionell FREIGEGEBEN" in res_approve
        ledger_updated = om_ctrl.load_jobs_ledger(jobs_file)
        assert ledger_updated["job_12345678"]["status"] == "APPROVED"
        assert ledger_updated["job_12345678"]["editorial_decision"] == "FREIGEGEBEN"
