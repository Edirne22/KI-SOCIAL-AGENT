"""Agent 16 / Racing Scout: official MotoGP-, Moto2-, Moto3-, WorldSBK- and WorldSSP sources – V8.5.3."""
import re,requests,html,unicodedata
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT Motorcycle Racing Agency'}
# Separate official class pages are intentional: the combined MotoGP news page only exposes a
# small rotating subset. Class feeds create a deeper current reserve without relaxing freshness/QM.
SOURCES=[
 ('MotoGP','https://www.motogp.com/en/news'),
 ('Moto2','https://www.motogp.com/en/news/Moto2'),
 ('Moto3','https://www.motogp.com/en/news/Moto3'),
 ('WorldSBK','https://www.worldsbk.com/en/news'),
 ('WorldSSP','https://www.worldsbk.com/en/news/ssp')]
WATCHLIST={
 'Toprak Razgatlıoğlu':('Toprak Razgatlıoğlu','Toprak Razgatlioglu','Toprak Razgatlıoglu','Toprak Razgatliğlu','Razgatlıoğlu','Razgatlioglu'),
 'Can Öncü':('Can Öncü','Can Oncu','C. Öncü','C. Oncu','Öncü','Oncu'),
 'Deniz Öncü':('Deniz Öncü','Deniz Oncu','D. Öncü','D. Oncu'),
 'Bahattin Sofuoğlu':('Bahattin Sofuoğlu','Bahattin Sofuoglu','B. Sofuoğlu','B. Sofuoglu'),
 'Zayn Sofuoğlu':('Zayn Sofuoğlu','Zayn Sofuoglu','Z. Sofuoğlu','Z. Sofuoglu')}
FALLBACK=[
 ('Toprak Razgatlıoğlu','Toprak Razgatlioglu – MotoGP rider profile and 2026 rookie campaign','https://www.motogp.com/en/riders/toprak-razgatlioglu/c883a3b8-17ce-419d-b71b-32c252f6fc7e','MotoGP'),
 ('Can Öncü','Can Oncu takes first 2026 WorldSSP win in Race 1 comeback from P13','https://www.worldsbk.com/en/news/2026/09/14/oncu-takes-first-2026-worldssp-win-in-race-1-comeback-from-p13-im-happy-that-the-hard-work-paid-off/1089992','WorldSSP'),
 ('Bahattin Sofuoğlu','Bahattin Sofuoglu – WorldSBK 2026 rider profile','https://www.worldsbk.com/en/riders/bahattin-sofuoglu/8467','WorldSBK')]
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def fold(s):
 s=unicodedata.normalize('NFKD',(s or '').casefold()).replace('ı','i')
 return ''.join(ch for ch in s if not unicodedata.combining(ch)).replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_for(text):
 low=fold(text)
 for rider,aliases in WATCHLIST.items():
  for alias in aliases:
   a=fold(alias)
   if ' ' in a and len(a)>=5 and re.search(r'(?<![a-z])'+re.escape(a)+r'(?![a-z])',low):return rider
 if re.search(r'(?<![a-z])(can|c\.)\s+oncu(?![a-z])',low):return 'Can Öncü'
 return ''
def classify_series(default_series,title,url):
 text=fold((title or '')+' '+(url or ''))
 if 'worldssp300' in text or 'worldssp 300' in text or 'wssp300' in text:return 'WorldSSP300'
 if re.search(r'\b(to|into|joins?|move[sd]? to|challenge in)\s+(the\s+)?worldsbk\b',text) or 'new challenge in worldsbk' in text:return 'WorldSBK'
 if re.search(r'\b(to|into|joins?|move[sd]? to|seat for)\s+(the\s+)?motogp\b',text) or 'motogp seat' in text:return 'MotoGP'
 if 'worldssp' in text or 'world supersport' in text or 'supersport' in text or 'wssp' in text:return 'WorldSSP'
 # Preserve the actual GP class. Do not collapse Moto2/Moto3 into MotoGP.
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
  if len(t)<20 or u in seen or '/news/' not in u:continue
  seen.add(u);out.append((t,u,classify_series(series,t,u),rider_for(t+' '+u)))
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
