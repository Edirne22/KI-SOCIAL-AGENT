"""Independent semantic source-to-caption QM for Motorcycle Racing – hard facts fail closed, language is repairable."""
import json,re
from llm_client import generate
BRAND_HASHTAGS={'#buelentsbikelife'}

def _extract_json_object(raw):
    if not isinstance(raw, str):
        raise ValueError('json response must be a string')
    s = raw.strip()
    if not s:
        raise ValueError('empty json response')
    s = re.sub(r'^\s*```(?:json)?\s*', '', s, flags=re.I | re.S)
    s = re.sub(r'\s*```\s*$', '', s, flags=re.I | re.S)
    start = s.find('{')
    end = s.rfind('}')
    if start == -1 or end == -1 or end < start:
        raise json.JSONDecodeError('no JSON object found', s, 0)
    candidate = s[start:end+1]
    if s[:start].strip() or s[end+1:].strip():
        # Accept only whitespace around the JSON object. Any extra text is treated as malformed.
        raise json.JSONDecodeError('extra text around JSON object', s, start)
    return json.loads(candidate)

def _clean_json(raw):
    return _extract_json_object(raw)

def _fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def _system_hashtags(caption):
  blocks=[b.strip() for b in str(caption or '').split('\n\n') if b.strip()]
  if not blocks:return []
  tokens=blocks[-1].split();return tokens if tokens and all(t.startswith('#') for t in tokens) else []
def _caption_for_fact_review(caption,trusted_system_hashtags=None):
  trusted={str(x).casefold() for x in (trusted_system_hashtags or [])};parts=[]
  for token in str(caption or '').split():
   if token.casefold() in BRAND_HASHTAGS or token.casefold() in trusted:continue
   parts.append(token)
  return ' '.join(parts)
def infer_story_series(item):
  if item.get('canonical_fact_object') is not None:return item['canonical_fact_object']['series']
  t=_fold(' '.join((item.get('title',''),item.get('summary',''),item.get('url',''))))
  destination=[('MotoGP',(r'(?:join|joins|joining|move|moves|moving|switch|switches|seat|debut|to)\b.{0,45}\bmotogp',r'\bmotogp\b.{0,45}\b(?:2027|next season|next year)')),('WorldSBK',(r'(?:join|jo[...]
  for series,patterns in destination:
   if any(re.search(p,t) for p in patterns):return series
  if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
  if 'worldssp' in t or 'world supersport' in t:return 'WorldSSP'
  if 'worldsbk' in t or 'world superbike' in t:return 'WorldSBK'
  if re.search(r'(?<![a-z0-9])moto3(?![a-z0-9])',t):return 'Moto3'
  if re.search(r'(?<![a-z0-9])moto2(?![a-z0-9])',t):return 'Moto2'
  if re.search(r'(?<![a-z0-9])motogp(?![a-z0-9])',t):return 'MotoGP'
  return str(item.get('series','')).strip() or 'nicht eindeutig'
def _prompt(item,caption):
  title=str(item.get('title','')).strip();summary=str(item.get('summary','')).strip();inferred=infer_story_series(item);url=str(item.get('url','')).strip();trusted=_system_hashtags(caption);fact_ca[...]
  return f'''Du bist unabhaengiger Senior-Faktenpruefer fuer Motorrad-Racing. Trenne HARTE FAKTENFEHLER strikt von REPARIERBARER SPRACHE.\nQUELLFAKTEN:\nSERIE: {inferred}\nTITEL: {title}\nZUSAMMENF[...]
def review_detailed(item,caption):
  prompt=_prompt(item,caption);last=None
  for technical_attempt in range(3):
   try:
    o=_clean_json(generate('racing_semantic_qm',prompt));hard=all(o.get(k) is True for k in ('hard_fact_ok','series_ok','rider_team_ok','quote_ok'));language=all(o.get(k) is True for k in ('german_[...]
    if not hard and not hard_reasons:hard_reasons=['Harter Fakten-QM: Pflichtfeld FAIL']
    if hard and not language and not repair:repair=['Sprache/Stil reparieren']
    return {'hard_ok':hard,'language_ok':language,'hard_reasons':hard_reasons,'repair_reasons':repair}
   except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:last=e;continue
   except Exception as e:last=e;break
  return {'hard_ok':False,'language_ok':False,'hard_reasons':[f'Semantischer Fakten-QM technisch ungueltig nach 3 Versuchen: {type(last).__name__}: {str(last)[:140]}'],'repair_reasons':[]}
def review(item,caption):
  r=review_detailed(item,caption);ok=r['hard_ok'] and r['language_ok'];return ok,(r['hard_reasons']+r['repair_reasons'])
 

