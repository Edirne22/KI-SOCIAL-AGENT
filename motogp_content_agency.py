"""Daily MotoGP Content Agency – source-first, fail-safe, no publishing."""
from datetime import datetime, timezone
from pathlib import Path
import html, re, requests
from urllib.parse import urljoin
ROOT=Path('.')
OUT=ROOT/'memory'/'MOTOGP_DAILY_CONTENT.md'; ARCH=ROOT/'memory'/'MOTOGP_DAILY_ARCHIVE'
NEXT=ROOT/'content'/'MOTOGP_ROSTER_NEXT.md'
UA={'User-Agent':'Mozilla/5.0 KI-SOCIAL-AGENT MotoGP research'}
NEWS='https://www.motogp.com/en/news'; MARKET='https://www.motogp.com/en/news/rider-market'
def get(url):
 r=requests.get(url,headers=UA,timeout=30);r.raise_for_status();return r.text
def text(s): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',s))).strip()
def extract(page,limit=20):
 found=[];seen=set()
 for href,title in re.findall(r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',page,re.I|re.S):
  t=text(title);u=urljoin('https://www.motogp.com',href)
  if len(t)<20 or '/news/' not in u or t.casefold() in seen:continue
  seen.add(t.casefold());found.append((t,u))
  if len(found)>=limit:break
 return found
def roster_names():
 p=ROOT/'content'/'MOTOGP_ROSTER.md'
 if not p.exists():return []
 return [m.group(1).strip() for m in re.finditer(r'^-\s+#\d+\s+–\s+([^|\n]+)',p.read_text(encoding='utf-8'),re.M)]
def score(title,names):
 low=title.casefold();s=0
 for n in names:
  parts=n.casefold().split()
  if n.casefold() in low or (parts and parts[-1] in low):s+=4
 for k in ('win','victory','championship','title','rider','sign','join','2027','injur','return','preview','schedule','record','marquez','razgatlioglu'): 
  if k in low:s+=1
 return s
def next_roster(market_items):
 year=datetime.now(timezone.utc).year+1
 lines=[f'# MotoGP Roster {year} – bestätigte Vorschau','',f'**Stand:** {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC}','','**Status:** UNVOLLSTÄNDIG – nur offiziell bestätigte Meldungen; ersetzt den aktiven Roster nicht.','','## Offizielle Rider-Market-Meldungen','']
 for t,u in market_items[:20]:lines.append(f'- {t} — {u}')
 lines+=['','## Regel','Nur bestätigte MotoGP-Mitteilungen werden vorgemerkt. Erst eine vollständig bestätigte Startaufstellung darf zum aktiven Roster werden.','']
 NEXT.parent.mkdir(parents=True,exist_ok=True);NEXT.write_text('\n'.join(lines),encoding='utf-8')
def main():
 names=roster_names();news=extract(get(NEWS),30);market=extract(get(MARKET),20)
 merged=[];seen=set()
 for item in news+market:
  if item[1] not in seen:seen.add(item[1]);merged.append(item)
 merged.sort(key=lambda x:score(x[0],names),reverse=True)
 now=datetime.now(timezone.utc);lines=['# MotoGP Daily Content Agency','',f'**Recherche:** {now:%Y-%m-%d %H:%M UTC}','**Quelle zuerst:** offizielle MotoGP-Seite','', '## Top-Themen für Content','']
 for i,(t,u) in enumerate(merged[:12],1):
  lines += [f'### {i}. {t}',f'- Quelle: {u}',f'- Content-Chance: Fahrer-/News-Post mit belegtem Hook; Fakten vor Veröffentlichung gegen Quelle prüfen.', '- Hashtags: #MotoGP plus Fahrer/Team/Event nur wenn zum Thema passend.','']
 lines+=['## Redaktionelle Regeln','- Fahrerrotation gegen POST_HISTORY beachten.','- Ride With Me maximal 1x pro Kalenderwoche.','- Gerüchte nicht als Fakten verwenden.','- Keine automatische Veröffentlichung; menschliche Freigabe bleibt Pflicht.','']
 content='\n'.join(lines);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(content,encoding='utf-8');ARCH.mkdir(parents=True,exist_ok=True);(ARCH/f'{now:%Y-%m-%d}.md').write_text(content,encoding='utf-8');next_roster(market);print(f'MotoGP Content Agency: {len(merged)} offizielle Themen gesammelt.')
if __name__=='__main__':main()
