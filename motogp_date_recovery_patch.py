"""Diagnostic-only corrected date recovery; production/main remains unchanged."""
from datetime import datetime as dt, timezone
import re
MONTHS={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
def recover(x):
 url=(x.get('url') or '').lower();title=' '.join(str(x.get('title') or '').split())
 if 'motogp.com/' not in url or '/news/grand-prix/' not in url:return None
 m=re.search(r'\b\d{1,2}\s+([A-Za-z]{3})\s*-\s*(\d{1,2})\s+([A-Za-z]{3})\s+(20\d{2})\b',title,re.I)
 if m:
  mon=MONTHS.get(m.group(3).lower())
  if mon:
   try:return dt(int(m.group(4)),mon,int(m.group(2)),tzinfo=timezone.utc)
   except ValueError:return None
 m=re.search(r'\b\d{1,2}\s*-\s*(\d{1,2})\s+([A-Za-z]{3})\s+(20\d{2})\b',title,re.I)
 if m:
  mon=MONTHS.get(m.group(2).lower())
  if mon:
   try:return dt(int(m.group(3)),mon,int(m.group(1)),tzinfo=timezone.utc)
   except ValueError:return None
 return None
def install(a):
 if getattr(a,'_diagnostic_date_patch_installed',False):return a
 original=a.article_date
 def article_date(x):return recover(x) or original(x)
 a.article_date=article_date;a._diagnostic_date_patch_installed=True;return a
