"""Motorcycle Racing Agency V8.3 – aktuelle Top-5, Turkish bevorzugt, kontrollierter Vortags-Top10-Fallback."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from turkish_riders_scout import scout as turkish_scout, racing_scout
import json
from datetime import timedelta
TOP10=Path('memory/RACING_TOP10_POOL.json')
TURKISH_RIDERS=['Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu']
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def riders_in(text):return [n for n in RIDERS_V2 if fold(n) in fold(text)]
def is_turkish_focus(x):return bool(x.get('turkish_rider')) or any(fold(n) in fold(x.get('title','')+' '+x.get('summary','')) for n in TURKISH_RIDERS)
def series_for(x):
 if x.get('series'):return x['series']
 u=fold(x.get('url',''));t=fold(x.get('title','')+' '+x.get('summary',''))
 if 'worldsbk.com' in u:return 'WorldSSP' if any(v in t or v in u for v in ('worldssp','world supersport','supersport','/ssp')) else 'WorldSBK'
 return 'MotoGP'
def hashtags(x):
 s=series_for(x);tags=['#WorldSSP' if s=='WorldSSP' else '#WorldSBK' if s=='WorldSBK' else '#MotoGP'];names=riders_in(x.get('title','')+' '+x.get('summary',''))
 if x.get('turkish_rider') and x['turkish_rider'] not in names:names.insert(0,x['turkish_rider'])
 tags += ['#'+re.sub(r'[^A-Za-z0-9]','',n) for n in names[:2]]+['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def generic_story(x):
 title=re.sub(r'\s+',' ',x.get('title','')).strip();summary=re.sub(r'\s+',' ',x.get('summary','')).strip();r=x.get('turkish_rider') or (riders_in(title+' '+summary)[:1] or [''])[0];s=series_for(x)
 if not title or len(title)<18:return ('','','')
 if x.get('kind')=='profile' and r:return (f'{r} steht in der offiziellen {s}-Fahrerübersicht. Der Fahrer bleibt damit fest in unserem Racing-Radar.',f'🇹🇷 {r} im {s}-Fokus.',f'Wie verfolgst du die Saison von {r}?')
 fact=summary if len(summary)>=45 and not any(v in fold(summary) for v in ('cookie','javascript','privacy')) else title
 if len(fact)>360:fact=fact[:357].rsplit(' ',1)[0]+'…'
 return (fact,(f'🇹🇷 {r}: {title}' if r else f'🏁 {title}'),f'Wie ordnest du diese {s}-Meldung ein?')
def german_story(x):
 tl=fold(x.get('title',''))
 if 'game on' in tl and 'largest points deficit' in tl:return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das schon eine seiner stärksten Aufholjagden?')
 if 'pol espargaro' in tl and 'replace' in tl:return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró.','Wie stark schätzt du Pol bei diesem Comeback ein?')
 if 'acosta' in tl and 'ducati' in tl:return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team und wird Teamkollege von Marc Márquez.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Wie schätzt du Acosta neben Márquez ein?')
 return generic_story(x)
def own_caption(x):
 fact,hook,q=german_story(x);return f'{hook}\n\n{fact}\n\n{q}\n\n{hashtags(x)}' if fact else ''
def qualify_copy(x):
 x['caption']=own_caption(x)
 if not x['caption']:return False
 ok,errs=racing_review(x,x['caption']);x['qm_errors']=errs;return ok
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
 p=Path('memory/PUBLISHED.md')
 if not p.exists():return set()
 text=p.read_text(encoding='utf-8',errors='ignore');return set(re.findall(r'(?:motogp|worldsbk|worldssp):[A-Za-z0-9._:-]+',text,re.I))
def save_top10(items,now):
 data=load_pool();day=now.date().isoformat();rows=[]
 for x in items[:10]:rows.append({'story_key':story_key(x['title'],x['url']),'title':x['title'],'url':x['url'],'summary':x.get('summary',''),'preview':x.get('preview',''),'series':series_for(x),'turkish_rider':x.get('turkish_rider',''),'kind':x.get('kind','news')})
 data.setdefault('days',{})[day]=rows
 keep={(now.date()-timedelta(days=i)).isoformat() for i in range(3)};data['days']={k:v for k,v in data['days'].items() if k in keep};TOP10.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def yesterday_fallback(now,current_urls):
 data=load_pool();rows=data.get('days',{}).get((now.date()-timedelta(days=1)).isoformat(),[]);pub=published_keys();out=[]
 for r in rows:
  if r.get('url') in current_urls or r.get('story_key') in pub:continue
  x=dict(r);x['fallback_yesterday']=True
  if qualify_copy(x):out.append(x)
 return out
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 10','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Herkunft: {"Top-10 vom Vortag" if x.get("fallback_yesterday") else "Aktuell"}',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items,turk):
 msg=['🏍️ Motorcycle Racing Agency – 5 QM-GEPRÜFTE Tagesvorschläge','Quellen: MotoGP + WorldSBK + WorldSSP',('🇹🇷 Turkish-Rider: aktueller geeigneter Beitrag bevorzugt aufgenommen' if turk else '🇹🇷 Heute kein geeigneter neuer Turkish-Rider-Beitrag gefunden'),'✅ Domain-QM + Chief QM + Batch-QM: PASS','']
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
  seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'series':('WorldSSP' if 'worldssp' in fold(t+u) else 'WorldSBK' if 'worldsbk.com' in fold(u) else 'MotoGP'),'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),60)+extract(get(MARKET),30):
  u=canonical_url(url);key=story_key(title,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:160]:x=article_info(t,u);x.update(meta.get(u,{}));details.append(x)
 now=datetime.now(timezone.utc);qualified=[x for x in sorted(details,key=lambda z:score(z['title'],names),reverse=True) if qualify_copy(x)];turkish=[x for x in qualified if is_turkish_focus(x)]
 ranked=[]
 if turkish:ranked.append(turkish[0])
 for x in qualified:
  if len(ranked)>=10:break
  if not any(p['url']==x['url'] for p in ranked):ranked.append(x)
 save_top10(ranked,now)
 candidates=ranked[:5]
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
 turk=any(is_turkish_focus(x) for x in picks);fallbacks=sum(bool(x.get('fallback_yesterday')) for x in picks);counts={s:sum(series_for(x)==s for x in details) for s in ('MotoGP','WorldSBK','WorldSSP')}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nMotoGP: {counts["MotoGP"]}\nWorldSBK: {counts["WorldSBK"]}\nWorldSSP: {counts["WorldSSP"]}\nQualifizierte aktuelle Themen: {len(qualified)}\nTop-10 gespeichert: {len(ranked)}\nVortags-Fallbacks: {fallbacks}\nChief-QM PASS: {len(picks)}\n',encoding='utf-8')
 if len(picks)==5:write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk)
 else:send_message(f'🏍️ Racing Agency: nur {len(picks)}/5 Chief-QM-Pakete – auch nach geprüftem Vortags-Top10-Fallback. Keine unvollständige Auswahl gesendet.')
 print(f'Racing V8.3: raw={len(details)}, qualified={len(qualified)}, top10={len(ranked)}, fallback={fallbacks}, final={len(picks)}')
if __name__=='__main__':run_v8()
