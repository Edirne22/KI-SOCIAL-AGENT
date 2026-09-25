"""Single source of truth for Racing language rules from Main to final Chief-QM."""
from pathlib import Path
import hashlib,re

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
 lines=text().splitlines();header='## '+name;out=[];inside=False
 for line in lines:
  stripped=line.strip()
  if stripped==header:
   inside=True;continue
  if inside and stripped.startswith('## '):
   break
  if inside:out.append(line)
 return '\n'.join(out)
def blocked_phrases():
 return [line.strip()[2:] for line in _section('Vermeiden').splitlines() if line.strip().startswith('- ')]
def deterministic_errors(caption):
 low=_fold(caption);errs=[]
 for p in blocked_phrases():
  if _fold(p) in low:errs.append('Racing-Lexikon BLOCKED: '+p)
 return errs
