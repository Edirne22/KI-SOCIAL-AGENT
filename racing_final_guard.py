"""Deterministic last-mile truth guard. No LLM may override these checks."""
import re,unicodedata
PROMO=('behind the scenes','catch up','vlog','episode','episodes','fantasy','videopass','tickets','shop','giveaway')
def fold(s):
 s=unicodedata.normalize('NFKD',str(s or '')).casefold().replace('ı','i');return ''.join(c for c in s if not unicodedata.combining(c))
def source_text(item):return ' '.join((str(item.get('title','')),str(item.get('summary',''))))
def expected_series(item):
 t=fold(source_text(item));u=fold(item.get('url',''))
 # Explicit class in source facts always wins over website domain.
 if re.search(r'\bworldwcr\b|women.s circuit|women.s championship',t):return 'WorldWCR'
 if re.search(r'\bworldssp300\b',t):return 'WorldSSP300'
 if re.search(r'\bworldssp\b|world supersport',t):return 'WorldSSP'
 if re.search(r'\bworldsbk\b|world superbike',t):return 'WorldSBK'
 if re.search(r'\bmoto3\b',t):return 'Moto3'
 if re.search(r'\bmoto2\b',t):return 'Moto2'
 if re.search(r'\bmotogp\b',t):return 'MotoGP'
 declared=str(item.get('series','')).strip();return declared or ''
def review(item,caption):
 errors=[];src=fold(source_text(item));cap=fold(caption);series=expected_series(item);declared=str(item.get('series','')).strip()
 if any(p in src for p in PROMO):errors.append('Final-Guard: Promo/Vlog/Marketing statt Racing-News')
 if series=='WorldWCR':errors.append('Final-Guard: WorldWCR ist derzeit nicht als freigegebene Racing-Serie konfiguriert')
 if series and declared and declared!=series:errors.append(f'Final-Guard: Serien-Metadatum {declared} widerspricht Quelle {series}')
 tags={'MotoGP':'#motogp','Moto2':'#moto2','Moto3':'#moto3','WorldSBK':'#worldsbk','WorldSSP':'#worldssp','WorldSSP300':'#worldssp300'}
 if series in tags and tags[series] not in caption.casefold():errors.append(f'Final-Guard: Pflicht-Serienhashtag {tags[series]} fehlt')
 wrong=[tag for s,tag in tags.items() if s!=series and tag in caption.casefold()]
 if wrong:errors.append('Final-Guard: falscher Serienhashtag '+','.join(wrong))
 # Known corruption seen live: extra invented given names before a source-backed surname.
 if 'razgatlioglu' in cap and 'rahil etgar' in cap:errors.append('Final-Guard: erfundener/korruptierter Fahrername vor Razgatlioglu')
 # If caption asserts nationality, it must literally occur in source facts.
 for de,en in (('spanier','spanish'),('italiener','italian'),('turke','turkish'),('tuerke','turkish')):
  if de in cap and en not in src and de not in src:errors.append(f'Final-Guard: Nationalitaet {de} nicht in Quellenfakten')
 return not errors,errors
