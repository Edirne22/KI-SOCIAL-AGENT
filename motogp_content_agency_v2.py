"""Motorcycle Racing Agency V8.5.4 – source-locked series, freshness diagnostics, QM feedback loop."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from racing_semantic_qm import review_detailed as semantic_review_detailed
from turkish_riders_scout import scout as turkish_scout, racing_scout
from llm_client import generate,global_professional_context
from pathlib import Path
from datetime import timedelta,datetime as dt,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import json,re,time
VERSION='V8.5.4';TOP10=Path('memory/RACING_TOP10_POOL.json')
VALID_SERIES=('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300')
TURKISH_ALIASES={'Toprak Razgatlioglu':('toprak razgatlioglu','toprak razgatlıoğlu'),'Can Oncu':('can oncu','can öncü'),'Deniz Oncu':('deniz oncu','deniz öncü'),'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu')}
RIDERS_V2=list(TURKISH_ALIASES)+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado','Alvaro Bautista','Miguel Oliveira','Alberto Surra','Sergio Garcia','Iker Lecuona','Andrea Iannone','Sam Lowes','Alex Lowes','Jonathan Rea','Stefano Manzi','Jeremy Alcoba','Marcos Ramirez']
PROMO_WORDS=('fantasy','super boost','mystery boost','videopass','video pass','tickets','ticket','store','merch','merchandise','shop','giveaway','promo code','promotion','behind the scenes','catch up on','vlog')
RACING_WORDS=('race','racing','grand prix',' gp','practice','fp1','fp2','qualifying','pole','sprint','podium','win','victory','championship','title','rider','team','replace','injury','return','test','lap','grid','motogp','moto2','moto3','worldsbk','worldssp','supersport')
FEATURE_WORDS=('hall of fame','legend','inducted','tribute','anniversary','documentary','gallery','talking points')
BAD_GERMAN=('legende zu einer legende','mit großem anfangsbuchstaben','mit grossem anfangsbuchstaben','erfahrt alle wichtigen','zurück auf die zeichentafel','zurueck auf die zeichentafel','airtime zum testen')
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def article_text(x):return ' '.join((x.get('title',''),x.get('summary',''),x.get('url','')))
def riders_in(text):
 low=fold(text);out=[]
 for n in RIDERS_V2:
  full=fold(n);last=full.split()[-1]
  if full in low or (len(last)>=5 and re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',low)):out.append(n)
 return list(dict.fromkeys(out))
def detect_turkish_rider(x):
 text=fold(article_text(x))
 for rider,aliases in TURKISH_ALIASES.items():
  if any(fold(a) in text for a in aliases):return rider
 return ''
def enrich_turkish(x):
 r=x.get('turkish_rider') or detect_turkish_rider(x)
 if r:x['turkish_rider']=r
 return x
def _transfer_destination(story):
 s=fold(story)
 if 'motogp' in s and any(p in s for p in ('join motogp','joins motogp','to motogp','motogp switch','moves to motogp','move to motogp','switch to motogp','motogp debut')):return 'MotoGP'
 if ('worldsbk' in s or 'world superbike' in s) and any(p in s for p in ('join worldsbk','joins worldsbk','to worldsbk','worldsbk switch','moves to worldsbk','move to worldsbk','switch to worldsbk')):return 'WorldSBK'
 return ''
def lock_source_series(x,declared=None):
 d=(declared or x.get('source_series') or x.get('series') or '').strip();transfer=_transfer_destination(' '.join((x.get('title',''),x.get('summary',''))))
 if transfer:x['series']=transfer;x['series_locked']=True;x['series_origin']='explicit-transfer';return x
 if d in VALID_SERIES:x['series']=d;x['source_series']=d;x['series_locked']=True;x['series_origin']='official-feed';return x
 return x
def series_for_raw(x):
 transfer=_transfer_destination(' '.join((x.get('title',''),x.get('summary',''))))
 if transfer:return transfer
 locked=str(x.get('source_series') or (x.get('series') if x.get('series_locked') else '')).strip()
 if locked in VALID_SERIES:return locked
 u=fold(x.get('url',''));t=fold(article_text(x))
 if 'worldwcr' in t:return 'WorldWCR'
 if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
 if any(v in t for v in ('worldssp','world supersport','supersport')) and 'motogp' not in t:return 'WorldSSP'
 if 'worldsbk' in t or 'world superbike' in t:return 'WorldSBK'
 if re.search(r'(?<![a-z0-9])moto3(?![a-z0-9])',t):return 'Moto3'
 if re.search(r'(?<![a-z0-9])moto2(?![a-z0-9])',t):return 'Moto2'
 if re.search(r'(?<![a-z0-9])motogp(?![a-z0-9])',t):return 'MotoGP'
 declared=str(x.get('series','')).strip()
 if declared in VALID_SERIES:return declared
 if 'worldsbk.com' in u:return 'WorldSBK'
 return 'MotoGP'
def series_for(x):return series_for_raw(x)
def is_gp_family(x):return series_for(x) in ('MotoGP','Moto2','Moto3')
def is_turkish_focus(x):return bool(enrich_turkish(x).get('turkish_rider'))
_MONTHS={'jan':1,'feb':2,'mar':3,'apr':4,'may':5,'jun':6,'jul':7,'aug':8,'sep':9,'oct':10,'nov':11,'dec':12}
def _official_gp_event_end_date(x):
 """Recover the end date only from MotoGP official Grand Prix hub titles.
 This is intentionally narrow: no guessed dates and no third-party text.
 Examples: '11 - 13 Sep 2026' and '27 Feb - 1 Mar 2026'.
 """
 url=(x.get('url') or '').lower();title=' '.join(str(x.get('title') or '').split())
 if 'motogp.com/' not in url or '/news/grand-prix/' not in url:return None
 # Cross-month range: 27 Feb - 1 Mar 2026 -> use official event end date.
 m=re.search(r'\b\d{1,2}\s+([A-Za-z]{3})\s*-\s*(\d{1,2})\s+([A-Za-z]{3})\s+(20\d{2})\b',title,re.I)
 if m:
  mon=_MONTHS.get(m.group(2).lower())
  if mon:
   try:return dt(int(m.group(3)),mon,int(m.group(1)),tzinfo=timezone.utc)
   except ValueError:return None
 # Same-month range: 11 - 13 Sep 2026 -> use official event end date.
 m=re.search(r'\b\d{1,2}\s*-\s*(\d{1,2})\s+([A-Za-z]{3})\s+(20\d{2})\b',title,re.I)
 if m:
  mon=_MONTHS.get(m.group(2).lower())
  if mon:
   try:return dt(int(m.group(3)),mon,int(m.group(1)),tzinfo=timezone.utc)
   except ValueError:return None
 return None
def article_date(x):
 for key in ('published_at','published','date','pub_date'):
  v=x.get(key)
  if v:
   try:return dt.fromisoformat(str(v).replace('Z','+00:00')).astimezone(timezone.utc)
   except Exception:pass
 m=re.search(r'/(20\d{2})/(\d{2})/(\d{2})/',x.get('url',''))
 if m:
  try:return dt(int(m.group(1)),int(m.group(2)),int(m.group(3)),tzinfo=timezone.utc)
  except ValueError:pass
 return _official_gp_event_end_date(x)
def age_days(x,now):
 d=article_date(x);return (now-d).total_seconds()/86400 if d else 9999
def current_news(x,now,max_days=7):return x.get('kind','news')!='profile' and 0<=age_days(x,now)<=max_days
def freshness_reason(x,now,max_days=7):
 if x.get('kind','news')=='profile':return 'profile'
 d=article_date(x)
 if not d:return 'missing-date'
 age=(now-d).total_seconds()/86400
 if age<0:return 'future-date'
 if age>max_days:return 'older-than-7d'
 if not racing_relevant(x):return 'not-racing-or-promo'
 return 'fresh'
def freshness_diagnostics(items,now):
 reasons=Counter(freshness_reason(x,now) for x in items);by_series={}
 for s in VALID_SERIES:
  rows=[x for x in items if series_for(x)==s];by_series[s]={'raw':len(rows),'fresh':sum(freshness_reason(x,now)=='fresh' for x in rows),'missing_date':sum(freshness_reason(x,now)=='missing-date' for x in rows),'old':sum(freshness_reason(x,now)=='older-than-7d' for x in rows),'promo_irrelevant':sum(freshness_reason(x,now)=='not-racing-or-promo' for x in rows)}
 print('FRESHNESS DIAG reasons='+json.dumps(dict(reasons),ensure_ascii=False,sort_keys=True));print('FRESHNESS DIAG by_series='+json.dumps(by_series,ensure_ascii=False,sort_keys=True));return reasons,by_series
def is_feature(x):return any(w in fold(article_text(x)) for w in FEATURE_WORDS)
def racing_relevant(x):
 text=fold(article_text(x));return 'worldwcr' not in text and not any(w in text for w in PROMO_WORDS) and bool(riders_in(text) or detect_turkish_rider(x) or any(w in text for w in RACING_WORDS))
def editorial_score(x,names):
 age=max(0,age_days(x,dt.now(timezone.utc)));fresh=max(0,80-int(age*10));text=fold(article_text(x));sport=sum(12 for w in ('win','victory','pole','podium','championship','title','race','sprint','qualifying','injury','return','replace') if w in text);live=35 if any(w in text for w in ('race','sprint','qualifying','practice','fp1','fp2','championship','standings','injury','return','replace')) else 0
 return fresh+score(x.get('title',''),names)+sport+live+(30 if is_turkish_focus(x) else 0)+(-45 if is_feature(x) else 0)
def hashtags(x):
 s=series_for(x);series_tag={'Moto2':'#Moto2','Moto3':'#Moto3','WorldSSP':'#WorldSSP','WorldSSP300':'#WorldSSP300','WorldSBK':'#WorldSBK'}.get(s,'#MotoGP');names=riders_in(article_text(x));r=x.get('turkish_rider') or detect_turkish_rider(x)
 if r and r not in names:names.insert(0,r)
 tags=[series_tag]+['#'+re.sub(r'[^A-Za-z0-9]','',fold(n).title().replace(' ','')) for n in names[:2]]+['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def language_sane(caption):
 low=fold(caption);return not any(fold(x) in low for x in BAD_GERMAN) and not any(x in low for x in ('click here','read more','find out more','latest edition','talking points:'))
def _editor_prompt(x,repair_reasons=None):
 enrich_turkish(x);repair=''
 if repair_reasons:repair='\nRUECKGABE AUS DER QM-KETTE. Analysiere die Originalfakten erneut und behebe exakt diese Punkte. FAKTEN DUERFEN WEDER ERGAENZT NOCH VERAENDERT WERDEN:\n- '+'\n- '.join(repair_reasons[:10])+'\n'
 title=' '.join(str(x.get('title','')).split());summary=' '.join(str(x.get('summary','')).split());series=series_for(x);turkish=x.get('turkish_rider') or 'NEIN'
 return f'''Du arbeitest als Senior-Motorrad-Racing-Redakteur fuer Buelents Bike Life auf Premium-Niveau.\n{global_professional_context()}\nRACING-PFLICHTEN: SERIE ist deterministisch aus der offiziellen Quelle gesperrt und darf nicht umgedeutet werden. Die Quelle liefert nur Fakten – der fertige Post muss in Buelents eigener, direkten, leidenschaftlichen und natuerlichen Bike-Life-Stimme neu formuliert sein. Kein Kopieren der Quellensprache. Nur Tatsachen aus TITEL/ZUSAMMENFASSUNG verwenden. Keine Namen, Teams, Hersteller, Nationalitaeten, Serien, Orte, Jahre, Zahlen, Ergebnisse, Titel oder Beziehungen aus Vorwissen ergaenzen. P1 niemals als Q1 interpretieren. Keine direkten oder frei uebersetzten Zitate. Korrektes idiomatisches Deutsch, kein PR-Sprech, kein KI-Sprech, kein kuenstlicher Hype. 2–4 informative Saetze und danach eine konkrete Community-Frage. Keine Hashtags erzeugen.{repair}\nSERIE: {series}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nTURKISH_RIDER: {turkish}\nAntworte nur JSON: {{"hook":"...","body":"...","question":"..."}}'''
def _parse_editor_json(raw):
 raw=(raw or '').strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);o=json.loads(raw);hook=str(o.get('hook','')).strip();body=str(o.get('body','')).strip();q=str(o.get('question','')).strip()
 if not hook or not body or '?' not in q:raise ValueError('editor JSON missing hook/body/question')
 return hook,body,q
def german_editor(x,repair_reasons=None):
 if len(re.sub(r'\s+',' ',x.get('title','')).strip())<18:return ''
 last=None
 for technical_attempt in range(3):
  try:
   hook,body,q=_parse_editor_json(generate('final_captions',_editor_prompt(x,repair_reasons)))
   if not x.get('turkish_rider'):hook=hook.replace('🇹🇷','').strip()
   return f'{hook}\n\n{body}\n\n{q}\n\n{hashtags(x)}'
  except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:last=e;time.sleep(.5)
  except Exception as e:last=e;break
 print('EDITOR EXCEPTION:',type(last).__name__,str(last)[:180]);return ''
def reanalyse_source(x,reasons):
 """Return a failed item to research, refresh official facts, preserve deterministic metadata, then resend to editor."""
 keep={k:x.get(k) for k in ('source_series','series','series_locked','series_origin','turkish_rider','kind','fallback_yesterday') if x.get(k) not in (None,'')}
 try:
  fresh=article_info(x.get('title',''),x.get('url',''))
  for k in ('title','summary','preview','published_at'):
   if fresh.get(k):x[k]=fresh[k]
 except Exception as e:print('SOURCE RE-ANALYSIS FETCH FAIL:',type(e).__name__,str(e)[:160])
 x.update(keep);lock_source_series(x,keep.get('source_series') or keep.get('series'));x['research_retry_count']=x.get('research_retry_count',0)+1;x['last_qm_return']=list(reasons or [])[:10]
 print(f'QM → RESEARCH → EDITOR retry={x["research_retry_count"]}:',x.get('title','')[:90]);return x
def qualify_copy(x,initial_reasons=None):
 if not racing_relevant(x):return False
 lock_source_series(x);repair_reasons=initial_reasons
 for attempt in (1,2,3):
  x['caption']=german_editor(x,repair_reasons)
  if not x['caption']:repair_reasons=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REPAIR attempt={attempt}:',x.get('title','')[:90]);continue
  r_ok,r_err=racing_review(x,x['caption']);x['qm_errors']=r_err
  if not r_ok:
   if attempt<3:repair_reasons=['Racing-QM: '+e for e in r_err];reanalyse_source(x,repair_reasons);continue
   print('RACING-QM HARD REJECT after feedback loop:',x.get('title','')[:90],'|','; '.join(r_err)[:600]);break
  sem=semantic_review_detailed(x,x['caption']);x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
  if sem['ok'] and language_sane(x['caption']):return True
  reasons=['Semantic-QM: '+e for e in x['semantic_errors']]
  if not language_sane(x['caption']):reasons.append('Sprach-QM: unnatuerliche/fehlerhafte Formulierung')
  if attempt<3:repair_reasons=reasons;reanalyse_source(x,repair_reasons);continue
  print('SEMANTIC-QM HARD REJECT after feedback loop:',x.get('title','')[:90],'|','; '.join(reasons)[:600]);break
 return False
def qualify_parallel(items,max_workers=3):
 out=[]
 with ThreadPoolExecutor(max_workers=max_workers) as ex:
  futures={ex.submit(qualify_copy,x):x for x in items}
  for f in as_completed(futures):
   x=futures[f]
   try:
    if f.result():out.append(x)
   except Exception as e:print('QUALIFY EXCEPTION:',type(e).__name__,str(e)[:180])
 return out
def choose_mix(items,names,limit=5):
 ranked=sorted(items,key=lambda x:editorial_score(x,names),reverse=True);picked=[];series_count=Counter()
 def take(x):
  if x in picked or len(picked)>=limit:return False
  s=series_for(x)
  if s not in ('MotoGP','Moto2','Moto3') and series_count[s]>=3:return False
  picked.append(x);series_count[s]+=1;return True
 turks=[x for x in ranked if is_turkish_focus(x)]
 if turks:take(turks[0])
 gp=[x for x in ranked if is_gp_family(x)]
 for x in gp:
  if sum(is_gp_family(y) for y in picked)>=3:break
  take(x)
 for x in ranked:take(x)
 return picked[:limit]
def load_fallback(now):
 try:rows=json.loads(TOP10.read_text(encoding='utf-8'))
 except Exception:return []
 out=[]
 for x in rows:
  if not x.get('url') or already_published(x.get('title',''),x['url']):continue
  d=article_date(x)
  if not d or not (timedelta(0)<=now-d<=timedelta(days=7)):continue
  x['fallback_yesterday']=True;lock_source_series(x);out.append(x)
 return out
def save_top10(items,now):
 rows=[]
 for x in items[:20]:
  rows.append({k:x.get(k) for k in ('title','url','summary','series','source_series','series_locked','series_origin','preview','published_at','turkish_rider','kind')})
 TOP10.parent.mkdir(parents=True,exist_ok=True);TOP10.write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
def _strip_series_claims(caption,expected):
 c=caption or ''
 for s in VALID_SERIES:
  if s!=expected:c=re.sub(r'(?i)(?:in|bei|zur|der|die|das|im|ins|für|fuer)\s+(?:der\s+)?'+re.escape(s)+r'\b','im Racing',c)
 return c
def final_series_guard(x):
 expected=series_for(x);x['caption']=_strip_series_claims(x.get('caption',''),expected);ok,err=racing_review(x,x['caption'])
 if not ok:print('FINAL SERIES GUARD REJECT:',x.get('title','')[:90],'|','; '.join(err)[:400]);return False
 return True
def select_and_finish(items,names):
 pool=list(items);final=[];rounds=0
 while pool and len(final)<5 and rounds<3:
  rounds+=1;batch=choose_mix(pool,names,5-len(final));pool=[x for x in pool if x not in batch]
  batch=[x for x in batch if final_series_guard(x)]
  if not batch:continue
  q=review_batch(batch)
  for x in batch:
   key=x.get('story_key') or x.get('url');info=q['items'].get(key,{})
   if info.get('ok'):final.append(x)
   else:print('BATCH-QM REJECT:',x.get('title','')[:90],'|','; '.join(info.get('errors',[]))[:400])
 return final[:5]
def run_v8():
 now=dt.now(timezone.utc);names=roster_names();known=known_story_keys();raw=[]
 for title,url,series,rider in racing_scout(140):
  x={'title':title,'url':url,'series':series,'source_series':series,'series_locked':True,'series_origin':'official-feed','kind':'news'}
  if rider:x['turkish_rider']=rider
  raw.append(x)
 for title,url,rider in turkish_scout(70):raw.append({'title':title,'url':url,'turkish_rider':rider,'kind':'news'})
 seen=set();base=[]
 for x in raw:
  if x['url'] in seen or already_offered_or_published(x['title'],x['url'],known):continue
  seen.add(x['url']);base.append(x)
 details=[]
 with ThreadPoolExecutor(max_workers=5) as ex:
  fs={ex.submit(article_info,x['title'],x['url']):x for x in base}
  for f in as_completed(fs):
   src=fs[f]
   try:y=f.result();y.update({k:v for k,v in src.items() if k not in y or not y.get(k)});lock_source_series(y,src.get('source_series') or src.get('series'));enrich_turkish(y);details.append(y)
   except Exception as e:print('ARTICLE EXCEPTION:',type(e).__name__,str(e)[:160])
 freshness_diagnostics(details,now);fresh=[x for x in details if freshness_reason(x,now)=='fresh'];fresh.sort(key=lambda x:editorial_score(x,names),reverse=True)
 qualified=qualify_parallel(fresh[:60]);fallback=[]
 if len(qualified)<5:
  fb=[x for x in load_fallback(now) if x.get('url') not in {q.get('url') for q in qualified}]
  fallback=qualify_parallel(fb[:max(0,5-len(qualified))]);qualified.extend(fallback)
 save_top10(qualified,now);final=select_and_finish(qualified,names)
 if len(final)<5:print(f'BATCH BLOCKED: only {len(final)}/5 after independent QMs; nothing sent.');return []
 chief_pass=[]
 for x in final:
  cr=chief_review(x,x['caption']);x['chief_qm']=cr
  if cr.get('ok'):chief_pass.append(x)
  else:print('CHIEF-QM REJECT:',x.get('title','')[:90],'|','; '.join(cr.get('errors',[]))[:500])
 if len(chief_pass)<5:print(f'CHIEF BATCH BLOCKED: only {len(chief_pass)}/5; nothing sent.');return []
 for x in chief_pass:x['preview']=x.get('preview') or image_for(x.get('url',''));x['video_preview']=x.get('video_preview') or video_for(x.get('url',''))
 turk=sum(is_turkish_focus(x) for x in chief_pass);gp=sum(is_gp_family(x) for x in chief_pass);fb=sum(bool(x.get('fallback_yesterday')) for x in chief_pass)
 head=f'🏍️ BÜLENTS BIKE LIFE – RACING NEWS\n{now:%d.%m.%Y} | {VERSION}\n\nHeute: 5 Racing-Vorschläge | MotoGP-Familie: {gp}/5 | Türkischer Fahrer: {turk}/5 | ↩️ Top-20 vom Vortag: {fb}/5\n\n'
 blocks=[]
 for i,x in enumerate(chief_pass,1):
  src=f"{x.get('title','')}\n{x.get('url','')}";label='↩️ Top-20 vom Vortag\n' if x.get('fallback_yesterday') else ''
  blocks.append(f"{i}️⃣ {label}{x['caption']}\n\n📰 Offizielle Quelle:\n{src}\n\n🖼️ Vorschau: {x.get('preview') or 'kein freigegebenes Bild gefunden'}\n🎬 Video: {x.get('video_preview') or 'kein offizieller Video-Link gefunden'}\n\nFreigabe: {i} oder alle")
 session_id=now.strftime('%Y%m%d%H%M%S');save_session({'id':session_id,'created_at':now.isoformat(),'items':chief_pass,'selected':[],'status':'awaiting_approval'});telegram((head+'\n\n━━━━━━━━━━━━━━\n\n'.join(blocks))[:4000]);return chief_pass
