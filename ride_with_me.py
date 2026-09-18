import os,re
from datetime import datetime
from llm_client import global_professional_context
from llm_router import quick_chat

def analyze_ride_with_me():
 raw_prompt='''Arbeite als Senior-Produkt-/Community-Analyst auf Premium-Niveau; mindestens zehn Jahre professionelle Erfahrung sind der Qualitaetsmassstab, keine zu behauptende Biografie. Analysiere nur oeffentlich belegte Informationen zur Motorrad-App Ride With Me (ridewithme.app und offizieller Play-Store-Eintrag). Trenne belegte App-Funktionen klar von allgemeinen Nutzerbeduerfnissen und eigenen Feature-Ideen. Erfinde keine Bewertungen, Nutzerzahlen, Trends oder Erfahrungen. Erstelle: 1) App-Zusammenfassung, 2) moegliche Nutzerbeduerfnisse, 3) Feature-Ideen, 4) Social-Media-Ideen fuer Instagram/Facebook/TikTok. Zielgruppe deutsch/tuerkische Motorradfahrer und Reisefreudige; natuerliches Deutsch, per Du, wenige Emojis, keine PR-/KI-Floskeln.'''
 prompt=f'GLOBALER VERBINDLICHER STANDARD:\n{global_professional_context()}\n\nAUFGABE:\n{raw_prompt}'
 try:
  text=quick_chat(prompt,task_type="reasoning").strip()
  for p in (r'AIza[0-9A-Za-z_\-]{35}',r'AQ\.[A-Za-z0-9_\-]{40,}',r'sk-[A-Za-z0-9]{20,}',r'\b[A-Za-z0-9_\-]{50,}\b'):
   text=re.sub(p,'[ENTFERNT]',text)
  return text
 except RuntimeError as error:
  return f'FEHLER: {error}'

def save_ride_with_me_analysis(content):
 os.makedirs('ride-with-me',exist_ok=True);stamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S');entry=f'\n\n# Ride With Me Analyse vom {stamp}\n{content}\n'
 with open('ride-with-me/FEATURE_IDEAS.md','a',encoding='utf-8') as f:f.write(entry)
 with open('ride-with-me/USER_FEEDBACK.md','a',encoding='utf-8') as f:f.write('\n\n## Automatische Analyse\n'+content+'\n')

if __name__=='__main__':save_ride_with_me_analysis(analyze_ride_with_me())
