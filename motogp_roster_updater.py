"""Aktualisiert den MotoGP-Fahrer-/Team-Roster saisonal aus dem öffentlichen Web.

Sicherheitsprinzip:
- Recherche via Gemini Google Search Grounding (öffentliche Webquellen).
- Ein Roster wird nur übernommen, wenn die Saison explizit bestätigt ist und
  die Antwort mindestens zwei unterschiedliche Quellen-Domains enthält.
- Bevorzugt motogp.com; zweite Quelle dient dem Crosscheck.
- Keine Social-Handles werden geraten. Bestehende Handles werden nur bei
  eindeutigem Namensmatch übernommen.
- Bei Unsicherheit bleibt der letzte bestätigte Roster unverändert.
"""
from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from urllib.parse import urlparse

import requests

ROOT = Path(".")
CONFIG = ROOT / "config" / "followed_accounts.md"
ROSTER = ROOT / "content" / "MOTOGP_ROSTER.md"
LOG = ROOT / "memory" / "MOTOGP_ROSTER_LOG.md"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"


def season_year() -> int:
    forced = os.environ.get("MOTOGP_SEASON", "").strip()
    if forced.isdigit():
        return int(forced)
    return datetime.now(timezone.utc).year


def existing_handles() -> dict[str, str]:
    if not CONFIG.exists():
        return {}
    text = CONFIG.read_text(encoding="utf-8")
    result: dict[str, str] = {}
    for line in text.splitlines():
        m = re.match(r"-\s+([^\s|]+).*?–\s+(.+?)(?:\s+\(.*\))?$", line)
        if m:
            result[m.group(2).strip().casefold()] = m.group(1).strip()
    return result


def research(year: int, api_key: str) -> tuple[dict, list[dict]]:
    prompt = f"""Recherchiere die offiziell bestätigte MotoGP-Startaufstellung für die Saison {year} im öffentlichen Web.
Bevorzuge offizielle MotoGP-Quellen (motogp.com) und prüfe die Aufstellung zusätzlich gegen mindestens eine zweite seriöse Motorsportquelle.
Unterscheide bestätigte Fahrer/Teams strikt von Gerüchten, Testfahrern, Ersatzfahrern und noch unbestätigten Verträgen.
Wenn die vollständige Aufstellung für {year} noch nicht offiziell feststeht, setze confirmed=false und erkläre kurz warum.
Gib als Antwort NUR valides JSON ohne Markdown zurück:
{{"season":{year},"confirmed":true,"teams":[{{"team":"Teamname","riders":[{{"name":"Fahrername","number":"93"}}]}}],"note":"kurz"}}
Erfinde keine Fahrer, Teams, Nummern oder Social-Media-Handles."""
    payload = {"contents": [{"parts": [{"text": prompt}]}], "tools": [{"google_search": {}}]}
    r = requests.post(GEMINI_URL, headers={"Content-Type":"application/json","X-goog-api-key":api_key}, json=payload, timeout=120)
    r.raise_for_status()
    candidate = r.json().get("candidates", [{}])[0]
    text = "".join(p.get("text", "") for p in candidate.get("content", {}).get("parts", [])).strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I)
    return json.loads(text), candidate.get("groundingMetadata", {}).get("groundingChunks", [])


def sources(chunks: list[dict]) -> list[tuple[str, str]]:
    found, seen = [], set()
    for chunk in chunks:
        web = chunk.get("web", {}) if isinstance(chunk, dict) else {}
        url, title = web.get("uri"), web.get("title", "Quelle")
        if url and url not in seen:
            seen.add(url); found.append((title, url))
    return found


def valid(data: dict, src: list[tuple[str, str]], year: int) -> tuple[bool, str]:
    if data.get("season") != year or data.get("confirmed") is not True:
        return False, "Saison noch nicht vollständig bestätigt"
    teams = data.get("teams")
    if not isinstance(teams, list) or len(teams) < 8:
        return False, "Roster unvollständig"
    riders = [r for t in teams for r in (t.get("riders") or []) if r.get("name")]
    if len(riders) < 18:
        return False, "Zu wenige bestätigte Fahrer"
    domains = {urlparse(url).netloc.lower().removeprefix("www.") for _, url in src}
    if len(domains) < 2:
        return False, "Crosscheck mit zweiter Domain fehlt"
    return True, "OK"


def render(data: dict, src: list[tuple[str, str]], handles: dict[str, str]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [f"# MotoGP Roster {data['season']}", "", f"**Automatisch verifiziert:** {now}", "", "## Teams & Fahrer", ""]
    for team in data["teams"]:
        lines.append(f"### {team['team']}")
        for rider in team.get("riders", []):
            name = rider["name"].strip(); num = str(rider.get("number", "?")).strip()
            handle = handles.get(name.casefold())
            suffix = f" | Instagram: @{handle}" if handle else " | Instagram: nicht automatisch verifiziert"
            lines.append(f"- #{num} – {name}{suffix}")
        lines.append("")
    lines += ["## Quellen (Crosscheck)", ""]
    for title, url in src:
        lines.append(f"- {title}: {url}")
    lines += ["", "## Regel", "Diese Datei ist die zentrale saisonale Fahrer-/Teamquelle für die Content-Agenten. Unbestätigte Transfers und Gerüchte werden nicht als Roster übernommen.", ""]
    return "\n".join(lines)


def log(status: str, year: int, detail: str) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    old = LOG.read_text(encoding="utf-8") if LOG.exists() else "# MotoGP Roster Log\n"
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    LOG.write_text(old.rstrip() + f"\n- {stamp} | Saison {year} | {status} | {detail}\n", encoding="utf-8")


def main() -> None:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY fehlt")
    year = season_year()
    try:
        data, chunks = research(year, key)
        src = sources(chunks)
        ok, reason = valid(data, src, year)
        if not ok:
            log("NICHT AKTUALISIERT", year, reason)
            print(f"Roster bleibt unverändert: {reason}")
            return
        ROSTER.parent.mkdir(parents=True, exist_ok=True)
        ROSTER.write_text(render(data, src, existing_handles()), encoding="utf-8")
        log("AKTUALISIERT", year, f"{len(data['teams'])} Teams, Crosscheck {len(src)} Quellen")
        print(f"MotoGP-Roster {year} aktualisiert.")
    except Exception as exc:
        log("FEHLER", year, f"{type(exc).__name__}: {str(exc)[:180]}")
        raise


if __name__ == "__main__":
    main()
