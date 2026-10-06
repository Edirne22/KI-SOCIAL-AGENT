#!/usr/bin/env python3
"""Offline OpenCode image invariants. No provider key and no model call."""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import subprocess

EXPECTED_VERSION = "2.0.21"
EXPECTED_MODEL = "openrouter/anthropic/claude-sonnet-4.5"
CONFIG = pathlib.Path("/etc/opencode/opencode.json")
SHA_FILE = pathlib.Path("/etc/opencode/opencode.json.sha256")
CODE_CONFIG = pathlib.Path("/etc/opencode/code.json")
CODE_SHA_FILE = pathlib.Path("/etc/opencode/code.json.sha256")

def main() -> int:
    version = subprocess.run(
        ["opencode", "--version"],
        check=True,
        capture_output=True,
        text=True,
        env={"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": "/tmp"},
    ).stdout.strip()
    assert EXPECTED_VERSION in version, version
    debug_env = {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HOME": "/tmp",
        "OPENCODE_CONFIG": str(CONFIG),
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
    }
    debug = subprocess.run(
        ["opencode", "debug", "config"],
        check=True,
        capture_output=True,
        text=True,
        env=debug_env,
        timeout=30,
    )
    resolved = (debug.stdout or "") + "\n" + (debug.stderr or "")
    assert '"providerID": "openrouter"' in resolved, "resolved config did not retain OpenRouter provider"
    assert '"model": "anthropic/claude-sonnet-4.5"' in resolved, "resolved config did not retain fixed Claude model"
    raw = CONFIG.read_bytes()
    expected_sha = SHA_FILE.read_text(encoding="utf-8").strip()
    assert hashlib.sha256(raw).hexdigest() == expected_sha
    code_raw = CODE_CONFIG.read_bytes()
    code_expected_sha = CODE_SHA_FILE.read_text(encoding="utf-8").strip()
    assert hashlib.sha256(code_raw).hexdigest() == code_expected_sha
    cfg = json.loads(raw)
    assert cfg.get("model") == EXPECTED_MODEL
    providers = cfg.get("providers")
    assert isinstance(providers, dict) and set(providers) == {"openrouter"}
    openrouter = providers["openrouter"]
    assert openrouter.get("env") == ["OPENROUTER_API_KEY"]
    # The environment variable name is expected; a credential value must never be embedded.
    assert "apiKey" not in openrouter and "api_key" not in openrouter and "key" not in openrouter
    code_cfg = json.loads(code_raw)
    code_model = code_cfg["providers"]["openrouter"]["models"]["anthropic/claude-sonnet-4.5"]
    assert code_model["capabilities"]["tools"] is True
    rules = code_cfg.get("permissions")
    assert isinstance(rules, list) and rules
    assert any(x == {"action":"*","resource":"*","effect":"deny"} for x in rules)
    for command in ("git status*","git log*","git show*","git diff*","git rev-parse*","git branch*","git ls-files*"):
        assert {"action":"shell","resource":command,"effect":"allow"} in rules
    for command in ("git commit*","git push*","git fetch*","git pull*","git clone*"):
        assert {"action":"shell","resource":command,"effect":"deny"} in rules
    assert {"action":"edit","resource":"*","effect":"deny"} in rules
    assert subprocess.run(["git","--version"],capture_output=True,text=True,check=False).returncode == 0
    assert not os.access(CONFIG, os.W_OK), "config unexpectedly writable by runtime user"
    assert not os.access(CODE_CONFIG, os.W_OK), "code config unexpectedly writable by runtime user"
    assert os.geteuid() != 0, "runtime user must not be root"
    print("OPENCODE_IMAGE_INVARIANTS_OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
