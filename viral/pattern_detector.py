"""Datengetriebenes Viral-Learning: Muster, Funnel, Loops und kontrollierte Experimente."""
from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path

from .analyze_external import analyze as external
from .analyze_internal import analyze as internal

OUT = Path("memory/VIRAL_PATTERNS.md")
PERFORMANCE = Path("memory/PERFORMANCE.md")
EXPERIMENTS = Path("memory/EXPERIMENTS.md")
FUNNEL = Path("memory/FUNNEL_ANALYSIS.md")


def _entries() -> list[dict[str, int | str]]:
    text = PERFORMANCE.read_text(encoding="utf-8") if PERFORMANCE.exists() else ""
    entries = []
    for block in re.split(r"(?m)^## Beitrag vom ", text)[1:]:
        values: dict[str, int | str] = {}
        for label, key in (("Datum", "date"), ("Likes", "likes"), ("Kommentare", "comments"), ("Shares", "shares"), ("Gespeichert", "saved"), ("Reichweite", "reach")):
            match = re.search(rf"(?m)^{label}:\s*(.+?)\s*$", block)
            if match:
                values[key] = match.group(1).strip() if key == "date" else int(re.sub(r"\D", "", match.group(1)) or 0)
        values["title"] = (re.search(r"(?m)^Titel:\s*(.+)$", block) or [None, "Beitrag"])[1].strip()
        if values.get("date") and values.get("reach") is not None:
            entries.append(values)
    return entries


def analyze_funnel() -> str:
    cutoff = date.today().toordinal() - 7
    rows = [row for row in _entries() if date.fromisoformat(str(row["date"])).toordinal() >= cutoff]
    reach = sum(int(row.get("reach", 0)) for row in rows)
    engagement = sum(sum(int(row.get(key, 0)) for key in ("likes", "comments", "shares", "saved")) for row in rows)
    engagement_rate = engagement / reach * 100 if reach else None
    status = "nicht verfügbar (Instagram-/Facebook-Insights liefern Profilbesuche und neue Follower derzeit nicht)" 
    recommendation = (
        "Mehr Kommentare fördern: klare Frage oder konkrete Handlungsaufforderung in einem freigegebenen A/B-Test prüfen."
        if engagement_rate is not None and engagement_rate < 3
        else "Erst weitere echte Post-Daten sammeln; es werden keine Conversion-Werte geschätzt."
    )
    report = f"""# Conversion-Funnel

Stand: {datetime.now():%Y-%m-%d %H:%M}

## Letzte 7 Tage

- Reichweite: {reach:,}
- Engagement: {engagement:,}
- Engagement-Rate: {f"{engagement_rate:.2f} %" if engagement_rate is not None else "nicht verfügbar"}
- Profilbesuche: {status}
- Neue Follower: {status}

## Conversion-Rates

- Reichweite → Engagement: {f"{engagement_rate:.2f} %" if engagement_rate is not None else "nicht verfügbar"}
- Engagement → Profilbesuch: nicht verfügbar
- Profilbesuch → Follower: nicht verfügbar
- Gesamt: nicht verfügbar

## Größter Hebel

- {recommendation}
"""
    FUNNEL.write_text(report, encoding="utf-8")
    return report


def design_experiment() -> str:
    content = EXPERIMENTS.read_text(encoding="utf-8") if EXPERIMENTS.exists() else "# A/B-Experimente\n"
    title = "Frage-Hook vs. Aussage-Hook"
    if title.lower() in content.lower():
        return "Kein neuer Experiment-Vorschlag: Der Hook-Test ist bereits dokumentiert."
    if not _entries():
        return "Kein Experiment vorgeschlagen: Es fehlen noch eigene Performance-Daten."
    proposal = f"""\n### Vorschlag: {title}
- Erstellt: {date.today().isoformat()}
- Hypothese: Frage-Hooks erzeugen mehr Kommentare pro Reichweite als Aussage-Hooks.
- Variante A: „Warum fährst du noch geradeaus?“
- Variante B: „Diese Kurvenroute ändert alles.“
- Metrik: Kommentare pro Reichweite
- Status: VORGESCHLAGEN
- Ergebnis: –
"""
    marker = "## Vorgeschlagene Experimente"
    if marker in content:
        content = content.replace(marker, marker + proposal, 1)
    else:
        content = content.rstrip() + "\n\n" + marker + proposal
    EXPERIMENTS.write_text(content.rstrip() + "\n", encoding="utf-8")
    try:
        from telegram_bot import send_message
        send_message("Neues Experiment vorgeschlagen: Frage-Hook vs. Aussage-Hook. Zustimmen und starten mit: experiment: start Frage-Hook vs. Aussage-Hook")
    except Exception as exc:
        print(f"Telegram-Experimenthinweis übersprungen: {exc}")
    return f"Experiment vorgeschlagen: {title} (noch nicht aktiv)."


def detect_viral_loops(rows: list[dict[str, int | str]]) -> str:
    if not rows:
        return "- Noch keine belastbaren Loop-Daten vorhanden.\n"
    high_comments = [row for row in rows if int(row.get("comments", 0)) > 0 and int(row.get("reach", 0)) > 0]
    if not high_comments:
        return "- Keine nachweisbare Viral-Schleife: Es fehlen Kommentare oder Reichweite.\n"
    return "- Beobachtung: Beiträge mit Kommentaren erhalten Interaktion. Kausalität wird erst nach einem freigegebenen A/B-Test behauptet.\n"


def recommend_next_experiment() -> str:
    content = EXPERIMENTS.read_text(encoding="utf-8") if EXPERIMENTS.exists() else ""
    if "## Abgeschlossene Experimente" in content and "Ergebnis:" in content.split("## Abgeschlossene Experimente", 1)[-1]:
        return "- Nächster Test: Nur aus dokumentierten Ergebnissen ableiten; vor Start Freigabe einholen.\n"
    return "- Nächster Test: Zuerst einen Vorschlag bestätigen und sauber messen.\n"


def main() -> None:
    rows = _entries()
    funnel = analyze_funnel()
    experiment = design_experiment()
    report = f"""# Viral-Muster

Stand: {datetime.now():%Y-%m-%d %H:%M}

{external()}
{internal()}
## Funnel-Learning
- {funnel.split("## Größter Hebel", 1)[-1].strip()}

## Viral-Loops
{detect_viral_loops(rows)}
## Experimente
- {experiment}
{recommend_next_experiment()}
## Arbeitsregel
- Nur echte, nachvollziehbare Daten. Keine gekauften Interaktionen und keine fremden Inhalte kopieren.
"""
    OUT.write_text(report, encoding="utf-8")
    for path, title in ((Path("memory/HOOKS_THAT_WORK.md"), "# Hooks, die wirken"), (Path("memory/LESSONS_LEARNED.md"), "# Lessons Learned")):
        old = path.read_text(encoding="utf-8") if path.exists() else title + "\n"
        path.write_text(old.rstrip() + f"\n\n- {datetime.now():%Y-%m-%d}: Viral-, Funnel- und Experiment-Learning aktualisiert.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
