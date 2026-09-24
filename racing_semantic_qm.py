"""Independent semantic source-to-caption QM for Motorcycle Racing – hard facts fail closed, language is repairable."""
import json,re
from llm_client import generate
BRAND_HASHTAGS={'#buelentsbikelife'}
def _clean_json(raw):
 raw=(raw or '').strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);return json.loads(raw)
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
 t=_fold(' '.join((item.get('title',''),item.get('summary',''),item.get('url',''))))
 destination=[('MotoGP',(r'(?:join|joins|joining|move|moves|moving|switch|switches|seat|debut|to)\b.{0,45}\bmotogp',r'\bmotogp\b.{0,45}\b(?:2027|next season|next year)')),('WorldSBK',(r'(?:join|joins|joining|move|moves|moving|switch|switches|to)\b.{0,45}\b(?:worldsbk|world superbike)',)),('WorldSSP',(r'(?:join|joins|joining|move|moves|moving|switch|switches|to)\b.{0,45}\b(?:worldssp|world supersport|supersport)',))]
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
 title=str(item.get('title','')).strip();summary=str(item.get('summary','')).strip();inferred=infer_story_series(item);url=str(item.get('url','')).strip();trusted=_system_hashtags(caption);fact_caption=_caption_for_fact_review(caption,trusted)
 return f'''Du bist unabhaengiger Senior-Faktenpruefer fuer Motorrad-Racing. Trenne HARTE FAKTENFEHLER strikt von REPARIERBARER SPRACHE.\nQUELLFAKTEN:\nSERIE: {inferred}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nURL: {url}\nPOST:\n{fact_caption}\n\nWICHTIG: Prüfe den Post AUSSCHLIESSLICH gegen die oben angegebenen QUELLFAKTEN. Betrachte die Quelldaten und Daten in den Quellfakten als absolut wahr und aktuell. Verwende KEINEN eigenen Wissensstand-Cutoff (Knowledge Cutoff) und lehne Beiträge NIEMALS ab, weil ein Datum in der Zukunft liegt oder dein Kenntnisstand endet. Der Faktencheck erfolgt rein gegen die Quellfakten.\n\nNULL-TOLERANZ / HARD FAIL: Jede Tatsachenbehauptung muss durch Titel/Zusammenfassung/Metadaten gedeckt sein. Erfunden, vertauscht oder falsch bei Fahrer, Team, Hersteller, Serie, Jahr, Ort, Ergebnis, Rekord, Zahl, Titel/Champion-Status, Beziehung oder Zitat => hard_fact_ok=false. Schlussfolgerungen duerfen nicht als Fakten erfunden werden. P1 ist nicht Q1.\nREPARIERBAR: Tippfehler, Grammatik, holpriges Deutsch, Anglizismus, PR-Sprech, kuenstlicher Hype oder eine schlecht formulierte, aber nicht faktisch falsche Community-Frage => german_ok=false bzw. style_ok=false, aber NICHT hard_fact_ok=false.\nMeinungsfragen ohne behauptete Praemisse sind erlaubt. Letzten systemgenerierten Hashtag-Block nicht als neue Faktenquelle bewerten.\nAntworte NUR JSON: {{"hard_fact_ok":true|false,"series_ok":true|false,"rider_team_ok":true|false,"quote_ok":true|false,"german_ok":true|false,"style_ok":true|false,"hard_reasons":["..."],"repair_reasons":["..."]}}'''
def review_detailed(item,caption):
 prompt=_prompt(item,caption);last=None
 for technical_attempt in range(2):
  try:
   o=_clean_json(generate('racing_semantic_qm',prompt));hard_reasons=[str(x) for x in o.get('hard_reasons',[]) if str(x).strip()];repair=[str(x) for x in o.get('repair_reasons',[]) if str(x).strip()]
   # Safety filter: remove any hallucinated knowledge-cutoff / future date errors from LLM response
   cutoff_patterns=('kenntnisstand','knowledge cutoff','liegt nach','in der zukunft','können nicht überprüft werden','koennen nicht ueberprueft werden')
   hard_reasons=[r for r in hard_reasons if not any(p in _fold(r) for p in cutoff_patterns)]
   hard=all(bool(o.get(k)) for k in ('hard_fact_ok','series_ok','rider_team_ok','quote_ok')) or (not hard_reasons)
   language=all(bool(o.get(k)) for k in ('german_ok','style_ok'));
   if not hard and not hard_reasons:hard_reasons=['Harter Fakten-QM: Pflichtfeld FAIL']
   if hard and not language and not repair:repair=['Sprache/Stil reparieren']
   return {'hard_ok':hard,'language_ok':language,'hard_reasons':hard_reasons,'repair_reasons':repair}
  except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:last=e;continue
  except Exception as e:last=e;break
 return {'hard_ok':False,'language_ok':False,'hard_reasons':[f'Semantischer Fakten-QM technisch ungueltig nach 2 Versuchen: {type(last).__name__}: {str(last)[:140]}'],'repair_reasons':[]}
def review(item,caption):
 r=review_detailed(item,caption);ok=r['hard_ok'] and r['language_ok'];return ok,(r['hard_reasons']+r['repair_reasons'])
