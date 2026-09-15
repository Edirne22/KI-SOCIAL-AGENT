import os,re,time,requests
from datetime import datetime
from memory_engine import get_context
from llm_client import global_professional_context
MODEL_LIST=['gemini-3.8-flash','gemini-3.7-flash','gemini-3.6-flash','gemini-3.5-flash','gemini-3.5-flash-lite']
def read(path,max_chars=10000):
 try:
  with open(path,'r',encoding='utf-8') as f:return f.read()[-max_chars:]
 except FileNotFoundError:return ''
def try_generate(key,prompt):
 prompt=f'GLOBALER VERBINDLICHER STANDARD:\n{global_professional_context()}\n\nAUFGABE:\n{prompt}';headers={'Content-Type':'application/json','X-goog-api-key':key};data={'contents':[{'parts':[{'text':prompt}]}]}
 for rnd in range(5):
  for model in MODEL_LIST:
   try:
    r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers=headers,json=data,timeout=120)
    if r.status_code==200:return re.sub(r'AIza[0-9A-Za-z_\-]{35}|AQ\.[A-Za-z0-9_\-]{40,}|sk-[A-Za-z0-9]{20,}','[ENTFERNT]',r.json()['candidates'][0]['content']['parts'][0]['text']).strip()
    if r.status_code in (401,403):raise RuntimeError(f'Gemini HTTP {r.status_code}')
    time.sleep(10)
   except RuntimeError:raise
   except Exception:time.sleep(10)
  if rnd<4:time.sleep(90)
 raise RuntimeError('Kein Gemini-Modell verfügbar')
def generate_weekly_plan():
 key=os.environ.get('GEMINI_API_KEY')
 if not key:return 'FEHLER: Kein API-Key gefunden.'
 roster=read('content/MOTOGP_ROSTER.md');history=read('memory/POST_HISTORY.md',7000);viral=read('memory/VIRAL_PATTERNS.md',5000);motogp_daily=read('memory/MOTOGP_DAILY_CONTENT.md',7000);learned=get_context(9000)
 prompt=f'''Arbeite als Senior-Social-Media-Planer auf Premium-Niveau. Erstelle einen Content-Plan fuer die kommenden 7 Tage fuer Buelents deutsch-tuerkische Motorrad-Community. Mindestens zehn Jahre professionelle Planungserfahrung sind der Qualitaetsmassstab, keine zu behauptende Biografie.\nMEMORY:\n{learned}\nROSTER:\n{roster}\nRACING DAILY:\n{motogp_daily}\nPOST-HISTORY:\n{history}\nVIRAL-MUSTER:\n{viral}\nRegeln: Fakten/Quellen vor Reichweite; MotoGP-Fahrer/Teams nur aus verifizierten Quellen; aktuelle Racing-Themen aus der Daily Agency; Turkish Riders bei echtem Anlass priorisieren, nicht erzwingen; Ride With Me max. 1x/Woche; max. 6 relevante Hashtags; keine identischen Hooks; keine englischen Rohtexte oder Satz-fuer-Satz-Uebersetzung; keine erfundenen Transfers, Ergebnisse, Zitate, Trends oder Kennzahlen; fehlende Werte nicht schaetzen.\nFuer Montag bis Sonntag: Thema, Plattform, Fahrer-Fokus, Hook, Beschreibung, Hashtags Instagram/TikTok, visuelle Idee, Memory-Bezug.'''
 return try_generate(key,prompt)
def save_weekly_plan(content):
 os.makedirs('content',exist_ok=True)
 with open('content/WOCHENPLAN.md','a',encoding='utf-8') as f:f.write(f'\n\n# Wochenplan vom {datetime.now():%Y-%m-%d %H:%M:%S}\n{content}\n')
if __name__=='__main__':save_weekly_plan(generate_weekly_plan())
