"""Motorcycle Racing Agency V8.5.3 – audited fail-closed facts with repairable language."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from racing_semantic_qm import review as semantic_review, review_detailed as semantic_review_detailed
from turkish_riders_scout import scout as turkish_scout, racing_scout
from llm_client import generate,global_professional_context
from pathlib import Path
from datetime import timedelta,datetime as dt,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,re,time
VERSION='V8.5.3';TOP10=Path('memory/RACING_TOP10_POOL.json')
TURKISH_ALIASES={'Toprak Razgatlioglu':('toprak razgatlioglu','toprak razgatlıoğlu'),'Can Oncu':('can oncu','can öncü'),'Deniz Oncu':('deniz oncu','deniz öncü'),'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu')}
TURKISH_RIDERS=list(TURKISH_ALIASES)
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado','Alvaro Bautista','Miguel Oliveira','Alberto Surra','Sergio Garcia','Iker Lecuona','Andrea Iannone','Sam Lowes','Alex Lowes','Jonathan Rea','Stefano Manzi','Jeremy Alcoba','Marcos Ramirez']
PROMO_WORDS=('fantasy','super boost','mystery boost','videopass','video pass','tickets','ticket','store','merch','merchandise','shop','giveaway','promo code','promotion')
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
def series_for_raw(x):
 u=fold(x.get('url',''));story=fold(' '.join((x.get('title',''),x.get('summary',''))));t=fold(article_text(x))
 if 'motogp' in story and any(p in story for p in ('join motogp','joins motogp','to motogp','motogp switch','moves to motogp','move to motogp','switch to motogp')):return 'MotoGP'
 if ('worldsbk' in story or 'world superbike' in story) and any(p in story for p in ('join worldsbk','joins worldsbk','to worldsbk','worldsbk switch','moves to worldsbk','move to worldsbk','switch to worldsbk')):return 'WorldSBK'
 if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
 if any(v in t for v in ('worldssp','world supersport','supersport')) and 'motogp' not in t:return 'WorldSSP'
 if 'worldsbk' in t or 'world superbike' in t:return 'WorldSBK'
 if re.search(r'(?<![a-z0-9])moto3(?![a-z0-9])',t):return 'Moto3'
 if re.search(r'(?<![a-z0-9])moto2(?![a-z0-9])',t):return 'Moto2'
 if re.search(r'(?<![a-z0-9])motogp(?![a-z0-9])',t):return 'MotoGP'
 declared=str(x.get('series','')).strip()
 if declared in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300'):return declared
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
def is_feature(x):return any(w in fold(article_text(x)) for w in FEATURE_WORDS)
def racing_relevant(x):
 text=fold(article_text(x));return not any(w in text for w in PROMO_WORDS) and bool(riders_in(text) or detect_turkish_rider(x) or any(w in text for w in RACING_WORDS))
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
 if repair_reasons:repair='\nSPRACH-/STIL-REPARATUR. Behebe diese Punkte. FAKTEN DUERFEN WEDER ERGAENZT NOCH VERAENDERT WERDEN:\n- '+'\n- '.join(repair_reasons[:10])+'\n'
 title=' '.join(str(x.get('title','')).split());summary=' '.join(str(x.get('summary','')).split());series=series_for(x);turkish=x.get('turkish_rider') or 'NEIN'
 return f'''Du arbeitest als Senior-Motorrad-Racing-Redakteur auf Premium-Niveau.\n{global_professional_context()}\nRACING-PFLICHTEN: Nur Tatsachen aus TITEL/ZUSAMMENFASSUNG verwenden. Keine Namen, Teams, Hersteller, Nationalitaeten, Serien, Orte, Jahre, Zahlen, Ergebnisse, Titel oder Beziehungen aus Vorwissen ergaenzen. P1 niemals als Q1 interpretieren. Keine direkten oder frei uebersetzten Zitate. Korrektes idiomatisches Deutsch, kein PR-Sprech, kein kuenstlicher Hype. 2–4 informative Saetze und danach eine konkrete Community-Frage. Meinungsfragen ohne unbelegte Praemisse sind erlaubt. Keine Hashtags erzeugen.{repair}\nSERIE: {series}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nTURKISH_RIDER: {turkish}\nAntworte nur JSON: {{"hook":"...","body":"...","question":"..."}}'''
def _parse_editor_json(raw):
 raw=(raw or '').strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);o=json.loads(raw);hook=str(o.get('hook','')).strip();body=str(o.get('body','')).strip();q=str(o.get('question','')).strip()
 if not hook or not body or '?' not in q:raise ValueError('editor JSON missing hook/body/question')
 return hook,body,q
def german_editor(x,repair_reasons=None):
 if len(re.sub(r'\s+',' ',x.get('title','')).strip())<18:return ''
 prompt=_editor_prompt(x,repair_reasons);last=None
 for technical_attempt in range(3):
  try:
   hook,body,q=_parse_editor_json(generate('final_captions',prompt))
   if not x.get('turkish_rider'):hook=hook.replace('🇹🇷','').strip()
   c=f'{hook}\n\n{body}\n\n{q}\n\n{hashtags(x)}';return c
  except (json.JSONDecodeError,KeyError,TypeError,ValueError) as e:last=e;time.sleep(.5);continue
  except Exception as e:last=e;break
 print('EDITOR EXCEPTION:',type(last).__name__,str(last)[:180]);return ''
def qualify_copy(x):
 if not racing_relevant(x):return False
 repair_reasons=None
 # Initial text plus up to TWO language/style repairs. Hard fact failures are never repaired into acceptance.
 for attempt in (1,2,3):
  x['caption']=german_editor(x,repair_reasons)
  if not x['caption']:
   repair_reasons=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REPAIR attempt={attempt}:',x.get('title','')[:90]);continue
  r_ok,r_err=racing_review(x,x['caption']);x['qm_errors']=r_err
  if not r_ok:
   # Deterministic Racing-QM remains fail-closed; it may catch structural/factual defects.
   if attempt<3:
    repair_reasons=['Racing-QM: '+e for e in r_err];print(f'RACING-QM REPAIR attempt={attempt}:',x.get('title','')[:90],'|','; '.join(r_err)[:500]);continue
   print('RACING-QM HARD REJECT:',x.get('title','')[:90],'|','; '.join(r_err)[:600]);break
  sem=semantic_review_detailed(x,x['caption']);x['semantic_errors']=sem['hard_reasons']+sem['repair_reasons']
  if not sem['hard_ok']:
   print(f'SEMANTIC HARD-FACT REJECT attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['hard_reasons'])[:700]);break
  if not sem['language_ok']:
   if attempt<3:
    repair_reasons=['Sprach-QM: '+e for e in sem['repair_reasons']];print(f'LANGUAGE REPAIR attempt={attempt}:',x.get('title','')[:90],'|','; '.join(sem['repair_reasons'])[:500]);continue
   print('LANGUAGE REJECT after repairs:',x.get('title','')[:90]);break
  if not language_sane(x['caption']):
   if attempt<3:repair_reasons=['Deutsch/PR-Sprech deterministisch bereinigen'];continue
   break
  x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
 x['semantic_qm']='FAIL';x['rewrite_count']=min(2,(attempt-1));return False
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
 if not ok:print('CHIEF-QM REJECT:',x.get('title','')[:90],'|','; '.join(errs)[:600])
 return ok
def load_pool():
 try:return json.loads(TOP10.read_text(encoding='utf-8'))
 except Exception:return {'version':1,'days':{}}
def published_keys():
 p=Path('content/PUBLISHED.md');return set(re.findall(r'(?:motogp|moto2|moto3|worldsbk|worldssp):[A-Za-z0-9._:-]+',p.read_text(encoding='utf-8',errors='ignore'))) if p.exists() else set()
def save_top10(items,now):
 data=load_pool();day=now.date().isoformat();rows=[]
 for x in items[:20]:rows.append({'story_key':story_key(x['title'],x['url']),'title':x['title'],'url':x['url'],'summary':x.get('summary',''),'preview':x.get('preview',''),'published_at':x.get('published_at') or x.get('published') or x.get('date') or x.get('pub_date'),'series':series_for(x),'turkish_rider':x.get('turkish_rider',''),'kind':x.get('kind','news')})
 data.setdefault('days',{})[day]=rows;keep={(now.date()-timedelta(days=i)).isoformat() for i in range(3)};data['days']={k:v for k,v in data['days'].items() if k in keep};TOP10.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def yesterday_raw(now,current_urls):
 rows=load_pool().get('days',{}).get((now.date()-timedelta(days=1)).isoformat(),[]);pub=published_keys();out=[]
 for r in rows:
  if r.get('url') in current_urls or r.get('story_key') in pub:continue
  x=enrich_turkish(dict(r));x['fallback_yesterday']=True
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
  if not is_gp_family(x) and sum(series_for(y)==s for y in picks)>=3:continue
  fp=re.sub(r'#[^\s]+','',fold(x.get('caption','')));fp=re.sub(r'\s+',' ',fp).strip()
  if fp in seen_fp:continue
  batch=review_batch([x]);b_ok,b_err=batch[0]
  if not b_ok:continue
  if finish_item(x,len(picks)+1):picks.append(x);seen_fp.add(fp)
 return picks
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 18',f'Agency-Version: {VERSION}','Approval-Status: READY','Professional-Agent-Standard: V1.0','Human-Writing-Protocol: V1.0','Semantic-Fakten-QM: PASS','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS','Racing-QM: PASS','Semantic-Fakten-QM: PASS',f'Neufassungen: {x.get("rewrite_count",0)}',f'Herkunft: {"Top-20 vom Vortag" if x.get("fallback_yesterday") else "Aktuell"}',f'Artikelalter-Tage: {age_days(x,now):.1f}',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.parent.mkdir(parents=True,exist_ok=True);SESSION.write_text('\n'.join(lines)+'\n',encoding='utf-8')
def invalidate_session(now,reason,passed=0):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 18',f'Agency-Version: {VERSION}','QM: FAIL','Approval-Status: BLOCKED',f'Session-Timestamp: {int(now.timestamp())}',f'Bestandene-Pakete: {passed}/5',f'Grund: {reason}','','Keine Freigabe moeglich. Erst ein neuer Lauf mit 5/5 PASS erzeugt eine freigabefaehige Session.'];SESSION.parent.mkdir(parents=True,exist_ok=True);SESSION.write_text('\n'.join(lines)+'\n',encoding='utf-8')
def telegram_preview(items,turk):
 mix=', '.join(f'{s} {sum(series_for(x)==s for x in items)}' for s in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300') if any(series_for(x)==s for x in items));msg=[f'🏍️ Motorcycle Racing Agency {VERSION} – 5 qualitätsgeprüfte Tagesvorschläge','🔎 Fakten-QM: NULL-TOLERANZ | Sprache: bis zu 2 Reparaturschleifen',f'Serienmix: {mix}',('🇹🇷 Turkish-Rider: aktuelle geeignete Story aufgenommen' if turk else '🇹🇷 Heute keine geeignete neue Turkish-Rider-Story gefunden'),'']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {"↩️ Top-20 vom Vortag | " if x.get("fallback_yesterday") else ""}[{series_for(x)}] {x["caption"]}',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v8():
 names=roster_names();known=known_story_keys();raw=[];seen=set();meta={}
 for t,u,s,r in racing_scout(140):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'series':s,**({'turkish_rider':r} if r else {})}
 for t,u,r in turkish_scout(70):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),100)+extract(get(MARKET),60):
  u=canonical_url(url);key=story_key(title,u)
  if u not in seen and key not in known:seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:320]:
  x=article_info(t,u);x.update(meta.get(u,{}));details.append(enrich_turkish(x))
 now=dt.now(timezone.utc);fresh=[x for x in details if current_news(x,now,7) and racing_relevant(x)];fresh.sort(key=lambda z:editorial_score(z,names),reverse=True)
 # Broader verified pool: up to 60 fresh stories may enter copy QM; quality gates are unchanged for facts.
 current_q=qualify_parallel(fresh[:60],3);fallback_raw=yesterday_raw(now,{x.get('url') for x in current_q});fallback_q=qualify_parallel(fallback_raw[:20],3) if len(current_q)<15 else [];qualified=current_q+[x for x in fallback_q if x.get('url') not in {y.get('url') for y in current_q}];qualified.sort(key=lambda x:editorial_score(x,names),reverse=True);save_top10(qualified,now);picks=select_and_finish(qualified,names);turk=any(is_turkish_focus(x) for x in picks);mix={s:sum(series_for(x)==s for x in picks) for s in ('MotoGP','Moto2','Moto3','WorldSBK','WorldSSP','WorldSSP300')}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency {VERSION}\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nAktuelle Racing-News <=7 Tage: {len(fresh)}\nAktuell voll Copy-QM qualifiziert: {len(current_q)}\nVortag voll Copy-QM qualifiziert: {len(fallback_q)}\nGesamtpool nach Racing+Semantic-QM: {len(qualified)}\nFinaler Mix: {mix}\nTurkish-Rider erkannt: {turk}\nFakten-QM: NULL-TOLERANZ\nSprachreparaturen: bis zu 2\nChief-QM PASS: {len(picks)}\n',encoding='utf-8')
 if len(picks)==5:write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk)
 else:
  invalidate_session(now,'Komplette Profi-QM-Kette lieferte weniger als 5 freigabefaehige Pakete',len(picks));send_message(f'🏍️ Racing Agency {VERSION}: nur {len(picks)}/5 Pakete bestanden. Fakten-QM bleibt Null-Toleranz; reparierbare Sprache erhielt bis zu zwei Korrekturschleifen.')
 print(f'{VERSION}: raw={len(details)}, fresh={len(fresh)}, current_q={len(current_q)}, fallback_q={len(fallback_q)}, final={len(picks)}, mix={mix}, Turkish={turk}')
if __name__=='__main__':run_v8()
