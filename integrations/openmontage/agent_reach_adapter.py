"""Agent Reach subprocess boundary; disabled until explicit runtime provisioning.

Agent Reach is an installer/doctor for upstream tools, not an autonomous
fact-checker. Avoid automatic package installs and implicit login/cookie access.
"""
from __future__ import annotations
import shutil
import subprocess

def availability() -> dict:
    binary = shutil.which("agent-reach")
    return {"installed": bool(binary), "executable": binary, "enabled": False}

def doctor(timeout: int = 20) -> dict:
    binary = shutil.which("agent-reach")
    if not binary:
        return {"status": "UNAVAILABLE", "reason": "AGENT_REACH_NOT_INSTALLED"}
    try:
        result = subprocess.run([binary, "doctor"], capture_output=True,
                                text=True, timeout=timeout, check=False)
        return {"status": "OK" if result.returncode == 0 else "DEGRADED",
                "exit_code": result.returncode}
    except (OSError, subprocess.TimeoutExpired):
        return {"status": "UNAVAILABLE", "reason": "DOCTOR_FAILED"}
