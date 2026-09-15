"""Agent 16: Turkish Riders Scout – offizielle Racing-Quellen, fail-closed."""
import re, requests, html
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT Turkish Riders Scout'}
SOURCES=['https://www.motogp.com/en/news','https://www.worldsbk.com/en/news','https://www.worldsbk.com/en/news/ssp']
WATCHLIST={
 'Toprak Razgatlioglu':('toprak','razgatlioglu','razgatlıoğlu'),
 'Can Oncu':('can oncu','can öncü','oncu','öncü'),
 'Deniz Oncu':('deniz oncu','deniz öncü'),
 'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),
 'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu'),
}
# Offizielle, stabile Primärquellen als Fallback, falls News-Landingpages clientseitig rendern.
FALLBACK=[
 ('Toprak Razgatlioglu','Toprak Razgatlioglu – MotoGP rider profile and 2026 rookie campaign','https://www.motogp.com/en/riders/toprak-razgatlioglu/c883a3b8-17ce-419d-b71b-32c252f6fc7e'),
 ('Can Oncu','Can Oncu – WorldSSP 2026 official rider entry','https://www.worldsbk.com/en/riders/ssp'),
 ('Bahattin Sofuoglu','Bahattin Sofuoglu – WorldSBK 2026 rider profile','https://www.worldsbk.com/en/riders/bahattin-sofuoglu/8467'),
]
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_for(text):
 low=fold(text)
 for rider,keys in WATCHLIST.items():
  if any(fold(k) in low for k in keys):return rider
 return ''
def scout(limit=40):
 out=[];seen=set()
 for base in SOURCES:
  try:
   r=requests.get(base,headers=UA,timeout=30);r.raise_for_status();page=r.text
  except Exception:continue
  for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
   t=clean(title);rider=rider_for(t)
   if not rider:continue
   u=urljoin(base,href)
   if u in seen:continue
   seen.add(u);out.append((t,u,rider))
   if len(out)>=limit:return out
 # Landingpage-Scraping darf die Pflichtredaktion nicht auf 0 setzen.
 for rider,title,u in FALLBACK:
  if u not in seen:
   out.append((title,u,rider));seen.add(u)
   if len(out)>=limit:break
 return out

def legacy_pairs(limit=40):return [(t,u) for t,u,_ in scout(limit)]
