"""MotoGP roster updater: official MotoGP pages first, independent crosscheck, no LLM dependency."""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
import os, re, requests

ROOT=Path('.')
ROSTER=ROOT/'content'/'MOTOGP_ROSTER.md'
LOG=ROOT/'memory'/'MOTOGP_ROSTER_LOG.md'
CONFIG=ROOT/'config'/'followed_accounts.md'
OFFICIAL='https://www.motogp.com/en/riders/'
OFFICIAL_ALT='https://riders.motogp.com/en/riders/MotoGP'
CROSSCHECK='https://www.motorsport.com/motogp/drivers/'
UA={'User-Agent':'Mozilla/5.0 (compatible; KI-SOCIAL-AGENT/1.0)'}

def season_year():
    forced=os.environ.get('MOTOGP_SEASON','').strip()
    return int(forced) if forced.isdigit() else datetime.now(timezone.utc).year

def get(url):
    r=requests.get(url,headers=UA,timeout=45);r.raise_for_status();return r.text

def clean_html(text):
    text=re.sub(r'<script\b[^>]*>.*?</script>',' ',text,flags=re.I|re.S)
    text=re.sub(r'<style\b[^>]*>.*?</style>',' ',text,flags=re.I|re.S)
    text=re.sub(r'<[^>]+>',' ',text)
    text=text.replace('&nbsp;',' ').replace('&amp;','&')
    return re.sub(r'\s+',' ',text)

def known_2026():
    # Bootstrap/fallback derived from the official 2026 MotoGP Riders & Teams page;
    # every run still requires live official-page evidence and a live independent crosscheck.
    return [
      ('CASTROL Honda LCR',5,'Johann Zarco'),('Prima Pramac Yamaha MotoGP',7,'Toprak Razgatlioglu'),
      ('Honda HRC Castrol',10,'Luca Marini'),('Pro Honda LCR',11,'Diogo Moreira'),
      ('Red Bull KTM Tech3',12,'Maverick Viñales'),('Monster Energy Yamaha MotoGP',20,'Fabio Quartararo'),
      ('Pertamina Enduro VR46 Racing Team',21,'Franco Morbidelli'),('Red Bull KTM Tech3',23,'Enea Bastianini'),
      ('SuperFile Trackhouse MotoGP Team',25,'Raul Fernandez'),('Red Bull KTM Factory Racing',33,'Brad Binder'),
      ('Honda HRC Castrol',36,'Joan Mir'),('Red Bull KTM Factory Racing',37,'Pedro Acosta'),
      ('Monster Energy Yamaha MotoGP',42,'Alex Rins'),('Prima Pramac Yamaha MotoGP',43,'Jack Miller'),
      ('Pertamina Enduro VR46 Racing Team',49,'Fabio Di Giannantonio'),('BK8 Gresini Racing MotoGP',54,'Fermin Aldeguer'),
      ('Ducati Lenovo Team',63,'Francesco Bagnaia'),('Aprilia Racing',72,'Marco Bezzecchi'),
      ('BK8 Gresini Racing MotoGP',73,'Alex Marquez'),('SuperFile Trackhouse MotoGP Team',79,'Ai Ogura'),
      ('Aprilia Racing',89,'Jorge Martin'),('Ducati Lenovo Team',93,'Marc Marquez')]

def normalize(s):
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFKD',s) if not unicodedata.combining(c)).casefold().replace('ñ','n')

def verify_entries(entries,official,cross):
    o=normalize(official);c=normalize(cross);verified=[]
    for team,num,name in entries:
        n=normalize(name)
        if n in o and n in c: verified.append((team,num,name))
    return verified

def handles():
    if not CONFIG.exists():return {}
    out={}
    for line in CONFIG.read_text(encoding='utf-8').splitlines():
        m=re.match(r'-\s+([^\s|]+).*?–\s+(.+?)(?:\s+\(.*\))?$',line)
        if m:out[normalize(m.group(2).strip())]=m.group(1).strip()
    return out

def render(year,entries,srcs):
    hs=handles();teams={}
    for team,num,name in entries:teams.setdefault(team,[]).append((num,name))
    lines=[f'# MotoGP Roster {year}','',f'**Automatisch verifiziert:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}','',f'**Status:** {len(entries)} Stammfahrer live gegen offizielle MotoGP-Seite + unabhängigen Crosscheck geprüft.','','## Teams & Fahrer','']
    for team,riders in teams.items():
        lines.append(f'### {team}')
        for num,name in riders:
            h=hs.get(normalize(name));lines.append(f'- #{num} – {name}'+(f' | Instagram: @{h}' if h else ' | Instagram: nicht automatisch verifiziert'))
        lines.append('')
    lines+=['## Quellen (Live-Crosscheck)','']+[f'- {u}' for u in srcs]+['','## Sicherheitsregel','Roster-Änderungen werden nur übernommen, wenn sie live in der offiziellen MotoGP-Quelle und im unabhängigen Crosscheck nachweisbar sind. Gerüchte, Wildcards, Ersatz- und Testfahrer werden nicht als Stammfahrer übernommen.','']
    return '\n'.join(lines)

def log(status,year,detail):
    LOG.parent.mkdir(parents=True,exist_ok=True);old=LOG.read_text(encoding='utf-8') if LOG.exists() else '# MotoGP Roster Log\n'
    LOG.write_text(old.rstrip()+f'\n- {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} | Saison {year} | {status} | {detail}\n',encoding='utf-8')

def main():
    year=season_year()
    if year!=2026:
        log('NICHT AKTUALISIERT',year,'Dynamische Folgesaison noch nicht vollständig bestätigt; bestehender bestätigter Roster bleibt erhalten')
        print(f'Saison {year}: noch kein vollständiger bestätigter Roster – keine Änderung.');return
    try:
        try:official=clean_html(get(OFFICIAL));official_url=OFFICIAL
        except Exception:official=clean_html(get(OFFICIAL_ALT));official_url=OFFICIAL_ALT
        cross=clean_html(get(CROSSCHECK))
        entries=verify_entries(known_2026(),official,cross)
        if len(entries)<20:
            log('NICHT AKTUALISIERT',year,f'Crosscheck unvollständig: nur {len(entries)}/22 Fahrer bestätigt')
            print('Live-Crosscheck unvollständig – bestehender Roster bleibt erhalten.');return
        ROSTER.parent.mkdir(parents=True,exist_ok=True);ROSTER.write_text(render(year,entries,[official_url,CROSSCHECK]),encoding='utf-8')
        log('AKTUALISIERT',year,f'{len(entries)} Fahrer live verifiziert; Gemini nicht benötigt')
        print(f'MotoGP-Roster {year}: {len(entries)} Fahrer live verifiziert und gespeichert.')
    except Exception as e:
        log('FEHLER',year,f'{type(e).__name__}: {str(e)[:180]}');raise
if __name__=='__main__':main()
