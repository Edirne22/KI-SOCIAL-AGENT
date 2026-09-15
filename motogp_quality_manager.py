"""Finales Quality Management für MotoGP-Pakete vor Telegram/Freigabe."""
from pathlib import Path
import re

VOICE = Path('memory/MOTOGP_VOICE_RULES.md')
BANNED = (
    'motogp im fokus',
    'eines der relevanten motogp-themen',
    'die fakten stammen aus der offiziellen meldung',
    'der social-text wird bewusst eigenständig formuliert',
    'für die einordnung verwenden wir ausschließlich',
    'rund um ',
    'was ist für dich der spannendste punkt an dieser story',
)


def _surname(name):
    return name.strip().split()[-1].casefold()


def review(item, caption):
    """Fail-closed Endkontrolle. Liefert (ok, fehlerliste)."""
    errors=[]
    low=caption.casefold()
    title=(item.get('title') or '').casefold()
    summary=(item.get('summary') or '').casefold()
    source=title+' '+summary

    for phrase in BANNED:
        if phrase in low:
            errors.append('verbotener/generischer Stil: '+phrase)

    # Struktur: konkrete Hook, Faktenkörper, Frage, Hashtags.
    parts=[p.strip() for p in caption.split('\n\n') if p.strip()]
    if len(parts) < 4: errors.append('Poststruktur unvollständig')
    if '?' not in caption: errors.append('keine Community-Frage')
    tags=re.findall(r'#[A-Za-z0-9ÄÖÜäöüß]+',caption)
    if not (4 <= len(tags) <= 7): errors.append('Hashtag-Anzahl nicht 4–7')

    # Mindestens ein tragender Begriff aus dem Titel muss im Text vorkommen.
    title_words=[w for w in re.findall(r'[a-z0-9]+',title) if len(w)>=5 and w not in {'motogp','confirmed','title','sprint'}]
    if title_words and not any(w in low for w in title_words[:8]):
        errors.append('Text nicht konkret genug an Artikel gebunden')

    # Fahrer-Hashtags dürfen nur vorkommen, wenn der Name in Titel/Metadaten vorkommt.
    rider_tags={
      'marcmarquez':'marc marquez','alexmarquez':'alex marquez','pedroacosta':'pedro acosta',
      'jorgemartin':'jorge martin','marcobezzecchi':'marco bezzecchi','fabioquartararo':'fabio quartararo',
      'francescobagnaia':'francesco bagnaia','toprakrazgatlioglu':'toprak razgatlioglu'
    }
    compact_tags={t[1:].casefold() for t in tags}
    for tag,name in rider_tags.items():
        if tag in compact_tags and name not in source:
            errors.append('unpassender Fahrer-Hashtag: #'+tag)

    # Keine sichtbare Redaktions-/Quellen-Metasprache im Captiontext.
    if re.search(r'\b(quelle|redaktion|social-text|offizielle meldung)\b',low):
        errors.append('interne Quellen-/Redaktionssprache im Post')

    return not errors, errors


def review_batch(items):
    """Zusätzlich prüfen, dass unterschiedliche Stories nicht denselben Copy-Block bekommen."""
    seen=set(); result=[]
    for item in items:
        caption=item.get('caption','').strip()
        fingerprint=re.sub(r'#[^\s]+','',caption.casefold())
        fingerprint=re.sub(r'\s+',' ',fingerprint).strip()
        ok,errors=review(item,caption)
        if fingerprint in seen:
            ok=False; errors.append('Copy-Duplikat innerhalb derselben Auswahl')
        seen.add(fingerprint)
        result.append((ok,errors))
    return result
