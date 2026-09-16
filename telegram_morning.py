"""Sendet nur freigabefaehige allgemeine Content-Ideen als Telegram-Anfrage.
Racing-News duerfen nicht mehr ueber diese schwachere Legacy-Kette freigegeben werden.
"""
from __future__ import annotations
import re,time
from datetime import datetime
from pathlib import Path
from telegram_bot import send_message
CONTENT_PLAN=Path('content/CONTENT_PLAN.md');SESSION_FILE=Path('memory/TELEGRAM_SESSION.md')
RACING_TERMS=('motogp','moto2','moto3','worldsbk','worldssp','superbike','supersport','marquez','bagnaia','acosta','quartararo','razgatlioglu','öncü','oncu','sofuoglu','sofuoğlu','misano','qualifying','pole','grid penalty','championship')
def _field(block,name):
 m=re.search(rf'(?m)^{re.escape(name)}:\s*(.+)$',block);return m.group(1).strip() if m else '–'
def _short_description(block):
 m=re.search(r'Instagram-Caption:\s*\n(.+?)(?=\n\n(?:Facebook-Post|TikTok-Skript|Visuelle Idee|Hashtags|Trend-Bezug|---)|\Z)',block,re.S);text=m.group(1).strip() if m else _field(block,'Thema');return re.sub(r'\s+',' ',text)[:280]
def _is_racing(block):
 low=block.casefold();return any(x.casefold() in low for x in RACING_TERMS)
def _has_source(block):
 src=_field(block,'Inspirations-Quelle');return src.startswith('http://') or src.startswith('https://')
def load_latest_posts():
 if not CONTENT_PLAN.is_file():raise FileNotFoundError(f'Content-Plan nicht gefunden: {CONTENT_PLAN}')
 content=CONTENT_PLAN.read_text(encoding='utf-8');matches=list(re.finditer(r'^--- BEITRAG\s+([1-3])\s+---\s*\n(.*?)(?=^--- BEITRAG\s+[1-3]\s+---|\Z)',content,re.M|re.S))
 if len(matches)<3:raise RuntimeError('Im CONTENT_PLAN.md wurden nicht drei vollständige Beiträge gefunden.')
 posts=[]
 for match in matches[-3:]:
  block=match.group(2).strip()
  # Hard separation: all Racing claims go through Racing V8.5+ and its full QM chain.
  if _is_racing(block):
   print('MORNING SKIP RACING:',_field(block,'Titel'));continue
  posts.append({'number':str(len(posts)+1),'title':_field(block,'Titel'),'hook':_field(block,'Hook'),'platform':_field(block,'Plattform'),'description':_short_description(block),'full_text':block,'source':_field(block,'Inspirations-Quelle')})
 return posts
def build_message(posts):
 lines=[f'Guten Morgen Bülent – hier sind deine {len(posts)} geprüften allgemeinen Content-Entwürfe:']
 for p in posts:lines += ['',f"{p['number']}. {p['title']}",f"Hook: {p['hook']}",f"Plattform: {p['platform']}",f"Kurz: {p['description']}"]
 lines += ['','Racing-News (MotoGP/Moto2/Moto3/WorldSBK/WorldSSP) werden ausschließlich über die Racing-Profi-QM freigegeben.','Antworte mit den Nummern, mit alle oder ✅ für alle, oder mit nein bzw. ❌ für keine Freigabe.','Eine Freigabe trägt Beiträge nur in PUBLISHED.md ein; veröffentlicht wird nichts automatisch.']
 return '\n'.join(lines)
def save_session(posts):
 SESSION_FILE.parent.mkdir(parents=True,exist_ok=True);now=datetime.now().strftime('%Y-%m-%d %H:%M:%S');timestamp=int(time.time());lines=['# Telegram-Freigabe-Sitzung','',f'Datum: {now}',f'Session-Timestamp: {timestamp}','Status: WARTET AUF ANTWORT','Scope: GENERAL-NON-RACING','']
 for p in posts:lines += [f"## Beitrag {p['number']}",f"Titel: {p['title']}",f"Hook: {p['hook']}",f"Plattform: {p['platform']}",f"Beschreibung: {p['description']}",f"Quelle: {p['source']}",'','### Vollständiger Entwurf',p['full_text'],'']
 SESSION_FILE.write_text('\n'.join(lines).rstrip()+'\n',encoding='utf-8')
def main():
 posts=load_latest_posts()
 if not posts:
  print('Keine allgemeinen Non-Racing-Beiträge zur Freigabe; Telegram wird nicht mit ungeprüften Racing-Entwürfen befüllt.');return
 send_message(build_message(posts));save_session(posts);print('Telegram-Freigabeanfrage erfolgreich gesendet.')
if __name__=='__main__':main()
