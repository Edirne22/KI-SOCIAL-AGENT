#!/usr/bin/env bash
set -uo pipefail
cd /workspaces/KI-SOCIAL-AGENT 2>/dev/null || cd "$(dirname "$0")/.."
echo "=== KI-SOCIAL-AGENT: Codespaces Selbsttest ==="
echo "Branch: $(git branch --show-current)"
python --version || exit 2
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg fehlt – installiere automatisch (nur Codespace)."
  sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg || { echo "FFmpeg-Installation fehlgeschlagen"; exit 2; }
fi
ffmpeg -version | head -n 1
if ! python -m pytest --version; then echo "FEHLT: pytest"; exit 2; fi
mkdir -p /tmp/ki-social-testreports
set +e
python -m pytest -q tests/test_hermes_dynamic_claims_count.py tests/test_hermes_toprak_factcheck_regression.py tests/test_hermes_production.py tests/test_hermes_live_workers.py 2>&1 | tee /tmp/ki-social-testreports/hermes-pytest.log
rc=${PIPESTATUS[0]}
set -e
echo "=== Ergebnis: Exit-Code $rc ==="
echo "Protokoll: /tmp/ki-social-testreports/hermes-pytest.log"
exit "$rc"
