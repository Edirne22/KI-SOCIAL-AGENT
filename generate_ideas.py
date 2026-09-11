import os
import re
import time
import requests
from datetime import datetime

MODEL_LIST = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
]

MEMORY_FILES = [
    "memory/USER_PREFERENCES.md",
    "memory/HOOKS_THAT_WORK.md",
    "memory/LESSONS_LEARNED.md",
    "memory/POST_HISTORY.md",
    "memory/RESEARCH_LOG.md",
]

KNOWLEDGE_FILES = [
    "ride-with-me/FEATURE_IDEAS.md",
    "content/TURKISH_RACERS.md",
    "content/MOTOGP_CALENDAR.md",
    "content/TURKISH_BIKER_COMMUNITY.md",
    "rules/BRAND_RULES.md",
    "rules/SAFETY_RULES.md",
]

def read_file(path, max_chars=2500):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return content[-max_chars:]
    except FileNotFoundError:
        return ""

def read_all():
    """Liest Gedächtnis + Wissensdateien für den Prompt."""
    parts = []
    for path in MEMORY_FILES + KNOWLEDGE_FILES:
        content = read_file(path)
        if content:
            parts.append(f"\n--- {path} ---\n{content}")
    return "\n".join(parts)

def try_generate(api_key, prompt):
    headers = {
        "Content-Type": "application/json",
        "X-goog-api-key": api_key
    }
    data = {"contents": [{"parts": [{"text": prompt}]}]}

    max_rounds = 5
    pause_between_models = 10
    pause_between_rounds = 90

    for round_number in range(1, max_rounds + 1):
        print(f"Starte Durchlauf {round_number} von {max_rounds}")
        for model in MODEL_LIST:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
            try:
                response = requests.post(url, headers=headers, json=data, timeout=120)
                if response.status_code == 200:
                    result = response.json()
                    text = result["candidates"][0]["content"]["parts"][0]["text"]
                    # Erweiterter Key-Filter
                    text = re.sub(r'AIza[0-9A-Za-z_\-]{35}', '[ENTFERNT]', text)
                    text = re.sub(r'AQ\.[A-Za-z0-9_\-]{40,}', '[ENTFERNT]', text)
                    text = re.sub(r'sk-[A-Za-z0-9]{20,}', '[ENTFERNT]', text)
                    text = re.sub(r'\b[A-Za-z0-9_\-]{50,}\b', '[ENTFERNT]', text)
                    print(f"Erfolg mit Modell: {model}")
                    return text.strip()
                else:
                    print(f"Modell {model}: Status {response.status_code} – probiere nächstes...")
                    time.sleep(pause_between_models)
            except Exception as e:
                print(f"Modell {model}: Fehler – {e}")
                time.sleep(pause_between_models)

        if round_number < max_rounds:
            print(f"Durchlauf {round_number} beendet – warte {pause_between_rounds} Sekunden...")
            time.sleep(pause_between_rounds)

    return "FEHLER: Kein Modell verfügbar nach mehreren Durchläufen."

def extract_titles(text):
    """Zieht alle Titel aus der generierten Antwort."""
    return re.findall(r"Titel:\s*(.+)", text)

def extract_hooks(text):
    """Zieht alle Hooks aus der generierten Antwort."""
    return re.findall(r"Hook:\s*(.+)", text)

def save_to_history(text):
    """Schreibt generierte Beiträge in POST_HISTORY.md."""
    titles = extract_titles(text)
    hooks = extract_hooks(text)
    if not titles:
        return
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n### {timestamp} | Entwurf generiert\n"
    for i, title in enumerate(titles, 1):
        hook = hooks[i-1] if i <= len(hooks) else "–"
        entry += f"- Titel {i}: {title.strip()}\n- Hook {i}: {hook.strip()}\n"

    with open("memory/POST_HISTORY.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"POST_HISTORY.md aktualisiert ({len(titles)} Titel).")

def generate_content_plan():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "FEHLER: Kein API-Key gefunden."

    knowledge = read_all()
    knowledge_part = f"Berücksichtige folgende Wissens- und Gedächtnisquellen:\n{knowledge}\n" if knowledge else ""

    prompt = f"""Erstelle 3 komplette Content-Ideen für einen Social-Media-Agenten.
Themen: Motorrad, Reisen, Lifestyle, Technik, KI, MotoGP.
Zielgruppe: 18-65 Jahre, deutsch und türkisch, Motorradfahrer und Reisefreudige.
Stil: locker, per Du, wenige Emojis, kurze Captions.
Wichtig: Gib keine Zugangsdaten, Passwörter oder API-Schlüssel aus.

{knowledge_part}

BESONDERE PRIORITÄTEN:
1. Wenn am kommenden Wochenende ein MotoGP-Rennen stattfindet (siehe MotoGP-Kalender),
   baue mindestens einen Beitrag zum Rennwochenende ein.
2. Türkische Rennfahrer haben IMMER Vorrang:
   Toprak Razgatlıoğlu, Deniz Öncü, Can Öncü, Bahattin Sofuoğlu, Kenan Sofuoğlu, Zayn Sofuoğlu.
   Erwähne sie namentlich und markiere wenn möglich ihre Instagram-Handles.
3. Vermeide Wiederholungen – nutze POST_HISTORY.md, um schon behandelte Themen zu erkennen.
4. Nutze bewährte Hooks aus HOOKS_THAT_WORK.md als Inspiration.
5. Community-Themen (Türkische Biker in Deutschland) sind willkommen.

Erstelle zu jeder Idee:
- Titel
- Plattform (Instagram/TikTok/Facebook/Reel/Story)
- Thema
- Hook
- Instagram-Caption (kurz, mit Hashtags)
- Facebook-Post (etwas ausführlicher)
- TikTok-Skript (Hook + 3-4 Szenen + Call-to-Action)
- Visuelle Idee
- Hashtag-Vorschläge
- Trend-Bezug

Formatiere die Antwort exakt so:

--- BEITRAG 1 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
...

--- BEITRAG 2 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
...

--- BEITRAG 3 ---
Titel: ...
Plattform: ...
Thema: ...
Hook: ...

Instagram-Caption:
...

Facebook-Post:
...

TikTok-Skript:
...

Visuelle Idee:
...

Hashtags Instagram:
#...

Hashtags TikTok:
#...

Trend-Bezug:
...
"""

    return try_generate(api_key, prompt)

def save_content_plan(content):
    os.makedirs("content", exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"\n\n## Automatisch generierte Beiträge vom {timestamp}\n{content}\n"
    with open("content/CONTENT_PLAN.md", "a", encoding="utf-8") as f:
        f.write(entry)
    print("Content-Plan gespeichert.")

if __name__ == "__main__":
    content = generate_content_plan()
    save_content_plan(content)
    if not content.startswith("FEHLER"):
        save_to_history(content)
