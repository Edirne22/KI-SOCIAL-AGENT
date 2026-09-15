"""Saisonaler MotoGP-Roster-Updater mit Web-Grounding, Crosscheck und Fail-closed."""
from __future__ import annotations
from datetime import datetime, timezone
import json, os, re, time
from pathlib import Path
from urllib.parse import urlparse
import requests
ROOT=Path('.');CONFIG=ROOT/'config'/'followed_accounts.md';ROSTER=ROOT/'content'/'MOTOGP_ROSTER.md';LOG=ROOT/'memory'/'MOTOGP_ROSTER_LOG.md'
MODELS=('gemini-3.8-flash','gemini-3.7-flash','gemini-3.6-flash','gemini-3.5-flash','gemini-3.5-flash-lite');BASE='https://generativelanguage.googleapis.com/v1beta/models'
def season_year():
 f=os.environ.get('MOTOGP_SEASON','').strip();return int(f) if f.isdigit() else datetime.now(timezone.utc).year
def existing_handles():
 if not CONFIG.exists():return {}
 out={}
 for line in CONFIG.read_text(encoding='utf-8').splitlines():
  m=re.match(r'-\s+([^\s|]+).*?–\s+(.+?)(?:\s+\(.*\))?$',line)
  if m:out[m.group(2).strip().casefold()]=m.group(1).strip()
 return out
def research(year,key):
 prompt=f'''Recherchiere die offiziell bestätigte MotoGP-Startaufstellung für die Saison {year} im öffentlichen Web. Bevorzuge motogp.com und prüfe zusätzlich mindestens eine zweite seriöse Motorsportquelle. Unterscheide Stammfahrer strikt von Gerüchten, Test- und Ersatzfahrern. Wenn die vollständige Aufstellung noch nicht offiziell feststeht, setze confirmed=false. Antworte NUR als valides JSON ohne Markdown: {{"season":{year},"confirmed":true,"teams":[{{"team":"Teamname","riders":[{{"name":"Fahrername","number":"93"}}]}}],"note":"kurz"}}. Erfinde nichts.'''
 payload={'contents':[{'parts':[{'text':prompt}]}],'tools':[{'google_search':{}}]};last='kein Modell'
 for rnd in range(3):
  for model in MODELS:
   try:
    r=requests.post(f'{BASE}/{model}:generateContent',headers={'Content-Type':'application/json','X-goog-api-key':key},json=payload,timeout=120)
    if r.status_code==200:
     c=r.json().get('candidates',[{}])[0];text=''.join(p.get('text','') for p in c.get('content',{}).get('parts',[])).strip();text=re.sub(r'^```(?:json)?\s*|\s*```$','',text,flags=re.I);return json.loads(text),c.get('groundingMetadata',{}).get('groundingChunks',[])
    last=f'{model}: HTTP {r.status_code}'
    if r.status_code in (401,403):raise RuntimeError(last)
    time.sleep(12 if r.status_code==429 else 5)
   except (requests.Timeout,requests.ConnectionError) as e:last=f'{model}: {type(e).__name__}';time.sleep(8)
  if rnd<2:time.sleep(45*(rnd+1))
 raise RuntimeError(f'Web-Grounding nach Retries nicht verfügbar ({last})')
def sources(chunks):
 out=[];seen=set()
 for c in chunks:
  w=c.get('web',{}) if isinstance(c,dict) else {};u=w.get('uri');t=w.get('title','Quelle')
  if u and u not in seen:seen.add(u);out.append((t,u))
 return out
def valid(data,src,year):
 if data.get('season')!=year or data.get('confirmed') is not True:return False,'Saison noch nicht vollständig bestätigt'
 teams=data.get('teams');
 if not isinstance(teams,list) or len(teams)<8:return False,'Roster unvollständig'
 riders=[r for t in teams for r in (t.get('riders') or []) if isinstance(r,dict) and r.get('name')]
 if len(riders)<18:return False,'Zu wenige bestätigte Fahrer'
 domains={urlparse(u).netloc.lower().removeprefix('www.') for _,u in src}
 if len(domains)<2:return False,'Crosscheck mit zweiter Domain fehlt'
 return True,'OK'
def render(data,src,handles):
 lines=[f'# MotoGP Roster {data["season"]}','',f'**Automatisch verifiziert:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}','','## Teams & Fahrer','']
 for team in data['teams']:
  lines.append(f'### {team["team"]}')
  for r in team.get('riders',[]):
   n=r['name'].strip();num=str(r.get('number','?')).strip();h=handles.get(n.casefold());lines.append(f'- #{num} – {n}'+(f' | Instagram: @{h}' if h else ' | Instagram: nicht automatisch verifiziert'))
  lines.append('')
 lines+=['## Quellen (Crosscheck)','']+[f'- {t}: {u}' for t,u in src]+['','## Regel','Diese Datei ist die zentrale saisonale Fahrer-/Teamquelle. Unbestätigte Transfers und Gerüchte werden nicht übernommen.',''];return '\n'.join(lines)
def log(status,year,detail):
 LOG.parent.mkdir(parents=True,exist_ok=True);old=LOG.read_text(encoding='utf-8') if LOG.exists() else '# MotoGP Roster Log\n';LOG.write_text(old.rstrip()+f'\n- {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} | Saison {year} | {status} | {detail}\n',encoding='utf-8')
def main():
 key=os.environ.get('GEMINI_API_KEY');year=season_year()
 if not key:raise RuntimeError('GEMINI_API_KEY fehlt')
 try:
  data,chunks=research(year,key);src=sources(chunks);ok,reason=valid(data,src,year)
  if not ok:log('NICHT AKTUALISIERT',year,reason);print(f'Roster bleibt unverändert: {reason}');return
  ROSTER.parent.mkdir(parents=True,exist_ok=True);ROSTER.write_text(render(data,src,existing_handles()),encoding='utf-8');log('AKTUALISIERT',year,f'{len(data["teams"])} Teams, {len(src)} Quellen');print(f'MotoGP-Roster {year} aktualisiert.')
 except Exception as e:log('FEHLER',year,f'{type(e).__name__}: {str(e)[:180]}');raise
if __name__=='__main__':main()
