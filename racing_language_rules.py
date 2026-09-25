"""Single source of truth for Racing language rules from Main to final Chief-QM."""
from pathlib import Path
import hashlib

LEXICON_PATH=Path('config/RACING_LANGUAGE_LEXICON.md')
def text():
 try:return LEXICON_PATH.read_text(encoding='utf-8').strip()
 except Exception:return ''
def version():
 raw=text().encode('utf-8');return hashlib.sha256(raw).hexdigest()[:12] if raw else 'missing'
def prompt_contract(stage):
 return f"""VERBINDLICHES RACING-SPRACHLEXIKON (Version {version()}, Stufe {stage}):
{text()}
LEXIKON-KETTENREGEL: Dieses Lexikon ist fuer alle Racing-Stufen verbindlich. Es ist niemals eine Faktenquelle. PREFERRED steuert Formulierung; VERMEIDEN/BLOCKED darf nicht freigegeben werden; 'Nur mit ausdruecklicher Quellenstuetzung' darf nur verwendet werden, wenn TITEL/ZUSAMMENFASSUNG die Aussage tragen. Kein Folgeagent darf den Text gegen einen eigenen Stilstandard umschreiben oder eine Lexikon-Regel abschwaechen."""
def _fold(s):
 return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ä','a').replace('ş','s').replace('ç','c')
def _section(name):
 raw=text();lines=raw.splitlines();out=[];inside=False
 for line in lines:
  if line.startswith('## '):
   if inside:break
   inside=(line.strip()==f'## {name}')
   continue
  if inside:out.append(line)
 return '\n'.join(out)
def blocked_phrases():
 return [x.strip()[2:] for x in _section('Vermeiden').splitlines() if x.strip().startswith('- ')]
def _items(name):
 return [x.strip()[2:] for x in _section(name).splitlines() if x.strip().startswith('- ')]
def blocked_variants():
 out={}
 for row in _items('Deterministische BLOCKED-Varianten'):
  if '=>' not in row:continue
  canonical,raw=row.split('=>',1)
  out[canonical.strip()]=[x.strip() for x in raw.split('|') if x.strip()]
 return out
def deterministic_errors(caption):
 low=_fold(caption);errs=[]
 aliases=blocked_variants()
 for p in blocked_phrases():
  variants=[p]+aliases.get(p,[])
  if any(_fold(v) in low for v in variants):
   errs.append('Racing-Lexikon BLOCKED: '+p)
 english=[_fold(x) for x in _items('Englische Nachrichtenfragmente')]
 hits=[x for x in english if x and x in low]
 if len(hits)>=2:errs.append('Racing-Lexikon BLOCKED: englischer Nachrichtenblock')
 return errs
