import os,re,time,requests
from datetime import datetime
from llm_client import global_professional_context
MODEL_LIST=['gemini-3.8-flash','gemini-3.7-flash','gemini-3.6-flash','gemini-3.5-flash','gemini-3.5-flash-lite']
def try_generate(key,prompt):
 prompt=f'GLOBALER VERBINDLICHER STANDARD:\n{global_professional_context()}\n\nAUFGABE:\n{prompt}';headers={'Content-Type':'application/json','X-goog-api-key':key};data={'contents':[{'parts':[{'text':prompt}]}]}
 for rnd in range(1,6):
  for model in MODEL_LIST:
   try:
    r=requests.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',headers=headers,json=data,timeout=120)
    if r.status_code==200:
     text=r.json()['candidates'][0]['content']['parts'][0]['text']
     for p in (r'AIza[0-9A-Za-z_\-]{35}',r'AQ\.[A-Za-z0-9_\-]{40,}',r'sk-[A-Za-z0-9]{20,}',r'\b[A-Za-z0-9_\-]{50,}\b'):text=re.sub(p,'[ENTFERNT]',text)
     return text.strip()
    if r.status_code in (401,403):raise RuntimeError(f'Gemini HTTP {r.status_code}')
    time.sleep(10)
   except RuntimeError:raise
   except Exception:time.sleep(10)
  if rnd<5:time.sleep(90)
 raise RuntimeError('Kein Gemini-Modell war nach mehreren Versuchen verfuegbar.')
def analyze_ride_with_me():
 key=os.environ.get('GEMINI_API_KEY')
 if not key:return 'FEHLER: Kein API-Key gefunden.'
 prompt='''Arbeite als Senior-Produkt-/Community-Analyst auf Premium-Niveau; mindestens zehn Jahre professionelle Erfahrung sind der Qualitaetsmassstab, keine zu behauptende Biografie. Analysiere nur oeffentlich belegte Informationen zur Motorrad-App Ride With Me (ridewithme.app und offizieller Play-Store-Eintrag). Trenne belegte App-Funktionen klar von allgemeinen Nutzerbeduerfnissen und eigenen Feature-Ideen. Erfinde keine Bewertungen, Nutzerzahlen, Trends oder Erfahrungen. Erstelle: 1) App-Zusammenfassung, 2) moegliche Nutzerbeduerfnisse, 3) Feature-Ideen, 4) Social-Media-Ideen fuer Instagram/Facebook/TikTok. Zielgruppe deutsch/tuerkische Motorradfahrer und Reisefreudige; natuerliches Deutsch, per Du, wenige Emojis, keine PR-/KI-Floskeln.'''
 return try_generate(key,prompt)
def save_ride_with_me_analysis(content):
 os.makedirs('ride-with-me',exist_ok=True);stamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S');entry=f'\n\n# Ride With Me Analyse vom {stamp}\n{content}\n'
 with open('ride-with-me/FEATURE_IDEAS.md','a',encoding='utf-8') as f:f.write(entry)
 with open('ride-with-me/USER_FEEDBACK.md','a',encoding='utf-8') as f:f.write('\n\n## Automatische Analyse\n'+content+'\n')
if __name__=='__main__':save_ride_with_me_analysis(analyze_ride_with_me())
