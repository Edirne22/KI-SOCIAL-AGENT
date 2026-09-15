import os
import re
import time
import requests
from datetime import datetime

from llm_client import get_agent_context
from memory_engine import get_context

MODEL_LIST = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
MEMORY_FILES = ["memory/USER_PREFERENCES.md", "memory/HOOKS_THAT_WORK.md", "memory/LESSONS_LEARNED.md", "memory/POST_HISTORY.md", "memory/RESEARCH_LOG.md", "memory/VIRAL_PATTERNS.md"]
KNOWLEDGE_FILES = ["content/MOTOGP_ROSTER.md", "content/TURKISH_RACERS.md", "content/MOTOGP_CALENDAR.md", "content/TURKISH_BIKER_COMMUNITY.md", "rules/BRAND_RULES.md", "rules/SAFETY_RULES.md", "rules/VIRAL_RULES.md"]
INSPIRATION_REPORT = "memory/INSPIRATION_IDEAS.md"
MOTOGP_DAILY = "memory/MOTOGP_DAILY_CONTENT.md"

def read_file(path, max_chars=3500):
    try:
        with open(path, "r", encoding="utf-8") as f: return f.read()[-max_chars:]
    except FileNotFoundError: return ""

def read_all():
    parts=[]
    for path in MEMORY_FILES + KNOWLEDGE_FILES:
        content=read_file(path)
        if content: parts.append(f"\n--- {path} ---\n{content}")
    return "\n".join(parts)

def try_generate(api_key, prompt):
    headers={"Content-Type":"application/json","X-goog-api-key":api_key}; data={"contents":[{"parts":[{"text":prompt}]}]}
    for round_number in range(1,6):
        for model in MODEL_LIST:
            try:
                r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",headers=headers,json=data,timeout=120)
                if r.status_code==200:
                    text=r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    for pattern in (r'AIza[0-9A-Za-z_\-]{35}',r'AQ\.[A-Za-z0-9_\-]{40,}',r'sk-[A-Za-z0-9]{20,}',r'\b[A-Za-z0-9_\-]{50,}\b'): text=re.sub(pattern,'[ENTFERNT]',text)
                    return text.strip()
                if r.status_code in (401,403): raise RuntimeError(f"Gemini HTTP {r.status_code}")
                time.sleep(10)
            except RuntimeError: raise
            except Exception: time.sleep(10)
        if round_number<5: time.sleep(90)
    raise RuntimeError("Kein Gemini-Modell verfügbar.")

def save_to_history(text):
    titles=re.findall(r"Titel:\s*(.+)",text); hooks=re.findall(r"Hook:\s*(.+)",text)
    if not titles:return
    entry=f"\n### {datetime.now():%Y-%m-%d %H:%M} | Entwurf generiert\n"
    for i,title in enumerate(titles): entry+=f"- Titel {i+1}: {title.strip()}\n- Hook {i+1}: {(hooks[i] if i<len(hooks) else '–').strip()}\n"
    with open("memory/POST_HISTORY.md","a",encoding="utf-8") as f:f.write(entry)

def generate_content_plan():
    api_key=os.environ.get("GEMINI_API_KEY")
    if not api_key:return "FEHLER: Kein API-Key gefunden."
    knowledge=read_all(); inspiration=read_file(INSPIRATION_REPORT,7000); motogp_daily=read_file(MOTOGP_DAILY,7000)
    learned=get_context(9000); agent_context=get_agent_context(["01_content_creator","04_social_media_strategist","14_memory_curator"])
    prompt=f"""Erstelle 3 komplette Content-Ideen für Bülents deutsch-türkische Motorrad-Community.
Stil locker, per Du, wenige Emojis, kurze Captions. Keine Zugangsdaten ausgeben.

GESCHLOSSENES MEMORY – VERBINDLICH VOR DER ERSTELLUNG:\n{learned}
WISSEN/WEITERE MEMORIES:\n{knowledge}
AGENTEN-KONTEXT:\n{agent_context}
MOTOGP DAILY AGENCY:\n{motogp_daily or 'Kein aktuelles MotoGP-Tagesbriefing.'}
AKTUELLER INSPIRATIONSREPORT:\n{inspiration or 'Keine aktuelle externe Quelle.'}

VERBINDLICHE CONTENT-STRATEGIE:
1. MEMORY_CONTEXT zuerst anwenden. Direkte Nutzerkorrekturen und harte Regeln haben Vorrang vor externen Trends. Performance-Hypothesen nicht als Garantie behandeln.
2. `content/MOTOGP_ROSTER.md` ist die zentrale verifizierte Quelle für aktuelle MotoGP-Teams/Fahrer. Bei aktuellen MotoGP-Themen `MOTOGP_DAILY_CONTENT.md` priorisieren und die dortige Quelle beibehalten.
3. MotoGP-Ideen bevorzugt auf EINEN Fahrer konzentrieren: aktuelle News, Rennwochenende, Ergebnis, Duell, Technik, Rookie-Entwicklung, Comeback oder belegte Story.
4. Rotiere durch den Roster und nutze POST_HISTORY. Türkische Racer bei starkem aktuellem Anlass Prio 1, aber nicht künstlich erzwingen.
5. Ride With Me maximal EINMAL pro Kalenderwoche.
6. Hashtags professionell/relevant; keine erfundenen Trends und kein Spam.
7. Nutze eigene bestätigte Performance-Learnings, VIRAL_PATTERNS und HOOKS_THAT_WORK. Schwache/fehlende Daten nicht schätzen.
8. Reale Fahrer-/Team-/Rennbehauptungen brauchen konkrete Quelle. Quelle ist Faktenbasis, niemals Textvorlage: keine englischen Rohtexte, Metadaten oder Satz-für-Satz-Übersetzungen übernehmen.
9. Hooks dürfen nicht wortgleich aus jüngsten Entwürfen wiederholt werden und müssen semantisch zum Thema passen.
10. Keine KI-Rennaufnahme als echte Szene darstellen. Keine erfundenen Zahlen, Zitate, Quellen oder Transfers.

Für jede Idee exakt:
--- BEITRAG X ---
Titel: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Thema: ...
Hook: ...
Instagram-Caption: ...
Facebook-Post: ...
TikTok-Skript: ...
Visuelle Idee: ...
Medienvorschlag: QUELLE_PRÜFEN oder KI_ERLAUBT
Hashtags Instagram: ...
Hashtags TikTok: ...
Trend-Bezug: ...
Viral-Score: X/10
Inspirations-Plattform: ...
Inspirations-Quelle: vollständige URL oder Keine aktuelle externe Quelle verwendet.
"""
    return try_generate(api_key,prompt)

def save_content_plan(content):
    os.makedirs("content",exist_ok=True)
    with open("content/CONTENT_PLAN.md","a",encoding="utf-8") as f:f.write(f"\n\n## Automatisch generierte Beiträge vom {datetime.now():%Y-%m-%d %H:%M:%S}\n{content}\n")

if __name__=="__main__":
    content=generate_content_plan(); save_content_plan(content)
    if not content.startswith("FEHLER"):save_to_history(content)
