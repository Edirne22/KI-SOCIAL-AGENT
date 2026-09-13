"""Koordiniert Inspirationsquellen und erstellt einen detaillierten, belegten Report."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import os
from pathlib import Path
import re
import time

import requests

from . import apify_agent, brightdata_agent, crawlbase_agent
from .report_builder import build, evidence_count
from telegram_bot import send_message

MEM = Path("memory")
GEMINI_DEBUG = MEM / "GEMINI_DEBUG.md"
FOLLOW_REPORT = MEM / "FOLLOW_ANALYSIS.md"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent"
RETRY_DELAYS = (30, 60, 120)


def _gemini(prompt: str, api_key: str, grounded: bool = False) -> tuple[str, list[dict]]:
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    if grounded:
        payload["tools"] = [{"google_search": {}}]
    response = requests.post(
        GEMINI_URL,
        headers={"Content-Type": "application/json", "X-goog-api-key": api_key},
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    candidate = response.json().get("candidates", [{}])[0]
    text = "".join(part.get("text", "") for part in candidate.get("content", {}).get("parts", [])).strip()
    return text, candidate.get("groundingMetadata", {}).get("groundingChunks", [])


def _write_gemini_debug(status: str, error: str, prompt: str, posts: int, attempts: int) -> None:
    """Speichert nur Metadaten, niemals Prompt, Schlüssel oder Rohdaten."""
    GEMINI_DEBUG.parent.mkdir(parents=True, exist_ok=True)
    old = GEMINI_DEBUG.read_text(encoding="utf-8") if GEMINI_DEBUG.exists() else "# Gemini Debug\n"
    safe_error = re.sub(r"AIza[\w-]+", "[REDACTED]", error)[:500]
    entry = [
        f"\n## Gemini-Zusammenfassung ({datetime.now():%Y-%m-%d %H:%M})",
        f"- HTTP-Status: {status}",
        f"- Fehler: {safe_error or 'keine'}",
        f"- Payload-Größe: {len(prompt.encode('utf-8')) / 1024:.1f} KB",
        f"- Verarbeitete Posts: {posts}",
        f"- Versuche: {attempts}",
    ]
    GEMINI_DEBUG.write_text(old.rstrip() + "\n".join(entry) + "\n", encoding="utf-8")


def _retry_after(response: requests.Response | None, fallback: int) -> int:
    if response is None:
        return fallback
    try:
        return max(fallback, int(response.headers.get("Retry-After", "0")))
    except ValueError:
        return fallback


def _gemini_with_retry(prompt: str, api_key: str, posts: int) -> str | None:
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            text, _ = _gemini(prompt, api_key)
            _write_gemini_debug("200", "", prompt, posts, attempt + 1)
            return text or None
        except requests.HTTPError as error:
            response = error.response
            status = str(response.status_code) if response is not None else "HTTP-Fehler"
            retryable = status == "429" or (status.isdigit() and 500 <= int(status) <= 599)
            if retryable and attempt < len(RETRY_DELAYS):
                time.sleep(_retry_after(response, RETRY_DELAYS[attempt]) if status == "429" else RETRY_DELAYS[attempt])
                continue
            _write_gemini_debug(status, str(error), prompt, posts, attempt + 1)
            return None
        except requests.Timeout:
            if attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt])
                continue
            _write_gemini_debug("Timeout", "Zeitüberschreitung", prompt, posts, attempt + 1)
            return None
        except requests.RequestException as error:
            _write_gemini_debug(type(error).__name__, str(error), prompt, posts, attempt + 1)
            return None
    return None


def _grounded_evidence(api_key: str) -> str:
    prompt = """Recherchiere öffentliche, aktuelle Themen der letzten 7 Tage für eine deutsch-türkische Motorrad-Community:
Toprak Razgatlıoğlu, Deniz und Can Öncü, MotoGP, WorldSBK sowie Motorrad-Reise. Nenne ausschließlich Fakten, die du mit öffentlichen Quellen belegen kannst. Keine erfundenen Zahlen oder Links."""
    try:
        text, chunks = _gemini(prompt, api_key, grounded=True)
    except (requests.RequestException, KeyError, IndexError, ValueError) as error:
        return f"# Gemini Search Grounding\n\nKeine Grounding-Daten verfügbar: {type(error).__name__}.\n"

    lines = ["# Gemini Search Grounding", "", "## Öffentliche Quellen"]
    seen = set()
    for index, chunk in enumerate(chunks, start=1):
        web = chunk.get("web", {}) if isinstance(chunk, dict) else {}
        url = web.get("uri")
        title = web.get("title", "Ohne Titel")
        if not url or url in seen:
            continue
        seen.add(url)
        lines += [f"### Datensatz {index}", f"- Titel: {title}", "- Datum: nicht verfügbar", f"- URL: {url}", "- Engagement: nicht verfügbar"]
    if not seen:
        lines.append("Keine verifizierbaren Grounding-Links erhalten.")
    if text:
        lines += ["", "## Recherche-Notiz", text]
    return "\n".join(lines) + "\n"


def _number(value: str) -> int:
    numbers = re.findall(r"\d+", value.replace(".", "").replace(",", ""))
    return int(numbers[-1]) if numbers else 0


def _top_posts(reports: dict[str, str], limit: int = 30) -> list[dict[str, str | int]]:
    """Extrahiert bestehende Markdown-Datensätze und priorisiert Engagement."""
    posts: list[dict[str, str | int]] = []
    for provider, report in reports.items():
        blocks = re.split(r"(?=^### Datensatz \d+)", report, flags=re.MULTILINE)
        for block in blocks:
            if not block.startswith("### Datensatz"):
                continue
            def field(name: str) -> str:
                match = re.search(rf"(?m)^- {re.escape(name)}: (.*)$", block)
                return match.group(1).strip() if match else "nicht verfügbar"
            title, url, date = field("Titel"), field("URL"), field("Datum")
            if url == "nicht verfügbar":
                continue
            score = sum(_number(field(label)) for label in ("Likes", "Kommentare", "Shares", "Reposts", "Retweets", "Views", "Antworten"))
            posts.append({"platform": provider, "title": title, "url": url, "date": date, "engagement": score})
    return sorted(posts, key=lambda item: int(item["engagement"]), reverse=True)[:limit]


def _top_posts_text(posts: list[dict[str, str | int]]) -> str:
    if not posts:
        return "Keine strukturierten Beiträge vorhanden."
    lines = []
    for index, post in enumerate(posts, 1):
        lines += [
            f"### Datensatz {index}",
            f"- Plattform: {post['platform']}",
            f"- Titel: {post['title']}",
            f"- Datum: {post['date']}",
            f"- URL: {post['url']}",
            f"- Engagement: {post['engagement']}",
        ]
    return "\n".join(lines)


def _fallback_with_raw_data(reports: dict[str, str], posts: list[dict[str, str | int]]) -> str:
    base = build(reports)
    return base + "\n## Gemini-Status\nGemini nicht verfügbar – Rohdaten der wichtigsten Beiträge folgen.\n\n## Rohdaten\n" + _top_posts_text(posts) + "\n"


def _follow_context() -> str:
    """Übernimmt nur die eigene, begrenzte Erkenntnis-Sektion als Inspiration."""
    if not FOLLOW_REPORT.exists():
        return "Keine aktuelle Follow-Analyse verfügbar."
    report = FOLLOW_REPORT.read_text(encoding="utf-8")
    match = re.search(r"(?ms)^## Erkenntnisse für Bülent\s*\n(.*?)(?=^## |\Z)", report)
    if not match:
        return "Keine nutzbaren Follow-Erkenntnisse verfügbar."
    return match.group(1).strip()[:1500]


def summarize(reports: dict[str, str]) -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    posts = _top_posts(reports)
    if not api_key:
        return _fallback_with_raw_data(reports, posts)

    enriched = dict(reports)
    if evidence_count(enriched) < 5:
        enriched["Gemini Search Grounding"] = _grounded_evidence(api_key)
        posts = _top_posts(enriched)

    evidence = _top_posts_text(posts)
    follow_context = _follow_context()
    prompt = f"""Hier sind die bis zu 30 engagiertesten öffentlichen Social-Media- und Suchbeiträge der letzten 7 Tage. Die Daten sind strukturiert und quellengebunden.

{evidence}

Erstelle einen unmittelbar nutzbaren, deutschsprachigen Report für Bülents deutsch-türkische Motorrad-/Reise-Community.\n\nZusätzliche, nicht als Fakten zu behandelnde Muster aus einer öffentlichen Follow-Stichprobe:\n{follow_context}\nNutze sie nur als kreative Orientierung. Kopiere keine fremden Texte und leite daraus keine unbelegten Tatsachen ab.\n
## Top-5 Trending Themen (mit Belegen)
Für jedes Thema: Name, Quelle als vollständige URL, Datum und warum es trending ist. Nutze Engagement-Zahlen nur, wenn sie in den Daten stehen; sonst schreibe „Engagement: nicht verfügbar“. Wenn weniger als fünf belegte Themen vorliegen, schreibe deutlich: „Report eingeschränkt – nur X belegte Themen gefunden.“ Erfinde niemals Namen, Daten, URLs oder Zahlen.

## 3 konkrete Content-Ideen für Bülent
Für jede Idee zwingend:
- Titel:
- Format: Reel, Post oder Story
- Hook: „vollständig ausgeschriebene erste Zeile“
- Inspirations-Quelle: vollständige URL aus den Daten
- Warum passend: kurzer, konkreter Satz
Keine abstrakten Platzhalter und keine Quelle erfinden. Falls es keine belegte Quelle gibt, kennzeichne die Idee als „nicht erstellt“.

## Quellen
Alle verwendeten URLs nummeriert. Verwende ausschließlich URLs, die in den obigen strukturierten Daten stehen.
"""
    text = _gemini_with_retry(prompt, api_key, len(posts))
    return "# Inspiration-Ideen\n\n" + text + "\n" if text else _fallback_with_raw_data(enriched, posts)


def main() -> None:
    jobs = {"Apify": apify_agent.run, "Bright Data": brightdata_agent.run, "Crawlbase": crawlbase_agent.run}
    reports: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=3) as pool:
        future_to_name = {pool.submit(function): name for name, function in jobs.items()}
        for task in as_completed(future_to_name):
            name = future_to_name[task]
            try:
                reports[name] = task.result()
            except Exception as error:
                reports[name] = f"# {name}\n\nKeine Daten: {type(error).__name__}.\n"

    report = summarize(reports)
    (MEM / "INSPIRATION_IDEAS.md").write_text(report, encoding="utf-8")
    week = datetime.now().strftime("%Y-W%W")
    archive = MEM / "INSPIRATION_ARCHIVE"
    archive.mkdir(parents=True, exist_ok=True)
    (archive / f"{week}.md").write_text(report, encoding="utf-8")
    log = MEM / "INSPIRATION_LOG.md"
    old = log.read_text(encoding="utf-8") if log.exists() else "# Inspiration-Log\n"
    log.write_text(old + f"\n- {datetime.now():%Y-%m-%d %H:%M}: " + ", ".join(reports) + "\n", encoding="utf-8")
    try:
        send_message("Inspiration-Analyse fertig. Der Report enthält nur belegte Themen und Quellen.")
    except RuntimeError as error:
        print(f"Telegram übersprungen: {error}")


if __name__ == "__main__":
    main()
