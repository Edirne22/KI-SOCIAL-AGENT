"""Racing Content Agency V6 – 5 Pakete, Turkish-Riders-Pflichtslot, fail-closed QM."""
from motogp_content_agency import *
from motogp_quality_manager import review as racing_review, review_batch
from chief_quality_manager import review as chief_review
from turkish_riders_scout import legacy_pairs as turkish_scout
TURKISH_RIDERS=['Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu']
RIDERS_V2=TURKISH_RIDERS+['Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def riders_in(text):
 low=fold(text);return [n for n in RIDERS_V2 if fold(n) in low]
def is_turkish_focus(item):return any(fold(n) in fold(item.get('title','')+' '+item.get('summary','')) for n in TURKISH_RIDERS)
def hashtags(item):
 tags=['#MotoGP' if 'motogp.com' in fold(item.get('url','')) else '#WorldSBK']
 for n in riders_in(item.get('title','')+' '+item.get('summary',''))[:2]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
 tags+=['#MotorradRacing','#RacingDeutschland','#BuelentsBikeLife'];return ' '.join(dict.fromkeys(tags))
def german_story(item):
 tl=fold(item.get('title',''));low=fold(item.get('title','')+' '+item.get('summary',''))
 # Offizielle Profile/Fallbacks: nur belegbare, zeitstabile Fakten verwenden.
 if 'toprak razgatlioglu' in low and ('rider profile' in tl or '/riders/' in item.get('url','')):return ('Toprak Razgatlıoğlu fährt 2026 seine erste MotoGP-Saison für Prima Pramac Yamaha. Nach seinen WorldSBK-Titeln beginnt für El Turco damit das nächste große Kapitel auf der Yamaha.','🇹🇷 El Turco ist jetzt MotoGP-Rookie – Toprak startet sein neues Kapitel mit Yamaha.','Wie bewertest du Topraks erste MotoGP-Saison bisher?')
 if 'can oncu' in low and ('official rider entry' in tl or '/riders/ssp' in item.get('url','')):return ('Can Öncü steht 2026 mit der #61 im permanenten WorldSSP-Feld und fährt für Pata Yamaha Ten Kate Racing auf der Yamaha R9.','🇹🇷 Can Öncü bleibt 2026 eine der türkischen Hoffnungen in der WorldSSP.','Was traust du Can mit der Yamaha R9 in dieser Saison noch zu?')
 if 'bahattin sofuoglu' in low and ('rider profile' in tl or '/riders/bahattin' in item.get('url','')):return ('Bahattin Sofuoğlu bestreitet 2026 seine zweite WorldSBK-Saison mit Motoxracing Yamaha. Nach seinem Rookie-Jahr geht es für die #54 darum, den nächsten Schritt Richtung Top Ten zu machen.','🇹🇷 Bahattin Sofuoğlu geht mit Yamaha in sein zweites WorldSBK-Jahr.','Wo siehst du Bahattin im starken WorldSBK-Feld?')
 if 'can oncu' in low and ('pole' in low or 'third pole' in low):return ('Can Öncü sichert sich in Misano seine dritte WorldSSP-Pole der Saison 2026. Damit startet die #61 aus der bestmöglichen Position in den Rennsamstag.','🇹🇷 Can Öncü auf Pole – die #61 setzt in Misano ein Ausrufezeichen.','Kann Can diese Pace auch im Rennen in einen Sieg umsetzen?')
 if 'martin soars to silverstone' in tl and 'sprint' in tl:return ('Jorge Martin gewinnt den Sprint in Silverstone vor Ai Ogura und Marco Bezzecchi. Für Aprilia wird der Samstag damit besonders stark.','🇬🇧 Aprilia räumt in Silverstone ab – Martin führt das Sprint-Podium an.','Ist Aprilia für dich inzwischen der stärkste Gegner im Titelkampf?')
 if 'fends off acosta and bezzecchi' in tl and 'aragon' in tl:return ('Marc Márquez setzt sich in Aragón gegen Pedro Acosta und Marco Bezzecchi durch.','🔥 Márquez behauptet sich in Aragón gegen Acosta und Bezzecchi.','Wer von den drei hat dich am meisten überzeugt?')
 if 'retaliates to hold off alex marquez' in tl and 'aragon' in tl:return ('Marc Márquez schlägt im Aragón-Sprint zurück und hält Alex Márquez hinter sich. Marco Bezzecchi komplettiert das Podium.','⚔️ Márquez gegen Márquez: Marc gewinnt das Aragón-Duell vor Alex.','War Marc an diesem Tag einfach zu stark?')
 if 'game on' in tl and 'largest points deficit' in tl:return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das schon eine seiner stärksten Aufholjagden?')
 if 'pol espargaro' in tl and 'replace' in tl:return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró.','Wie stark schätzt du Pol bei diesem Comeback ein?')
 if 'acosta' in tl and 'ducati' in tl:return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team und wird Teamkollege von Marc Márquez.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Wie schätzt du Acosta neben Márquez ein?')
 if 'bezzecchi' in tl and ('pole' in tl or 'lap record' in tl):return ('Marco Bezzecchi setzt im Qualifying ein starkes Zeichen und holt sich die Pole.','⏱️ Bezzecchi setzt ein richtig starkes Zeichen.','Wer ist für dich aktuell über eine schnelle Runde stärker?')
 return ('','','')
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
 item['story_key']=story_key(item['title'],item['url']);ok,errs=chief_review('Racing',item,item['caption'],item['instagram_media'],item['url'],racing_review);item['chief_errors']=errs;return ok
def write_session(items,now):
 lines=['# Racing Telegram Approval Session','Session-Version: 8','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1` bis `motogp 5`, Kombinationen oder `motogp alle`.','']
 for i,x in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Kategorie: {"Turkish Riders" if is_turkish_focus(x) else "MotoGP"}',f'Story-Key: {story_key(x["title"],x["url"])}',f'Titel: {x["title"]}',f'Quelle: {x["url"]}',f'Instagram-Bild: {x["instagram_media"]}',f'Quellen-Preview: {x.get("preview") or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{x["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt offizielle Quellen-Linkvorschau.','']
 SESSION.write_text('\n'.join(lines),encoding='utf-8')
def telegram_preview(items):
 msg=['🏁 Racing Content Agency – 5 QM-GEPRÜFTE Tagesvorschläge','🇹🇷 Turkish-Riders-Slot: PASS','✅ Domain-QM + Chief QM + Batch-QM: PASS','']
 for i,x in enumerate(items,1):msg += [f'{i}️⃣ {x["caption"]}','🖼️ Medium: vorbereitet',f'🔗 Quelle: {x["url"]}','']
 msg+=['Freigabe: motogp 1–5 / Kombination / motogp alle','Ablehnen: motogp nein'];send_message('\n'.join(msg)[:4000])
def run_v6():
 names=roster_names();known=known_story_keys();raw=[];seen=set();special=turkish_scout(30);base=extract(get(NEWS),60)+extract(get(MARKET),30)
 for title,url in special+base:
  u=canonical_url(url);key=story_key(title,u)
  if u in seen or key in known:continue
  seen.add(u);raw.append((title,u))
 details=[article_info(t,u) for t,u in raw[:60]];now=datetime.now(timezone.utc);candidates=[]
 # Pflichtslot zuerst; unbekannte Stories werden nicht erfunden.
 turkish=[x for x in details if is_turkish_focus(x) and qualify_copy(x)]
 if turkish:candidates.append(turkish[0])
 if candidates:
  for x in sorted(details,key=lambda z:score(z['title'],names),reverse=True):
   if len(candidates)>=5:break
   if x['url']==candidates[0]['url'] or not qualify_copy(x):continue
   candidates.append(x)
 # Batch-QM VOR teurer Medienerzeugung.
 if len(candidates)==5:
  batch=review_batch(candidates)
  candidates=[x for x,(ok,_) in zip(candidates,batch) if ok]
 picks=[]
 if len(candidates)==5:
  for i,x in enumerate(candidates,1):
   if finish_item(x,i):picks.append(x)
 turk=bool(picks and is_turkish_focus(picks[0]))
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(f'# Racing Daily Content Agency\n\nStand: {now:%Y-%m-%d %H:%M UTC}\nRohkandidaten: {len(details)}\nTurkish Copy-Kandidaten: {len(turkish)}\nBatch-QM Kandidaten: {len(candidates)}\nChief-QM PASS: {len(picks)}\nTurkish-Rider-Slot: {"PASS" if turk else "FAIL"}\n',encoding='utf-8')
 if len(picks)==5 and turk:
  write_session(picks,now);remember_offered(picks,now);telegram_preview(picks)
 else:send_message(f'🏁 Racing Agency: {len(picks)}/5 Chief-QM-Pakete, Turkish-Rider-Slot={"PASS" if turk else "FAIL"}. Keine unvollständige Auswahl gesendet.')
 print(f'Racing V6: raw={len(details)}, turkish_copy={len(turkish)}, batch={len(candidates)}, final={len(picks)}, Turkish={turk}')
if __name__=='__main__':run_v6()
