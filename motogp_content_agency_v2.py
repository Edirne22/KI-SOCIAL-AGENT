"""Racing Content Agency V5 – fünf QM-Pakete, Turkish-Riders-Redaktion als Pflichtslot."""
from motogp_content_agency import *
from motogp_quality_manager import review as motogp_review
from chief_quality_manager import review as chief_review
from turkish_riders_scout import scout as turkish_scout

TURKISH_RIDERS=['Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu']
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']

def fold(s):
 return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def riders_in(text):
 low=fold(text);return [n for n in RIDERS_V2 if fold(n) in low]
def is_turkish_focus(item):
 low=fold(item.get('title','')+' '+item.get('summary',''))
 return any(fold(n) in low for n in TURKISH_RIDERS)
def hashtags(item):
 host=fold(item.get('url',''));tags=['#MotoGP' if 'motogp.com' in host else '#WorldSBK']
 for n in riders_in(item.get('title','')+' '+item.get('summary',''))[:3]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 tags += ['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))[:500]
def german_story(item):
 t=item.get('title','');tl=fold(t);d=item.get('summary','');low=fold(t+' '+d)
 if 'can oncu' in low and ('first 2026' in low or 'p13' in low or 'race 1' in low):return ('Can Öncü kämpft sich von Startplatz 13 bis ganz nach vorne und holt seinen ersten WorldSSP-Sieg der Saison 2026. Damit setzt die #61 nach der Sommerpause ein starkes Ausrufezeichen.','🇹🇷 Can Öncü meldet sich mit einer starken Aufholjagd zurück!','Wie stark war für dich dieser Weg von P13 bis zum Sieg? 🔥')
 # Für Turkish-Rider-Artikel ohne belastbares, bekanntes Faktenmuster niemals generischen Text erfinden.
 # Sie werden vom Copy-Gate übersprungen, bis konkrete Fakten extrahiert werden können.
 if any(fold(n) in low for n in TURKISH_RIDERS):return ('','','')
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
 filename=get_image_path(slugify(f'racing-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1)
 data=agnes_generate_image('Vertical 4:5 premium motorcycle racing editorial background, empty circuit, dramatic light, NO people, NO riders, NO motorcycles, NO logos, NO brands, NO text, NO watermark. Mood: '+item['caption'][:180])
 if not data:return ''
 save_bytes(data,filename);return filename.as_posix()
def write_session(items,now):
 lines=['# Racing Telegram Approval Session','Session-Version: 7','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen wie `motogp 1,3,5`, `motogp alle` oder `motogp nein`.','']
 for i,item in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Kategorie: {"Turkish Riders" if is_turkish_focus(item) else "MotoGP"}',f'Story-Key: {story_key(item["title"],item["url"])}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Instagram-Bild: {item["instagram_media"]}',f'Quellen-Preview: {item.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{item["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items):
 names=', '.join(TURKISH_RIDERS)
 msg=['🏁 Racing Content Agency – 5 QM-GEPRÜFTE Tagesvorschläge','🇹🇷 Mindestens ein Turkish-Riders-Slot aus der KNN54-Watchlist','✅ Domain-QM + Chief QM: PASS','']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {x["caption"]}','🖼️ Medium: vorbereitet',f'🔗 Quelle: {x["url"]}','']
 msg += ['Freigabe: motogp 1–5 / Kombination z.B. motogp 1,4 / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def enrich(raw):return article_info(raw[0],raw[1])
def qualify(item,index):
 item['caption']=own_caption(item)
 if not item['caption']:return False
 ok,_=motogp_review(item,item['caption'])
 if not ok:return False
 item['instagram_media']=prepare_media(item,index)
 if not item['instagram_media']:return False
 item['story_key']=story_key(item['title'],item['url'])
 ok,_=chief_review('Racing',item,item['caption'],item['instagram_media'],item['url'],motogp_review)
 return ok
def run_v5():
 names=roster_names();known=known_story_keys();base=extract(get(NEWS),60)+extract(get(MARKET),30);special=turkish_scout(30);raw=[];seen=set()
 for x in special+base:
  u=canonical_url(x[1]);key=story_key(x[0],u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((x[0],u))
 details=[enrich(x) for x in raw[:50]];now=datetime.now(timezone.utc);picks=[]
 # 1) Turkish-Rider-Pflichtslot zuerst vollständig qualifizieren.
 for item in [x for x in details if is_turkish_focus(x)]:
  if qualify(item,1):picks.append(item);break
 # 2) Nur wenn Pflichtslot PASS ist, auf fünf auffüllen.
 if picks:
  for item in sorted(details,key=lambda x:score(x['title'],names),reverse=True):
   if len(picks)>=5:break
   if any(p['url']==item['url'] for p in picks):continue
   if qualify(item,len(picks)+1):picks.append(item)
 turk=bool(picks and is_turkish_focus(picks[0]))
 OUT.parent.mkdir(parents=True,exist_ok=True)
 OUT.write_text(f'# Racing Daily Content Agency\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nNeue Kandidaten: {len(details)}\nChief-QM PASS: {len(picks)}\nTurkish-Rider-Slot: {"PASS" if turk else "FAIL"}\n',encoding='utf-8')
 if len(picks)==5 and turk:
  write_session(picks,now);remember_offered(picks,now);telegram_preview(picks)
 else:send_message(f'🏁 Racing Agency: {len(picks)}/5 Chief-QM-Pakete, Turkish-Rider-Slot={"PASS" if turk else "FAIL"}. Keine unvollständige Tagesauswahl gesendet.')
 print(f'Racing V5: {len(picks)}/5, Turkish={turk}')
if __name__=='__main__':run_v5()
