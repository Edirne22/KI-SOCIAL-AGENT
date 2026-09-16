"""Independent semantic source-to-caption QM for Motorcycle Racing.

V8.6 minimal hardening: tolerant extraction of one complete JSON object,
strict schema/boolean validation, and a per-run caption-result cache.
"""
import hashlib
import json
import re

from llm_client import generate

BRAND_HASHTAGS = {'#buelentsbikelife'}


def _clean_json(raw):
    """Extract one complete JSON object without inventing missing content."""
    if not isinstance(raw, str):
        raise ValueError('semantic QM response must be a string')
    text = raw.strip()
    if not text:
        raise ValueError('semantic QM response is empty')
    # Fences are presentation only; surrounding prose is tolerated because the
    # decoded object is schema-validated below. Truncated JSON still fails.
    text = re.sub(r'```(?:json)?', '', text, flags=re.I).replace('```', '').strip()
    decoder = json.JSONDecoder()
    for start, char in enumerate(text):
        if char != '{':
            continue
        try:
            value, _ = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise json.JSONDecodeError('no complete JSON object found', text, 0)


def _fold(s):
    return (s or '').casefold().replace('ı', 'i').replace('ğ', 'g').replace('ü', 'u').replace('ö', 'o').replace('ş', 's').replace('ç', 'c')


def _system_hashtags(caption):
    blocks = [b.strip() for b in str(caption or '').split('\n\n') if b.strip()]
    if not blocks:
        return []
    tokens = blocks[-1].split()
    return tokens if tokens and all(t.startswith('#') for t in tokens) else []


def _caption_for_fact_review(caption, trusted_system_hashtags=None):
    trusted = {str(x).casefold() for x in (trusted_system_hashtags or [])}
    return ' '.join(token for token in str(caption or '').split()
                    if token.casefold() not in BRAND_HASHTAGS
                    and token.casefold() not in trusted)


def _caption_fingerprint(caption):
    normalized = re.sub(r'#[^\s]+', '', str(caption or ''))
    normalized = re.sub(r'\s+', ' ', normalized).strip().casefold()
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def reset_caption_cache():
    review_detailed._caption_cache = {}


def infer_story_series(item):
    cfo = item.get('canonical_fact_object')
    if cfo is not None:
        return cfo.get('series', 'nicht eindeutig')
    text = _fold(' '.join((item.get('title', ''), item.get('summary', ''), item.get('url', ''))))
    if 'worldssp300' in text or 'worldssp 300' in text:
        return 'WorldSSP300'
    if 'worldssp' in text or 'world supersport' in text:
        return 'WorldSSP'
    if 'worldsbk' in text or 'world superbike' in text:
        return 'WorldSBK'
    for series in ('Moto3', 'Moto2', 'MotoGP'):
        if re.search(r'(?<![a-z0-9])' + series.casefold() + r'(?![a-z0-9])', text):
            return series
    return str(item.get('series', '')).strip() or 'nicht eindeutig'


def _prompt(item, caption):
    title = str(item.get('title', '')).strip()
    summary = str(item.get('summary', '')).strip()
    cfo = item.get('canonical_fact_object')
    facts = json.dumps(cfo, ensure_ascii=False) if cfo is not None else 'Keine CFO vorhanden.'
    return f'''Du bist unabhaengiger Senior-Faktenpruefer fuer Motorrad-Racing.
Trenne HARTE FAKTENFEHLER strikt von REPARIERBARER SPRACHE.
QUELLFAKTEN:
SERIE: {infer_story_series(item)}
TITEL: {title}
ZUSAMMENFASSUNG: {summary}
URL: {str(item.get('url', '')).strip()}
CANONICAL FACT OBJECT: {facts}
POST OHNE SYSTEM-HASHTAGS:
{_caption_for_fact_review(caption, _system_hashtags(caption))}
Jede Tatsachenbehauptung muss durch die Quelle oder das CFO gedeckt sein.
Keine Ergaenzungen aus Vorwissen. P1 ist nicht Q1. Modalitaet erhalten.
Antworte nur als JSON mit echten Boolean-Werten, ohne Markdown:
{{"hard_fact_ok":true,"series_ok":true,"rider_team_ok":true,"quote_ok":true,"german_ok":true,"style_ok":true,"hard_reasons":[],"repair_reasons":[]}}'''


def _validate_result(value):
    if not isinstance(value, dict):
        raise ValueError('semantic QM result must be an object')
    required = ('hard_fact_ok', 'series_ok', 'rider_team_ok', 'quote_ok', 'german_ok', 'style_ok')
    if any(type(value.get(key)) is not bool for key in required):
        raise ValueError('semantic QM fields must contain real JSON booleans')
    for key in ('hard_reasons', 'repair_reasons'):
        reasons = value.get(key, [])
        if not isinstance(reasons, list) or any(not isinstance(x, str) for x in reasons):
            raise ValueError(f'{key} must be a list of strings')
    return value


def review_detailed(item, caption):
    fp = _caption_fingerprint(caption)
    cache = getattr(review_detailed, '_caption_cache', None)
    if cache is None:
        reset_caption_cache()
        cache = review_detailed._caption_cache
    if fp in cache:
        cached = dict(cache[fp])
        cached['caption_cache_hit'] = True
        print('SEMANTIC-QM CAPTION-CACHE HIT:', item.get('title', '')[:90])
        return cached

    prompt = _prompt(item, caption)
    last = None
    for attempt in range(3):
        try:
            value = _validate_result(_clean_json(generate('racing_semantic_qm', prompt)))
            hard = all(value[key] is True for key in ('hard_fact_ok', 'series_ok', 'rider_team_ok', 'quote_ok'))
            language = value['german_ok'] is True and value['style_ok'] is True
            hard_reasons = [x for x in value.get('hard_reasons', []) if x.strip()]
            repair_reasons = [x for x in value.get('repair_reasons', []) if x.strip()]
            if not hard and not hard_reasons:
                hard_reasons = ['Harter Fakten-QM: Pflichtfeld FAIL']
            if hard and not language and not repair_reasons:
                repair_reasons = ['Sprache/Stil reparieren']
            result = {'hard_ok': hard, 'language_ok': language,
                      'hard_reasons': hard_reasons, 'repair_reasons': repair_reasons}
            cache[fp] = result
            return result
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            last = exc
            print(f'SEMANTIC-QM JSON-PARSE-FEHLER Versuch {attempt + 1}/3:', item.get('title', '')[:90], '|', type(exc).__name__, str(exc)[:200])
        except Exception as exc:
            last = exc
            print('SEMANTIC-QM UNERWARTETER FEHLER:', item.get('title', '')[:90], '|', type(exc).__name__, str(exc)[:200])
            break
    return {'hard_ok': False, 'language_ok': False, 'technical_error': True,
            'hard_reasons': [f'Semantischer Fakten-QM technisch ungueltig nach 3 Versuchen: {type(last).__name__}: {str(last)[:140]}'],
            'repair_reasons': []}


def review(item, caption):
    result = review_detailed(item, caption)
    return result['hard_ok'] and result['language_ok'], result['hard_reasons'] + result['repair_reasons']
