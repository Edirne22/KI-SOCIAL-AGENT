from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from llm_router import quick_chat

LOG_PATH = ROOT / "memory" / "VISION_LOG.jsonl"
SUMMARY_PATH = ROOT / "memory" / "VISION_SUMMARY.md"


def _parse_timestamp(value: str) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _load_recent_entries() -> list[dict]:
    if not LOG_PATH.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    entries: list[dict] = []

    for line_number, raw_line in enumerate(
        LOG_PATH.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        line = raw_line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as exc:
            print(f"[vision-summary] Ungültige JSONL-Zeile {line_number}: {exc}")
            continue
        if not isinstance(entry, dict):
            print(f"[vision-summary] Zeile {line_number} ist kein JSON-Objekt.")
            continue

        timestamp = _parse_timestamp(entry.get("timestamp"))
        if timestamp is None:
            print(f"[vision-summary] Zeile {line_number} ohne gültigen Timestamp.")
            continue
        if timestamp >= cutoff:
            entries.append(entry)

    return entries


def _write_summary(body: str, generated_at: datetime, mode_counts: Counter) -> None:
    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)

    counts = ", ".join(
        f"{mode}: {count}"
        for mode, count in sorted(mode_counts.items())
    ) or "keine"

    content = (
        "# Vision Summary\n\n"
        f"**Stand:** {generated_at.isoformat()}\n"
        f"**Zeitraum:** letzte 7 Tage\n"
        f"**Modi:** {counts}\n\n"
        f"{body.strip()}\n"
    )
    SUMMARY_PATH.write_text(content, encoding="utf-8")


def main() -> int:
    try:
        now = datetime.now(timezone.utc)
        entries = _load_recent_entries()
        mode_counts = Counter(
            str(entry.get("mode") or "unbekannt")
            for entry in entries
        )

        if len(entries) < 3:
            _write_summary(
                f"Zu wenig Daten: nur {len(entries)} Vision-Analyse(n) "
                "in den letzten 7 Tagen. Für eine belastbare Zusammenfassung "
                "werden mindestens 3 Einträge benötigt.",
                now,
                mode_counts,
            )
            print(
                f"[vision-summary] Zu wenig Daten ({len(entries)} Einträge); "
                "Hinweis geschrieben."
            )
            return 0

        analyses = []
        for entry in entries:
            analyses.append({
                "timestamp": entry.get("timestamp"),
                "mode": entry.get("mode"),
                "model": entry.get("model"),
                "result": entry.get("result"),
                "tables_present": bool(entry.get("tables_present")),
                "error": entry.get("error"),
            })

        prompt = (
            f"Hier sind {len(entries)} Bild-Analysen der letzten 7 Tage.\n"
            "Erstelle eine kompakte Zusammenfassung auf Deutsch.\n"
            "Antworte AUSSCHLIESSLICH auf Deutsch.\n"
            "Verwende keine anderen Sprachen, keine chinesischen Zeichen, "
            "keine englischen Wörter außer Fachbegriffen.\n"
            "Struktur:\n"
            "- Welche Themen kommen häufig vor?\n"
            "- Welche Accounts/Posts wurden analysiert?\n"
            "- Auffällige Muster (z. B. ähnliche Hooks, CTAs)?\n"
            "Nur Fakten, keine Spekulation.\n"
            f"Modus-Häufigkeiten: {dict(mode_counts)}\n"
            "Analysen: "
            + json.dumps(analyses, ensure_ascii=False)
        )

        result = quick_chat(prompt, task_type="reasoning")
        _write_summary(result, now, mode_counts)
        print(
            f"[vision-summary] Summary aus {len(entries)} Einträgen geschrieben."
        )
        return 0
    except Exception as exc:
        print(f"[vision-summary] Fehler: {exc}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
