"""Independent semantic source-to-caption QM for Motorcycle Racing.

The provider response is parsed fail-closed. Only a complete JSON object with the
expected boolean fields is accepted; technical provider/format failures are
reported separately from editorial failures.
"""
import json
import re
from llm_client import generate

BRAND_HASHTAGS = {'#buelentsbikelife'}


def _clean_json(raw):
    if not isinstance(raw, str):
        raise ValueError('semantic QM response must be a string')
    text = raw.strip()
    if not text:
        raise ValueError('semantic QM response is empty')
    # Code fences are an explicitly supported presentation wrapper. No other
    # prose is accepted before or after the JSON object.
    if text.startswith('```'):
        match = re.fullmatch(r'```(?:json)?\s*(.*?)\s*```', text, flags=re.I | re.S)
        if not match:
            raise ValueError('malformed JSON code fence')
        text = match.group(1).strip()
    if not text.startswith('{') or not text.endswith('}'):
        raise ValueError('semantic QM response is not one JSON object')
    value = json.loads(text)
    if not isinstance(value, dict):
        raise ValueError('semantic QM response must be a JSON object')
    return value


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
    url = str(item.get('url', '')).strip()
    cfo = item.get('canonical_fact_object')
    facts = json.dumps(cfo, ensure_ascii=False) if cfo is not None else 'Keine CFO vorhanden.'
    review_caption = _caption_for_fact_review(caption, _system_hashtags(caption))
    return f'''Du bist unabhängiger Senior-Faktenprüfer für Motorrad-Racing.
Trenne harte Faktenfehler strikt von reparierbarer Sprache.
QUELLFAKTEN:
SERIE: {infer_story_series(item)}
TITEL: {title}
ZUSAMMENFASSUNG: {summary}
URL: {url}
CANONICAL FACT OBJECT: {facts}
POST OHNE SYSTEM-HASHTAGS: {review_caption}
Antworte ausschließlich als ein JSON-Objekt ohne Markdown und ohne Zusatztext:
{{"hard_fact_ok":true,"series_ok":true,"rider_team_ok":true,"quote_ok":true,"german_ok":true,"style_ok":true,"hard_reasons":[],"repair_reasons":[]}}'''


def _validate_result(value):
    required = ('hard_fact_ok', 'series_ok', 'rider_team_ok', 'quote_ok', 'german_ok', 'style_ok')
    if set(value) - set(required) - {'hard_reasons', 'repair_reasons'}:
        raise ValueError('semantic QM response contains unknown fields')
    if any(type(value.get(key)) is not bool for key in required):
        raise ValueError('semantic QM boolean fields must be real JSON booleans')
    for key in ('hard_reasons', 'repair_reasons'):
        reasons = value.get(key, [])
        if not isinstance(reasons, list) or any(not isinstance(x, str) for x in reasons):
            raise ValueError(f'{key} must be a list of strings')
    return value


def review_detailed(item, caption):
    prompt = _prompt(item, caption)
    last = None
    for _ in range(3):
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
            return {'hard_ok': hard, 'language_ok': language,
                    'hard_reasons': hard_reasons, 'repair_reasons': repair_reasons}
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            last = exc
        except Exception as exc:
            last = exc
            break
    return {'hard_ok': False, 'language_ok': False,
            'technical_error': True,
            'hard_reasons': [f'Semantischer Fakten-QM technisch ungueltig nach 3 Versuchen: {type(last).__name__}: {str(last)[:140]}'],
            'repair_reasons': []}


def review(item, caption):
    result = review_detailed(item, caption)
    ok = result['hard_ok'] and result['language_ok']
    return ok, result['hard_reasons'] + result['repair_reasons']
