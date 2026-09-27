import ast
from pathlib import Path

p=Path('motogp_content_agency_v2.py')
src=p.read_text(encoding='utf-8')
ast.parse(src)
ns={}
# Load only deterministic helpers without importing production dependencies.
start=src.index('def _explicit_source_series')
end=src.index('def _editor_prompt')
pre="import re, unicodedata\n"+"def fold(s):\n s=unicodedata.normalize('NFKD',str(s).replace('ı','i'));return ''.join(c for c in s if not unicodedata.combining(c)).lower()\n"+"def racing_lexicon_errors(c): return []\n"
exec(pre+src[start:end],ns)
series=ns['_explicit_source_series']({'title':'WSSP Superpole İtalya: Alcoba Cremona’da, Can Öncü 6. sırada bitirdi','summary':''})
assert series=='WorldSSP',series
assert ns['language_sane']('Can Öncü puansız ayrıldı.') is False
assert ns['language_sane']('Can Öncü blieb ohne Punkte.') is True
print('TEST – Turkish Series + German Language Hardening: PASS')
