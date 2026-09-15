"""MotoGP Content Agency V3 – Voice Memory + Domain-QM + Chief-QM vor Telegram."""
from motogp_content_agency import *
from motogp_quality_manager import review as motogp_review
from chief_quality_manager import review as chief_review

RIDERS_V2=['Toprak Razgatlioglu','Marc Marquez','Alex Marquez','Marco Bezzecchi','Jorge Martin','Pedro Acosta','Francesco Bagnaia','Fabio Quartararo','Jack Miller','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado']

def riders_in(text):
    low=text.casefold(); found=[]
    for n in RIDERS_V2:
        if n.casefold() in low: found.append(n)
    surnames={}
    for n in RIDERS_V2:surnames.setdefault(n.split()[-1].casefold(),[]).append(n)
    for surname,names in surnames.items():
        if len(names)==1 and re.search(rf'\b{re.escape(surname)}\b',low) and names[0] not in found:found.append(names[0])
    return found

def hashtags(item):
    tags=['#MotoGP']; people=riders_in(item['title']+' '+item['summary'])
    for n in people[:3]:tags.append('#'+re.sub(r'[^A-Za-z0-9]','',n))
    low=(item['title']+' '+item['summary']).casefold()
    for k,v in [('ducati','#Ducati'),('aprilia','#ApriliaRacing'),('yamaha','#YamahaRacing'),('ktm','#KTM'),('honda','#HondaRacing'),('misano','#SanMarinoGP'),('aragon','#AragonGP'),('silverstone','#BritishGP')]:
        if k in low and v not in tags:tags.append(v)
    tags += ['#MotorradRacing','#MotoGPDeutschland']; return ' '.join(tags[:7])

def german_story(item):
    t=item['title']; tl=t.casefold(); people=riders_in(t); p=people[0] if people else 'MotoGP'
    if 'martin soars to silverstone' in tl and 'sprint' in tl:return ('Jorge Martin gewinnt den Sprint in Silverstone vor Ai Ogura und Marco Bezzecchi. Für Aprilia wird der Samstag besonders stark: drei Aprilia-Fahrer belegen die ersten drei Plätze, während Marc Márquez einen schwierigen Sprint erlebt.','🇬🇧 Aprilia räumt in Silverstone ab – Martin führt ein Sprint-Podium komplett in Aprilia-Hand an.','Ist Aprilia für dich inzwischen der stärkste Gegner im Titelkampf?')
    if 'fends off acosta and bezzecchi' in tl and 'aragon' in tl:return ('Marc Márquez setzt sich in Aragón gegen Pedro Acosta und Marco Bezzecchi durch. An der Spitze wird hart gekämpft, und mit diesem Ergebnis verschiebt sich der Titelkampf erneut.','🔥 Márquez behauptet sich in Aragón gegen Acosta und Bezzecchi.','Wer von den drei hat dich in diesem Rennen am meisten überzeugt?')
    if 'retaliates to hold off alex marquez' in tl and 'aragon' in tl:return ('Marc Márquez schlägt im Aragón-Sprint zurück und hält Alex Márquez hinter sich. Marco Bezzecchi komplettiert als Dritter das Podium.','⚔️ Márquez gegen Márquez: Marc gewinnt das Aragón-Duell vor Alex.','Hättest du Alex Márquez den Sieg zugetraut oder war Marc an diesem Tag zu stark?')
    if 'game on' in tl and 'largest points deficit' in tl:return ('Marc Márquez hat einen Rückstand von 102 Punkten aufgeholt und daraus die Führung in der Weltmeisterschaft gemacht. Sieben Rennwochenenden zuvor sah die Ausgangslage noch völlig anders aus.','📈 102 Punkte aufgeholt: Márquez dreht den WM-Kampf komplett.','Ist das für dich schon eine seiner stärksten MotoGP-Aufholjagden?')
    if 'pol espargaro' in tl and 'replace' in tl and 'viñales' in tl:return ('Pol Espargaró springt erneut für den verletzten Maverick Viñales ein und kehrt beim Österreich-GP für KTM ins Renngeschehen zurück.','🔄 KTM setzt erneut auf Pol Espargaró als Ersatz für Viñales.','Wie stark schätzt du Pol bei diesem Comeback ein?')
    if 'acosta' in tl and 'ducati' in tl and ('2027' in tl or 'join' in tl):return ('Pedro Acosta fährt ab 2027 für das Ducati Lenovo Team. Damit bekommt Marc Márquez einen der stärksten jungen Fahrer im Feld als Teamkollegen.','🔥 Ducati setzt für 2027 ein echtes Ausrufezeichen!','Acosta neben Márquez – wie schätzt du diese Kombination sportlich ein?')
    if 'bezzecchi' in tl and ('pole' in tl or 'lap record' in tl):return ('Marco Bezzecchi setzt im Qualifying ein starkes Zeichen und holt sich die Pole vor Marc Márquez.','⏱️ Bezzecchi schlägt Márquez im Kampf um die Pole.','Wer ist für dich aktuell über eine schnelle Runde stärker?')
    return ('','','')

def own_caption(item):
    fact,hook,question=german_story(item)
    return f'{hook}\n\n{fact}\n\n{question}\n\n{hashtags(item)}' if fact else ''

def prepare_media(item,index):
    caption=item['caption']; filename=get_image_path(slugify(f'motogp-editorial-{datetime.now(timezone.utc):%Y-%m-%d}-{index}-{item["title"]}'),1)
    prompt=('Vertical 4:5 premium motorsport editorial social-media background. Empty modern European motorcycle racing circuit at dramatic golden hour. NO people, NO riders, NO motorcycles, NO helmets, NO team colors, NO manufacturer branding, NO sponsor logos, NO trademarks, NO readable text, NO watermark. Original generic racing visual, photorealistic. Editorial mood only: '+caption[:220])
    data=agnes_generate_image(prompt)
    if not data:return ''
    save_bytes(data,filename); return filename.as_posix()

def write_session(items,now):
    lines=['# MotoGP Telegram Approval Session','Session-Version: 5','QM: PASS',f'Session-Timestamp: {int(now.timestamp())}','','Antwort: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle` oder `motogp nein`.','']
    for i,item in enumerate(items,1):lines += [f'## Beitrag {i}','QM: PASS',f'Story-Key: {story_key(item["title"],item["url"])}',f'Titel: {item["title"]}',f'Quelle: {item["url"]}',f'Instagram-Bild: {item["instagram_media"]}',f'Quellen-Preview: {item["preview"] or "Zielseite/Plattform"}','Plattformen: Instagram + Facebook',f'Text:\n{item["caption"]}','','Rechte-Gate: eigene generische Instagram-Editorial-Grafik; Facebook nutzt die offizielle Quellen-Linkvorschau.','']
    SESSION.write_text('\n'.join(lines),encoding='utf-8')

def telegram_preview(items):
    msg=['🏁 MotoGP Content Agency – QM-GEPRÜFTE Tagesauswahl','','✅ Domain-QM + Chief Quality Manager: PASS','']
    for i,item in enumerate(items,1):msg += [f'{i}️⃣ {item["caption"]}','🖼️ Instagram-Medium: vorbereitet',f'🔗 Quelle: {item["url"]}','']
    msg += ['Freigabe: motogp 1 / motogp 2 / motogp 3 / motogp alle','Ablehnen: motogp nein']; send_message('\n'.join(msg)[:4000])

def run_v3():
    learned=get_context(9000); names=roster_names(); news=extract(get(NEWS),60); market=extract(get(MARKET),30); merged=[]; seen=set(); known=known_story_keys(); skipped=[]
    for raw in news+market:
        key=story_key(raw[0],raw[1])
        if raw[1] in seen:continue
        seen.add(raw[1])
        if key in known:skipped.append(raw);continue
        merged.append(raw)
    merged.sort(key=lambda x:score(x[0],names),reverse=True); details=[article_info(t,u) for t,u in merged[:30]]; now=datetime.now(timezone.utc)
    lines=['# MotoGP Daily Content Agency','',f'**Recherche:** {now:%Y-%m-%d %H:%M UTC}','**Closed-Loop Memory:** aktiv','**Story-Dedupe:** aktiv','**Bülents Bike Life Voice:** verbindlich','**Domain-QM:** Pflicht','**Chief Quality Manager:** Pflicht / fail-closed',f'**Memory-Treffer übersprungen:** {len(skipped)}','','## Analysierte neue Themen','']
    for i,item in enumerate(details,1):lines += [f'### {i}. {item["title"]}',f'- Story-Key: {story_key(item["title"],item["url"])}',f'- Quelle: {item["url"]}',f'- Quellen-Metadaten: {item["summary"] or "keine belastbare Meta-Zusammenfassung"}','']
    content='\n'.join(lines);OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(content,encoding='utf-8');ARCH.mkdir(parents=True,exist_ok=True);(ARCH/f'{now:%Y-%m-%d}.md').write_text(content,encoding='utf-8');next_roster(market)
    picks=[]
    for item in details:
        if story_key(item['title'],item['url']) in known:continue
        item['caption']=own_caption(item)
        if not item['caption']:continue
        # Domain-QM zuerst – bevor teure Medien erzeugt werden.
        domain_ok,domain_errors=motogp_review(item,item['caption'])
        if not domain_ok:
            print('DOMAIN-QM FAIL:',item['title'],domain_errors);continue
        media=prepare_media(item,len(picks)+1)
        if not media:continue
        item['instagram_media']=media;item['story_key']=story_key(item['title'],item['url'])
        # Chief-QM ist die letzte technische Instanz vor Telegram.
        chief_ok,chief_errors=chief_review('MotoGP',item,item['caption'],media,item['url'],motogp_review)
        if not chief_ok:
            print('CHIEF-QM FAIL:',item['title'],chief_errors);continue
        picks.append(item)
        if len(picks)==3:break
    if len(picks)==3:
        write_session(picks,now);remember_offered(picks,now);telegram_preview(picks)
    else:
        send_message(f'🏁 MotoGP Content Agency: Chief QM hat nur {len(picks)} von 3 Paketen freigegeben. Es werden keine ungeprüften Ersatz-/Fülltexte an dich geschickt.')
    print(f'MotoGP V3/QM: {len(details)} analysiert, {len(skipped)} bekannte gesperrt, {len(picks)} Chief-QM PASS.')

if __name__=='__main__':run_v3()
