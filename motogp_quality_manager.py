"""Finales Domain-QM für Racing-Pakete vor Chief-QM und Telegram – V8.4.4."""
import re
BANNED=('motogp im fokus','eines der relevanten motogp-themen','die fakten stammen aus der offiziellen meldung','der social-text wird bewusst eigenständig formuliert','für die einordnung verwenden wir ausschließlich','was ist für dich der spannendste punkt an dieser story','größte understatement-leistung','groesste understatement-leistung','motogp-gran premio','einen duell','im letzten runde','im letzten runde','eine duell')
ENGLISH_MARKERS=(' out the ',' quickest ',' reigning ',' leads ',' opening stint ',' beats ',' pole in ',' qualifying ',' line-up ',' revealed ',' denies ',' points cover ',' world champion ',' sprint stand-off ',' from 2027 ',' alongside ',' weekend at ',' does the business ')
TURKISH=('toprak razgatlioglu','can oncu','deniz oncu','bahattin sofuoglu','zayn sofuoglu')
RIDER_NAMES=('Marc Marquez','Alex Marquez','Pedro Acosta','Jorge Martin','Marco Bezzecchi','Fabio Quartararo','Francesco Bagnaia','Toprak Razgatlioglu','Can Oncu','Deniz Oncu','Bahattin Sofuoglu','Zayn Sofuoglu','Brad Binder','Maverick Viñales','Enea Bastianini','Joan Mir','Luca Marini','Alex Rins','Franco Morbidelli','Fabio Di Giannantonio','Fermin Aldeguer','Ai Ogura','Raul Fernandez','Johann Zarco','Diogo Moreira','Pol Espargaro','Nicolo Bulega','Daniel Holgado','Iker Lecuona','Alvaro Bautista','Andrea Iannone','Sam Lowes','Alex Lowes','Jonathan Rea','Stefano Manzi','Jeremy Alcoba','Marcos Ramirez','Sergio Garcia')
RIDERS={re.sub(r'[^a-z0-9]','',n.casefold()):n for n in RIDER_NAMES}
def fold(s):return (s or '').casefold().replace('ı','i').replace('ğ','g').replace('ü','u').replace('ö','o').replace('ş','s').replace('ç','c')
def rider_matches(text):
 low=fold(text);out=[]
 for n in RIDER_NAMES:
  f=fold(n);last=f.split()[-1]
  if f in low or (len(last)>=5 and re.search(r'(?<![a-z])'+re.escape(last)+r'(?![a-z])',low)):out.append(n)
 return list(dict.fromkeys(out))
def review(item,caption):
 errors=[];low=fold(caption);source=fold((item.get('title') or '')+' '+(item.get('summary') or ''))
 for p in BANNED:
  if fold(p) in low:errors.append('verbotener/unnatürlicher Stil: '+p)
 padded=' '+low+' ';hits=[m for m in ENGLISH_MARKERS if m in padded]
 if len(hits)>=2:errors.append('Deutsch-Gate FAIL: englischer Nachrichtenblock erkannt')
 if '🇹🇷' in caption and not any(fold(n) in low for n in TURKISH):errors.append('Turkish-Flag ohne Turkish Rider')
 parts=[p.strip() for p in caption.split('\n\n') if p.strip()]
 if len(parts)<4:errors.append('Poststruktur unvollständig')
 if '?' not in caption:errors.append('keine Community-Frage')
 tags=re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption)
 if not (4<=len(tags)<=7):errors.append('Hashtag-Anzahl nicht 4–7')
 source_riders=rider_matches(source);caption_riders=rider_matches(low)
 if source_riders and not set(source_riders)&set(caption_riders):errors.append('Text nicht an den Fahrer der Quelle gebunden')
 compact={fold(t[1:]) for t in tags}
 for rider in source_riders[:2]:
  expected=fold(re.sub(r'[^A-Za-z0-9]','',rider))
  if expected not in compact:errors.append('Fahrer-Hashtag fehlt: #'+re.sub(r'[^A-Za-z0-9]','',rider))
 for tag,name in RIDERS.items():
  if tag in compact and name not in source_riders:errors.append('unpassender Fahrer-Hashtag: #'+tag)
 nums=set(re.findall(r'\b\d{1,4}\b',source)) & set(re.findall(r'\b\d{1,4}\b',low))
 if not source_riders and not nums:
  title_words=[w for w in re.findall(r'[a-z0-9]+',fold(item.get('title',''))) if len(w)>=5 and w not in {'motogp','worldsbk','worldssp','confirmed','title','sprint'}]
  if title_words and not any(w in low for w in title_words[:8]):errors.append('Text nicht konkret genug an Artikel gebunden')
 if re.search(r'\b(quelle|redaktion|social-text|offizielle meldung)\b',low):errors.append('interne Quellen-/Redaktionssprache im Post')
 # Quote-Sicherheit: keine direkten Anführungszeichen im Social-Text. Quellenzitate werden paraphrasiert.
 body='\n'.join(p for p in parts if not p.startswith('#'))
 if any(q in body for q in ('"','“','”','„','«','»')):errors.append('direktes/übersetztes Zitat im Post – paraphrasieren')
 return not errors,errors
def review_batch(items):
 seen=set();result=[]
 for item in items:
  caption=item.get('caption','').strip();fp=re.sub(r'#[^\s]+','',fold(caption));fp=re.sub(r'\s+',' ',fp).strip();ok,errors=review(item,caption)
  if fp in seen:ok=False;errors.append('Copy-Duplikat innerhalb derselben Auswahl')
  seen.add(fp);result.append((ok,errors))
 return result
