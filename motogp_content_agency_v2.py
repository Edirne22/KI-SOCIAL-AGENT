"""Motorcycle Racing Agency V8.4.3 – Turkish-Erkennung, Race-Prioritaet, Sprach-QM, schnellere Pipeline."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from turkish_riders_scout import scout as turkish_scout, racing_scout
from llm_client import generate
import json
from datetime import timedelta, datetime as dt
from concurrent.futures import ThreadPoolExecutor, as_completed
TOP10=Path('memory/RACING_TOP10_POOL.json')
TURKISH_ALIASES={'Toprak Razgatlioglu':('toprak razgatlioglu','toprak razgatlıoğlu'),'Can Oncu':('can oncu','can öncü'),'Deniz Oncu':('deniz oncu','deniz öncü'),'Bahattin Sofuoglu':('bahattin sofuoglu','bahattin sofuoğlu'),'Zayn Sofuoglu':('zayn sofuoglu','zayn sofuoğlu')}
TURKISH_RIDERS=list(TURKISH_ALIASES)
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']
PROMO_WORDS=('fantasy','super boost','mystery boost','videopass','video pass','tickets','ticket','store','merch','merchandise','shop','giveaway','promo code','promotion')
RACING_WORDS=('race','racing','grand prix',' gp','practice','fp1','fp2','qualifying','pole','sprint','podium','win','victory','championship','title','rider','team','replace','injury','return','test','lap','grid','motogp','moto2','moto3','worldsbk','worldssp','supersport')
FEATURE_WORDS=('hall of fame','legend','inducted','tribute','anniversary','documentary','gallery','talking points')
BAD_GERMAN=('legende zu einer legende','mit großem anfangsbuchstaben','mit grossem anfangsbuchstaben','erfahrt alle wichtigen','unter dem titel','neueste ausgabe an der adriaküste','neueste ausgabe an der adriakueste')
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def article_text(x):return ' '.join((x.get('title',''),x.get('summary',''),x.get('url','')))
def riders_in(text):return [n for n in RIDERS_V2 if fold(n) in fold(text)]
def detect_turkish_rider(x):
 text=fold(article_text(x))
 for rider,aliases in TURKISH_ALIASES.items():
  if any(fold(a) in text for a in aliases):return rider
 # WorldSSP official headlines often shorten Can Öncü to Oncu/Öncü. Deniz is excluded explicitly.
 if 'oncu' in text and 'deniz' not in text and series_for_raw(x)=='WorldSSP':return 'Can Oncu'
 return ''
def enrich_turkish(x):
 r=x.get('turkish_rider') or detect_turkish_rider(x)
 if r:x['turkish_rider']=r
 return x
def series_for_raw(x):
 if x.get('series'):return x['series']
 u=fold(x.get('url',''));t=fold(article_text(x))
 if 'worldsbk.com' in u:
  if 'worldssp300' in t or 'worldssp 300' in t:return 'WorldSSP300'
  return 'WorldSSP' if any(v in t or v in u for v in ('worldssp','world supersport','supersport','/ssp')) else 'WorldSBK'
 return 'MotoGP'
def series_for(x):return series_for_raw(x)
def is_turkish_focus(x):return bool(enrich_turkish(x).get('turkish_rider'))
def article_date(x):
 m=re.search(r'/(20\d{2})/(\d{2})/(\d{2})/',x.get('url',''))
 if not m:return None
 try:return dt(int(m.group(1)),int(m.group(2)),int(m.group(3)),tzinfo=timezone.utc)
 except ValueError:return None
def age_days(x,now):
 d=article_date(x);return (now-d).total_seconds()/86400 if d else 9999
def current_news(x,now,max_days=7):return x.get('kind','news')!='profile' and 0<=age_days(x,now)<=max_days
def is_feature(x):return any(w in fold(article_text(x)) for w in FEATURE_WORDS)
def racing_relevant(x):
 text=fold(article_text(x))
 if any(w in text for w in PROMO_WORDS):return False
 return bool(riders_in(text) or detect_turkish_rider(x) or any(w in text for w in RACING_WORDS))
def editorial_score(x,names):
 age=max(0,age_days(x,datetime.now(timezone.utc)));fresh=max(0,80-int(age*10));base=score(x.get('title',''),names);text=fold(article_text(x))
 sport=sum(12 for w in ('win','victory','pole','podium','championship','title','race','sprint','qualifying','injury','return','replace') if w in text)
 live=35 if any(w in text for w in ('race','sprint','qualifying','practice','fp1','fp2','championship','standings','injury','return','replace')) else 0
 return fresh+base+sport+live+(30 if is_turkish_focus(x) else 0)+(-45 if is_feature(x) else 0)
def hashtags(x):
 enrich_turkish(x);s=series_for(x);tags=['#WorldSSP' if s=='WorldSSP' else '#WorldSBK' if s=='WorldSBK' else '#MotoGP'];names=riders_in(article_text(x))
 if x.get('turkish_rider') and x['turkish_rider'] not in names:names.insert(0,x['turkish_rider'])
 tags += ['#'+re.sub(r'[^A-Za-z0-9]','',n) for n in names[:2]]+['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def language_sane(caption):
 low=fold(caption)
 return not any(fold(x) in low for x in BAD_GERMAN) and not any(x in low for x in ('click here','read more','find out more','latest edition','talking points:'))
def german_editor(x):
 enrich_turkish(x);title=re.sub(r'\s+',' ',x.get('title','')).strip();summary=re.sub(r'\s+',' ',x.get('summary','')).strip();series=series_for(x);turk=x.get('turkish_rider','')
 if not title or len(title)<18:return ''
 prompt=f'''Du bist der deutsche Motorrad-Racing-Redakteur für Bülents Bike Life. Schreibe aus den offiziellen Quellfakten einen eigenständigen deutschen Social-Media-Post.\nSERIE: {series}\nTITEL: {title}\nZUSAMMENFASSUNG: {summary}\nTURKISH_RIDER: {turk or 'NEIN'}\nREGELN: Nur belegte Fakten aus TITEL/ZUSAMMENFASSUNG. Nichts erfinden. Keine neuen Zitate, Zahlen, Namen, Orte oder Ergebnisse. Natürliches idiomatisches Deutsch, keine wörtlich übersetzten englischen Redewendungen und keine Navigation wie Erfahrt/Read more. 2 bis 4 informative Sätze. Konkreter Hook, Haupttext, konkrete Community-Frage. Keine Meta-Sätze, keine künstliche Hype-Sprache. Hall-of-Fame/Legend/Feature-Themen sachlich. 🇹🇷 nur wenn TURKISH_RIDER nicht NEIN. Keine Hashtags. Antworte ausschließlich als JSON: {{"hook":"...","body":"...","question":"..."}}'''
 try:
  raw=generate('final_captions',prompt).strip();raw=re.sub(r'^```(?:json)?\s*|\s*```$','',raw,flags=re.I|re.S);obj=json.loads(raw);hook=str(obj.get('hook','')).strip();body=str(obj.get('body','')).strip();q=str(obj.get('question','')).strip()
  if not hook or not body or '?' not in q:return ''
  if not turk:hook=hook.replace('🇹🇷','').strip()
  caption=f'{hook}\n\n{body}\n\n{q}\n\n{hashtags(x)}';return caption if language_sane(caption) else ''
 except Exception as e:print('DE-Redakteur FAIL:',type(e).__name__,str(e)[:180]);return ''
def qualify_copy(x):
 if not racing_relevant(x):return False
 x['caption']=german_editor(x)
 if not x['caption']:return False
 ok,errs=racing_review(x,x['caption']);x['qm_errors']=errs;return ok
def qualify_parallel(items,max_workers=5):
 out=[]
 with ThreadPoolExecutor(max_workers=max_workers) as ex:
  jobs={ex.submit(qualify_copy,x):x for x in items}
  for f in as_completed(jobs):
   try:
    if f.result():out.append(jobs[f])
   except Exception as e:print('Parallel-DE FAIL:',type(e).__name__,str(e)[:160])
 return out
def prepare_media(x,i):
 filename=get_image_path(slugify(f'racing-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{i}-{x["title"]}'),1);data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+x['caption'][:180])
 if not data:return ''
 save_bytes(data,filename);return filename.as_posix()
def finish_item(x,i):
 x['instagram_media']=prepare_media(x,i)
 if not x['instagram_media']:return False
 x['story_key']=story_key(x['title'],x['url']);ok,errs=chief_review('Motorcycle Racing',x,x['caption'],x['instagram_media'],x['url'],racing_review);x['chief_errors']=errs;return ok
def load_pool():
 try:return json.loads(TOP10.read_text(encoding='utf-8'))
 except Exception:return {'version':1,'days':{}}
def published_keys():
 p=Path('content/PUBLISHED.md')
 if not p.exists():return set()
 return set(re.findall(r'(?:motogp|worldsbk|worldssp):[A-Za-z0-9._:-]+',p.read_text(encoding='utf-8',errors='ignore'),re.I))
def save_top10(items,now):
 data=load_pool();day=now.date().isoformat();rows=[]
 for x in items[:10]:
  enrich_turkish(x);rows.append({'story_key':story_key(x['title'],x['url']),'title':x['title'],'url':x['url'],'summary':x.get('summary',''),'preview':x.get('preview',''),'series':series_for(x),'turkish_rider':x.get('turkish_rider',''),'kind':x.get('kind','news')})
 data.setdefault('days',{})[day]=rows;keep={(now.date()-timedelta(days=i)).isoformat() for i in range(3)};data['days']={k:v for k,v in data['days'].items() if k in keep};TOP10.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def yesterday_fallback(now,current_urls):
 data=load_pool();rows=data.get('days',{}).get((now.date()-timedelta(days=1)).isoformat(),[]);pub=published_keys();eligible=[]
 for r in rows:
  if r.get('url') in current_urls or r.get('story_key') in pub:continue
  x=enrich_turkish(dict(r));x['fallback_yesterday']=True
  if current_news(x,now,7) and racing_relevant(x):eligible.append(x)
 return qualify_parallel(eligible[:8],4)
def smart_mix(qualified,names):
 pool=sorted(qualified,key=lambda x:editorial_score(x,names),reverse=True);chosen=[];turk=[x for x in pool if is_turkish_focus(x) and not is_feature(x)]
 if turk:chosen.append(turk[0])
 race_pool=[x for x in pool if not is_feature(x)];mg=[x for x in race_pool if series_for(x)=='MotoGP' and x not in chosen]
 for x in mg[:max(0,3-sum(series_for(y)=='MotoGP' for y in chosen))]:chosen.append(x)
 for source in (race_pool,pool):
  for x in source:
   if len(chosen)>=5:break
   if x in chosen:continue
   s=series_for(x)
   if s!='MotoGP' and sum(series_for(y)==s for y in chosen)>=3:continue
   chosen.append(x)
  if len(chosen)>=5:break
 return chosen[:5]
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 14','Agency-Version: V8.4.3','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Herkunft: {"Top-10 vom Vortag" if x.get("fallback_yesterday") else "Aktuell"}',f'Artikelalter-Tage: {age_days(x,now):.1f}',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items,turk):
 mix=', '.join(f'{s} {sum(series_for(x)==s for x in items)}' for s in ('MotoGP','WorldSBK','WorldSSP') if any(series_for(x)==s for x in items))
 msg=['🏍️ Motorcycle Racing Agency V8.4.3 – 5 AKTUELLE RACING-Tagesvorschläge','Aktualitäts-Gate: max. 7 Tage | Promo/Fantasy: gesperrt | Race-News priorisiert',f'Serienmix: {mix}',('🇹🇷 Turkish-Rider: aktueller geeigneter Beitrag bevorzugt aufgenommen' if turk else '🇹🇷 Heute kein geeigneter neuer Turkish-Rider-Beitrag gefunden'),'🇩🇪 DE-Redakteur + Sprach-QM + Racing-QM + Chief-QM + Batch-QM: PASS','']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {"↩️ Top-10 vom Vortag | " if x.get("fallback_yesterday") else ""}[{series_for(x)}] {x["caption"]}','🖼️ Medium: vorbereitet',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v8():
 names=roster_names();known=known_story_keys();raw=[];seen=set();meta={}
 for t,u,s,r in racing_scout(80):
  u=canonical_url(u);key=story_key(t,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((t,u));meta[u]={'series':s,**({'turkish_rider':r} if r else {})}
 for t,u,r in turkish_scout(40):
  u=canonical_url(u);key=story_key(t,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),60)+extract(get(MARKET),30):
  u=canonical_url(url);key=story_key(title,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:180]:
  x=article_info(t,u);x.update(meta.get(u,{}));details.append(enrich_turkish(x))
 now=datetime.now(timezone.utc);fresh=[x for x in details if current_news(x,now,7) and racing_relevant(x)];fresh.sort(key=lambda z:editorial_score(z,names),reverse=True)
 # Performance: 20 bestbewertete Kandidaten, 5 parallele DE/QM-Worker statt bis zu 50 serieller KI-Aufrufe.
 qualified=qualify_parallel(fresh[:20],5);qualified.sort(key=lambda x:editorial_score(x,names),reverse=True);ranked=qualified[:10];save_top10(ranked,now);candidates=smart_mix(qualified,names)
 if len(candidates)<5:
  for x in yesterday_fallback(now,{p['url'] for p in candidates}):
   if len(candidates)>=5:break
   candidates.append(x)
 if len(candidates)==5:
  batch=review_batch(candidates);candidates=[x for x,(ok,_) in zip(candidates,batch) if ok]
 picks=[]
 if len(candidates)==5:
  for i,x in enumerate(candidates,1):
   if finish_item(x,i):picks.append(x)
 turk=any(is_turkish_focus(x) for x in picks);fallbacks=sum(bool(x.get('fallback_yesterday')) for x in picks);mix={s:sum(series_for(x)==s for x in picks) for s in ('MotoGP','WorldSBK','WorldSSP')}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency V8.4.3\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nAktuelle Racing-News <=7 Tage: {len(fresh)}\nDE+QM qualifiziert: {len(qualified)}\nTop-10 gespeichert: {len(ranked)}\nVortags-Fallbacks: {fallbacks}\nFinaler Mix: {mix}\nTurkish-Rider erkannt: {turk}\nChief-QM PASS: {len(picks)}\n',encoding='utf-8')
 if len(picks)==5:write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk)
 else:send_message(f'🏍️ Racing Agency V8.4.3: nur {len(picks)}/5 aktuelle relevante Racing-Pakete. Keine Promo-, Alt- oder sprachlich unsauberen Meldungen zum Auffüllen.')
 print(f'Racing V8.4.3: raw={len(details)}, fresh_racing={len(fresh)}, de_qm={len(qualified)}, final={len(picks)}, mix={mix}, TurkishIncluded={turk}')
if __name__=='__main__':run_v8()
