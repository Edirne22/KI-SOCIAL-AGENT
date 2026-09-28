"""Independent semantic source-to-caption QM for Motorcycle Racing – SOURCE-FACT-CONTRACT-V1, fail closed."""
import json,re
from llm_client import generate,redact_secrets
from racing_language_rules import prompt_contract as racing_lexicon_contract
from racing_event_contract import source_event_contract, session_errors
from racing_source_claim_guard import claim_strength_errors

BRAND_HASHTAGS={'#buelentsbikelife'}
SOURCE_FACT_CONTRACT_VERSION='SOURCE-FACT-CONTRACT-V1'
_ALLOWED_EVIDENCE_FIELDS={'series','title','summary'}

class SemanticContractError(ValueError):
 def __init__(self,stage,reason):
  super().__init__(reason);self.stage=stage

def _diag_response(raw,limit=240):
 text=redact_secrets(str(raw or '')).replace('\r',' ').replace('\n',' ')
 text=re.sub(r'\s+',' ',text).strip()
 return text[:limit]

def _contract_error(stage,reason):raise SemanticContractError(stage,reason)

def _clean_json(raw):
 raw=(raw or '').strip()
 raw=re.sub(r'^\`\`\`(?:json)?\s*|\s*\`\`\`$','',raw,flags=re.I|re.S).strip()
 try:return json.loads(raw)
 except json.JSONDecodeError as first:
  # Recover one complete top-level JSON object from harmless provider prose.
  start=raw.find('{')
  if start<0:raise
  depth=0;quoted=False;escaped=False
  for i,ch in enumerate(raw[start:],start):
   if quoted:
    if escaped:escaped=False
    elif ch=='\\':escaped=True
    elif ch=='"':quoted=False
    continue
   if ch=='"':quoted=True
   elif ch=='{':depth+=1
   elif ch=='}':
    depth-=1
    if depth==0:
     candidate=raw[start:i+1]
     try:return json.loads(candidate)
     except json.JSONDecodeError:raise first
  raise first
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

def _locked_metadata(item):
 out={'event_session':source_event_contract(item)}
 for key in ('source_series','trusted_series','riders','numbers'):
  value=item.get(key)
  if value not in (None,'',[],{}):out[key]=value
 return out

def _source_fields(item):
 return {'series':infer_story_series(item),'title':str(item.get('title','')).strip(),'summary':str(item.get('summary','')).strip(),'locked_metadata':_locked_metadata(item)}

def _evidence_exists(item,evidence):
 field=str(evidence.get('source_field','')).strip();quote=str(evidence.get('quote','')).strip()
 if not quote:return False
 fields=_source_fields(item)
 if field in _ALLOWED_EVIDENCE_FIELDS:return _fold(quote) in _fold(fields[field])
 if field.startswith('locked_metadata.'):
  key=field.split('.',1)[1]
  if key not in fields['locked_metadata']:return False
  value=fields['locked_metadata'][key]
  text=' '.join(map(str,value)) if isinstance(value,(list,tuple,set)) else str(value)
  return _fold(quote) in _fold(text)
 return False

def _validate_contract(item,o):
 if o.get('contract_version')!=SOURCE_FACT_CONTRACT_VERSION:_contract_error('contract_version','SOURCE-FACT-CONTRACT version missing/invalid')
 if o.get('coverage_complete') is not True:_contract_error('coverage','coverage_complete must be true')
 claims=o.get('claims')
 if not isinstance(claims,list) or not claims:_contract_error('claims','claims missing/empty')
 hard_reasons=[];normalized=[]
 for claim in claims:
  if not isinstance(claim,dict):_contract_error('claim_schema','claim must be object')
  text=str(claim.get('claim','')).strip();kind=claim.get('claim_type');status=claim.get('status');evidence=claim.get('source_evidence',[])
  if not text or kind not in ('FACT','OPINION_QUESTION') or status not in ('SUPPORTED','UNSUPPORTED') or not isinstance(evidence,list):_contract_error('claim_schema','claim schema invalid')
  if status=='SUPPORTED' and kind=='FACT':
   if not evidence or not all(isinstance(e,dict) and _evidence_exists(item,e) for e in evidence):_contract_error('evidence',f'FACT evidence invalid: {text[:80]}')
  # Only unsupported factual assertions are hard failures. A genuinely open
  # opinion/community question is not a source-fact claim and must not kill
  # an otherwise verified Racing story.
  if status=='UNSUPPORTED' and kind=='FACT':
   hard_reasons.append(f'UNSUPPORTED: {text}')
  normalized.append({'claim':text,'claim_type':kind,'status':status,'source_evidence':evidence})
 hard=not hard_reasons and all(c['status']=='SUPPORTED' for c in normalized if c['claim_type']=='FACT')
 return hard,hard_reasons,normalized

def _prompt(item,caption):
 fields=_source_fields(item);url=str(item.get('url','')).strip();trusted=_system_hashtags(caption);fact_caption=_caption_for_fact_review(caption,trusted)
 return f'''Du bist unabhaengiger Senior-Faktenpruefer fuer Motorrad-Racing. Arbeite strikt nach {SOURCE_FACT_CONTRACT_VERSION}.
ERLAUBTE QUELLFAKTEN:
SERIE: {fields["series"]}
TITEL: {fields["title"]}
ZUSAMMENFASSUNG: {fields["summary"]}
LOCKED_METADATA: {json.dumps(fields["locked_metadata"],ensure_ascii=False)}
URL (nur Provenienz, KEINE Faktenquelle): {url}
POST:
{fact_caption}

SOURCE-FACT-CONTRACT-V1:
1. Zerlege ALLE expliziten und impliziten Tatsachenbehauptungen in einzelne FACT-Claims. Zusammengesetzte Aussagen aufteilen.
2. Neue Formulierung ist erlaubt. Neue Information ist verboten. Nutze ausschließlich Serie, Titel, Zusammenfassung und LOCKED_METADATA. Kein Vorwissen, keine Websuche, keine Plausibilität.
3. Jeder SUPPORTED FACT braucht source_evidence mit source_field und einem EXAKTEN, wörtlich in diesem Quellfeld vorhandenen quote. Semantische Paraphrase ist erlaubt, aber der Beleg muss wörtlich aus der Quelle stammen.
4. Kann ein FACT keiner konkreten Quellaussage eindeutig zugeordnet werden: status=UNSUPPORTED. Ein UNSUPPORTED Claim bedeutet HARD FAIL.
5. Meinungsfragen ohne Tatsachenprämisse sind OPINION_QUESTION. Enthält eine Frage eine Tatsachenprämisse, erfasse diese zusätzlich als eigenen FACT.
6. coverage_complete=true NUR wenn wirklich alle Tatsachenbehauptungen des Posts erfasst wurden. Unsicherheit => coverage_complete=false.
7. URL und systemgenerierte Hashtags sind niemals Faktenquellen.
8. Datumsangaben der Quelle gelten als aktuell; kein Knowledge-Cutoff-Einwand.

REPARIERBAR: Tippfehler, Grammatik, holpriges Deutsch, Anglizismus, PR-Sprech oder künstlicher Hype => german_ok/style_ok=false, nicht automatisch Faktenfehler.

{racing_lexicon_contract('SEMANTIC-QM')}
Antworte NUR JSON:
{{"contract_version":"SOURCE-FACT-CONTRACT-V1","coverage_complete":true|false,"claims":[{{"claim":"...","claim_type":"FACT|OPINION_QUESTION","status":"SUPPORTED|UNSUPPORTED","source_evidence":[{{"source_field":"title|summary|series|locked_metadata.<key>","quote":"exakter Quelltext"}}]}}],"german_ok":true|false,"style_ok":true|false,"repair_reasons":["..."]}}'''

def review_detailed(item,caption):
 deterministic=session_errors(item,caption,'Semantic-QM')
 if deterministic:
  return {'hard_ok':False,'language_ok':True,'hard_reasons':deterministic,'repair_reasons':[],'claims':[],'coverage_complete':False,'contract_version':SOURCE_FACT_CONTRACT_VERSION,'technical_error':False}
 prompt=_prompt(item,caption);raw=''
 try:
  raw=generate('racing_semantic_qm',prompt)
  o=_clean_json(raw)
  hard,hard_reasons,claims=_validate_contract(item,o)
  language=all(o.get(k) is True for k in ('german_ok','style_ok'))
  repair=[str(x) for x in o.get('repair_reasons',[]) if str(x).strip()]
  if hard and not language and not repair:repair=['Sprache/Stil reparieren']
  return {'hard_ok':hard,'language_ok':language,'hard_reasons':hard_reasons,'repair_reasons':repair,'claims':claims,'coverage_complete':True,'contract_version':SOURCE_FACT_CONTRACT_VERSION,'technical_error':False}
 except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:
  stage=getattr(e,'stage','json_parse' if isinstance(e,json.JSONDecodeError) else 'response_validation')
  reason=str(e)[:140];diag=_diag_response(raw)
  return {'hard_ok':False,'language_ok':False,'hard_reasons':[f'Semantischer Fakten-QM technisch ungueltig: {type(e).__name__}: {reason}'],'repair_reasons':[],'claims':[],'coverage_complete':False,'contract_version':SOURCE_FACT_CONTRACT_VERSION,'technical_error':True,'technical_reason':type(e).__name__,'technical_stage':stage,'technical_detail':reason,'response_diagnostic':diag}
 except Exception as e:
  return {'hard_ok':False,'language_ok':False,'hard_reasons':[f'Semantischer Fakten-QM Provider nicht verfuegbar: {type(e).__name__}: {str(e)[:140]}'],'repair_reasons':[],'claims':[],'coverage_complete':False,'contract_version':SOURCE_FACT_CONTRACT_VERSION,'technical_error':True,'technical_reason':type(e).__name__}

def review(item,caption):
 r=review_detailed(item,caption);ok=r['hard_ok'] and r['language_ok'];return ok,(r['hard_reasons']+r['repair_reasons'])
