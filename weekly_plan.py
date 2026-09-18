import os,re
from datetime import datetime
from memory_engine import get_context
from llm_client import global_professional_context
from llm_router import quick_chat

def read(path,max_chars=10000):
 try:
  with open(path,'r',encoding='utf-8') as f:return f.read()[-max_chars:]
 except FileNotFoundError:return ''

def generate_weekly_plan():
 roster=read('content/MOTOGP_ROSTER.md');history=read('memory/POST_HISTORY.md',7000);viral=read('memory/VIRAL_PATTERNS.md',5000);motogp_daily=read('memory/MOTOGP_DAILY_CONTENT.md',7000);learned=get_context(9000)
 raw_prompt=f'''Arbeite als Senior-Social-Media-Planer auf Premium-Niveau. Erstelle einen Content-Plan fuer die kommenden 7 Tage fuer Buelents deutsch-tuerkische Motorrad-Community. Mindestens zehn Jahre professionelle Planungserfahrung sind der Qualitaetsmassstab, keine zu behauptende Biografie.\nMEMORY:\n{learned}\nROSTER:\n{roster}\nRACING DAILY:\n{motogp_daily}\nPOST-HISTORY:\n{history}\nVIRAL-MUSTER:\n{viral}\nRegeln: Fakten/Quellen vor Reichweite; MotoGP-Fahrer/Teams nur aus verifizierten Quellen; aktuelle Racing-Themen aus der Daily Agency; Turkish Riders bei echtem Anlass priorisieren, nicht erzwingen; Ride With Me max. 1x/Woche; max. 6 relevante Hashtags; keine identischen Hooks; keine englischen Rohtexte oder Satz-fuer-Satz-Uebersetzung; keine erfundenen Transfers, Ergebnisse, Zitate, Trends oder Kennzahlen; fehlende Werte nicht schaetzen.\nFuer Montag bis Sonntag: Thema, Plattform, Fahrer-Fokus, Hook, Beschreibung, Hashtags Instagram/TikTok, visuelle Idee, Memory-Bezug.'''
 prompt=f'GLOBALER VERBINDLICHER STANDARD:\n{global_professional_context()}\n\nAUFGABE:\n{raw_prompt}'
 try:
  text=quick_chat(prompt,task_type="reasoning").strip()
  for pattern in (r'AIza[0-9A-Za-z_\-]{35}',r'AQ\.[A-Za-z0-9_\-]{40,}',r'sk-[A-Za-z0-9]{20,}',r'\b[A-Za-z0-9_\-]{50,}\b'):
   text=re.sub(pattern,'[ENTFERNT]',text)
  return text
 except RuntimeError as error:
  return f'FEHLER: {error}'

def save_weekly_plan(content):
 os.makedirs('content',exist_ok=True)
 with open('content/WOCHENPLAN.md','a',encoding='utf-8') as f:f.write(f'\n\n# Wochenplan vom {datetime.now():%Y-%m-%d %H:%M:%S}\n{content}\n')

if __name__=='__main__':save_weekly_plan(generate_weekly_plan())
