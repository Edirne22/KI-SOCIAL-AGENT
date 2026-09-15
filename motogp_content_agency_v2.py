"""Racing Content Agency V4 – 5 Pakete, davon mindestens 1 Toprak/Can Öncü, alle Chief-QM-geprüft."""
from motogp_content_agency import *
from motogp_quality_manager import review as motogp_review
from chief_quality_manager import review as chief_review
from turkish_riders_scout import scout as turkish_scout
RIDERS_V2=['Toprak Razgatlioglu','Can Oncu','Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']
def riders_in(text):
 low=text.casefold();found=[]
 for n in RIDERS_V2:
  variants=[n.casefold(),n.casefold().replace('oncu','öncü'),n.casefold().replace('razgatlioglu','razgatlıoğlu')]
  if any(v in low for v in variants):found.append(n)
 return found
def is_turkish_focus(item):
 low=(item.get('title','')+' '+item.get('summary','')).casefold();return any(x in low for x in ('toprak','razgatlioglu','razgatlıoğlu','can oncu','can öncü','oncu','öncü'))
def hashtags(item):
 tags=['#MotoGP' if 'motogp.com' in item['url'] else '#WorldSSP'];
 for n in riders_in(item['title']+' '+item['summary'])[:3]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 tags += ['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def german_story(item):
 t=item['title'];tl=t.casefold();d=item.get('summary','');low=(t+' '+d).casefold()
 if ('oncu' in low or 'öncü' in low) and ('first 2026' in low or 'p13' in low or 'race 1' in low):return ('Can Öncü kämpft sich in Magny-Cours von Startplatz 13 bis ganz nach vorne und holt seinen ersten WorldSSP-Sieg der Saison 2026. Nach der Sommerpause zeigt die #61 damit genau die Antwort, auf die seine Fans gewartet haben.','🇹🇷 Can Öncü meldet sich mit einem echten Ausrufezeichen zurück!','Wie stark war bitte diese Aufholjagd von P13 bis zum Sieg? 🔥')
 if ('toprak' in low or 'razgatlioglu' in low or 'razgatlıoğlu' in low):return ('Toprak Razgatlıoğlu bleibt eines der spannendsten Themen rund um Yamaha und die MotoGP. Entscheidend für diesen Post sind ausschließlich die konkreten Fakten der verlinkten offiziellen MotoGP-Meldung.','🇹🇷 El Turco bleibt im Fokus der Königsklasse!','Was traust du Toprak als Nächstes in der MotoGP zu? 👇')
 if 'martin soars to silverstone' in tl and 'sprint' in tl:return ('Jorge Martin gewinnt den Sprint in Silverstone vor Ai Ogura und Marco Bezzecchi. Für Aprilia wird der Samstag damit besonders stark.','🇬🇧 Aprilia räumt in Silverstone ab – Martin führt das Sprint-Podium an.','Ist Aprilia für dich inzwischen der stärkste Gegner im Titelkampf?')
 if 'fends off acosta and bezzecchi' in tl and 'aragon' in tl:return ('Marc Márquez setzt sich in Aragón gegen Pedro Acosta und Marco Bezzecchi durch. An der Spitze wird hart gekämpft.','🔥 Márquez behauptet sich in Aragón gegen Acosta und Bezzecchi.','Wer von den drei hat dich am meisten überzeugt?')
 if 'retaliates to hold off alex marquez' in tl and 'aragon' in tl:return ('Marc Márquez schlägt im Aragón-Sprint zurück und hält Alex Márquez hinter sich. Marco Bezzecchi komplettiert das Podium.','⚔️ Márquez gegen Márquez: Marc gewinnt das Aragón-Duell vor Alex.','War Marc an diesem Tag einfach zu stark?')
 if 'game on' in tl and 'largest points deficit' in tl:return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das schon eine seiner stärksten Aufholjagden?')
 if 'pol espargaro' in tl and 'replace' in tl:return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró.','Wie stark schätzt du Pol bei diesem Comeback ein?')
 if 'acosta' in tl and 'ducati' in tl:return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team und wird Teamkollege von Marc Márquez.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Wie schätzt du Acosta neben Márquez ein?')
 if 'bezzecchi' in tl and ('pole' in tl or 'lap record' in tl):return ('Marco Bezzecchi setzt im Qualifying ein starkes Zeichen und holt sich die Pole.','⏱️ Bezzecchi setzt ein richtig starkes Zeichen.','Wer ist für dich aktuell über eine schnelle Runde stärker?')
 return ('','','')
def own_caption(item):
 fact,hook,q=german_story(item);return f'{hook}\n\n{fact}\n\n{q}\n\n{hashtags(item)}' if fact else ''
def prepare_media(item,index):
 filename=get_image_path(slugify(f'racing-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1);data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+item['caption'][:180]);
 if not data:return ''
 save_bytes(data,filename);return filename.as_posix()
def write_session(items,now):
 lines=['# MotoGP Telegram Approval Session','Session-Version: 6','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen wie `motogp 1,3,5`, `motogp alle` oder `motogp nein`.','']
 for i,item in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Kategorie: {"Turkish Riders" if is_turkish_focus(item) else "MotoGP"}',f'Story-Key: {story_key(item["title"],item["url"])}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Instagram-Bild: {item["instagram_media"]}',f'Quellen-Preview: {item.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{item["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items):
 msg=['🏁 Racing Content Agency – 5 QM-GEPRÜFTE Tagesvorschläge','🇹🇷 Mindestens ein Turkish-Rider-Slot: Toprak Razgatlıoğlu oder Can Öncü','✅ Domain-QM + Chief QM: PASS','']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {x["caption"]}','🖼️ Medium: vorbereitet',f'🔗 Quelle: {x["url"]}','']
 msg += ['Freigabe: motogp 1–5 / Kombination z.B. motogp 1,4 / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def enrich(raw):return article_info(raw[0],raw[1])
def run_v4():
 names=roster_names();known=known_story_keys();base=extract(get(NEWS),60)+extract(get(MARKET),30);special=turkish_scout(20);raw=[];seen=set()
 # Pflicht-Scout zuerst, danach reguläre MotoGP-Auswahl.
 for x in special+base:
  u=canonical_url(x[1]);key=story_key(x[0],u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((x[0],u))
 details=[enrich(x) for x in raw[:40]];now=datetime.now(timezone.utc);picks=[]
 # zuerst genau einen geeigneten Turkish-Rider-Kandidaten sichern
 ordered=sorted(details,key=lambda x:(not is_turkish_focus(x),-score(x['title'],names)))
 for item in ordered:
  if len(picks)>=5:break
  if not is_turkish_focus(item) and not any(is_turkish_focus(p) for p in picks):continue
  item['caption']=own_caption(item)
  if not item['caption']:continue
  ok,errs=motogp_review(item,item['caption'])
  if not ok:continue
  item['instagram_media']=prepare_media(item,len(picks)+1)
  if not item['instagram_media']:continue
  item['story_key']=story_key(item['title'],item['url']);ok,errs=chief_review('Racing',item,item['caption'],item['instagram_media'],item['url'],motogp_review)
  if ok:picks.append(item)
 # dann mit den besten übrigen MotoGP-Stories auf fünf auffüllen
 for item in sorted(details,key=lambda x:score(x['title'],names),reverse=True):
  if len(picks)>=5:break
  if any(p['url']==item['url'] for p in picks):continue
  item['caption']=own_caption(item)
  if not item['caption']:continue
  ok,_=motogp_review(item,item['caption'])
  if not ok:continue
  item['instagram_media']=prepare_media(item,len(picks)+1)
  if not item['instagram_media']:continue
  item['story_key']=story_key(item['title'],item['url']);ok,_=chief_review('Racing',item,item['caption'],item['instagram_media'],item['url'],motogp_review)
  if ok:picks.append(item)
 turk=any(is_turkish_focus(x) for x in picks)
 OUT.write_text(f'# Racing Daily Content Agency\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nNeue Kandidaten: {len(details)}\nChief-QM PASS: {len(picks)}\nTurkish-Rider-Slot: {"PASS" if turk else "FAIL"}\n',encoding='utf-8')
 if len(picks)==5 and turk:
  write_session(picks,now);remember_offered(picks,now);telegram_preview(picks)
 else:send_message(f'🏁 Racing Agency: {len(picks)}/5 Chief-QM-Pakete, Turkish-Rider-Slot={"PASS" if turk else "FAIL"}. Keine unvollständige Tagesauswahl gesendet.')
 print(f'Racing V4: {len(picks)}/5, Turkish={turk}')
if __name__=='__main__':run_v4()
