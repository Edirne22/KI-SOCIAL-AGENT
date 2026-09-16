"""MotoGP Content Agency – source-first, memory-aware, story-deduped, media-ready."""
from datetime import datetime, timezone
from pathlib import Path
import html,re,requests,json
from urllib.parse import urljoin,urlsplit,urlunsplit
from telegram_bot import send_message
from memory_engine import get_context
from generate_agnes_media import agnes_generate_image,save_bytes
from asset_paths import get_image_path,slugify
ROOT=Path('.');OUT=ROOT/'memory'/'MOTOGP_DAILY_CONTENT.md';ARCH=ROOT/'memory'/'MOTOGP_DAILY_ARCHIVE';NEXT=ROOT/'content'/'MOTOGP_ROSTER_NEXT.md';SESSION=ROOT/'memory'/'MOTOGP_APPROVAL_SESSION.md';STORY_MEMORY=ROOT/'memory'/'MOTOGP_STORY_MEMORY.md';PUBLISHED=ROOT/'content'/'PUBLISHED.md';UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT MotoGP research'};NEWS='https://www.motogp.com/en/news';MARKET='https://www.motogp.com/en/news/rider-market';SESSION_VERSION=3
def get(url):
 r=requests.get(url,headers=UA,timeout=30);r.raise_for_status();return r.text
def clean(s):
 s=html.unescape(re.sub(r'<[^>]+>',' ',s or ''));s=re.sub(r'\s+',' ',s).strip();s=re.sub(r'^\s*(?:-->|→|[-–—]+)\s*','',s);s=re.sub(r'\s+\d{1,2}\s+[A-Z][a-z]{2}\s+20\d{2}\s+By\s+motogp\.com.*$','',s,flags=re.I);return s.strip(' -–—|')
def canonical_url(url):
 try:
  p=urlsplit(url.strip());return urlunsplit((p.scheme.lower(),p.netloc.lower(),p.path.rstrip('/'),'',''))
 except Exception:return url.strip()
def story_key(title,url):
 m=re.search(r'/(\d{6,})(?:/)?$',canonical_url(url))
 if m:return 'motogp:'+m.group(1)
 words=re.findall(r'[a-z0-9]+',clean(title).casefold());stop={'the','a','an','to','for','and','of','in','on','at','with','from','is','are','confirmed'};return 'title:'+'-'.join(w for w in words if w not in stop)[:180]
def story_memory_text():
 chunks=[]
 for p in (STORY_MEMORY,SESSION,PUBLISHED):
  if p.exists():chunks.append(p.read_text(encoding='utf-8',errors='ignore'))
 return '\n'.join(chunks)
def known_story_keys():
 raw=story_memory_text();keys=set()
 for u in re.findall(r'https?://[^\s)]+',raw):
  u=u.rstrip('.,;`>')
  if 'motogp.com/' in u:keys.add(story_key('',u))
 for k in re.findall(r'(?m)^Story-Key:\s*(\S+)\s*$',raw):keys.add(k.strip())
 return keys
def remember_offered(items,now):
 existing=STORY_MEMORY.read_text(encoding='utf-8') if STORY_MEMORY.exists() else '# MotoGP Story Memory\n\n';keys=set(re.findall(r'(?m)^Story-Key:\s*(\S+)\s*$',existing));rows=[]
 for item in items:
  key=story_key(item['title'],item['url'])
  if key in keys:continue
  rows += [f'## {now:%Y-%m-%d %H:%M UTC} – ANGEBOTEN',f'Story-Key: {key}',f'Titel: {item["title"]}',f'Quelle: {canonical_url(item["url"])}',''];keys.add(key)
 if rows:STORY_MEMORY.parent.mkdir(parents=True,exist_ok=True);STORY_MEMORY.write_text(existing.rstrip()+'\n\n'+'\n'.join(rows).rstrip()+'\n',encoding='utf-8')
def meta(page,name):
 for p in [rf'<meta[^>]+(?:property|name)=["\']{re.escape(name)}["\'][^>]+content=["\']([^"\']+)',rf'<meta[^>]+content=["\']([^"\']+)["\'][^>]+(?:property|name)=["\']{re.escape(name)}["\']']:
  m=re.search(p,page,re.I|re.S)
  if m:return clean(m.group(1))
 return ''
def published_time(page):
 for name in ('article:published_time','date','datePublished','publish-date','pubdate'):
  v=meta(page,name)
  if v:return v
 m=re.search(r'"datePublished"\s*:\s*"([^"]+)"',page,re.I)
 if m:return html.unescape(m.group(1))
 m=re.search(r'<time[^>]+datetime=["\']([^"\']+)',page,re.I)
 return html.unescape(m.group(1)) if m else ''
def extract(page,limit=60):
 found=[];seen=set()
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  u=canonical_url(urljoin('https://www.motogp.com',href));t=clean(title)
  if len(t)<20 or '/news/' not in u or u in seen:continue
  seen.add(u);found.append((t,u))
  if len(found)>=limit:break
 return found
def roster_names():
 p=ROOT/'content'/'MOTOGP_ROSTER.md'
 if not p.exists():return []
 return [m.group(1).strip() for m in re.finditer(r'^-\s+#\d+\s+–\s+([^|\n]+)',p.read_text(encoding='utf-8'),re.M)]
def recent_history():
 p=ROOT/'memory'/'POST_HISTORY.md';return p.read_text(encoding='utf-8')[-8000:].casefold() if p.exists() else ''
def score(title,names):
 low=title.casefold();s=0
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
 pub=''
 try:
  page=get(url);title=meta(page,'og:title') or title;desc=meta(page,'description') or meta(page,'og:description');og=meta(page,'og:image');pub=published_time(page)
 except Exception:desc='';og=''
 return {'title':clean(title),'url':canonical_url(url),'summary':clean(desc)[:700],'preview':og,'published_at':pub}
def riders_in(text):
 known=['Toprak Razgatlioglu','Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira'];low=text.casefold();return [n for n in known if n.split()[-1].casefold() in low]
def hashtags(item):
 tags=['#MotoGP'];people=riders_in(item['title']+' '+item['summary'])
 for n in people[:2]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 low=(item['title']+' '+item['summary']).casefold()
 for k,v in [('ducati','#Ducati'),('aprilia','#Aprilia'),('yamaha','#YamahaRacing'),('ktm','#KTM'),('honda','#HondaRacing'),('misano','#SanMarinoGP')]:
  if k in low and v not in tags:tags.append(v)
 tags += ['#MotorradRacing','#MotoGPDeutschland'];return ' '.join(tags[:6])
