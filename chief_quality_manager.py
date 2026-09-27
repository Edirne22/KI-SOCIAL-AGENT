"""Zentrale, fail-closed End-QM-Schicht fuer KI-SOCIAL-AGENT – Human Writing Protocol V1.0."""
from pathlib import Path
from datetime import datetime,timezone
import re
from racing_language_rules import deterministic_errors as racing_lexicon_errors
from turkish_rider_names import CANONICAL_ALIASES
LOG=Path('memory/QUALITY_MANAGER_LOG.md');PROTOCOL=Path('config/HUMAN_WRITING_PROTOCOL.md')
BAD_LANGUAGE=()
AI_PHRASES=('natürlich!','gerne!','selbstverständlich!','lassen sie uns','es ist wichtig zu beachten','zusammenfassend lässt sich sagen','abschließend lässt sich festhalten','ich hoffe, das hilft','als ki','als sprachmodell','ich habe den text bewusst','der folgende text klingt natürlich')
PR_WORDS=('bahnbrechend','wegweisend','erstklassig','immense bedeutung','entscheidenden wendepunkt','weitreichende auswirkungen','stellt einen meilenstein dar','verpasst nicht')
BAD_REDUNDANCY=(r'\bbestaetig\w*\b.{0,55}\bbestaetig\w*\b',r'\bbestatig\w*\b.{0,55}\bbestatig\w*\b')
INTERNAL_MARKERS=('turn0search','turn1search','contentreference','oaicite','system prompt','interne tool-id')
def _fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ä','a').replace('ş','s').replace('ç','c')
def _log(domain,item,ok,errors):
 LOG.parent.mkdir(parents=True,exist_ok=True);old=LOG.read_text(encoding='utf-8') if LOG.exists() else '# Chief Quality Manager Log\n\n';title=item.get('title','ohne Titel');state='PASS' if ok else 'FAIL';row=f'## {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} | {domain} | {state}\nTitel: {title}\nStory-Key: {item.get("story_key","")}\nGründe: {"; ".join(errors) if errors else "alle Gates bestanden"}\nHuman-Writing-Protocol: V1.0\n\n';LOG.write_text(old+row,encoding='utf-8')
def _source_names(item):
 text=' '.join(str(item.get(k,'')) for k in ('title','summary','video_transcript'))
 return {m.group(0) for m in re.finditer(r"(?<![#@])\\b[A-ZÄÖÜ][A-Za-zÀ-ž’'-]{3,}\\b",text)}
def _one_edit_or_transposition(a,b):
 if a==b:return False
 if abs(len(a)-len(b))>1:return False
 if len(a)==len(b):
  diffs=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
  if len(diffs)==1:return True
  return len(diffs)==2 and diffs[1]==diffs[0]+1 and a[diffs[0]]==b[diffs[1]] and a[diffs[1]]==b[diffs[0]]
 short,long=(a,b) if len(a)<len(b) else (b,a)
 i=j=diffs=0
 while i<len(short) and j<len(long):
  if short[i]==long[j]:i+=1;j+=1
  else:diffs+=1;j+=1
  if diffs>1:return False
 return True
def _editorial_text(caption):
 text=str(caption or '').split('Quelle / weitere Infos:',1)[0]
 return re.sub(r'(?m)^\\s*#[^\\n]*$','',text)
def _name_spelling_errors(item,caption):
 source_fold={_fold(n):n for n in _source_names(item)}
 source_text=_fold(' '.join(str(item.get(k,'')) for k in ('title','summary','video_transcript')))
 for canonical,aliases in CANONICAL_ALIASES.items():
  if any(_fold(a) in source_text for a in aliases):source_fold[_fold(canonical)]=canonical
 errors=[]
 for token in re.findall(r"(?<![#@])\\b[A-ZÄÖÜ][A-Za-zÀ-ž’'-]{3,}\\b",_editorial_text(caption)):
  folded=_fold(token)
  variants=[folded]
  if folded.endswith('s'):variants.append(folded[:-1])
  if any(v in source_fold for v in variants):continue
  matches=[sf for v in variants for sf in source_fold if _one_edit_or_transposition(v,sf)]
  if matches:errors.append(f'Sprach-QM FAIL: möglicher Namens-Tippfehler {token} (Quelle: {source_fold[matches[0]]})')
 return errors
def _german_sentence_errors(caption):
 low=_fold(_editorial_text(caption))
 patterns=((r'\\bweltmeister\\s+20\\d{2}\\s+(?:motogp|worldsbk|worldssp)\\s+(?:fest|steht)\\b','unidiomatische Titel-/Serien-Wortstellung'),(r'\\bsteht\\s+mit\\s+platz\\s+\\w+\\s+(?:plotzlich\\s+)?als\\s+weltmeister\\b','unidiomatische Weltmeister-Formulierung'))
 return ['Sprach-QM FAIL: '+label for pattern,label in patterns if re.search(pattern,low)]

def human_text_review(domain,item,caption):
 errors=[];low=_fold(caption or '')
 if not caption.strip():errors.append('Copy fehlt')
 if any(x in low for x in ('social-text','redaktion','die fakten stammen aus der offiziellen meldung','eines der relevanten')):errors.append('interne/generische Meta-Sprache')
 bad=[p for p in BAD_LANGUAGE if _fold(p) in low]
 if bad:errors.append('Sprach-QM FAIL: '+', '.join(bad))
 if any(_fold(p) in low for p in AI_PHRASES):errors.append('Human-Protocol FAIL: KI-/Vorlagen-Floskel')
 if any(_fold(p) in low for p in PR_WORDS):errors.append('Human-Protocol FAIL: unbelegte PR-/Hype-Sprache')
 if any(re.search(p,low) for p in BAD_REDUNDANCY):errors.append('Sprach-QM FAIL: redundante Wiederholung')
 if any(_fold(p) in low for p in INTERNAL_MARKERS):errors.append('Human-Protocol FAIL: interner Marker im Output')
 if any(q in caption for q in ('"','“','”','„','«','»')):errors.append('Quote-Safety FAIL: direkte/übersetzte Zitate nicht freigeben')
 text_without_tags=re.sub(r'#[A-Za-z0-9ÄÖÜäöüß]+','',caption)
 sentence_count=len(re.findall(r'[^.!?\n][.!?](?:\s|$)',text_without_tags.strip()))
 if sentence_count<2:errors.append('Struktur-QM FAIL: mindestens 2 Sätze erforderlich')
 if len(re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption))<3:errors.append('zu wenige relevante Hashtags')
 if domain=='Motorcycle Racing':
  errors.extend('Human-Protocol FAIL: '+e for e in racing_lexicon_errors(caption))
  errors.extend(_name_spelling_errors(item,caption))
  errors.extend(_german_sentence_errors(caption))
 return not errors,errors

def review(domain,item,caption,media_path='',source_url='',domain_reviewer=None):
 ok,errors=human_text_review(domain,item,caption);errors=list(errors)
 if not source_url.startswith('http'):errors.append('belastbare Quelle fehlt')
 if not media_path or media_path.strip().casefold()=='auto':errors.append('publishbares Medium fehlt')
 elif not Path(media_path).is_file():errors.append('Medienpfad existiert nicht')
 if domain_reviewer:
  domain_ok,de=domain_reviewer(item,caption)
  if not domain_ok:errors.extend('Domain-QM: '+e for e in de)
 if domain=='Motorcycle Racing':
  from racing_final_guard import review as final_truth_review
  truth_ok,truth_errors=final_truth_review(item,caption)
  if not truth_ok:errors.extend(truth_errors)
 ok=not errors;_log(domain,item,ok,errors);return ok,errors
def review_batch(domain,items,domain_reviewer=None):
 results=[];seen=set()
 for item in items:
  caption=item.get('caption','');fp=re.sub(r'#[^\s]+','',caption.casefold());fp=re.sub(r'\s+',' ',fp).strip();ok,errors=review(domain,item,caption,item.get('instagram_media',''),item.get('url',''),domain_reviewer)
  if fp in seen:ok=False;errors=errors+['Copy-Duplikat im Batch'];_log(domain,item,False,['Copy-Duplikat im Batch'])
  seen.add(fp);results.append((ok,errors))
 return results
