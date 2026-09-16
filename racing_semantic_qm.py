"""Independent semantic source-to-caption QM for Motorcycle Racing – fail closed."""
import json,re
from llm_client import generate
BRAND_HASHTAGS={'#buelentsbikelife'}
def _clean_json(raw):
 raw=(raw or '').strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);return json.loads(raw)
def _fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def _caption_for_fact_review(caption):
 """Brand tags are editorial identity, not source facts. Rider/series/topic tags remain reviewable."""
 parts=[]
 for token in str(caption or '').split():
  if token.casefold() in BRAND_HASHTAGS:continue
  parts.append(token)
 return ' '.join(parts)
def infer_story_series(item):
 """Independent hint only; transition destination wording outranks origin mentions."""
 t=_fold(' '.join((item.get('title',''),item.get('summary',''),item.get('url',''))))
 destination=[('MotoGP',(r'(?:join|joins|joining|move|moves|moving|switch|switches|seat|debut|to)\b.{0,45}\bmotogp',r'\bmotogp\b.{0,45}\b(?:2027|next season|next year)')),('WorldSBK',(r'(?:join|joins|joining|move|moves|moving|switch|switches|to)\b.{0,45}\b(?:worldsbk|world superbike)',)),('WorldSSP',(r'(?:join|joins|joining|move|moves|moving|switch|switches|to)\b.{0,45}\b(?:worldssp|world supersport|supersport)',))]
 for series,patterns in destination:
  if any(re.search(p,t) for p in patterns):return series
 if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
 if 'worldssp' in t or 'world supersport' in t:return 'WorldSSP'
 if 'worldsbk' in t or 'world superbike' in t:return 'WorldSBK'
 if any(x in t for x in ('motogp','moto2','moto3')):return 'MotoGP'
 return str(item.get('series','')).strip() or 'nicht eindeutig'
def _prompt(item,caption):
 title=str(item.get('title','')).strip();summary=str(item.get('summary','')).strip();declared=str(item.get('series','')).strip() or 'nicht angegeben';inferred=infer_story_series(item);url=str(item.get('url','')).strip();fact_caption=_caption_for_fact_review(caption)
 return f'''Du bist ein unabhaengiger Senior-Faktenpruefer fuer Motorrad-Racing auf Premium-Niveau. Mindestens zehn Jahre professionelle Faktenpruefung sind der Qualitaetsmassstab, keine zu behauptende Biografie. Pruefe den fertigen deutschen Social-Post SATZ FUER SATZ ausschliesslich gegen die gelieferten Quellenfakten.\n\nQUELLFAKTEN:\nDEKLARIERTE SERIE: {declared}\nUNABHAENGIGER SERIEN-HINWEIS AUS STORYTEXT: {inferred}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nURL: {url}\n\nPOST OHNE REINEN MARKENHASHTAG:\n{fact_caption}\n\nHARTE REGELN:\n1. Jede Tatsachenbehauptung muss eindeutig durch Titel/Zusammenfassung/Metadaten gedeckt sein.\n2. Erfunden, vertauscht oder falsch zugeordnet bei Fahrer, Team, Hersteller, Serie/Klasse, Jahr, Ort, Ergebnis, Rekord, Zahl, Titel/Champion-Status oder Beziehung => FAIL.\n3. Bei Transfer-/Wechselstories Herkunft und Zielserie sauber unterscheiden. Widerspricht die deklarierte Serie dem klaren Storytext, FAIL mit konkretem Grund.\n4. Keine Schlussfolgerung als Tatsache, wenn die Quelle sie nicht sagt.\n5. Direkte oder frei uebersetzte Zitate => FAIL; gedeckte Paraphrase ist erlaubt.\n6. Natuerliches korrektes idiomatisches Deutsch ist Pflicht. Wortsalat, Grammatikfehler, Lehnuebersetzung, PR-Sprech oder kuenstlicher Hype => FAIL.\n7. Community-Frage darf keine unbelegte Tatsache voraussetzen.\n8. Fachliche Hashtags auf falsche Fahrer/Serie/Thema pruefen. Der feste Markenhashtag #BuelentsBikeLife ist redaktionelle Identitaet und benoetigt KEINEN Quellenbeleg; er wurde vor diesem Faktencheck entfernt und darf niemals deshalb beanstandet werden.\n9. Bei Unsicherheit => FAIL.\nAntworte NUR mit syntaktisch gueltigem JSON, ohne Markdown: {{"pass":true|false,"reasons":["..."],"unsupported_claims":["..."],"series_ok":true|false,"rider_team_ok":true|false,"german_ok":true|false,"quote_ok":true|false}}'''
def review(item,caption):
 prompt=_prompt(item,caption);last=None
 for technical_attempt in range(2):
  try:
   o=_clean_json(generate('racing_semantic_qm',prompt));ok=all(bool(o.get(k)) for k in ('pass','series_ok','rider_team_ok','german_ok','quote_ok'));reasons=[str(x) for x in o.get('reasons',[]) if str(x).strip()];unsupported=[str(x) for x in o.get('unsupported_claims',[]) if str(x).strip()];reasons += ['Nicht belegt: '+x for x in unsupported]
   if not ok and not reasons:reasons=['Semantischer Fakten-QM: nicht alle Pflichtfelder PASS']
   return ok,reasons
  except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:
   last=e
   if technical_attempt==0:continue
  except Exception as e:
   last=e;break
 return False,[f'Semantischer Fakten-QM nicht verfuegbar/ungueltig nach technischem Retry: {type(last).__name__}: {str(last)[:140]}']
