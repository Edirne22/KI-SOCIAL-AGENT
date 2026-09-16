"""V8.6 source-only facts, deterministic guards and atomic exact-span repairs.

Catalogs identify forbidden additions; they never supply facts or aliases to the CFO.
Unrecognized semantics remain the responsibility of the independent Semantic-QM.
"""
import hashlib
import json
import re
import unicodedata
from difflib import SequenceMatcher

SERIES = {
    'MotoGP': ('MotoGP',), 'Moto2': ('Moto2',), 'Moto3': ('Moto3',),
    'WorldSBK': ('WorldSBK', 'World Superbike', 'Superbike'),
    'WorldSSP': ('WorldSSP', 'World Supersport', 'Supersport'),
    'WorldSSP300': ('WorldSSP300', 'WorldSSP 300', 'Supersport 300'),
    'WorldWCR': ('WorldWCR',),
}
LOCATIONS = ('San Marino', 'Mugello', 'Misano', 'Austria', 'Spielberg', 'Assen',
             'Jerez', 'Silverstone', 'Barcelona', 'Aragon', 'Sepang', 'Phillip Island',
             'Red Bull Ring', 'Portimao', 'Valencia', 'Sachsenring', 'Lusail')
TEAMS = ('Tech3', 'Pramac', 'Gresini', 'VR46', 'Trackhouse', 'Intact GP', 'Ajo')
MANUFACTURERS = ('Ducati', 'Yamaha', 'Honda', 'KTM', 'Aprilia', 'BMW', 'Kawasaki', 'Triumph')
GENERIC_TAGS = ('#MotorradRacing', '#RacingDeutschland', '#BuelentsBikeLife')
NUMBER = re.compile(r'(?<![\w])(?:P|Q|FP)?\d+(?:[.,:]\d+)*(?:%|s|km|mph|kph)?(?![\w])', re.I)
WORD = re.compile(r"[^\W\d_]+(?:[-'][^\W\d_]+)*", re.UNICODE)
LEADER = re.compile(r'championship leader|championship lead|WM[- ]?F.hr|Weltmeisterschaftsf.hr|Meisterschaftsf.hr|Tabellenf.hr|f.hrt.{0,20}(?:WM|Meisterschaft)|Spitze.{0,20}(?:WM|Meisterschaft)', re.I)
WEAK = re.compile(r'\b(targets?|aims?|expected|set to|could|may|might|hopes?|plans?)\b', re.I)
STRONG = re.compile(r'\b(wird|garantiert|sicher|definitiv|best.tigt|steht fest)\b', re.I)
STOP_ENTITIES = set('The A An And Of In On For To From With At As After Before Who Meet New Best How What This That He His Her It News Official Home Practice Qualifying Friday Saturday Sunday Monday Tuesday Wednesday Thursday GP P Q FP'.split())

def fold(text):
    return ''.join(c for c in unicodedata.normalize('NFKD', str(text)).casefold().replace('ı', 'i') if not unicodedata.combining(c))

def contains(text, value):
    return bool(re.search(r'(?<!\w)' + re.escape(fold(value)) + r'(?!\w)', fold(text)))

def source_text(item):
    return str(item.get('title', '')) + '\n' + str(item.get('summary', ''))

def series_mentions(text):
    # Longest aliases consume their span, preventing WorldSSP300 -> WorldSSP.
    hits = []
    aliases = sorted(((alias, key) for key, vals in SERIES.items() for alias in vals), key=lambda x: -len(x[0]))
    remaining = text
    for alias, key in aliases:
        pattern = re.compile(r'(?<!\w)' + re.escape(alias) + r'(?!\w)', re.I)
        if pattern.search(remaining):
            hits.append(key)
            remaining = pattern.sub(' ', remaining)
    return sorted(set(hits))

def select_series(item):
    title = str(item.get('title', ''))
    source = re.sub(r'The Official Home of MotoGP', '', source_text(item), flags=re.I)
    for series in SERIES:
        if re.search(r'(?:joins?|to|switch to|debut (?:in|from))\s+' + re.escape(series) + r'\b', source, re.I):
            return series, 'explicit-source-destination'
        if re.search(r'\b' + re.escape(series) + r'\s+(?:debut|switch)\b', title, re.I):
            return series, 'explicit-source-destination'
    title_hits = series_mentions(title)
    if len(title_hits) == 1:
        return title_hits[0], 'source-title'
    hits = series_mentions(source)
    if len(hits) == 1:
        return hits[0], 'source-text'
    # Original feed metadata, never roster-based inference or trusted_series cache.
    supplied = str(item.get('source_series') or item.get('series') or '')
    if supplied in SERIES:
        return supplied, 'source-metadata'
    return '', 'unknown'

def evidence(source, value, **extra):
    start = source.find(value)
    return dict(value=value, evidence={'start': start, 'end': start + len(value), 'text': value}, **extra)

def literals(source, catalog):
    result = []
    for term in catalog:
        for match in re.finditer(r'(?<!\w)' + re.escape(term) + r'(?!\w)', source, re.I):
            if match.group() not in [x['value'] for x in result]:
                result.append(evidence(source, match.group()))
    return result

def build_cfo(item, rider_catalog=()):
    source = source_text(item)
    series, origin = select_series(item)
    entities = []
    for m in WORD.finditer(source):
        token = m.group()
        if token[0].isupper() and token not in STOP_ENTITIES and not series_mentions(token):
            if token not in [e['value'] for e in entities]:
                entities.append(evidence(source, token, kind='unclassified_source_token'))
    riders = []
    # Recognition may use a catalog, but output is only an exact source substring.
    for name in rider_catalog:
        parts = name.split()
        if parts:
            riders.extend(literals(source, (name if contains(source, name) else parts[-1],)))
    for m in re.finditer(r'\b([A-Z][a-zÀ-ž]+(?: [A-Z][a-zÀ-ž]+)?)\s+(?:claims|grabs|storms|takes|wins|targets|denies|fastest|signs|returns|leads)\b', source):
        riders.append(evidence(source, m.group(1)))
    riders = list({r['value']: r for r in riders}.values())
    numbers = [evidence(source, m.group()) for m in NUMBER.finditer(source)]
    positions = [dict(n, scope='source-context-only') for n in numbers if re.fullmatch(r'(?:P|Q|FP)\d+', n['value'], re.I)]
    claims = []
    relationships = []
    for m in re.finditer(r'[^\n.!?]+(?:[.!?]|$)', source):
        value = m.group().strip()
        if not value:
            continue
        modes = [w.group() for w in WEAK.finditer(value)]
        claim = evidence(source, value, id='claim-' + str(len(claims) + 1), modality=modes or ['as-stated'])
        claims.append(claim)
        for rel in re.finditer(r'\b(joins?|signs?|teammates?|grandsons?|sons?|brothers?|moves? from)\b', value, re.I):
            relationships.append(dict(claim_id=claim['id'], relation_marker=rel.group(), evidence=claim['evidence']))
    return {
        'schema_version': '8.6', 'source': {'title': str(item.get('title', '')), 'summary': str(item.get('summary', ''))},
        'source_sha256': hashlib.sha256(source.encode()).hexdigest(),
        'series': series, 'series_origin': origin, 'source_series_mentions': series_mentions(source),
        'event': [evidence(source, m.group()) for m in re.finditer(r'\b(?:[A-Z][a-z]+\s+){1,3}(?:GP|Grand Prix)\b', source)],
        'session': literals(source, ('Practice', 'Qualifying', 'Sprint', 'Race', 'FP1', 'FP2', 'Q1', 'Q2')),
        'riders': riders, 'entities': entities, 'teams': literals(source, TEAMS),
        'manufacturers': literals(source, MANUFACTURERS), 'locations': literals(source, LOCATIONS),
        'dates': [evidence(source, m.group()) for m in re.finditer(r'\b\d{4}(?:-\d{2}-\d{2})?\b', source)],
        'positions': positions, 'numbers': numbers, 'relationships': relationships, 'claims': claims,
        'modality': [{'claim_id': c['id'], 'markers': c['modality']} for c in claims],
        'forbidden_inferences': ['no_prior_knowledge', 'no_name_expansion', 'no_new_entities_or_numbers',
            'no_series_substitution', 'session_position_is_not_championship_lead',
            'no_class_assignment_to_unqualified_championship_leader', 'no_modality_strengthening',
            'no_inferred_team_location_nationality_or_relationship'],
    }

def validate_cfo(cfo, item, rider_catalog=()):
    # Recompute all fields: even an evidence-bearing but modified CFO is rejected.
    return [] if cfo == build_cfo(item, rider_catalog) else ['CFO: source or canonical facts changed']

def tags(cfo):
    rider_tags = ['#' + re.sub(r'[^A-Za-z0-9]', '', fold(r['value']).title()) for r in cfo['riders'][:2]]
    return ' '.join(dict.fromkeys((['#' + cfo['series']] if cfo['series'] else []) + rider_tags + list(GENERIC_TAGS)))

def guard_errors(cfo, caption, rider_catalog=()):
    source = source_text(cfo['source'])
    errors = []
    text = re.sub(r'#[\w]+', '', str(caption))
    for series in series_mentions(caption):
        if series != cfo['series'] and series not in cfo['source_series_mentions']:
            errors.append('CFO-Series: unsupported series ' + series)
    allowed_tags = {fold(t) for t in tags(cfo).split()}
    for tag in re.findall(r'#[\w]+', str(caption)):
        if fold(tag) not in allowed_tags:
            errors.append('CFO-Entity: unsupported hashtag ' + tag)
    source_numbers = {fold(n['value']).replace(',', '.') for n in cfo['numbers']}
    source_numbers.update(n[1:] for n in list(source_numbers) if re.fullmatch(r'p\d+', n))
    for m in NUMBER.finditer(text):
        if fold(m.group()).replace(',', '.') not in source_numbers:
            errors.append('CFO-Number: unsupported number/position ' + m.group())
    # Catalog is deny-only. First names and surnames are checked separately.
    terms = set(LOCATIONS + TEAMS + MANUFACTURERS)
    for name in rider_catalog:
        terms.update(p for p in name.split() if len(p) > 2)
    # Proper-name tokens near a source name catch inserted first names (Aras Agius).
    source_names = {r['value'].split()[-1] for r in cfo['riders']}
    location_words = {part for loc in LOCATIONS for part in loc.split()}
    source_names.update(e['value'] for e in cfo['entities'] if e['value'] not in location_words)
    for term in terms:
        if contains(text, term) and not contains(source, term):
            errors.append('CFO-Entity: unsupported entity ' + term)
    if cfo['riders'] and not any(contains(text, r['value']) for r in cfo['riders']):
        errors.append('CFO-Entity: source rider missing or substituted')
    for m in re.finditer(r'\b([A-Z][a-zÀ-ž]+)\s+(?:holt|gewinnt|fährt|sichert|wechselt|führt|kehrt|startet)\b', text):
        if not contains(source, m.group(1)) and m.group(1) not in {'Er', 'Sie', 'Wer'}:
            errors.append('CFO-Entity: unsupported subject ' + m.group(1))
    words = list(WORD.finditer(text))
    for i, m in enumerate(words):
        word = m.group()
        if contains(source, word):
            continue
        # Small spelling mutations of source tokens must not pass as a new identity.
        for name in source_names:
            if len(name) >= 5 and len(word) >= 5 and fold(word) != fold(name) and SequenceMatcher(None, fold(name), fold(word)).ratio() >= .84:
                errors.append('CFO-Entity: changed source spelling ' + word)
                break
        if word[0].isupper() and i + 1 < len(words) and words[i + 1].group() in source_names:
            gap = text[m.end():words[i + 1].start()]
            if gap == ' ' and word not in {'Der', 'Die', 'Das', 'Auch', 'Für', 'Bei', 'Mit', 'Ohne', 'Und', 'Doch', 'In', 'Nach', 'Vor', 'Während', 'Jetzt', 'Heute', 'Wieder', 'Nun', 'Kann', 'Wird'}:
                errors.append('CFO-Entity: unsupported name prefix ' + word)
    if LEADER.search(text) and not LEADER.search(source):
        errors.append('CFO-Claim: session position is not championship leadership')
    if WEAK.search(source) and STRONG.search(text):
        errors.append('CFO-Modality: possible strengthening of a qualified source claim')
    return sorted(set(errors))

def apply_patch(caption, raw):
    """All edits address the original text; no cascading or partial application."""
    if not isinstance(raw, str) or len(raw) > 20000:
        raise ValueError('invalid patch payload')
    obj = json.loads(raw)
    if not isinstance(obj, dict) or set(obj) != {'patches'}:
        raise ValueError('expected patches object only')
    patches = obj['patches']
    if not isinstance(patches, list) or not 1 <= len(patches) <= 8:
        raise ValueError('expected 1..8 patches')
    spans = []
    for patch in patches:
        if not isinstance(patch, dict) or set(patch) != {'old', 'new'}:
            raise ValueError('expected exact old/new strings')
        old, new = patch['old'], patch['new']
        if not isinstance(old, str) or not old or not isinstance(new, str) or old == new:
            raise ValueError('invalid or no-op replacement')
        if caption.count(old) != 1:
            raise ValueError('old span must occur exactly once')
        if old == caption or len(old) > max(160, len(caption) // 2) or len(new) > max(240, len(caption) // 2):
            raise ValueError('patch too broad')
        start = caption.index(old)
        spans.append((start, start + len(old), new))
    spans.sort()
    if any(a[1] > b[0] for a, b in zip(spans, spans[1:])):
        raise ValueError('overlapping patches')
    if sum(end - start for start, end, _ in spans) > len(caption) * .6:
        raise ValueError('total patch scope too broad')
    result = caption
    for start, end, new in reversed(spans):
        result = result[:start] + new + result[end:]
    if not result.strip():
        raise ValueError('empty repaired caption')
    return result
