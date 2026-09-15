import os
import re
import time
import requests
from datetime import datetime

from llm_client import get_agent_context

MODEL_LIST = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
MEMORY_FILES = ["memory/USER_PREFERENCES.md", "memory/HOOKS_THAT_WORK.md", "memory/LESSONS_LEARNED.md", "memory/POST_HISTORY.md", "memory/RESEARCH_LOG.md", "memory/VIRAL_PATTERNS.md"]
KNOWLEDGE_FILES = ["content/MOTOGP_ROSTER.md", "content/TURKISH_RACERS.md", "content/MOTOGP_CALENDAR.md", "content/TURKISH_BIKER_COMMUNITY.md", "rules/BRAND_RULES.md", "rules/SAFETY_RULES.md", "rules/VIRAL_RULES.md"]
INSPIRATION_REPORT = "memory/INSPIRATION_IDEAS.md"

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
    knowledge=read_all(); inspiration=read_file(INSPIRATION_REPORT,7000); agent_context=get_agent_context(["01_content_creator","04_social_media_strategist"])
    prompt=f"""Erstelle 3 komplette Content-Ideen für Bülents deutsch-türkische Motorrad-Community.
Stil locker, per Du, wenige Emojis, kurze Captions. Keine Zugangsdaten ausgeben.

WISSEN/MEMORY:\n{knowledge}
AGENTEN-KONTEXT:\n{agent_context}
AKTUELLER INSPIRATIONSREPORT:\n{inspiration or 'Keine aktuelle externe Quelle.'}

VERBINDLICHE CONTENT-STRATEGIE:
1. `content/MOTOGP_ROSTER.md` ist die zentrale, automatisch im Web verifizierte Quelle für aktuelle MotoGP-Teams und Fahrer. Verwende bei MotoGP-Fahrerideen nur Fahrer/Teams aus diesem Roster. Keine veralteten Saisonlisten raten.
2. Konzentriere MotoGP-Ideen bevorzugt auf EINEN einzelnen Fahrer: aktuelle News, Rennwochenende, Ergebnis, Duell, Technik, Rookie-Entwicklung, Comeback oder belegte Story.
3. Rotiere durch den aktuellen Roster und nutze POST_HISTORY, damit nicht ständig dieselben Fahrer erscheinen. Türkische Racer bleiben bei starkem aktuellem Anlass Prio 1.
4. Ride With Me maximal EINMAL pro Kalenderwoche. Prüfe POST_HISTORY; wenn diese Woche bereits Ride With Me vorkam, keine weitere Idee dazu.
5. Hashtags professionell und relevant: Fahrername/Startnummer (wenn sinnvoll), Team/Hersteller, #MotoGP, aktueller GP/Rennort sowie passende Nischen-/Community-Tags. Keine erfundenen Trending-Hashtags, kein Spam und keine irrelevante Hashtag-Wolke.
6. Nutze VIRAL_PATTERNS und HOOKS_THAT_WORK. Optimiere auf Besucher, Likes, Kommentare, Shares und Saves, aber gib keine Erfolgsgarantie.
7. Reale Fahrer/Teams/Rennmeldungen benötigen eine konkrete belegte Quelle aus dem Inspirationsreport; bevorzuge offizielle MotoGP-Quellen. Keine KI-Rennaufnahme als echt darstellen; Medienvorschlag QUELLE_PRÜFEN.
8. Wenn am kommenden Wochenende ein MotoGP-Rennen stattfindet, mindestens eine passende Fahreridee einbauen.
9. Vermeide Wiederholungen und erfundene Zahlen, Quellen oder Transfers.

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
