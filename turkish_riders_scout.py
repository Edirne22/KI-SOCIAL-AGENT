"""Agent 16: liefert neue Primärquellen-Kandidaten zu Toprak Razgatlioglu oder Can Oncu."""
import re,requests,html
from urllib.parse import urljoin
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT Turkish Riders Scout'}
SOURCES=['https://www.motogp.com/en/news','https://www.worldsbk.com/en/news/ssp']
KEYS=('toprak','razgatlioglu','razgatlıoğlu','oncu','öncü')
def clean(s):return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s or ''))).strip()
def scout(limit=20):
 out=[];seen=set()
 for base in SOURCES:
  try:
   page=requests.get(base,headers=UA,timeout=30).text
  except Exception:continue
  for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
   t=clean(title);low=t.casefold()
   if not any(k in low for k in KEYS):continue
   u=urljoin(base,href)
   if u in seen:continue
   seen.add(u);out.append((t,u))
   if len(out)>=limit:return out
 return out
