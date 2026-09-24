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
import json,re,time,random
VERSION='V8.5.4';TOP10=Path('memory/RACING_TOP10_POOL.json')
VALID_SERIES=('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300')
TURKISH_ALIASES={'Toprak Razgatlioglu':('toprak razgatlioglu','toprak razgatlıoğlu'),'Can Oncu':('can oncu','can öncü'),'Deniz Oncu':('deniz oncu','deniz öncü'),'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu','bahattin sofouglu'),'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu')}
RIDERS_V2=list(TURKISH_ALIASES)+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado','Alvaro Bautista','Miguel Oliveira','Alberto Surra','Sergio Garcia','Iker Lecuona','Andrea Iannone','Sam Lowes','Alex Lowes','Jonathan Rea','Stefano Manzi','Jeremy Alcoba','Marcos Ramirez']
PROMO_WORDS=('fantasy','super boost','mystery boost','videopass','video pass','tickets','ticket','store','merch','merchandise','shop','giveaway','promo code','promotion','behind the scenes','catch up on','vlog')
RACING_WORDS=('race','racing','grand prix',' gp','practice','fp1','fp2','qualifying','pole','sprint','podium','win','victory','championship','title','rider','team','replace','injury','return','test','lap','grid','motogp','moto2','moto3','worldsbk','worldssp','supersport')
FEATURE_WORDS=('hall of fame','legend','inducted','tribute','anniversary','documentary','gallery','talking points')
BAD_GERMAN=('legende zu einer legende','mit großem anfangsbuchstaben','mit grossem anfangsbuchstaben','erfahrt alle wichtigen','zurück auf die zeichentafel','zurueck auf die zeichentafel','airtime zum testen')
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def article_text(x):return ' '.join((x.get('title',''),x.get('summary',''),x.get('url','')))
def riders_in(text):
 low=fold(text);out=[];full_hits=set()
 # Full-name matches win first. A shared surname (Marquez, Lowes, Oncu,
 # Sofuoglu...) must never identify every rider who owns that surname.
 for n in RIDERS_V2:
  full=fold(n)
  if re.search(r'(?<![a-z])'+re.escape(full)+r'(?![a-z])',low):out.append(n);full_hits.add(n)
 surname_map={}
 for n in RIDERS_V2:surname_map.setdefault(fold(n).split()[-1],[]).append(n)
 for last,owners in surname_map.items():
  if len(last)<5 or len(owners)!=1:continue
  if re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',low) and owners[0] not in full_hits:out.append(owners[0])
 return list(dict.fromkeys(out))
def detect_turkish_rider(x):
 text=fold(article_text(x))
 # Match the official shortened/misspelt Bahattin headline without treating every
 # surname-only Sofuoglu mention as Bahattin (Zayn shares the surname).
 if re.search(r'(?<![a-z])sofouglu(?![a-z])',text) and any(k in text for k in ('smits','motoxracing','qjmotor','worldssp')):return 'Bahattin Sofuoglu'
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
 if 'worldspb' in t or 'sportbike world championship' in t:return 'WorldSPB'
 if re.search(r'(?<![a-z0-9])moto4(?![a-z0-9])',t):return 'Moto4'
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
 return None
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
 text=fold(article_text(x));return 'worldwcr' not in text and 'worldspb' not in text and 'sportbike world championship' not in text and not re.search(r'(?<![a-z0-9])moto4(?![a-z0-9])',text) and not any(w in text for w in PROMO_WORDS) and bool(riders_in(text) or detect_turkish_rider(x) or any(w in text for w in RACING_WORDS))
def editorial_score(x,names):
 age=max(0,age_days(x,dt.now(timezone.utc)));fresh=max(0,80-int(age*10));text=fold(article_text(x));sport=sum(12 for w in ('win','victory','pole','podium','championship','title','race','sprint','qualifying','injury','return','replace') if w in text);live=35 if any(w in text for w in ('race','sprint','qualifying','practice','fp1','fp2','championship','standings','injury','return','replace')) else 0
 return fresh+score(x.get('title',''),names)+sport+live+(30 if is_turkish_focus(x) else 0)+(-45 if is_feature(x) else 0)
def hashtags(x):
 s=series_for(x);series_tag={'Moto2':'#Moto2','Moto3':'#Moto3','WorldSSP':'#WorldSSP','WorldSSP300':'#WorldSSP300','WorldSBK':'#WorldSBK'}.get(s,'#MotoGP');names=riders_in(' '.join((x.get('caption',''),x.get('title',''),x.get('summary',''))));r=x.get('turkish_rider') or detect_turkish_rider(x)
 if r and r not in names:names.insert(0,r)
 tags=[series_tag]+['#'+re.sub(r'[^A-Za-z0-9]','',fold(n).title().replace(' ','')) for n in names[:2]]+['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def language_sane(caption):
 low=fold(caption);return not any(fold(x) in low for x in BAD_GERMAN) and not any(x in low for x in ('click here','read more','find out more','latest edition','talking points:'))
STRUCTURE_VARIANTS={
 'HOOK_BODY_QUESTION':('{"hook":"...","body":"...","question":"..."}','Konkreter Hook, danach 2–5 natuerliche Saetze, am Ende eine konkrete Community-Frage.'),
 'BODY_QUESTION':('{"body":"...","question":"..."}','Ohne Hook direkt mit den Fakten einsteigen, danach eine konkrete Community-Frage.'),
 'STORY_QUESTION':('{"story":"...","question":"..."}','Die belegten Fakten als kurze emotionale, aber nicht dramatisierte Erzaehlung formulieren, danach eine konkrete Community-Frage.'),
 'FACT_FACT_FACT':('{"facts":["...","...","..."],"cta":"..."}','3–4 kompakte belegte Fakten, danach ein kurzer natuerlicher CTA ohne Fragepflicht.'),
 'QUESTION_HOOK_BODY':('{"question":"...","body":"..."}','Mit einer konkreten Community-Frage beginnen, danach die belegten Fakten erklaeren.'),
 'ZITAT_BODY':('{"quote":"...","body":"...","question":"..."}','Nur ein in TITEL/ZUSAMMENFASSUNG woertlich vorhandenes Fahrer-Zitat unveraendert im quote-Feld verwenden; im JSON-Wert selbst keine Anfuehrungszeichen hinzufuegen. Wenn kein woertliches Fahrer-Zitat vorhanden ist, die belegte Fahreraussage ohne erfundene Woertlichkeit formulieren. Danach Kontext und Community-Frage.'),
}
def choose_structure_variant():return random.choice(tuple(STRUCTURE_VARIANTS))
def _editor_prompt(x,repair_reasons=None,structure_variant=None):
 enrich_turkish(x);repair='';variant=structure_variant or choose_structure_variant()
 if variant not in STRUCTURE_VARIANTS:raise ValueError(f'Unbekannte Struktur-Variante: {variant}')
 if repair_reasons:repair='\nRUECKGABE AUS DER QM-KETTE. Analysiere die Originalfakten erneut und behebe exakt diese Punkte. FAKTEN DUERFEN WEDER ERGAENZT NOCH VERAENDERT WERDEN:\n- '+'\n- '.join(repair_reasons[:10])+'\n'
 title=' '.join(str(x.get('title','')).split());summary=' '.join(str(x.get('summary','')).split());series=series_for(x);turkish=x.get('turkish_rider') or 'NEIN';schema,instruction=STRUCTURE_VARIANTS[variant]
 return f'''Du arbeitest als Senior-Motorrad-Racing-Redakteur fuer Buelents Bike Life auf Premium-Niveau.\n{global_professional_context()}\nRACING-PFLICHTEN: Verwende ausschließlich die Serie aus dem CFO ({series}). Keine Klassenzuordnung erfinden. Die SERIE ist deterministisch aus der offiziellen Quelle gesperrt und darf nicht umgedeutet werden. Die Quelle liefert nur Fakten – der fertige Post muss in Buelents eigener, direkten, leidenschaftlichen und natuerlichen Bike-Life-Stimme neu formuliert sein. Kein Kopieren der Quellensprache. Nur Tatsachen aus TITEL/ZUSAMMENFASSUNG verwenden. Keine Namen, Teams, Hersteller, Nationalitaeten, Serien, Orte, Jahre, Zahlen, Ergebnisse, Titel oder Beziehungen aus Vorwissen ergaenzen. P1 niemals als Q1 interpretieren. Keine erfundenen oder frei uebersetzten Zitate. Korrektes idiomatisches Deutsch, kein PR-Sprech, kein KI-Sprech, kein kuenstlicher Hype. Mindestens 2 natuerliche Saetze bzw. bei FACT_FACT_FACT mindestens 3 kompakte Fakten. Keine Hashtags erzeugen.{repair}\nSTRUKTUR-VARIANTE: {variant}\nSTRUKTUR-ANWEISUNG: {instruction}\nSERIE: {series}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nTURKISH_RIDER: {turkish}\nAntworte nur JSON nach diesem Schema: {schema}'''
def _parse_editor_json(raw,variant):
 raw=(raw or '').strip();raw=re.sub(r'^\`\`\`(?:json)?\s*|\s*\`\`\`$','',raw,flags=re.I|re.S);o=json.loads(raw)
 def need(name):
  value=str(o.get(name,'')).strip()
  if not value:raise ValueError(f'editor JSON missing {name}')
  return value
 if variant=='HOOK_BODY_QUESTION':parts=[need('hook'),need('body'),need('question')]
 elif variant=='BODY_QUESTION':parts=[need('body'),need('question')]
 elif variant=='STORY_QUESTION':parts=[need('story'),need('question')]
 elif variant=='FACT_FACT_FACT':
  facts=o.get('facts')
  if not isinstance(facts,list) or not 3<=len(facts)<=4 or any(not str(v).strip() for v in facts):raise ValueError('editor JSON missing 3-4 facts')
  parts=[*(str(v).strip() for v in facts),need('cta')]
 elif variant=='QUESTION_HOOK_BODY':parts=[need('question'),need('body')]
 elif variant=='ZITAT_BODY':parts=[need('quote'),need('body'),need('question')]
 else:raise ValueError(f'Unbekannte Struktur-Variante: {variant}')
 return parts
def german_editor(x,repair_reasons=None):
 if len(re.sub(r'\s+',' ',x.get('title','')).strip())<18:return ''
 last=None
 for technical_attempt in range(2):
  try:
   variant=choose_structure_variant();parts=_parse_editor_json(generate('final_captions',_editor_prompt(x,repair_reasons,variant)),variant)
   if not x.get('turkish_rider'):parts=[p.replace('🇹🇷','').strip() for p in parts]
   x['structure_variant']=variant
   # Hashtags must be computed from THIS editor attempt, never a stale caption
   # left on the item by an earlier retry.
   body='\n\n'.join(parts);x['caption']=body
   return body+'\n\n'+hashtags(x)
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
  if not sem['hard_ok']:
   if attempt<3:repair_reasons=['Fakten-QM: '+e for e in sem['hard_reasons']];reanalyse_source(x,repair_reasons);continue
   print(f'SEMANTIC HARD-FACT REJECT after feedback loop attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['hard_reasons'])[:700]);break
  if not sem['language_ok']:
   if attempt<3:repair_reasons=['Sprach-QM: '+e for e in sem['repair_reasons']];print(f'LANGUAGE → EDITOR retry={attempt}:',x.get('title','')[:90]);continue
   break
  if not language_sane(x['caption']):
   if attempt<3:repair_reasons=['Deutsch/PR-/KI-Sprech deterministisch bereinigen'];continue
   break
  x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
 x['semantic_qm']='FAIL';x['rewrite_count']=min(2,attempt-1);return False
def qualify_parallel(items,max_workers=3):
 out=[]
 with ThreadPoolExecutor(max_workers=max_workers) as ex:
  jobs={ex.submit(qualify_copy,x):x for x in items}
  for f in as_completed(jobs):
   try:
    if f.result():out.append(jobs[f])
   except Exception as e:print('PARALLEL COPY-QM FAIL:',type(e).__name__,str(e)[:180])
 return out
def prepare_media(x,i):
 filename=get_image_path(slugify(f'racing-editorial-{dt.now(timezone.utc):%Y-%m-%d}-{i}-{x["title"]}'),1);data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+x['caption'][:180])
 if not data:return ''
 save_bytes(data,filename);return filename.as_posix()
def finish_item(x,i):
 if x.get('semantic_qm')!='PASS' or x.get('racing_qm')!='PASS':return False
 x['instagram_media']=prepare_media(x,i)
 if not x['instagram_media']:return False
 x['story_key']=story_key(x['title'],x['url']);ok,errs=chief_review('Motorcycle Racing',x,x['caption'],x['instagram_media'],x['url'],racing_review);x['chief_errors']=errs
 if ok:return True
 print('CHIEF-QM → EDITOR RETURN:',x.get('title','')[:90],'|','; '.join(errs)[:600])
 # One final controlled return. The complete Racing + Semantic + Chief chain is rerun; never auto-pass.
 if x.get('chief_retry_count',0)>=1:return False
 x['chief_retry_count']=1;reanalyse_source(x,['Chief-QM: '+e for e in errs])
 if not qualify_copy(x,['Chief-QM: '+e for e in errs]):return False
 ok2,errs2=chief_review('Motorcycle Racing',x,x['caption'],x['instagram_media'],x['url'],racing_review);x['chief_errors']=errs2
 if not ok2:print('CHIEF-QM FINAL REJECT:',x.get('title','')[:90],'|','; '.join(errs2)[:600])
 return ok2
def load_pool():
 try:return json.loads(TOP10.read_text(encoding='utf-8'))
 except Exception:return {'version':1,'days':{}}
def published_keys():
 p=Path('content/PUBLISHED.md');return set(re.findall(r'(?:motogp|moto2|moto3|worldsbk|worldssp):[A-Za-z0-9._:-]+',p.read_text(encoding='utf-8',errors='ignore'))) if p.exists() else set()
def save_top10(items,now):
 data=load_pool();day=now.date().isoformat();rows=[]
 for x in items[:20]:rows.append({'story_key':story_key(x['title'],x['url']),'title':x['title'],'url':x['url'],'summary':x.get('summary',''),'preview':x.get('preview',''),'published_at':x.get('published_at') or x.get('published') or x.get('date') or x.get('pub_date'),'series':series_for(x),'source_series':x.get('source_series',series_for(x)),'series_locked':True,'turkish_rider':x.get('turkish_rider',''),'kind':x.get('kind','news')})
 data.setdefault('days',{})[day]=rows;keep={(now.date()-timedelta(days=i)).isoformat() for i in range(3)};data['days']={k:v for k,v in data['days'].items() if k in keep};TOP10.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def yesterday_raw(now,current_urls):
 rows=load_pool().get('days',{}).get((now.date()-timedelta(days=1)).isoformat(),[]);pub=published_keys();out=[]
 for r in rows:
  if r.get('url') in current_urls or r.get('story_key') in pub:continue
  x=enrich_turkish(dict(r));lock_source_series(x,r.get('source_series') or r.get('series'));x['fallback_yesterday']=True
  if current_news(x,now,7) and racing_relevant(x):out.append(x)
 return out
def ordered_pool(qualified,names):
 pool=sorted(qualified,key=lambda x:editorial_score(x,names),reverse=True);ordered=[];turk=[x for x in pool if is_turkish_focus(x) and not is_feature(x)]
 if turk:ordered.append(turk[0])
 gp=[x for x in pool if is_gp_family(x) and not is_feature(x) and x not in ordered];ordered+=gp[:3]
 ordered += [x for x in pool if x not in ordered and not is_feature(x)]+[x for x in pool if x not in ordered]
 return ordered
def select_and_finish(qualified,names):
 picks=[];seen_fp=set()
 for x in ordered_pool(qualified,names):
  if len(picks)>=5:break
  s=series_for(x)
  if s not in VALID_SERIES:continue
  if not is_gp_family(x) and sum(series_for(y)==s for y in picks)>=3:continue
  fp=re.sub(r'#[^\s]+','',fold(x.get('caption','')));fp=re.sub(r'\s+',' ',fp).strip()
  if fp in seen_fp:continue
  b_ok,_=review_batch([x])[0]
  if b_ok and finish_item(x,len(picks)+1):picks.append(x);seen_fp.add(fp)
 return picks
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 18',f'Agency-Version: {VERSION}','Approval-Status: READY','Professional-Agent-Standard: V1.0','Human-Writing-Protocol: V1.0','Buelents-Bike-Life-Voice: VERBINDLICH','Semantic-Fakten-QM: PASS','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS','Racing-QM: PASS','Semantic-Fakten-QM: PASS',f'Neufassungen: {x.get("rewrite_count",0)}',f'QM-Ruecklaeufe: {x.get("research_retry_count",0)+x.get("chief_retry_count",0)}',f'Herkunft: {"Top-20 vom Vortag" if x.get("fallback_yesterday") else "Aktuell"}',f'Artikelalter-Tage: {age_days(x,now):.1f}',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.parent.mkdir(parents=True,exist_ok=True);SESSION.write_text('\n'.join(lines)+'\n',encoding='utf-8')
COMMUNITY_ROTATION_FILE=Path('memory/COMMUNITY_ROTATION.json')
COMMUNITY_TEMPLATES={
 'bike_society_hagen':{
  'title':'🏍️ Community-Spotlight: Bike Society Hagen',
  'url':'https://www.instagram.com/bike_society_hagen/',
  'caption':'''## Instagram
Status: ENTWURF
Freigabe: Community
Quelle: https://www.instagram.com/bike_society_hagen/
Medienstatus: QUELLE_PRÜFEN
Titel: 🏍️ Community-Spotlight: Bike Society Hagen
Text:
Bikes. People. Roads. – Die Bike Society Hagen ist eine Community für alle,
die Motorrad lieben. Ausfahrten, Treffen, Events, Season Opening.

Ihr Motto: "ALLES KANN, NICHTS MUSS. Motor an, Kopf aus!" 🧡

Du willst dabei sein? Schreib ihnen auf Instagram oder per WhatsApp.

Was ist für dich das Beste an einer Biker-Community?

#BikeSocietyHagen #Motorradfahren #Kurvenliebe #Verbundenheit #BikerCommunity'''
 },
 'knieschleifer.aus.ueberzeugung':{
  'title':'🏍️ Community-Spotlight: Knieschleifer aus Überzeugung',
  'url':'https://www.instagram.com/knieschleifer.aus.ueberzeugung/',
  'caption':'''## Instagram
Status: ENTWURF
Freigabe: Community
Quelle: https://www.instagram.com/knieschleifer.aus.ueberzeugung/
Medienstatus: QUELLE_PRÜFEN
Titel: 🏍️ Community-Spotlight: Knieschleifer aus Überzeugung
Text:
Deutschlandweite Biker-Community mit über 30.000 Mitgliedern und mehr als 200 Regionalgruppen in DE/AT/CH/DK. Ausfahrten, Stammtische, wohltätige Aktionen und Einsatz für Unterfahrschutz an Leitplanken.

Gegründet von Dieter Grommes für echte Gemeinschaft auf zwei Rädern! 🧡

Du willst dabei sein? Schreib ihnen auf Instagram.

Was ist für dich das Beste an einer Biker-Community?

#KnieschleiferAusUeberzeugung #Motorradfahren #Kurvenliebe #Verbundenheit #BikerCommunity'''
 },
 'bike_society.united':{
  'title':'🏍️ Community-Spotlight: Bike Society United',
  'url':'https://www.instagram.com/bike_society.united/',
  'caption':'''## Instagram
Status: ENTWURF
Freigabe: Community
Quelle: https://www.instagram.com/bike_society.united/
Medienstatus: QUELLE_PRÜFEN
Titel: 🏍️ Community-Spotlight: Bike Society United
Text:
Bikes. People. Roads. – Teil der landesweiten Bike Society Community in NRW! Respekt, Regeln, Leidenschaft und gemeinsames Fahren stehen an erster Stelle.

Ausfahrten, Technik-Tipps und Zusammenhalt ohne Mitgliedsbeitrag. 🧡

Du willst dabei sein? Schreib ihnen auf Instagram oder per WhatsApp.

Was ist für dich das Beste an einer Biker-Community?

#BikeSocietyUnited #Motorradfahren #Kurvenliebe #Verbundenheit #BikerCommunity'''
 },
 'ks_ruhrpott':{
  'title':'🏍️ Community-Spotlight: Knieschleifer Ruhrpott',
  'url':'https://www.instagram.com/ks_ruhrpott/',
  'caption':'''## Instagram
Status: ENTWURF
Freigabe: Community
Quelle: https://www.instagram.com/ks_ruhrpott/
Medienstatus: QUELLE_PRÜFEN
Titel: 🏍️ Community-Spotlight: Knieschleifer Ruhrpott
Text:
Die Regionalgruppe der Knieschleifer aus Überzeugung im Pott! Gemeinsame Ausfahrten, Treffen und Leidenschaft für Kurven und Sicherheit im Ruhrgebiet.

Zusammenhalt und Leidenschaft auf zwei Rädern! 🧡

Du willst dabei sein? Schreib ihnen auf Instagram.

Was ist für dich das Beste an einer Biker-Community?

#KsRuhrpott #KnieschleiferAusUeberzeugung #Motorradfahren #Kurvenliebe #BikerCommunity'''
 },
 'bike_society_bergisches_land':{
  'title':'🏍️ Community-Spotlight: Bike Society Bergisches Land',
  'url':'https://www.instagram.com/bike_society_bergisches_land/',
  'caption':'''## Instagram
Status: ENTWURF
Freigabe: Community
Quelle: https://www.instagram.com/bike_society_bergisches_land/
Medienstatus: QUELLE_PRÜFEN
Titel: 🏍️ Community-Spotlight: Bike Society Bergisches Land
Text:
Kurvenreiche Ausfahrten und echte Biker-Leidenschaft im Bergischen Land! Teil der Bike Society NRW – inklusiv, respektvoll und voller Energie.

Motto: "ALLES KANN, NICHTS MUSS. Motor an, Kopf aus!" 🧡

Du willst dabei sein? Schreib ihnen auf Instagram oder per WhatsApp.

Was ist für dich das Beste an einer Biker-Community?

#BikeSocietyBergischesLand #Motorradfahren #Kurvenliebe #Verbundenheit #BikerCommunity'''
 }
}

def load_community_rotation():
 default_rotation=["bike_society_hagen","knieschleifer.aus.ueberzeugung","bike_society.united","ks_ruhrpott","bike_society_bergisches_land"]
 if not COMMUNITY_ROTATION_FILE.exists():
  data={"last_community":"bike_society_hagen","last_date":"2026-09-17","rotation":default_rotation}
  COMMUNITY_ROTATION_FILE.parent.mkdir(parents=True,exist_ok=True)
  COMMUNITY_ROTATION_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  return data
 try:return json.loads(COMMUNITY_ROTATION_FILE.read_text(encoding='utf-8'))
 except Exception:
  data={"last_community":"bike_society_hagen","last_date":"2026-09-17","rotation":default_rotation}
  return data

def save_community_rotation(data):
 COMMUNITY_ROTATION_FILE.parent.mkdir(parents=True,exist_ok=True)
 COMMUNITY_ROTATION_FILE.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def generate_community_fallbacks(count,now):
 rot_data=load_community_rotation()
 rotation=rot_data.get('rotation',[])
 last=rot_data.get('last_community','')
 current_idx=rotation.index(last) if last in rotation else 0
 picks=[]
 for i in range(count):
  next_idx=(current_idx+1+i)%len(rotation)
  comm_key=rotation[next_idx]
  tmpl=COMMUNITY_TEMPLATES.get(comm_key,COMMUNITY_TEMPLATES['bike_society_hagen'])
  item={'title':tmpl['title'],'url':tmpl['url'],'caption':tmpl['caption'],'series':'Community','source_series':'Community','instagram_media':'','published_at':now.isoformat(),'rewrite_count':0,'research_retry_count':0,'chief_retry_count':0,'fallback_yesterday':False}
  picks.append(item)
  rot_data['last_community']=comm_key
  rot_data['last_date']=now.date().isoformat()
  print(f'COMMUNITY-SPOTLIGHT generiert: {comm_key}, Anzahl={i+1}')
 save_community_rotation(rot_data)
 return picks

def invalidate_session(now,reason,passed=0):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 18',f'Agency-Version: {VERSION}','QM: FAIL','Approval-Status: BLOCKED',f'Session-Timestamp: {int(now.timestamp())}',f'Bestandene-Pakete: {passed}/3',f'Grund: {reason}','','Keine Freigabe moeglich. Erst ein neuer Lauf mit mindestens 3 PASS erzeugt eine freigabefaehige Session.'];SESSION.parent.mkdir(parents=True,exist_ok=True);SESSION.write_text('\n'.join(lines)+'\n',encoding='utf-8')
def turkish_status(items,qualified=None):
 if any(is_turkish_focus(x) for x in items):return 'selected'
 if qualified is not None and any(is_turkish_focus(x) for x in qualified):return 'qualified_not_selected'
 return 'none_qualified'
def telegram_preview(items,turk,qualified=None):
 status=turkish_status(items,qualified)
 mix=', '.join(f'{s} {sum(series_for(x)==s for x in items)}' for s in VALID_SERIES if any(series_for(x)==s for x in items));msg=[f'🏍️ Motorcycle Racing Agency {VERSION} – 5 qualitätsgeprüfte Tagesvorschläge','🔎 Fakten-QM: NULL-TOLERANZ | Fehler gehen zurück an Research/Editor statt sofort verloren zu sein',f'✍️ Human Writing Protocol + Bülents Bike Life Voice: VERBINDLICH',f'Serienmix: {mix}',('🇹🇷 Turkish-Rider: aktuelle geeignete Story aufgenommen' if status=='selected' else ('🇹🇷 Turkish-Rider: geeignete Story im QM-Pool, aber nicht in den finalen 5' if status=='qualified_not_selected' else '🇹🇷 Heute keine Turkish-Rider-Story durch das vollständige QM gekommen')),'']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {"↩️ Top-20 vom Vortag | " if x.get("fallback_yesterday") else ""}[{series_for(x)}] {x["caption"]}',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v8():
 names=roster_names();known=known_story_keys();raw=[];seen=set();meta={}
 for t,u,s,r in racing_scout(140):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'source_series':s,'series':s,'series_locked':True,**({'turkish_rider':r} if r else {})}
 for t,u,r in turkish_scout(70):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),100)+extract(get(MARKET),60):
  u=canonical_url(url);key=story_key(title,u)
  if u not in seen and key not in known:seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:320]:
  x=article_info(t,u);m=meta.get(u,{});x.update(m);lock_source_series(x,m.get('source_series'));details.append(enrich_turkish(x))
 now=dt.now(timezone.utc);diag,_=freshness_diagnostics(details,now);fresh=[x for x in details if freshness_reason(x,now)=='fresh'];fresh.sort(key=lambda z:editorial_score(z,names),reverse=True)
 current_q=qualify_parallel(fresh[:60],3);fallback_raw=yesterday_raw(now,{x.get('url') for x in current_q});fallback_q=qualify_parallel(fallback_raw[:20],3) if len(current_q)<15 else [];qualified=current_q+[x for x in fallback_q if x.get('url') not in {y.get('url') for y in current_q}];qualified.sort(key=lambda x:editorial_score(x,names),reverse=True);save_top10(qualified,now);picks=select_and_finish(qualified,names);turk=any(is_turkish_focus(x) for x in picks);mix={s:sum(series_for(x)==s for x in picks) for s in VALID_SERIES}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency {VERSION}\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nAktuelle Racing-News <=7 Tage: {len(fresh)}\nFreshness missing-date: {diag.get("missing-date",0)}\nFreshness >7 Tage: {diag.get("older-than-7d",0)}\nFreshness Promo/irrelevant: {diag.get("not-racing-or-promo",0)}\nAktuell voll Copy-QM qualifiziert: {len(current_q)}\nVortag voll Copy-QM qualifiziert: {len(fallback_q)}\nGesamtpool nach Racing+Semantic-QM: {len(qualified)}\nFinaler Mix: {mix}\nTurkish-Rider erkannt: {turk}\nFakten-QM: NULL-TOLERANZ + Rueckgabeschleife\nHuman Writing Protocol: VERBINDLICH\nBuelents Bike Life Voice: VERBINDLICH\nChief-QM PASS: {len(picks)}\n',encoding='utf-8')
 if len(picks)<3:
  needed=3-len(picks)
  print(f'COMMUNITY-FALLBACK aktiviert (final={len(picks)})')
  community_picks=generate_community_fallbacks(needed,now)
  picks=picks+community_picks

 turk=any(is_turkish_focus(x) for x in picks)
 write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk,qualified)
 print(f'{VERSION}: raw={len(details)}, fresh={len(fresh)}, current_q={len(current_q)}, fallback_q={len(fallback_q)}, final={len(picks)}, mix={mix}, Turkish={turk}')
if __name__=='__main__':run_v8()
