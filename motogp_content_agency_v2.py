"""Motorcycle Racing Agency V8.4.6.3 – audited fail-closed editorial chain."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from racing_semantic_qm import review as semantic_review
from turkish_riders_scout import scout as turkish_scout, racing_scout
from llm_client import generate,global_professional_context
from pathlib import Path
from datetime import timedelta,datetime as dt,timezone
from concurrent.futures import ThreadPoolExecutor,as_completed
import json,re
VERSION='V8.4.6.3';TOP10=Path('memory/RACING_TOP10_POOL.json')
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
 u=fold(x.get('url',''));t=fold(article_text(x))
 if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
 if any(v in t for v in ('worldssp','world supersport','supersport')) and 'motogp' not in t:return 'WorldSSP'
 if 'worldsbk' in t or 'world superbike' in t:return 'WorldSBK'
 if any(v in t for v in ('motogp','moto2','moto3')):return 'MotoGP'
 if 'worldsbk.com' in u:return x.get('series') or 'WorldSBK'
 return x.get('series') or 'MotoGP'
def series_for(x):return series_for_raw(x)
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
 age=max(0,age_days(x,datetime.now(timezone.utc)));fresh=max(0,80-int(age*10));text=fold(article_text(x));sport=sum(12 for w in ('win','victory','pole','podium','championship','title','race','sprint','qualifying','injury','return','replace') if w in text);live=35 if any(w in text for w in ('race','sprint','qualifying','practice','fp1','fp2','championship','standings','injury','return','replace')) else 0
 return fresh+score(x.get('title',''),names)+sport+live+(30 if is_turkish_focus(x) else 0)+(-45 if is_feature(x) else 0)
def hashtags(x):
 s=series_for(x);series_tag={'WorldSSP':'#WorldSSP','WorldSSP300':'#WorldSSP300','WorldSBK':'#WorldSBK'}.get(s,'#MotoGP');names=riders_in(article_text(x));r=x.get('turkish_rider') or detect_turkish_rider(x)
 if r and r not in names:names.insert(0,r)
 tags=[series_tag]+['#'+re.sub(r'[^A-Za-z0-9]','',n) for n in names[:2]]+['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def language_sane(caption):
 low=fold(caption);return not any(fold(x) in low for x in BAD_GERMAN) and not any(x in low for x in ('click here','read more','find out more','latest edition','talking points:'))
def _editor_prompt(x,repair_reasons=None):
 enrich_turkish(x);repair=''
 if repair_reasons:repair='\nEINMALIGE QM-KORREKTUR. Behebe exakt diese Fehler, ohne neue Fakten hinzuzufuegen:\n- '+'\n- '.join(repair_reasons[:10])+'\n'
 title=' '.join(str(x.get('title','')).split())
 summary=' '.join(str(x.get('summary','')).split())
 series=series_for(x)
 turkish=x.get('turkish_rider') or 'NEIN'
 return f'''Du arbeitest als Senior-Motorrad-Racing-Redakteur auf Premium-Niveau. Mindestens zehn Jahre professionelle Erfahrung sind der Qualitaetsmassstab, keine zu behauptende Biografie.\n{global_professional_context()}\n\nRACING-PFLICHTEN: Nur Tatsachen aus TITEL/ZUSAMMENFASSUNG verwenden. Keine Namen, Teams, Hersteller, Serien, Orte, Jahre, Zahlen, Ergebnisse, Titel oder Beziehungen aus Vorwissen ergaenzen. Keine direkten Zitate. Quellzitate sachlich paraphrasieren. Korrektes idiomatisches Deutsch, kein PR-Sprech, kein kuenstlicher Hype. 2–4 informative Saetze und danach eine konkrete Community-Frage. Keine Hashtags erzeugen.{repair}\nSERIE: {series}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nTURKISH_RIDER: {turkish}\nAntworte nur JSON: {{"hook":"...","body":"...","question":"..."}}'''
def german_editor(x,repair_reasons=None):
 if len(re.sub(r'\s+',' ',x.get('title','')).strip())<18:return ''
 try:
  raw=generate('final_captions',_editor_prompt(x,repair_reasons)).strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);o=json.loads(raw);hook=str(o.get('hook','')).strip();body=str(o.get('body','')).strip();q=str(o.get('question','')).strip()
  if not hook or not body or '?' not in q:return ''
  if not x.get('turkish_rider'):hook=hook.replace('🇹🇷','').strip()
  c=f'{hook}\n\n{body}\n\n{q}\n\n{hashtags(x)}';return c if language_sane(c) else ''
 except Exception as e:print('EDITOR EXCEPTION:',type(e).__name__,str(e)[:180]);return ''
def qualify_copy(x):
 if not racing_relevant(x):return False
 repair_reasons=None
 for attempt in (1,2):
  x['caption']=german_editor(x,repair_reasons)
  if not x['caption']:
   reasons=['Redakteur lieferte keinen gueltigen strukturierten Text'];print(f'EDITOR REJECT attempt={attempt}:',x.get('title','')[:90])
  else:
   r_ok,r_err=racing_review(x,x['caption']);x['qm_errors']=r_err
   if not r_ok:
    reasons=['Racing-QM: '+e for e in r_err];print(f'RACING-QM REJECT attempt={attempt}:',x.get('title','')[:90],'|','; '.join(r_err)[:600])
   else:
    s_ok,s_err=semantic_review(x,x['caption']);x['semantic_errors']=s_err
    if s_ok:
     x['semantic_qm']='PASS';x['racing_qm']='PASS';x['rewrite_count']=attempt-1;print(f'FULL COPY-QM PASS attempt={attempt}:',x.get('title','')[:90]);return True
    reasons=['Semantic-QM: '+e for e in s_err];print(f'SEMANTIC-QM REJECT attempt={attempt}:',x.get('title','')[:90],'|','; '.join(s_err)[:700])
  if attempt==1:
   repair_reasons=reasons;print('QM REWRITE: genau eine kontrollierte Neufassung wird gestartet')
 x['semantic_qm']='FAIL';x['rewrite_count']=1;return False
def qualify_parallel(items,max_workers=4):
 out=[]
 with ThreadPoolExecutor(max_workers=max_workers) as ex:
  jobs={ex.submit(qualify_copy,x):x for x in items}
  for f in as_completed(jobs):
   try:
    if f.result():out.append(jobs[f])
   except Exception as e:print('PARALLEL COPY-QM FAIL:',type(e).__name__,str(e)[:180])
 return out
def prepare_media(x,i):
 filename=get_image_path(slugify(f'racing-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{i}-{x["title"]}'),1);data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+x['caption'][:180])
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
 p=Path('content/PUBLISHED.md');return set(re.findall(r'(?:motogp|worldsbk|worldssp):[A-Za-z0-9._:-]+',p.read_text(encoding='utf-8',errors='ignore'))) if p.exists() else set()
def save_top10(items,now):
 data=load_pool();day=now.date().isoformat();rows=[]
 for x in items[:10]:rows.append({'story_key':story_key(x['title'],x['url']),'title':x['title'],'url':x['url'],'summary':x.get('summary',''),'preview':x.get('preview',''),'series':series_for(x),'turkish_rider':x.get('turkish_rider',''),'kind':x.get('kind','news')})
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
 mg=[x for x in pool if series_for(x)=='MotoGP' and not is_feature(x) and x not in ordered];ordered+=mg[:3]
 ordered += [x for x in pool if x not in ordered and not is_feature(x)]+[x for x in pool if x not in ordered]
 return ordered
def select_and_finish(qualified,names):
 picks=[];seen_fp=set()
 for x in ordered_pool(qualified,names):
  if len(picks)>=5:break
  s=series_for(x)
  if s!='MotoGP' and sum(series_for(y)==s for y in picks)>=3:continue
  fp=re.sub(r'#[^\s]+','',fold(x.get('caption','')));fp=re.sub(r'\s+',' ',fp).strip()
  if fp in seen_fp:continue
  b_ok,b_err=review_batch([x])[0]
  if not b_ok:continue
  if finish_item(x,len(picks)+1):picks.append(x);seen_fp.add(fp)
 return picks
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 17',f'Agency-Version: {VERSION}','Professional-Agent-Standard: V1.0','Human-Writing-Protocol: V1.0','Semantic-Fakten-QM: PASS','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS','Racing-QM: PASS','Semantic-Fakten-QM: PASS',f'Neufassungen: {x.get("rewrite_count",0)}',f'Herkunft: {"Top-10 vom Vortag" if x.get("fallback_yesterday") else "Aktuell"}',f'Artikelalter-Tage: {age_days(x,now):.1f}',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items,turk):
 mix=', '.join(f'{s} {sum(series_for(x)==s for x in items)}' for s in ('MotoGP','WorldSBK','WorldSSP','WorldSSP300') if any(series_for(x)==s for x in items));msg=[f'🏍️ Motorcycle Racing Agency {VERSION} – 5 qualitätsgeprüfte Tagesvorschläge','🎓 Professional Agent Standard V1.0','✍️ Human Writing Protocol V1.0','🔎 Racing-QM + Semantic-Fakten-QM + Chief-QM: PASS',f'Serienmix: {mix}',('🇹🇷 Turkish-Rider: aktuelle geeignete Story aufgenommen' if turk else '🇹🇷 Heute keine geeignete neue Turkish-Rider-Story gefunden'),'']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {"↩️ Top-10 vom Vortag | " if x.get("fallback_yesterday") else ""}[{series_for(x)}] {x["caption"]}',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v8():
 names=roster_names();known=known_story_keys();raw=[];seen=set();meta={}
 for t,u,s,r in racing_scout(100):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'series':s,**({'turkish_rider':r} if r else {})}
 for t,u,r in turkish_scout(50):
  u=canonical_url(u);key=story_key(t,u)
  if u not in seen and key not in known:seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),80)+extract(get(MARKET),40):
  u=canonical_url(url);key=story_key(title,u)
  if u not in seen and key not in known:seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:220]:
  x=article_info(t,u);x.update(meta.get(u,{}));details.append(enrich_turkish(x))
 now=datetime.now(timezone.utc);fresh=[x for x in details if current_news(x,now,7) and racing_relevant(x)];fresh.sort(key=lambda z:editorial_score(z,names),reverse=True)
 current_q=qualify_parallel(fresh[:30],4);fallback_raw=yesterday_raw(now,{x.get('url') for x in current_q});fallback_q=qualify_parallel(fallback_raw[:10],3) if len(current_q)<8 else [];qualified=current_q+[x for x in fallback_q if x.get('url') not in {y.get('url') for y in current_q}];qualified.sort(key=lambda x:editorial_score(x,names),reverse=True);save_top10(qualified,now);picks=select_and_finish(qualified,names);turk=any(is_turkish_focus(x) for x in picks);mix={s:sum(series_for(x)==s for x in picks) for s in ('MotoGP','WorldSBK','WorldSSP','WorldSSP300')}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency {VERSION}\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nAktuelle Racing-News <=7 Tage: {len(fresh)}\nAktuell voll Copy-QM qualifiziert: {len(current_q)}\nVortag voll Copy-QM qualifiziert: {len(fallback_q)}\nGesamtpool nach Racing+Semantic-QM: {len(qualified)}\nFinaler Mix: {mix}\nTurkish-Rider erkannt: {turk}\nProfessional Agent Standard: V1.0\nHuman Writing Protocol: V1.0\nChief-QM PASS: {len(picks)}\n',encoding='utf-8')
 if len(picks)==5:write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk)
 else:send_message(f'🏍️ Racing Agency {VERSION}: nur {len(picks)}/5 Pakete bestanden die komplette Profi-QM-Kette. Kein unsicherer Beitrag wird aufgefüllt.')
 print(f'{VERSION}: raw={len(details)}, fresh={len(fresh)}, current_q={len(current_q)}, fallback_q={len(fallback_q)}, final={len(picks)}, mix={mix}, Turkish={turk}')
if __name__=='__main__':run_v8()
