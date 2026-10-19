#!/usr/bin/env bash
set -uo pipefail
cd /workspaces/KI-SOCIAL-AGENT 2>/dev/null || cd "$(dirname "$0")/.."
echo "=== KI-SOCIAL-AGENT: Codespaces Selbsttest ==="
echo "Branch: $(git branch --show-current)"
python --version || exit 2
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "FFmpeg fehlt – installiere automatisch (nur Codespace)."
  # Debian's third-party Yarn source can have an expired/missing signing key.
  # Disable only that source inside this disposable Codespace, never bypass apt signature checks.
  if grep -Rls 'dl.yarnpkg.com' /etc/apt/sources.list.d /etc/apt/sources.list 2>/dev/null | grep -q .; then
    echo "Deaktiviere fehlerhafte Yarn-Paketquelle nur in diesem Codespace."
    while IFS= read -r source; do
      case "$source" in
        /etc/apt/sources.list.d/*.list)
          sudo sed -i '/dl\.yarnpkg\.com/s/^[[:space:]]*deb/# disabled for Codespaces ffmpeg setup: deb/' "$source" ;;
        /etc/apt/sources.list.d/*.sources)
          echo "Yarn-Deb822-Quelle erkannt: $source; automatische Änderung nicht sicher." >&2; exit 2 ;;
        /etc/apt/sources.list)
          sudo sed -i '/dl\.yarnpkg\.com/s/^[[:space:]]*deb/# disabled for Codespaces ffmpeg setup: deb/' "$source" ;;
      esac
    done < <(grep -Rls 'dl.yarnpkg.com' /etc/apt/sources.list.d /etc/apt/sources.list 2>/dev/null)
  fi
  sudo apt-get update -qq && sudo env DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ffmpeg || { echo "FFmpeg-Installation fehlgeschlagen"; exit 2; }
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
