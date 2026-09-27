"""Agent 16 / Racing Scout: official MotoGP-, Moto2-, Moto3-, WorldSBK- and WorldSSP sources – V8.5.4."""
import re,requests,html,unicodedata
from urllib.parse import quote_plus
from turkish_rider_names import CANONICAL_ALIASES, RIDER_CONTEXT, canonical_rider
from turkish_rider_memory import remember_verified, remember_candidate
from motoetkinlik_source import discover_news as motoetkinlik_discover_news, reference_snapshots as motoetkinlik_reference_snapshots
from urllib.parse import urljoin, urlsplit
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
TURKISH_WEB_SOURCES=(
 ('TMF','https://www.tmf.org.tr/Haberler/'),
 ('AnadoluAjansi','https://www.aa.com.tr/tr/spor'),
 ('Motoron','https://www.motoron.com.tr/kategori/yarislar/'),
 ('MotorsportTR','https://tr.motorsport.com/'),
 ('TRMotoSports','https://www.trmotosports.com/'),
 ('TRF1MotoGP','https://trf1.net/motor-sporlari/motogp/'),
 ('MotoEtkinlikMotoGP','https://motoetkinlik.com/kategori/motogp/'),
 ('MotoEtkinlikMoto2','https://motoetkinlik.com/kategori/moto2/'),
 ('MotoEtkinlikMoto3','https://motoetkinlik.com/kategori/moto3/'),
 ('MotoEtkinlikWorldSBK','https://motoetkinlik.com/kategori/wsbk/'),
 ('MotoEtkinlikWorldSSP','https://motoetkinlik.com/kategori/worldssp/'),
 ('MotoEtkinlikYaris','https://motoetkinlik.com/kategori/yaris/'),
)
# Open Turkish web sources are preferred over social scraping: crawlable, source-linked,
# and suitable for the same downstream freshness/fact gates.
TURKISH_MEDIA_SOURCES=(
 ('MotoEtkinlikcom','https://www.instagram.com/motoetkinlikcom/'),
 ('MotoEtkinlikRacing','https://www.instagram.com/motoetkinlikracing/'),
 ('TurkiyeSBK','https://www.instagram.com/turkiyesbk/'),
)
TURKISH_RACING_TERMS=(
 'podyum','podyuma çıktı','kürsüye çıktı','birinci oldu','zirvede','şampiyon','şampiyonluk',
 'dama bayrak','zafer','kazandı','yarış','en hızlı tur','puan','sıralama turları','pole pozisyonu',
 'yarış öncesi','yarış sonrası','yarış dışı','nefes kesen yarış','tarihi başarı','tarih yazdı',
 'milli sporcu','milli gurur','pist','serbest antrenman','ısınma turu','viraj','lastik','kaza',
 'düşüş','ceza','kırmızı bayrak','sarı bayrak','mekanik arıza','minigp','juniorgp','talent cup',
 'motogp','moto2','moto3','worldsbk','wsbk','worldssp','ssp'
)
def racing_relevance(text):
 low=fold(text)
 return sum(1 for term in TURKISH_RACING_TERMS if fold(term) in low)

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
  parsed=urlsplit(u)
  aa_article=(urlsplit(base).hostname in ('aa.com.tr','www.aa.com.tr')
              and parsed.hostname in ('aa.com.tr','www.aa.com.tr')
              and parsed.scheme in ('http','https')
              and re.fullmatch(r'/tr/spor/[^/]+/[0-9]+/?',parsed.path) is not None)
  if len(t)<20 or u in seen or not ('/news/' in u.lower() or '/haberler/' in u.lower() or aa_article):continue
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


def _turkish_site_crawl(source,base,max_pages=30,depth=2):
 """Breadth-first crawl of same-site landing/category pages; articles stay discovery-only."""
 host=(urlsplit(base).hostname or '').lower().removeprefix('www.');queue=[(base,0)];visited=set();rows=[];seen_urls=set()
 while queue and len(visited)<max_pages:
  page_url,d=queue.pop(0)
  if page_url in visited:continue
  visited.add(page_url)
  try:r=requests.get(page_url,headers=UA,timeout=30);r.raise_for_status();page=r.text
  except Exception as e:
   print(f'TURKISH WEB CRAWL FAIL {source}: {type(e).__name__}: {str(e)[:100]}');continue
  for href,title in re.findall(r'href=["\\\']([^"\\\']+)["\\\'][^>]*>(.*?)</a>',page,re.I|re.S):
   u=urljoin(page_url,href);parsed=urlsplit(u);t=clean(title)
   if (parsed.hostname or '').lower().removeprefix('www.')!=host or parsed.scheme not in ('http','https'):continue
   low=u.lower();path=parsed.path.rstrip('/')
   aa_article=(host in ('aa.com.tr','www.aa.com.tr') and
               re.fullmatch(r'/tr/spor/.+/[0-9]+',path) is not None)
   tmf_article=(host in ('tmf.org.tr','www.tmf.org.tr') and
                path.lower().startswith('/haberler/') and path.lower()!='/haberler')
   motoron_article=(host in ('motoron.com.tr','www.motoron.com.tr') and
                    path.lower().startswith('/motosiklet-haber/'))
   motorsport_article=(host=='tr.motorsport.com' and
                       re.fullmatch(r'/[^/]+/news/.+/[0-9]+',path.lower()) is not None)
   trmotosports_article=(host in ('trmotosports.com','www.trmotosports.com') and
                         re.fullmatch(r'/[^/]+',path.lower()) is not None and
                         path.lower() not in ('/motogp-izle','/worldsbk-izle'))
   trf1_article=(host in ('trf1.net','www.trf1.net') and
                 re.fullmatch(r'/motor-sporlari/[^/]+/.+/[0-9]+',path.lower()) is not None)
   motoetkinlik_article=(host=='motoetkinlik.com' and
                         re.fullmatch(r'/[^/]+',path.lower()) is not None and
                         path.lower() not in ('/giris-yap','/kayit-ol','/forum','/iletisim'))
   article=(aa_article or tmf_article or motoron_article or motorsport_article or
            trmotosports_article or trf1_article or motoetkinlik_article) and len(t)>=20
   if article and u not in seen_urls:
    seen_urls.add(u);rows.append((t,u,classify_series(source,t,u),rider_for(t+' '+u,source)))
   # Follow same-site category/index pages, but cap depth/pages to avoid an unbounded spider.
   route=path.lower()+'/'
   pagination=bool(re.search(r'(?:/page/|/sayfa/|[?&](?:page|sayfa)=)\d+',u,re.I))
   motorsport_dead_nav=(host=='tr.motorsport.com' and re.fullmatch(r'/[^/]+(?:/(?:news|schedule|videos|drivers|teams))?/?',parsed.path.lower()) is not None)
   motoetkinlik_nav=(host=='motoetkinlik.com' and any(path.lower().startswith('/kategori/'+k) for k in ('motogp','moto2','moto3','wsbk','worldssp','yaris')))
   category=(any(k in route for k in ('/haber','/spor','/motosiklet','/motor','/kategori','/brans','/yaris','/yarış','/motogp','/moto2','/moto3','/superbike','/worldsbk','/worldssp','/supersport')) or pagination) and not motorsport_dead_nav
   if d<depth and (category or motoetkinlik_nav) and not article and u not in visited and all(u!=q[0] for q in queue):queue.append((u,d+1))
 rows.sort(key=lambda x:racing_relevance(x[0]+' '+x[1]),reverse=True)
 print(f'TURKISH WEB CRAWL {source}: pages={len(visited)} candidates={len(rows)}')
 return rows

def _turkish_web_search(rider,aliases,limit=20):
 """Search the public Turkish web per registered rider instead of trusting portal front pages."""
 out=[];seen=set()
 terms=[]
 for name in (rider,)+tuple(aliases or ()):
  if name and fold(name) not in {fold(x) for x in terms}:terms.append(name)
 # One query includes canonical and ASCII spellings, reducing throttling while keeping
 # the shared identity check and Turkish-domain boundary.
 names=' OR '.join(f'"{name}"' for name in terms[:3])
 q=quote_plus(f'({names}) motosiklet site:.tr')
 url='https://www.google.com/search?q='+q+'&num='+str(min(limit,20))
 try:
  r=requests.get(url,headers=UA,timeout=30);r.raise_for_status();page=r.text
 except Exception as e:
  print(f'TURKISH WEB SEARCH FAIL {rider}: {type(e).__name__}: {str(e)[:100]}');return out
 for href,title in re.findall(r"<a[^>]+href=[\\\"'](?:/url\\?q=)?([^\\\"'&]+)[^>]*>(.*?)</a>",page,re.I|re.S):
  u=html.unescape(href);t=clean(title);result_host=(urlsplit(u).hostname or '').lower()
  if not u.startswith('http') or not result_host.endswith('.tr') or len(t)<10 or u in seen:continue
  if rider_for(t+' '+u,'')!=rider:continue
  seen.add(u);out.append((t,u,'',rider))
  if len(out)>=limit:return out
 return out

def turkish_web_scout(limit_per_source=120):
 """Scan open Turkish .tr/.com.tr racing/news pages for every registered rider.

 This lane is deliberately registry-driven: Unicode canonical names and ASCII aliases
 are resolved by rider_for(); unknown does not become false. Returned URLs still pass
 article freshness and fact/QM gates downstream.
 """
 out=[];seen=set()
 # Dedicated deterministic MotoEtkinlik adapter.  It preserves the verified
 # category endpoint as lineage while all candidates still pass the normal
 # rider registry, freshness and downstream Truth/QM gates.
 for row in motoetkinlik_discover_news(limit_per_endpoint=min(limit_per_source,120)):
  title,url=row.get('title',''),row.get('url','')
  detected_series=row.get('series','')
  resolved=rider_for(title+' '+url,detected_series or 'MotoEtkinlik')
  if not resolved or resolved not in RIDER_SOURCES or url in seen:continue
  series=detected_series if detected_series in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300','WorldSPB','Moto4') else RIDER_SOURCES[resolved].get('series','')
  seen.add(url);out.append((title,url,resolved,series))
 for source,base in TURKISH_WEB_SOURCES:
  rows=_turkish_site_crawl(source,base,max_pages=30,depth=2)
  for title,url,detected_series,rider in rows:
   resolved=rider or rider_for(title+' '+url,detected_series or source)
   if not resolved or resolved not in RIDER_SOURCES or url in seen:continue
   series=detected_series if detected_series in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300','WorldSPB','Moto4') else RIDER_SOURCES[resolved].get('series','')
   seen.add(url);out.append((title,url,resolved,series))
 # Portal front pages are shallow (AA is mostly football; TMF may expose only a few cards).
 # Fill discovery per rider/alias so current articles deeper in the site can be found.
 for rider,aliases in CANONICAL_ALIASES.items():
  for title,url,detected_series,resolved in _turkish_web_search(rider,aliases,20):
   if url in seen:continue
   series=classify_series(RIDER_SOURCES.get(rider,{}).get('series',''),title,url)
   seen.add(url);out.append((title,url,rider,series))
 print(f'TURKISH WEB SCOUT: {len(out)} registered-rider candidates')
 return out

def _search_fallback(source,base,limit):
 """Public web-index fallback for social profiles that reject direct HTTP scraping.

 The social profile remains the discovery target; indexed result snippets are hints only.
 Downstream article/source fact gates remain authoritative.
 """
 host='www.instagram.com'
 handle=base.rstrip('/').split('/')[-1]
 q=quote_plus(f'site:{host}/{handle} Turkish motorcycle racing')
 search_url='https://www.google.com/search?q='+q+'&num='+str(min(limit,20))
 out=[];seen=set()
 try:
  r=requests.get(search_url,headers=UA,timeout=30);r.raise_for_status();page=r.text
 except Exception as e:
  print(f'TURKISH MEDIA FALLBACK FAIL {source}: {type(e).__name__}: {str(e)[:120]}');return out
 for href,title in re.findall(r"<a[^>]+href=[\\\"'](?:/url\\?q=)?([^\\\"'&]+)[^>]*>(.*?)</a>",page,re.I|re.S):
  t=clean(title);u=html.unescape(href)
  if not u.startswith('http') or handle not in u or len(t)<10 or u in seen:continue
  if not ('/p/' in u or '/reel/' in u):continue
  seen.add(u);out.append((t,u,'',rider_for(t+' '+u,'')))
  if len(out)>=limit:break
 return out

def turkish_media_scout(limit_per_source=80):
 """Scan Turkish specialist racing media for stories about every registered rider.

 These are discovery inputs only. Identity is resolved through the shared registry;
 downstream fact/QM gates remain authoritative.
 """
 out=[];seen=set()
 for source,base in TURKISH_MEDIA_SOURCES:
  rows=_anchors(source,base,limit_per_source)
  if not rows:
   rows=_search_fallback(source,base,limit_per_source)
   if rows: print(f'TURKISH MEDIA FALLBACK {source}: {len(rows)} indexed candidates')
  for title,url,detected_series,rider in rows:
   resolved=rider or rider_for(title+' '+url,detected_series or source)
   if not resolved or resolved not in RIDER_SOURCES or url in seen:continue
   # Specialist-media labels are not racing series. Prefer detected evidence, else registry context.
   series=detected_series if detected_series in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300','WorldSPB','Moto4') else RIDER_SOURCES[resolved].get('series','')
   seen.add(url);out.append((title,url,resolved,series))
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


def motoetkinlik_reference_data():
 """MotoEtkinlik structured reference pages with explicit source lineage.

 These snapshots are corroborating source material only.  They do not bypass
 Racing/Truth/QM authority or human approval.
 """
 return motoetkinlik_reference_snapshots()
