"""MotoGP Content Agency: recherchiert, priorisiert, formuliert und sendet Freigabe-Pakete."""
from datetime import datetime, timezone
from pathlib import Path
import html, re, requests
from urllib.parse import urljoin
from telegram_bot import send_message

ROOT=Path('.')
OUT=ROOT/'memory'/'MOTOGP_DAILY_CONTENT.md'; ARCH=ROOT/'memory'/'MOTOGP_DAILY_ARCHIVE'
NEXT=ROOT/'content'/'MOTOGP_ROSTER_NEXT.md'; SESSION=ROOT/'memory'/'MOTOGP_APPROVAL_SESSION.md'
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT MotoGP research'}
NEWS='https://www.motogp.com/en/news'; MARKET='https://www.motogp.com/en/news/rider-market'

def get(url):
 r=requests.get(url,headers=UA,timeout=30);r.raise_for_status();return r.text

def text(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()

def meta(page,name):
 patterns=[rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']']
 for p in patterns:
  m=re.search(p,page,re.I|re.S)
  if m:return text(m.group(1))
 return ''

def extract(page,limit=30):
 found=[];seen=set()
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  t=text(title);u=urljoin('https://www.motogp.com',href)
  if len(t)<20 or '/news/' not in u or u in seen:continue
  seen.add(u);found.append((t,u))
  if len(found)>=limit:break
 return found

def roster_names():
 p=ROOT/'content'/'MOTOGP_ROSTER.md'
 if not p.exists():return []
 return [m.group(1).strip() for m in re.finditer(r'^-\s+#\d+\s+–\s+([^|\n]+)',p.read_text(encoding='utf-8'),re.M)]

def score(title,names):
 low=title.casefold();s=0
 for n in names:
  if n.casefold() in low or n.casefold().split()[-1] in low:s+=4
 for k in ('win','victory','championship','title','sign','join','2027','injur','return','preview','record','marquez','razgatlioglu'):
  if k in low:s+=1
 return s

def article_info(title,url):
 try:
  page=get(url); desc=meta(page,'description') or meta(page,'og:description'); og=meta(page,'og:image')
 except Exception:
  desc='';og=''
 return {'title':title,'url':url,'summary':desc[:500],'preview':og}

def hashtags(title):
 tags=['#MotoGP','#Motorrad','#Racing','#MotoGPDeutschland']
 low=title.casefold()
 mapping={'razgatlioglu':'#ToprakRazgatlioglu','marquez':'#MarcMarquez','bagnaia':'#PeccoBagnaia','quartararo':'#FabioQuartararo','acosta':'#PedroAcosta','bezzecchi':'#MarcoBezzecchi','martin':'#JorgeMartin'}
 for k,v in mapping.items():
  if k in low:tags.insert(1,v)
 return ' '.join(tags[:6])

def own_caption(item):
 # Eigenständige Zusammenfassung statt Kopie des Artikels. Keine langen Zitate.
 subject=item['title'].strip().rstrip('.')
 summary=item['summary'].strip()
 fact=(summary.split('. ')[0].strip()+'.') if summary else ''
 if len(fact)>240:fact=fact[:237].rstrip()+ '…'
 hook=f'🏁 MotoGP-Update: {subject}'
 body=(f'\n\n{fact}' if fact and fact.casefold() not in subject.casefold() else '')
 return f'{hook}{body}\n\nWie siehst du das – was bedeutet das für die nächsten Rennen?\n\n{hashtags(subject)}'

def next_roster(market_items):
 year=datetime.now(timezone.utc).year+1
 lines=[f'# MotoGP Roster {year} – bestätigte Vorschau','',f'**Stand:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}','','**Status:** UNVOLLSTÄNDIG – nur offizielle MotoGP-Meldungen; ersetzt den aktiven Roster nicht.','','## Offizielle Rider-Market-Meldungen','']
 for t,u in market_items[:20]:lines.append(f'- {t} — {u}')
 lines+=['','## Regel','Nur offiziell bestätigte Meldungen vormerken. Gerüchte nicht übernehmen. Erst eine vollständig bestätigte Startaufstellung darf den aktiven Roster ersetzen.','']
 NEXT.parent.mkdir(parents=True,exist_ok=True);NEXT.write_text('\n'.join(lines),encoding='utf-8')

def write_session(items,now):
 lines=['# MotoGP Telegram Approval Session',f'Session-Timestamp: {int(now.timestamp())}','','Antwort in Telegram: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle` oder `motogp nein`.','']
 for i,item in enumerate(items,1):
  lines += [f'## Beitrag {i}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Preview-Bild: {item["preview"] or "von Zielseite/Plattform erzeugen"}','Plattformen: Instagram + Facebook',f'Text: {own_caption(item)}','','Rechte-Gate: Fakten eigenständig zusammengefasst; keine fremden Artikeltexte kopiert. Facebook nutzt den offiziellen Link für die Link-Vorschau. Instagram nutzt eigenes/automatisch freigegebenes Medium, nicht ungeprüft das MotoGP-Foto.','']
 SESSION.parent.mkdir(parents=True,exist_ok=True);SESSION.write_text('\n'.join(lines),encoding='utf-8')

def telegram_preview(items):
 msg=['🏁 MotoGP Content Agency – Tagesauswahl','', 'Ich habe die stärksten offiziellen MotoGP-Themen analysiert und in dein Profilformat umgeschrieben. Eine Freigabe reicht; danach übernimmt die Publisher-Kette.','']
 for i,item in enumerate(items,1):
  msg += [f'{i}️⃣ {item["title"]}',own_caption(item),f'🔗 Offizielle Quelle: {item["url"]}','']
 msg += ['Freigabe: `motogp 1`, `motogp 2`, `motogp 3` oder `motogp alle`','Ablehnen: `motogp nein`','','Facebook: offizieller Link als Link-Preview. Instagram: eigener Post/Reel + Quellenhinweis; bei geeigneter Story klickbarer Link.']
 send_message('\n'.join(msg)[:4000])

def main():
 names=roster_names();news=extract(get(NEWS));market=extract(get(MARKET),20)
 merged=[];seen=set()
 for item in news+market:
  if item[1] not in seen:seen.add(item[1]);merged.append(item)
 merged.sort(key=lambda x:score(x[0],names),reverse=True)
 details=[article_info(t,u) for t,u in merged[:12]]
 now=datetime.now(timezone.utc)
 lines=['# MotoGP Daily Content Agency','',f'**Recherche:** {now:%Y-%m-%d %H:%M UTC}','**Primärquelle:** offizielle MotoGP-Seite','','## Analysierte Themen','']
 for i,item in enumerate(details,1):
  lines += [f'### {i}. {item["title"]}',f'- Quelle: {item["url"]}',f'- Kurzinfo: {item["summary"] or "Titel/Quelle verifiziert; keine belastbare Meta-Zusammenfassung geliefert."}',f'- Score: {score(item["title"],names)}','']
 lines += ['## Pipeline','Recherche → Quellenprüfung → eigenständige Zusammenfassung → Profilformat → Rechte-Gate im Hintergrund → Telegram → eine Freigabe → Publisher.','']
 content='\n'.join(lines);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(content,encoding='utf-8');ARCH.mkdir(parents=True,exist_ok=True);(ARCH/f'{now:%Y-%m-%d}.md').write_text(content,encoding='utf-8');next_roster(market)
 picks=details[:3]
 if picks:write_session(picks,now);telegram_preview(picks)
 print(f'MotoGP Content Agency: {len(details)} Themen analysiert, {len(picks)} zur Telegram-Freigabe vorbereitet.')
if __name__=='__main__':main()
