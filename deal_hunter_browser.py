"""Sichere Vorbereitung für spätere Coupon-Tests; Phase 2 ist standardmäßig deaktiviert."""

from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlparse

CONFIG_FILE = Path("config/deal_hunter_shops.json")
LOG_FILE = Path("memory/DEAL_TEST_LOG.md")


def test_coupon(url: str, coupon_code: str, product_selector: str | None = None) -> dict[str, str]:
    """Prüft ausschließlich Konfiguration und gibt ohne erlaubten Shop nie Browser-Aktionen aus."""
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return {"status": "nicht testbar", "reason": "Nur vollständige HTTPS-URLs sind erlaubt."}

    config = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    allowed = config.get("allowed_shops") or []
    if not allowed:
        return {"status": "nicht testbar", "reason": "Phase 2 ist deaktiviert: Händler-Allowlist ist leer."}

    return {"status": "nicht testbar", "reason": "Phase 2 ist vorbereitet, aber noch nicht aktiviert."}
