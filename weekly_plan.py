import os
import re
import time
import requests
from datetime import datetime

MODEL_LIST=["gemini-3.8-flash","gemini-3.7-flash","gemini-3.6-flash","gemini-3.5-flash","gemini-3.5-flash-lite"]

def read(path,max_chars=10000):
    try:
        with open(path,"r",encoding="utf-8") as f:return f.read()[-max_chars:]
    except FileNotFoundError:return ""

def try_generate(key,prompt):
    headers={"Content-Type":"application/json","X-goog-api-key":key};data={"contents":[{"parts":[{"text":prompt}]}]}
    for rnd in range(5):
        for model in MODEL_LIST:
            try:
                r=requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",headers=headers,json=data,timeout=120)
                if r.status_code==200:
                    text=r.json()["candidates"][0]["content"]["parts"][0]["text"]
                    return re.sub(r'AIza[0-9A-Za-z_\-]{35}|AQ\.[A-Za-z0-9_\-]{40,}|sk-[A-Za-z0-9]{20,}','[ENTFERNT]',text).strip()
                if r.status_code in (401,403):raise RuntimeError(f"Gemini HTTP {r.status_code}")
                time.sleep(10)
            except RuntimeError:raise
            except Exception:time.sleep(10)
        if rnd<4:time.sleep(90)
    raise RuntimeError("Kein Gemini-Modell verfügbar")

def generate_weekly_plan():
    key=os.environ.get("GEMINI_API_KEY")
    if not key:return "FEHLER: Kein API-Key gefunden."
    roster=read("content/MOTOGP_ROSTER.md"); history=read("memory/POST_HISTORY.md",7000); viral=read("memory/VIRAL_PATTERNS.md",5000)
    prompt=f"""Erstelle einen Content-Plan für die kommenden 7 Tage für eine deutsch-türkische Motorrad-Community.

AKTUELL VERIFIZIERTER MOTOGP-ROSTER:\n{roster or 'Noch kein automatisch verifizierter Roster vorhanden.'}
POST-HISTORY:\n{history}
VIRAL-MUSTER:\n{viral}

Regeln:
- MotoGP-Fahrer und Teams ausschließlich aus dem aktuellen MOTOGP_ROSTER verwenden; keine alten Saisonaufstellungen raten.
- Mehrere Tage dürfen MotoGP behandeln, aber jeweils bevorzugt EINEN Fahrer in den Mittelpunkt stellen und Fahrer rotieren.
- Türkische Racer bei starkem aktuellem Anlass priorisieren.
- Ride With Me höchstens EINMAL in dieser gesamten Woche.
- Professionelle, spezifische Hashtags: Fahrer, Team/Hersteller, MotoGP/GP und passende Community-Nische; kein Hashtag-Spam, max. 6 je Plattform.
- POST_HISTORY zur Vermeidung von Wiederholungen verwenden.
- Keine erfundenen Transfers, Ergebnisse oder Trending-Behauptungen.
- Reale Rennmedien nicht künstlich als echte Aufnahme erzeugen.

Für Montag bis Sonntag jeweils:
--- TAG X: Wochentag ---
Thema: ...
Plattform: Instagram/TikTok/Facebook/Reel/Story
Fahrer-Fokus: Name oder keiner
Hook: ...
Beschreibung: ...
Hashtags Instagram: ...
Hashtags TikTok: ...
Visuelle Idee: ...
"""
    return try_generate(key,prompt)

def save_weekly_plan(content):
    os.makedirs("content",exist_ok=True)
    with open("content/WOCHENPLAN.md","a",encoding="utf-8") as f:f.write(f"\n\n# Wochenplan vom {datetime.now():%Y-%m-%d %H:%M:%S}\n{content}\n")

if __name__=="__main__":save_weekly_plan(generate_weekly_plan())
