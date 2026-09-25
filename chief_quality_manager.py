"""Zentrale, fail-closed End-QM-Schicht fuer KI-SOCIAL-AGENT – Human Writing Protocol V1.0."""
from pathlib import Path
from datetime import datetime,timezone
import re
from racing_language_rules import deterministic_errors as racing_lexicon_errors
LOG=Path('memory/QUALITY_MANAGER_LOG.md');PROTOCOL=Path('config/HUMAN_WRITING_PROTOCOL.md')
BAD_LANGUAGE=()
AI_PHRASES=('natürlich!','gerne!','selbstverständlich!','lassen sie uns','es ist wichtig zu beachten','zusammenfassend lässt sich sagen','abschließend lässt sich festhalten','ich hoffe, das hilft','als ki','als sprachmodell','ich habe den text bewusst','der folgende text klingt natürlich')
PR_WORDS=('bahnbrechend','wegweisend','erstklassig','immense bedeutung','entscheidenden wendepunkt','weitreichende auswirkungen','stellt einen meilenstein dar','verpasst nicht')
BAD_REDUNDANCY=(r'\bbestaetig\w*\b.{0,55}\bbestaetig\w*\b',r'\bbestatig\w*\b.{0,55}\bbestatig\w*\b')
INTERNAL_MARKERS=('turn0search','turn1search','contentreference','oaicite','system prompt','interne tool-id')
def _fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ä','a').replace('ş','s').replace('ç','c')
def _log(domain,item,ok,errors):
 LOG.parent.mkdir(parents=True,exist_ok=True);old=LOG.read_text(encoding='utf-8') if LOG.exists() else '# Chief Quality Manager Log\n\n';title=item.get('title','ohne Titel');state='PASS' if ok else 'FAIL';row=f'## {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} | {domain} | {state}\nTitel: {title}\nStory-Key: {item.get("story_key","")}\nGründe: {"; ".join(errors) if errors else "alle Gates bestanden"}\nHuman-Writing-Protocol: V1.0\n\n';LOG.write_text(old+row,encoding='utf-8')
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
 if domain=='Motorcycle Racing':errors.extend('Human-Protocol FAIL: '+e for e in racing_lexicon_errors(caption))
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
