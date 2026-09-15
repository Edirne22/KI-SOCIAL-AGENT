"""Agent 16: KNN54/Turkish Riders Scout – Primärquellen-Kandidaten."""
import re,requests,html
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT KNN54 Turkish Riders Scout'}
# Serienquellen breit halten: MotoGP deckt MotoGP/Moto2/Moto3, WorldSBK SBK/SSP ab.
SOURCES=[
 'https://www.motogp.com/en/news',
 'https://www.worldsbk.com/en/news',
 'https://www.worldsbk.com/en/news/ssp',
]
WATCHLIST={
 'Toprak Razgatlioglu':('toprak','razgatlioglu','razgatlıoğlu'),
 'Can Oncu':('can oncu','can öncü','c. oncu','c. öncü'),
 'Deniz Oncu':('deniz oncu','deniz öncü','d. oncu','d. öncü'),
 'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),
 'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu'),
}
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def rider_for(text):
 low=text.casefold()
 for rider,keys in WATCHLIST.items():
  if any(k in low for k in keys):return rider
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
 return out

def legacy_pairs(limit=40):
 """Kompatibel mit der bestehenden Agency; Rider-Metadatum bleibt über rider_for verfügbar."""
 return [(t,u) for t,u,_ in scout(limit)]
