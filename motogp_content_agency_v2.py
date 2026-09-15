"""Motorcycle Racing Agency V8.2 – MotoGP + WorldSBK + WorldSSP, 5er-Auswahl; Turkish Rider bevorzugt, kein Zwang."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from turkish_riders_scout import scout as turkish_scout, racing_scout
TURKISH_RIDERS=['Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu']
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def riders_in(text):
 low=fold(text);return [n for n in RIDERS_V2 if fold(n) in low]
def is_turkish_focus(item):return bool(item.get('turkish_rider')) or any(fold(n) in fold(item.get('title','')+' '+item.get('summary','')) for n in TURKISH_RIDERS)
def series_for(item):
 if item.get('series'):return item['series']
 u=fold(item.get('url',''));text=fold(item.get('title','')+' '+item.get('summary',''))
 if 'worldsbk.com' in u:return 'WorldSSP' if any(x in text or x in u for x in ('worldssp','world supersport','supersport','/ssp')) else 'WorldSBK'
 return 'MotoGP'
def hashtags(item):
 series=series_for(item);tags=['#WorldSSP' if series=='WorldSSP' else '#WorldSBK' if series=='WorldSBK' else '#MotoGP']
 names=riders_in(item.get('title','')+' '+item.get('summary',''))
 if item.get('turkish_rider') and item['turkish_rider'] not in names:names.insert(0,item['turkish_rider'])
 for n in names[:2]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 tags+=['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def generic_story(item):
 title=re.sub(r'\s+',' ',item.get('title','')).strip();summary=re.sub(r'\s+',' ',item.get('summary','')).strip();r=item.get('turkish_rider') or (riders_in(title+' '+summary)[:1] or [''])[0];series=series_for(item)
 if not title or len(title)<18:return ('','','')
 if item.get('kind')=='profile' and r:return (f'{r} steht in der offiziellen {series}-Fahrerübersicht. Der Fahrer bleibt damit fest in unserem Racing-Radar.',f'🇹🇷 {r} im {series}-Fokus.',f'Wie verfolgst du die Saison von {r}?')
 fact=summary if len(summary)>=45 and not any(x in fold(summary) for x in ('cookie','javascript','privacy')) else title
 if len(fact)>360:fact=fact[:357].rsplit(' ',1)[0]+'…'
 hook=(f'🇹🇷 {r}: {title}' if r else f'🏁 {title}');return (fact,hook,f'Wie ordnest du diese {series}-Meldung ein?')
def german_story(item):
 tl=fold(item.get('title',''))
 if 'game on' in tl and 'largest points deficit' in tl:return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das schon eine seiner stärksten Aufholjagden?')
 if 'pol espargaro' in tl and 'replace' in tl:return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró.','Wie stark schätzt du Pol bei diesem Comeback ein?')
 if 'acosta' in tl and 'ducati' in tl:return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team und wird Teamkollege von Marc Márquez.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Wie schätzt du Acosta neben Márquez ein?')
 return generic_story(item)
def own_caption(item):
 fact,hook,q=german_story(item);return f'{hook}\n\n{fact}\n\n{q}\n\n{hashtags(item)}' if fact else ''
def prepare_media(item,index):
 filename=get_image_path(slugify(f'racing-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1);data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+item['caption'][:180])
 if not data:return ''
 save_bytes(data,filename);return filename.as_posix()
def qualify_copy(item):
 item['caption']=own_caption(item)
 if not item['caption']:return False
 ok,errs=racing_review(item,item['caption']);item['qm_errors']=errs;return ok
def finish_item(item,index):
 item['instagram_media']=prepare_media(item,index)
 if not item['instagram_media']:return False
 item['story_key']=story_key(item['title'],item['url']);ok,errs=chief_review('Motorcycle Racing',item,item['caption'],item['instagram_media'],item['url'],racing_review);item['chief_errors']=errs;return ok
def write_session(items,now):
 lines=['# Motorcycle Racing Telegram Approval Session','Session-Version: 10','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else series_for(x)}',f'Serie: {series_for(x)}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items,turkish_available):
 msg=['🏍️ Motorcycle Racing Agency – 5 QM-GEPRÜFTE Tagesvorschläge','Quellen: MotoGP + WorldSBK + WorldSSP',('🇹🇷 Turkish-Rider: aktueller geeigneter Beitrag bevorzugt aufgenommen' if turkish_available else '🇹🇷 Heute kein geeigneter neuer Turkish-Rider-Beitrag gefunden – 5 beste Racing-Themen gewählt'),'✅ Domain-QM + Chief QM + Batch-QM: PASS','']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ [{series_for(x)}] {x["caption"]}','🖼️ Medium: vorbereitet',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v8():
 names=roster_names();known=known_story_keys();raw=[];seen=set();meta={}
 for t,u,s,r in racing_scout(80):
  u=canonical_url(u);key=story_key(t,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((t,u));meta[u]={'series':s}
  if r:meta[u]['turkish_rider']=r
 for t,u,r in turkish_scout(40):
  u=canonical_url(u);key=story_key(t,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((t,u));meta[u]={'turkish_rider':r,'series':('WorldSSP' if 'worldssp' in fold(t+u) else 'WorldSBK' if 'worldsbk.com' in fold(u) else 'MotoGP'),'kind':('profile' if '/riders/' in u else 'news')}
 for title,url in extract(get(NEWS),60)+extract(get(MARKET),30):
  u=canonical_url(url);key=story_key(title,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((title,u))
 details=[]
 for t,u in raw[:160]:
  x=article_info(t,u);x.update(meta.get(u,{}));details.append(x)
 now=datetime.now(timezone.utc);candidates=[];turkish=[x for x in details if is_turkish_focus(x) and qualify_copy(x)]
 # Turkish Rider ist Bonus/Priorität, niemals Pflicht. Fehlt ein aktueller geeigneter Beitrag, werden die 5 besten übrigen Racing-Themen gewählt.
 if turkish:candidates.append(turkish[0])
 for x in sorted(details,key=lambda z:score(z['title'],names),reverse=True):
  if len(candidates)>=5:break
  if any(p['url']==x['url'] for p in candidates) or not qualify_copy(x):continue
  candidates.append(x)
 if len(candidates)==5:
  batch=review_batch(candidates);candidates=[x for x,(ok,_) in zip(candidates,batch) if ok]
 picks=[]
 if len(candidates)==5:
  for i,x in enumerate(candidates,1):
   if finish_item(x,i):picks.append(x)
 turk=any(is_turkish_focus(x) for x in picks);counts={s:sum(series_for(x)==s for x in details) for s in ('MotoGP','WorldSBK','WorldSSP')}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Motorcycle Racing Daily Agency\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nMotoGP: {counts["MotoGP"]}\nWorldSBK: {counts["WorldSBK"]}\nWorldSSP: {counts["WorldSSP"]}\nTurkish Copy-Kandidaten: {len(turkish)}\nBatch-QM Kandidaten: {len(candidates)}\nChief-QM PASS: {len(picks)}\nTurkish-Rider: {"INCLUDED" if turk else "NO-SUITABLE-CURRENT-STORY"}\n',encoding='utf-8')
 if len(picks)==5:
  write_session(picks,now);remember_offered(picks,now);telegram_preview(picks,turk)
 else:send_message(f'🏍️ Racing Agency: nur {len(picks)}/5 Chief-QM-Pakete. Keine unvollständige Auswahl gesendet.')
 print(f'Racing V8.2: raw={len(details)}, series={counts}, turkish_copy={len(turkish)}, batch={len(candidates)}, final={len(picks)}, TurkishIncluded={turk}')
if __name__=='__main__':run_v8()
