"""Agent 16 / Racing Scout: official MotoGP-, Moto2-, Moto3-, WorldSBK- and WorldSSP sources – V8.5.4."""
import re,requests,html,unicodedata
from turkish_rider_names import CANONICAL_ALIASES, RIDER_CONTEXT, canonical_rider
from turkish_rider_memory import remember_verified, remember_candidate
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT Motorcycle Racing Agency'}
# Specific class feeds MUST run before generic umbrella feeds. racing_scout de-duplicates by URL,
# therefore this order is the deterministic class lock for articles exposed on several pages.
SOURCES=[
 ('Moto2','https://www.motogp.com/en/news/Moto2'),
 ('Moto3','https://www.motogp.com/en/news/Moto3'),
 ('MotoGP','https://www.motogp.com/en/news'),
 ('WorldSSP','https://www.worldsbk.com/en/news/ssp'),
 ('WorldSBK','https://www.worldsbk.com/en/news')]
WATCHLIST=CANONICAL_ALIASES
RIDER_SOURCES=RIDER_CONTEXT
# Turkish specialist media are daily discovery sources for ALL registered riders.
# They may nominate T1-T5 candidates, but are not promoted to primary fact authority.
TURKISH_MEDIA_SOURCES=(
 ('MotoEtkinlikcom','https://www.instagram.com/motoetkinlikcom/'),
 ('MotoEtkinlikRacing','https://www.instagram.com/motoetkinlikracing/'),
 ('TurkiyeSBK','https://www.instagram.com/turkiyesbk/'),
)
FALLBACK=[
 ('Toprak Razgatlıoğlu','Toprak Razgatlioglu – MotoGP rider profile and 2026 rookie campaign','https://www.motogp.com/en/riders/toprak-razgatlioglu/c883a3b8-17ce-419d-b71b-32c252f6fc7e','MotoGP'),
 ('Can Öncü','Can Oncu takes first 2026 WorldSSP win in Race 1 comeback from P13','https://www.worldsbk.com/en/news/2026/09/14/oncu-takes-first-2026-worldssp-win-in-race-1-comeback-from-p13-im-happy-that-the-hard-work-paid-off/1089992','WorldSSP'),
 ('Bahattin Sofuoğlu','Bahattin Sofuoglu – WorldSSP 2026 rider profile','https://www.worldsbk.com/en/riders/bahattin-sofuoglu/8467','WorldSSP')]
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def fold(s):
 s=unicodedata.normalize('NFKD',(s or '').casefold()).replace('ı','i')
 return ''.join(ch for ch in s if not unicodedata.combining(ch)).replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_for(text,series=''):
 low=fold(text);canonical=canonical_rider(text)
 if canonical:return canonical
 context=fold((series or '')+' '+text)
 # Official headlines often use only a surname. Resolve it only where the
 # championship context makes the identity deterministic.
 if re.search(r'(?<![a-z])razgatlioglu(?![a-z])',low):return 'Toprak Razgatlıoğlu'
 if re.search(r'(?<![a-z])oncu(?![a-z])',low):
  if any(k in context for k in ('worldssp','supersport','wssp')):return 'Can Öncü'
  if any(k in context for k in ('moto2','moto3')):return 'Deniz Öncü'
 if re.search(r'(?<![a-z])sofuoglu(?![a-z])|(?<![a-z])sofouglu(?![a-z])',low):
  if any(k in context for k in ('zayn','r3 blu cru','r3 world cup')):return 'Zayn Sofuoğlu'
  if any(k in context for k in ('bahattin','smits','motoxracing','qjmotor','worldssp','worldsbk')):return 'Bahattin Sofuoğlu'
 return ''
def classify_series(default_series,title,url):
 text=fold((title or '')+' '+(url or ''))
 if 'worldspb' in text or 'sportbike world championship' in text:return 'WorldSPB'
 if re.search(r'(?<![a-z0-9])moto4(?![a-z0-9])',text):return 'Moto4'
 if 'worldssp300' in text or 'worldssp 300' in text or 'wssp300' in text:return 'WorldSSP300'
 if re.search(r'\b(to|into|joins?|move[sd]? to|challenge in)\s+(the\s+)?worldsbk\b',text) or 'new challenge in worldsbk' in text:return 'WorldSBK'
 if re.search(r'\b(to|into|joins?|move[sd]? to|seat for)\s+(the\s+)?motogp\b',text) or 'motogp seat' in text:return 'MotoGP'
 if 'worldssp' in text or 'world supersport' in text or 'supersport' in text or 'wssp' in text:return 'WorldSSP'
 if re.search(r'(?<![a-z0-9])moto3(?![a-z0-9])',text):return 'Moto3'
 if re.search(r'(?<![a-z0-9])moto2(?![a-z0-9])',text):return 'Moto2'
 if re.search(r'(?<![a-z0-9])motogp(?![a-z0-9])',text):return 'MotoGP'
 return default_series
def _anchors(series,base,limit):
 out=[];seen=set()
 try:r=requests.get(base,headers=UA,timeout=30);r.raise_for_status();page=r.text
 except Exception as e:
  print(f'RACING SCOUT SOURCE FAIL {series}: {type(e).__name__}: {str(e)[:120]}');return out
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  t=clean(title);u=urljoin(base,href)
  if len(t)<20 or u in seen or not ('/news/' in u.lower() or '/haberler/' in u.lower()):continue
  seen.add(u);out.append((t,u,classify_series(series,t,u),rider_for(t+' '+u,series)))
  if len(out)>=limit:break
 return out
def racing_scout(limit_per_source=50):
 out=[];seen=set()
 for series,base in SOURCES:
  rows=_anchors(series,base,limit_per_source)
  print(f'RACING SCOUT {series}: {len(rows)} candidates')
  for row in rows:
   if row[1] in seen:continue
   seen.add(row[1]);out.append(row)
 return out
def rider_centered_scout(limit_per_source=120):
 """Search each registered rider's official sources instead of relying on umbrella feeds.

 The returned candidates are still re-fetched by article_info(), so titles found here are
 discovery hints only. Freshness is decided later from the source article date.
 """
 out=[];seen=set()
 for rider,ctx in RIDER_SOURCES.items():
  series=str(ctx.get('series') or '')
  for base in ctx.get('official_sources') or ():
   for title,url,detected_series,detected_rider in _anchors(series,base,limit_per_source):
    resolved=detected_rider or rider_for(title+' '+url,series)
    # A rider-specific official page may link generic stories. Keep only links whose
    # visible source metadata resolves to this registered rider.
    if resolved!=rider:continue
    if url in seen:continue
    seen.add(url);out.append((title,url,rider,detected_series or series))
 print(f'TURKISH RIDER-CENTERED SCOUT: {len(out)} candidates from {len(RIDER_SOURCES)} riders')
 return out

def turkish_media_scout(limit_per_source=80):
 """Scan Turkish specialist racing media for stories about every registered rider.

 These are discovery inputs only. Identity is resolved through the shared registry;
 downstream fact/QM gates remain authoritative.
 """
 out=[];seen=set()
 for source,base in TURKISH_MEDIA_SOURCES:
  rows=_anchors(source,base,limit_per_source)
  for title,url,detected_series,rider in rows:
   resolved=rider or rider_for(title+' '+url,detected_series or source)
   if not resolved or resolved not in RIDER_SOURCES or url in seen:continue
   seen.add(url);out.append((title,url,resolved,detected_series or RIDER_SOURCES[resolved].get('series','')))
 print(f'TURKISH MEDIA SCOUT: {len(out)} registered-rider candidates')
 return out

def discovery_scout(limit_per_source=160):
 """Discovery lane for Turkish rookies/newcomers not yet in the registry.

 It scans trusted federation/championship discovery pages. Unknown names are memory
 candidates only; they are never auto-promoted into CANONICAL_ALIASES/RIDER_CONTEXT.
 """
 discovery_sources=[
  ('TMF','https://www.tmf.org.tr/Haberler/'),
  ('MotoGP','https://www.motogp.com/en/news'),
  ('WorldSBK','https://www.worldsbk.com/en/news'),
 ]
 leads=[];seen=set()
 turkish_markers=('turk','turkiye','türkiye','turkish','milli sporc','milli motosiklet')
 for series,base in discovery_sources:
  for title,url,detected_series,rider in _anchors(series,base,limit_per_source):
   if rider:
    ctx=RIDER_SOURCES.get(rider,{})
    remember_verified(rider,ctx.get('series') or detected_series or series,ctx.get('official_sources') or (base,),url)
    continue
   low=fold(title+' '+url)
   if not any(marker in low for marker in turkish_markers):continue
   # A generic 'Turkish rider' headline is a story lead, not a person identity.
   # Never store the article title itself as a rider candidate.
   if not rider: continue
   key=url
   if key in seen:continue
   seen.add(key)
   remember_candidate(rider,detected_series or series,url,title)
   leads.append((rider,url,detected_series or series))
 print(f'TURKISH DISCOVERY SCOUT: {len(leads)} unverified leads remembered')
 return leads

def scout(limit=40):
 out=[];seen=set()
 for t,u,s,r in racing_scout(limit):
  if r and u not in seen:out.append((t,u,r));seen.add(u)
  if len(out)>=limit:return out
 for rider,t,u,s in FALLBACK:
  if u not in seen:out.append((t,u,rider));seen.add(u)
  if len(out)>=limit:break
 return out
def legacy_pairs(limit=40):return [(t,u) for t,u,_ in scout(limit)]
def racing_pairs(limit_per_source=50):return [(t,u) for t,u,_,_ in racing_scout(limit_per_source)]
