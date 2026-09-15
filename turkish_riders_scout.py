"""Agent 16 / Racing Scout: offizielle MotoGP-, WorldSBK- und WorldSSP-Quellen."""
import re,requests,html
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT Motorcycle Racing Agency'}
SOURCES=[('MotoGP','https://www.motogp.com/en/news'),('WorldSBK','https://www.worldsbk.com/en/news'),('WorldSSP','https://www.worldsbk.com/en/news/ssp')]
WATCHLIST={
 'Toprak Razgatlioglu':('toprak razgatlioglu','toprak razgatlıoğlu','razgatlioglu','razgatlıoğlu'),
 'Can Oncu':('can oncu','can öncü'),
 'Deniz Oncu':('deniz oncu','deniz öncü'),
 'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),
 'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu'),
}
FALLBACK=[
 ('Toprak Razgatlioglu','Toprak Razgatlioglu – MotoGP rider profile and 2026 rookie campaign','https://www.motogp.com/en/riders/toprak-razgatlioglu/c883a3b8-17ce-419d-b71b-32c252f6fc7e','MotoGP'),
 ('Can Oncu','Can Oncu takes first 2026 WorldSSP win in Race 1 comeback from P13','https://www.worldsbk.com/en/news/2026/09/14/oncu-takes-first-2026-worldssp-win-in-race-1-comeback-from-p13-im-happy-that-the-hard-work-paid-off/1089992','WorldSSP'),
 ('Bahattin Sofuoglu','Bahattin Sofuoglu – WorldSBK 2026 rider profile','https://www.worldsbk.com/en/riders/bahattin-sofuoglu/8467','WorldSBK'),
]
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_for(text):
 low=fold(text)
 for rider in ('Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu','Toprak Razgatlioglu','Can Oncu'):
  if any(fold(k) in low for k in WATCHLIST[rider]):return rider
 return ''
def classify_series(default_series,title,url):
 """WorldSBK-Newsseite mischt Klassen; sichtbare Artikelmarker schlagen den Feed-Namen."""
 text=fold((title or '')+' '+(url or ''))
 if 'worldssp300' in text or 'worldssp 300' in text or 'wssp300' in text:return 'WorldSSP300'
 if 'worldssp' in text or 'world supersport' in text or 'supersport' in text or 'wssp' in text:return 'WorldSSP'
 if 'motogp' in text or 'moto2' in text or 'moto3' in text:return 'MotoGP'
 return default_series
def _anchors(series,base,limit):
 out=[];seen=set()
 try:
  r=requests.get(base,headers=UA,timeout=30);r.raise_for_status();page=r.text
 except Exception:return out
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  t=clean(title);u=urljoin(base,href)
  if len(t)<20 or u in seen or '/news/' not in u:continue
  seen.add(u);out.append((t,u,classify_series(series,t,u),rider_for(t)))
  if len(out)>=limit:break
 return out
def racing_scout(limit_per_source=50):
 out=[];seen=set()
 for series,base in SOURCES:
  for row in _anchors(series,base,limit_per_source):
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
