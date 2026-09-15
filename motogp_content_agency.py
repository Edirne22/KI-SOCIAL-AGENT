"""MotoGP Content Agency – source-first, memory-aware, media-ready before Telegram approval."""
from datetime import datetime, timezone
from pathlib import Path
import html, re, requests
from urllib.parse import urljoin
from telegram_bot import send_message
from memory_engine import get_context
from generate_agnes_media import agnes_generate_image, save_bytes
from asset_paths import get_image_path, slugify

ROOT=Path('.')
OUT=ROOT/'memory'/'MOTOGP_DAILY_CONTENT.md'; ARCH=ROOT/'memory'/'MOTOGP_DAILY_ARCHIVE'
NEXT=ROOT/'content'/'MOTOGP_ROSTER_NEXT.md'; SESSION=ROOT/'memory'/'MOTOGP_APPROVAL_SESSION.md'
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT MotoGP research'}
NEWS='https://www.motogp.com/en/news'; MARKET='https://www.motogp.com/en/news/rider-market'
SESSION_VERSION=2

def get(url):
 r=requests.get(url,headers=UA,timeout=30); r.raise_for_status(); return r.text

def clean(s):
 s=html.unescape(re.sub(r'<[^>]+>',' ',s or '')); s=re.sub(r'\s+',' ',s).strip()
 s=re.sub(r'^\s*(?:-->|→|[-–—]+)\s*','',s)
 s=re.sub(r'\s+\d{1,2}\s+[A-Z][a-z]{2}\s+20\d{2}\s+By\s+motogp\.com.*$','',s,flags=re.I)
 return s.strip(' -–—|')

def meta(page,name):
 for p in [rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']']:
  m=re.search(p,page,re.I|re.S)
  if m:return clean(m.group(1))
 return ''

def extract(page,limit=30):
 found=[]; seen=set()
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  u=urljoin('https://www.motogp.com',href); t=clean(title)
  if len(t)<20 or '/news/' not in u or u in seen:continue
  seen.add(u); found.append((t,u))
  if len(found)>=limit:break
 return found

def roster_names():
 p=ROOT/'content'/'MOTOGP_ROSTER.md'
 if not p.exists():return []
 return [m.group(1).strip() for m in re.finditer(r'^-\s+#\d+\s+–\s+([^|\n]+)',p.read_text(encoding='utf-8'),re.M)]

def recent_history():
 p=ROOT/'memory'/'POST_HISTORY.md'; return p.read_text(encoding='utf-8')[-8000:].casefold() if p.exists() else ''

def score(title,names):
 low=title.casefold(); s=0
 for n in names:
  if n.casefold() in low or n.casefold().split()[-1] in low:s+=4
 for k in ('win','victory','championship','title','sign','join','2027','injur','return','preview','record','marquez','razgatlioglu'):
  if k in low:s+=1
 hist=recent_history()
 for n in names:
  surname=n.casefold().split()[-1]
  if surname in low:s-=min(4,hist.count(surname)//2)
 return s

def article_info(title,url):
 try:
  page=get(url); title=meta(page,'og:title') or title; desc=meta(page,'description') or meta(page,'og:description'); og=meta(page,'og:image')
 except Exception: desc=''; og=''
 return {'title':clean(title),'url':url,'summary':clean(desc)[:500],'preview':og}

def riders_in(text):
 known=['Toprak Razgatlioglu','Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira']
 low=text.casefold(); return [n for n in known if n.split()[-1].casefold() in low]

def hashtags(item):
 tags=['#MotoGP']; people=riders_in(item['title']+' '+item['summary'])
 for n in people[:2]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 low=(item['title']+' '+item['summary']).casefold()
 for k,v in [('ducati','#Ducati'),('aprilia','#Aprilia'),('yamaha','#YamahaRacing'),('ktm','#KTM'),('honda','#HondaRacing'),('misano','#SanMarinoGP')]:
  if k in low and v not in tags:tags.append(v)
 tags += ['#MotorradRacing','#MotoGPDeutschland']; return ' '.join(tags[:6])

def german_story(item):
 t=item['title']; d=item['summary']; low=(t+' '+d).casefold(); people=riders_in(t+' '+d); p=people[0] if people else 'MotoGP'
 if 'acosta' in low and 'ducati' in low and ('2027' in low or 'join' in low):
  return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team. Damit bekommt Marc Márquez einen der stärksten jungen Fahrer im Feld als Teamkollegen.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Acosta neben Márquez – wie schätzt du diese Kombination sportlich ein?')
 if 'marquez' in low and ('title race lead' in low or 'championship' in low or 'victory' in low):
  return ('Marc Márquez hat in Misano maximal profitiert und sich mit dem Sieg wieder ganz nach vorne im Titelkampf geschoben. Der frühe Fehler von Marco Bezzecchi hat das Rennen entscheidend verändert.','🏁 Márquez schlägt zurück – der Titelkampf ist wieder völlig offen.','Wer hat für dich jetzt die besseren Karten im Titelkampf?')
 if 'bezzecchi' in low and ('pole' in low or 'lap record' in low or 'sub 90' in low):
  return ('Marco Bezzecchi hat in Misano mit einer extrem schnellen Runde die Pole geholt und Marc Márquez hinter sich gelassen.','⏱️ Bezzecchi setzt in Misano ein richtig starkes Zeichen.','Wer ist für dich aktuell über eine schnelle Runde stärker: Bezzecchi oder Márquez?')
 if 'confirmed' in low or 'join' in low or 'sign' in low:
  return (f'Rund um {p} gibt es eine offiziell bestätigte Personalentscheidung. Für uns zählen dabei nur die bestätigten Fakten der MotoGP-Quelle – keine Transfergerüchte.',f'🔄 Offiziell bestätigt: Bewegung rund um {p}.','Wie bewertest du diesen Wechsel sportlich?')
 if 'win' in low or 'victory' in low:
  return (f'{p} steht im Mittelpunkt des aktuellen MotoGP-Ergebnisses. Für die Einordnung verwenden wir ausschließlich bestätigte Angaben der offiziellen MotoGP-Quelle.',f'🏁 {p} liefert – und setzt damit ein sportliches Zeichen.','Was war für dich der entscheidende Moment?')
 return (f'{p} ist heute eines der relevanten MotoGP-Themen. Die Fakten stammen aus der offiziellen Meldung; der Social-Text wird bewusst eigenständig formuliert.',f'🏍️ MotoGP im Fokus: {p}.','Was ist für dich der spannendste Punkt an dieser Story?')

def own_caption(item):
 fact,hook,question=german_story(item); return f'{hook}\n\n{fact}\n\n{question}\n\n{hashtags(item)}'

def quality_ok(caption):
 bad=('-->','By motogp.com','MotoGP-Update:')
 if any(x.casefold() in caption.casefold() for x in bad):return False
 if re.search(r'\b(the|following|confirmed|joins|championship leader|lap record set)\b',caption,re.I):return False
 return True

def prepare_instagram_media(item,index):
 """Erzeugt VOR Telegram eine eigene neutrale Editorial-Grafik ohne reale Fahrer/Teams/Logos."""
 caption=own_caption(item)
 filename=get_image_path(slugify(f'motogp-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1)
 prompt=(
  'Vertical 4:5 premium motorsport editorial social-media background. '
  'Empty modern European motorcycle racing circuit at dramatic golden hour, asphalt, curbs, grandstands and speed atmosphere. '
  'NO people, NO riders, NO motorcycles, NO helmets, NO team colors, NO manufacturer branding, NO sponsor logos, NO trademarks, NO readable text, NO watermark. '
  'Original generic racing visual, photorealistic, high-end sports magazine photography, ample clean composition for a news post. '
  f'Editorial mood derived from this topic only, without depicting named persons or brands: {caption[:220]}'
 )
 data=agnes_generate_image(prompt)
 if not data:
  print(f'MEDIA-GATE: Beitrag {index} gesperrt – keine Instagram-Grafik erzeugt.')
  return ''
 save_bytes(data,filename)
 print(f'MEDIA-GATE: Beitrag {index} Instagram-Medium vorbereitet: {filename}')
 return filename.as_posix()

def next_roster(market_items):
 year=datetime.now(timezone.utc).year+1
 lines=[f'# MotoGP Roster {year} – bestätigte Vorschau','',f'**Stand:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}','','**Status:** UNVOLLSTÄNDIG – nur offizielle MotoGP-Meldungen; ersetzt den aktiven Roster nicht.','','## Offizielle Rider-Market-Meldungen','']
 for t,u in market_items[:20]:lines.append(f'- {clean(t)} — {u}')
 lines+=['','## Regel','Nur offiziell bestätigte Meldungen vormerken. Gerüchte nicht übernehmen. Erst eine vollständig bestätigte Startaufstellung darf den aktiven Roster ersetzen.','']
 NEXT.parent.mkdir(parents=True,exist_ok=True); NEXT.write_text('\n'.join(lines),encoding='utf-8')

def write_session(items,now):
 lines=['# MotoGP Telegram Approval Session',f'Session-Version: {SESSION_VERSION}',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle` oder `motogp nein`.','']
 for i,item in enumerate(items,1):
  caption=own_caption(item)
  lines += [f'## Beitrag {i}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Instagram-Bild: {item["instagram_media"]}',f'Quellen-Preview: {item["preview"] or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{caption}','','Rechte-Gate: Instagram nutzt eine vor Freigabe eigens erzeugte generische Editorial-Grafik ohne reale Fahrer, Motorräder, Teams, Logos oder Marken. Facebook veröffentlicht den offiziellen Quellenlink für die Link-Vorschau. Keine langen Originalpassagen.','']
 SESSION.parent.mkdir(parents=True,exist_ok=True); SESSION.write_text('\n'.join(lines),encoding='utf-8')

def telegram_preview(items):
 msg=['🏁 MotoGP Content Agency – Tagesauswahl','','3 fertig redigierte Vorschläge. Instagram-Medium bereits vorbereitet; Facebook nutzt die offizielle Link-Vorschau.','']
 for i,item in enumerate(items,1):msg += [f'{i}️⃣ {own_caption(item)}','🖼️ Instagram-Medium: vorbereitet',f'🔗 Quelle: {item["url"]}','']
 msg += ['Freigabe: motogp 1 / motogp 2 / motogp 3 / motogp alle','Ablehnen: motogp nein']; send_message('\n'.join(msg)[:4000])

def main():
 learned=get_context(9000); names=roster_names(); news=extract(get(NEWS)); market=extract(get(MARKET),20); merged=[]; seen=set()
 for item in news+market:
  if item[1] not in seen:seen.add(item[1]); merged.append(item)
 merged.sort(key=lambda x:score(x[0],names),reverse=True); details=[article_info(t,u) for t,u in merged[:12]]; now=datetime.now(timezone.utc)
 lines=['# MotoGP Daily Content Agency','',f'**Recherche:** {now:%Y-%m-%d %H:%M UTC}','**Primärquelle:** offizielle MotoGP-Seite','**Closed-Loop Memory:** aktiv','**Media-Gate:** Instagram-Medium muss vor Telegram vorhanden sein','','## Analysierte Themen','']
 for i,item in enumerate(details,1):lines += [f'### {i}. {item["title"]}',f'- Quelle: {item["url"]}',f'- Quellen-Metadaten: {item["summary"] or "keine belastbare Meta-Zusammenfassung"}',f'- Score inkl. Fahrerrotation: {score(item["title"],names)}','']
 lines += ['## Aktiver Memory-Kontext',learned[:3000],'','## Redaktion','Quellendaten werden nicht als Caption übernommen. Vor Telegram: Faktenkern → vollständig neu auf Deutsch → Hook/Frage → Hashtags → eigene neutrale Instagram-Grafik erzeugen → Media-Gate → Telegram. Facebook erhält den offiziellen Quellenlink.','']
 content='\n'.join(lines); OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(content,encoding='utf-8'); ARCH.mkdir(parents=True,exist_ok=True); (ARCH/f'{now:%Y-%m-%d}.md').write_text(content,encoding='utf-8'); next_roster(market)
 candidates=[item for item in details if quality_ok(own_caption(item))]
 picks=[]
 for item in candidates:
  media=prepare_instagram_media(item,len(picks)+1)
  if not media:continue
  item['instagram_media']=media; picks.append(item)
  if len(picks)==3:break
 if len(picks)==3:
  write_session(picks,now); telegram_preview(picks)
 else:
  print(f'MEDIA-GATE: Nur {len(picks)}/3 Pakete medienreif. Keine unvollständige Telegram-Auswahl gesendet.')
 print(f'MotoGP Content Agency: {len(details)} Themen analysiert, {len(picks)} vollständig medienreif vorbereitet.')
if __name__=='__main__':main()
