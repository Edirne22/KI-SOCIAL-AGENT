"""Erstellt den Wochenplan mit Racing-, Community- und Veröffentlichungshistorie."""

import os
import re
from datetime import date, datetime, timedelta

from memory_engine import get_context
from llm_client import global_professional_context
from llm_router import quick_chat


def read(path, max_chars=10000):
    try:
        with open(path, "r", encoding="utf-8") as handle:
            return handle.read()[-max_chars:]
    except FileNotFoundError:
        return ""


def generate_weekly_plan():
    today = date.today()
    end_date = today + timedelta(days=6)
    roster = read("content/MOTOGP_ROSTER.md")
    history = read("memory/POST_HISTORY.md", 7000)
    recent_plans = read("content/WOCHENPLAN.md", 9000)
    viral = read("memory/VIRAL_PATTERNS.md", 5000)
    motogp_daily = read("memory/MOTOGP_DAILY_CONTENT.md", 7000)
    calendar = read("content/MOTOGP_CALENDAR.md", 6000)
    biker_community = read("content/TURKISH_BIKER_COMMUNITY.md", 7000)
    followed_accounts = read("config/followed_accounts.md", 7000)
    community_rotation = read("memory/COMMUNITY_ROTATION.json", 3000)
    learned = get_context(9000)

    raw_prompt = f"""Erstelle einen konkreten Content-Plan für die nächsten sieben Tage
({today.isoformat()} bis {end_date.isoformat()}) für Bülents deutsch-türkische
Motorrad-Community. Plane für jeden Tag Thema, Plattform, Hook, ausformulierten
Beitrag, Hashtags und visuelle Idee.

MEMORY:
{learned}
LETZTE WOCHENPLÄNE (Wiederholungen vermeiden):
{recent_plans}
POST-HISTORY:
{history}
MOTOGP-FAHRER:
{roster}
MOTOGP-KALENDER UND WOCHENEND-ABLAUF:
{calendar}
AKTUELLE RACING-MELDUNGEN:
{motogp_daily}
BIKER-CLUBS UND COMMUNITY-INFORMATIONEN:
{biker_community}
GEFOLGTE COMMUNITY-ACCOUNTS:
{followed_accounts}
LETZTE COMMUNITY-ROTATION:
{community_rotation}
VIRAL-MUSTER:
{viral}

Verbindliche Regeln:
- Plane mindestens einen eigenständigen Beitrag über eine Biker-Gruppe oder
  einen Club aus den gelieferten Community-Quellen in dieser Woche ein.
- Wechsle den Club/Account gegenüber der letzten Community-Rotation ab.
- Nutze nur die gelieferten öffentlichen Informationen. Behaupte keine aktuelle
  Veranstaltung, Mitgliederzahl, Aussage oder Aktivität ohne aktuellen Beleg.
  Wenn keine aktuelle Meldung vorliegt, verwende ein respektvolles,
  zeitloses Community-Porträt.
- Verknüpfe Community und Racing nur, wenn es inhaltlich passt.
- MotoGP-Fahrer, Teams, Termine und Ergebnisse nur aus den gelieferten Quellen.
- Keine identischen Hooks aus den letzten Wochenplänen oder der Post-History.
- Turkish Riders bei echtem Anlass priorisieren, nicht erzwingen.
- Ride With Me höchstens einmal pro Woche; maximal sechs passende Hashtags.
- Keine erfundenen Transfers, Ergebnisse, Zitate, Trends oder Kennzahlen.
- Schreibe natürlich auf Deutsch; keine englischen Rohtexte und keine
  Satz-für-Satz-Übersetzungen.
- Gib klar an, wenn ein Fakt oder eine Sessionzeit in den Quellen fehlt.
- Markiere jeden Tag mit Datum und Wochentag. Keine Veröffentlichung auslösen;
  der Wochenplan ist ein Vorschlag zur Freigabe.

Qualitätsprüfung vor der Ausgabe:
- Sind alle sieben Tage des Zeitraums abgedeckt?
- Enthält genau mindestens ein Tag einen konkreten Club-/Gruppenbeitrag?
- Sind Themen und Hooks gegenüber der gespeicherten Historie unterschiedlich?
Wenn eine Bedingung nicht erfüllt ist, überarbeite den Plan vor der Ausgabe.
"""
    prompt = (
        f"GLOBALER VERBINDLICHER STANDARD:\n{global_professional_context()}\n\n"
        f"AUFGABE:\n{raw_prompt}"
    )

    text = quick_chat(prompt, task_type="reasoning").strip()
    if not text:
        raise RuntimeError("Wochenplan-Anbieter lieferte eine leere Antwort.")
    if text.upper().startswith("FEHLER:"):
        raise RuntimeError(text)

    # Schutz vor versehentlich ausgegebenen API-Schlüsseln.
    for pattern in (
        r"AIza[0-9A-Za-z_\-]{35}",
        r"AQ\.[A-Za-z0-9_\-]{40,}",
        r"sk-[A-Za-z0-9]{20,}",
        r"\b[A-Za-z0-9_\-]{50,}\b",
    ):
        text = re.sub(pattern, "[ENTFERNT]", text)

    if not re.search(r"community|club|gruppe|biker|turkbirler|t-bikers|bike society", text, re.I):
        raise RuntimeError("Wochenplan enthält keinen erkennbaren Biker-Community-Beitrag.")
    return text


def save_weekly_plan(content):
    if not content.strip():
        raise ValueError("Leerer Wochenplan wird nicht gespeichert.")
    os.makedirs("content", exist_ok=True)
    with open("content/WOCHENPLAN.md", "a", encoding="utf-8") as handle:
        handle.write(f"\n\n# Wochenplan vom {datetime.now():%Y-%m-%d %H:%M:%S}\n{content}\n")


if __name__ == "__main__":
    save_weekly_plan(generate_weekly_plan())
