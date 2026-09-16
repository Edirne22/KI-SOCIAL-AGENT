"""Deterministic last-mile truth guard. No LLM may override these checks."""
import re,unicodedata
PROMO=('behind the scenes','catch up','vlog','episode','episodes','fantasy','videopass','tickets','shop','giveaway')
# Current lower-class names are deterministic disambiguators when official generic motogp.com URLs omit class metadata.
MOTO3_NAMES=('quiles','almansa','uriarte','kelso','carpe');MOTO2_NAMES=('agius','gonzalez','canet','vietti','arbolino','holgado','moreira','oncu','öncü')
def fold(s):
 s=unicodedata.normalize('NFKD',str(s or '')).casefold().replace('ı','i');return ''.join(c for c in s if not unicodedata.combining(c))
def source_text(item):return ' '.join((str(item.get('title','')),str(item.get('summary',''))))
SERIES_PATTERNS=(
 ('WorldWCR',r'\bworldwcr\b|women.s circuit|women.s championship'),
 ('WorldSSP300',r'\bworldssp\s*300\b'),
 ('WorldSSP',r'\bworldssp\b(?!\s*300)|\bworld supersport\b(?!\s*300)'),
 ('WorldSBK',r'\bworldsbk\b|\bworld superbike\b'),
 ('Moto3',r'\bmoto3\b'),('Moto2',r'\bmoto2\b'),('MotoGP',r'\bmotogp\b'))

def _detect_explicit_series(text):
 matches=[series for series,pattern in SERIES_PATTERNS if re.search(pattern,text)]
 return matches[0] if len(matches)==1 else None

def expected_series(item):
 # 1. Explicit series in title (highest priority - no lower source may override)
 title_series=_detect_explicit_series(fold(item.get('title','')))
 if title_series:return title_series

 # 2. Explicit series in summary
 clean_summary=fold(item.get('summary','')).replace('the official home of motogp','')
 summary_series=_detect_explicit_series(clean_summary)
 if summary_series:return summary_series

 # 3. Feed metadata / Rider history / Source text hints
 t=fold(source_text(item))
 if any(re.search(r'(?<![a-z])'+re.escape(fold(n))+r'(?![a-z])',t) for n in MOTO3_NAMES):return 'Moto3'
 if any(re.search(r'(?<![a-z])'+re.escape(fold(n))+r'(?![a-z])',t) for n in MOTO2_NAMES):return 'Moto2'

 # 4. Fallback -> declared series or 'unknown'
 declared=str(item.get('series','')).strip()
 return declared if declared else 'unknown'
def review(item,caption):
 errors=[];src=fold(source_text(item));cap=fold(caption);series=expected_series(item);declared=str(item.get('series','')).strip()
 if any(p in src for p in PROMO):errors.append('Final-Guard: Promo/Vlog/Marketing statt Racing-News')
 if series=='WorldWCR':errors.append('Final-Guard: WorldWCR ist derzeit nicht als freigegebene Racing-Serie konfiguriert')
 if series and declared and declared!=series:errors.append(f'Final-Guard: Serien-Metadatum {declared} widerspricht Quelle {series}')
 tags={'MotoGP':'#motogp','Moto2':'#moto2','Moto3':'#moto3','WorldSBK':'#worldsbk','WorldSSP':'#worldssp','WorldSSP300':'#worldssp300'}
 if series in tags and tags[series] not in caption.casefold():errors.append(f'Final-Guard: Pflicht-Serienhashtag {tags[series]} fehlt')
 wrong=[tag for s,tag in tags.items() if s!=series and tag in caption.casefold()]
 if wrong:errors.append('Final-Guard: falscher Serienhashtag '+','.join(wrong))
 if 'razgatlioglu' in cap and 'rahil etgar' in cap:errors.append('Final-Guard: erfundener/korruptierter Fahrername vor Razgatlioglu')
 for de,en in (('spanier','spanish'),('italiener','italian'),('turke','turkish'),('tuerke','turkish')):
  if de in cap and en not in src and de not in src:errors.append(f'Final-Guard: Nationalitaet {de} nicht in Quellenfakten')
 return not errors,errors
