"""Qualitäts-Agent: prüft Workflow-Ergebnisse, Datenqualität und Sicherheitswarnungen.

Der Agent veröffentlicht nichts, startet keine Workflows neu und verändert keinen Content.
Er erstellt ausschließlich nachvollziehbare Berichte und eine optionale Telegram-Zusammenfassung.
"""
from __future__ import annotations

import argparse
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable
from urllib.parse import urlparse

import requests

ROOT = Path(".")
MEMORY = ROOT / "memory"
REPORT = MEMORY / "QUALITY_REPORT.md"
HISTORY = MEMORY / "QUALITY_HISTORY.md"
GITHUB_API = "https://api.github.com"
WORKFLOW_MAX_AGE_HOURS = {
    "Generate Daily Content Idea": 36,
    "Inspiration Agent": 96,
    "Analytics Fetch": 36,
    "Analytics Report": 36,
    "Telegram Receive Approval": 36,
}
MAX_INSPIRATION_AGE_DAYS = 7
RECOGNIZED_SOURCE_HOSTS = (
    "instagram.com",
    "facebook.com",
    "youtube.com",
    "youtu.be",
    "tiktok.com",
    "x.com",
    "twitter.com",
)
RECOGNIZED_YOUTUBE_CHANNELS = {
    "motogp",
    "worldsbk",
    "bmw motorrad",
    "red bull motorsports",
}
SECRET_PATTERNS = (
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"gh[pousr]_[0-9A-Za-z]{20,}"),
    re.compile(r"sk-[0-9A-Za-z_-]{20,}"),
)
SCAN_SUFFIXES = {".py", ".yml", ".yaml", ".md", ".json"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _result(level: str, title: str, detail: str) -> dict[str, str]:
    return {"level": level, "title": title, "detail": detail}


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _urls(text: str) -> list[str]:
    return [url.rstrip(".,;:!?)]}") for url in re.findall(r"https?://[^\s<>()\[\]]+", text)]


def _parse_datetime(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None


def check_required_files() -> list[dict[str, str]]:
    paths = {
        "Content-Plan": ROOT / "content" / "CONTENT_PLAN.md",
        "Freigabeplan": ROOT / "content" / "PUBLISHED.md",
        "Inspiration-Report": MEMORY / "INSPIRATION_IDEAS.md",
        "Bright-Data-Debug": MEMORY / "BRIGHTDATA_DEBUG.md",
    }
    results = []
    for name, path in paths.items():
        if path.is_file() and path.stat().st_size > 0:
            results.append(_result("OK", name, "Datei vorhanden und nicht leer."))
        else:
            results.append(_result("WARNUNG", name, f"Erwartete Datei fehlt oder ist leer: {path.as_posix()}"))
    return results


def check_inspiration() -> list[dict[str, str]]:
    text = _read(MEMORY / "INSPIRATION_IDEAS.md")
    if not text:
        return [_result("WARNUNG", "Inspiration", "Kein Inspirationsreport zum Prüfen vorhanden.")]
    urls = len(_urls(text))
    ideas = len(re.findall(r"(?m)^### Idee\s+\d+|^\d+\.\s+\*\*Idee\s+\d+\*\*", text))
    results = []
    if urls:
        results.append(_result("OK", "Inspiration-Quellen", f"{urls} verlinkte Quellen im Report erkannt."))
    else:
        results.append(_result("WARNUNG", "Inspiration-Quellen", "Keine verlinkten Quellen im Report erkannt."))
    if ideas >= 3:
        results.append(_result("OK", "Inspiration-Ideen", f"{ideas} konkrete Ideen erkannt."))
    elif "Gemini nicht verfügbar" in text:
        results.append(_result("WARNUNG", "Inspiration-Ideen", "Gemini war nicht verfügbar; der Rohdaten-Fallback ist aktiv."))
    else:
        results.append(_result("WARNUNG", "Inspiration-Ideen", f"Nur {ideas} konkrete Ideen erkannt."))
    return results


def check_youtube_fallback() -> list[dict[str, str]]:
    """Prüft nur die technische und nachvollziehbare Qualität des YouTube-Fallbacks."""
    source_text = _read(MEMORY / "INSPIRATION_YOUTUBE_APIFY.md")
    report_text = _read(MEMORY / "INSPIRATION_IDEAS.md")
    report_has_youtube = any("youtube.com/" in url or "youtu.be/" in url for url in _urls(report_text))
    if not source_text:
        if report_has_youtube:
            return [_result("OK", "YouTube-Fallback", "YouTube-Quellen im Report vorhanden; separater Apify-Report war für diesen Lauf nicht nötig.")]
        return [_result("WARNUNG", "YouTube-Fallback", "Kein YouTube-Quellreport und keine YouTube-Quelle im Inspirationsreport vorhanden.")]

    blocks = re.split(r"(?m)(?=^### Datensatz\s+\d+)", source_text)
    records = [block for block in blocks if re.search(r"(?m)^### Datensatz\s+\d+", block)]
    if not records:
        return [_result("WARNUNG", "YouTube-Fallback", "Apify-Quellreport vorhanden, aber keine verwertbaren Video-Datensätze erkannt.")]

    results = [_result("OK", "YouTube-Fallback", f"{len(records)} YouTube-Datensätze aus dem Apify-Fallback erkannt.")]
    urls = _urls(source_text)
    unique_urls = {url.lower() for url in urls}
    if len(urls) != len(unique_urls):
        results.append(_result("WARNUNG", "YouTube-Duplikate", f"{len(urls) - len(unique_urls)} doppelte Video-URL(s) im Quellreport erkannt."))
    else:
        results.append(_result("OK", "YouTube-Duplikate", "Keine doppelten Video-URLs im Quellreport erkannt."))

    channels = []
    for block in records:
        match = re.search(r"(?m)^- Kanal:\s*(.+)$", block)
        if match:
            channels.append(match.group(1).strip())
    recognized = [channel for channel in channels if channel.lower() in RECOGNIZED_YOUTUBE_CHANNELS]
    if recognized:
        results.append(
            _result(
                "OK",
                "YouTube-Quellenmix",
                f"{len(recognized)} Datensatz/Datensätze von bekannten Primärkanälen erkannt ({', '.join(sorted(set(recognized)))}).",
            )
        )
    else:
        results.append(
            _result(
                "WARNUNG",
                "YouTube-Quellenmix",
                "Keine bekannten Primärkanäle erkannt. Die Ideen sind nutzbar, Quellen vor einer Veröffentlichung aber manuell prüfen.",
            )
        )
    return results


def check_source_quality() -> list[dict[str, str]]:
    """Prüft Quellenstruktur und Wiederholungen, ohne externe Links aufzurufen."""
    text = _read(MEMORY / "INSPIRATION_IDEAS.md")
    if not text:
        return []
    urls = _urls(text)
    if not urls:
        return []

    results = []
    normalized = [url.lower() for url in urls]
    duplicate_count = len(normalized) - len(set(normalized))
    if duplicate_count:
        results.append(_result("WARNUNG", "Inspiration-Duplikate", f"{duplicate_count} wiederholte Quellen-URL(s) im Report erkannt."))
    else:
        results.append(_result("OK", "Inspiration-Duplikate", "Keine doppelten Quellen-URLs im Report erkannt."))

    unknown_hosts = sorted(
        {
            (urlparse(url).hostname or "").lower()
            for url in urls
            if not any((urlparse(url).hostname or "").lower().endswith(host) for host in RECOGNIZED_SOURCE_HOSTS)
        }
    )
    if unknown_hosts:
        results.append(_result("WARNUNG", "Quellenformat", "Unbekannte Quellen-Domain(s): " + ", ".join(unknown_hosts[:5]) + "."))
    else:
        results.append(_result("OK", "Quellenformat", "Alle Quellen stammen von erwarteten Social- oder Video-Plattformen."))

    idea_sources = [
        url.rstrip(".,;:!?)")
        for url in re.findall(r"(?m)^\s*-\s+\*\*Inspirations-Quelle:\*\*\s*(https?://\S+)", text)
    ]
    sources_section = text.split("## Quellen", 1)[1] if "## Quellen" in text else ""
    listed_sources = {url.lower() for url in _urls(sources_section)}
    missing = [url for url in idea_sources if url.lower() not in listed_sources]
    if missing:
        results.append(_result("WARNUNG", "Ideen-Belege", f"{len(missing)} Ideenquelle(n) fehlen in der Quellenliste."))
    elif idea_sources:
        results.append(_result("OK", "Ideen-Belege", f"Alle {len(idea_sources)} Ideenquellen sind in der Quellenliste dokumentiert."))
    return results


def check_inspiration_age() -> list[dict[str, str]]:
    """Warnt bei alten oder auffällig zukünftigen Quelldaten."""
    texts = (
        _read(MEMORY / "INSPIRATION_IDEAS.md"),
        _read(MEMORY / "INSPIRATION_YOUTUBE_APIFY.md"),
    )
    values = re.findall(r"(?m)^-\s+\*\*?Datum:?\*\?\*?\s*(\d{4}-\d{2}-\d{2}T[0-9:.+-]+Z?)", "\n".join(texts))
    dates = [parsed for value in values if (parsed := _parse_datetime(value))]
    if not dates:
        return [_result("WARNUNG", "Datenalter", "Keine auswertbaren Quelldaten gefunden.")]

    now = _now()
    stale = [date for date in dates if now - date > timedelta(days=MAX_INSPIRATION_AGE_DAYS)]
    future = [date for date in dates if date - now > timedelta(hours=6)]
    if future:
        return [_result("WARNUNG", "Datenalter", f"{len(future)} Quelle(n) tragen ein auffällig zukünftiges Datum; Quelle prüfen.")]
    if stale:
        return [_result("WARNUNG", "Datenalter", f"{len(stale)} Quelle(n) sind älter als {MAX_INSPIRATION_AGE_DAYS} Tage.")]
    newest = max(dates).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    return [_result("OK", "Datenalter", f"{len(dates)} Quelldaten geprüft; alle innerhalb von {MAX_INSPIRATION_AGE_DAYS} Tagen (neueste: {newest}).")]


def check_bright_data() -> list[dict[str, str]]:
    text = _read(MEMORY / "BRIGHTDATA_DEBUG.md")
    if not text:
        return [_result("WARNUNG", "Bright Data", "Noch kein Debug-Log vorhanden.")]
    latest = text[-12000:]
    results = []
    if re.search(r"HTTP-Status: (401|403)", latest):
        results.append(_result("KRITISCH", "Bright Data Zugang", "HTTP 401/403 erkannt – Token oder Zugriffsrechte prüfen."))
    elif re.search(r"Fehler: .*dead_page", latest):
        results.append(_result("WARNUNG", "Bright Data Quelle", "Mindestens eine Profil- oder Suchquelle ist nicht erreichbar."))
    else:
        results.append(_result("OK", "Bright Data Zugang", "Keine aktuellen Zugriffsfehler erkannt."))
    if "Leere Antwort – Plattform nicht verfügbar" in latest:
        results.append(_result("WARNUNG", "Bright Data YouTube", "YouTube liefert bei Bright Data eine leere Antwort; Apify-Fallback wird geprüft."))
    return results


def check_gemini() -> list[dict[str, str]]:
    text = _read(MEMORY / "GEMINI_DEBUG.md")
    if not text:
        return [_result("WARNUNG", "Gemini", "Noch keine Gemini-Diagnose vorhanden.")]
    latest = text[-3000:]
    if "- HTTP-Status: 200" in latest:
        return [_result("OK", "Gemini", "Letzte Zusammenfassung war erfolgreich.")]
    status = re.search(r"- HTTP-Status: (.+)", latest)
    detail = status.group(1).strip() if status else "unbekannt"
    return [_result("WARNUNG", "Gemini", f"Letzte Zusammenfassung nicht erfolgreich: {detail}.")]


def check_secret_hygiene() -> list[dict[str, str]]:
    findings: list[str] = []
    excluded = {".git", "assets", "__pycache__", "memory"}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SCAN_SUFFIXES:
            continue
        if any(part in excluded for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(pattern.search(text) for pattern in SECRET_PATTERNS):
            findings.append(path.as_posix())
    if findings:
        return [_result("KRITISCH", "Secret-Prüfung", "Möglicher Zugangsschlüssel in: " + ", ".join(findings[:5]))]
    return [_result("OK", "Secret-Prüfung", "Keine typischen Zugangsschlüssel in Projektdateien erkannt.")]


def check_workflows() -> list[dict[str, str]]:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not token or not repository:
        return [_result("WARNUNG", "Workflow-Status", "GitHub-Statusprüfung übersprungen: Token oder Repository fehlt.")]
    try:
        response = requests.get(
            f"{GITHUB_API}/repos/{repository}/actions/runs",
            headers={"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"},
            params={"per_page": 100},
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        return [_result("WARNUNG", "Workflow-Status", f"GitHub-Statusprüfung nicht möglich: {type(error).__name__}.")]
    runs = response.json().get("workflow_runs", [])
    results: list[dict[str, str]] = []
    for name in sorted(WORKFLOW_MAX_AGE_HOURS):
        matching = [run for run in runs if run.get("name") == name]
        if not matching:
            results.append(_result("WARNUNG", name, "Kein letzter Lauf in der GitHub-Antwort gefunden."))
            continue
        latest = matching[0]
        created = latest.get("created_at", "")
        try:
            cutoff = _now() - timedelta(hours=WORKFLOW_MAX_AGE_HOURS[name])
            recent = datetime.fromisoformat(created.replace("Z", "+00:00")) >= cutoff
        except ValueError:
            recent = True
        conclusion = latest.get("conclusion")
        status = latest.get("status")
        if recent and conclusion == "failure":
            results.append(_result("KRITISCH", name, "Letzter Lauf fehlgeschlagen."))
        elif recent and status == "in_progress":
            results.append(_result("WARNUNG", name, "Läuft noch."))
        elif recent and conclusion == "success":
            results.append(_result("OK", name, "Letzter Lauf erfolgreich."))
        else:
            results.append(_result("WARNUNG", name, f"Letzter Lauf ist älter als {WORKFLOW_MAX_AGE_HOURS[name]} Stunden."))
    return results


def build_report(results: list[dict[str, str]]) -> str:
    count = {level: sum(item["level"] == level for item in results) for level in ("OK", "WARNUNG", "KRITISCH")}
    status = "KRITISCH" if count["KRITISCH"] else "WARNUNG" if count["WARNUNG"] else "OK"
    lines = [
        "# Qualitätsreport",
        f"Stand: {datetime.now():%Y-%m-%d %H:%M}",
        f"Gesamtstatus: **{status}**",
        f"- OK: {count['OK']}",
        f"- Warnungen: {count['WARNUNG']}",
        f"- Kritisch: {count['KRITISCH']}",
        "",
        "## Prüfergebnisse",
    ]
    for item in results:
        icon = {"OK": "✅", "WARNUNG": "⚠️", "KRITISCH": "❌"}[item["level"]]
        lines.append(f"- {icon} **{item['title']}**: {item['detail']}")
    lines += [
        "",
        "## Sicherheitsregel",
        "Dieser Agent veröffentlicht nichts, startet keine Workflows neu und ändert keinen Content.",
    ]
    return "\n".join(lines) + "\n"


def append_history(report: str) -> None:
    MEMORY.mkdir(parents=True, exist_ok=True)
    summary = next((line for line in report.splitlines() if line.startswith("Gesamtstatus:")), "Gesamtstatus: unbekannt")
    old = _read(HISTORY) or "# Qualitätshistorie\n"
    HISTORY.write_text(old.rstrip() + f"\n- {datetime.now():%Y-%m-%d %H:%M}: {summary}\n", encoding="utf-8")


def notify(report: str) -> None:
    try:
        from telegram_bot import send_message
        summary = "\n".join(line for line in report.splitlines() if line.startswith(("Gesamtstatus:", "- OK:", "- Warnungen:", "- Kritisch:")))
        send_message("🔎 Qualitäts-Agent\n" + summary)
    except Exception as error:
        print(f"Telegram-Qualitätsmeldung übersprungen: {type(error).__name__}")


def run(send_telegram: bool = False) -> str:
    checks: tuple[Callable[[], list[dict[str, str]]], ...] = (
        check_required_files,
        check_inspiration,
        check_youtube_fallback,
        check_source_quality,
        check_inspiration_age,
        check_bright_data,
        check_gemini,
        check_secret_hygiene,
        check_workflows,
    )
    results = [item for check in checks for item in check()]
    report = build_report(results)
    MEMORY.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(report, encoding="utf-8")
    append_history(report)
    if send_telegram:
        notify(report)
    print(report)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify", action="store_true", help="Sendet die Kurzfassung an Telegram.")
    args = parser.parse_args()
    run(send_telegram=args.notify)
