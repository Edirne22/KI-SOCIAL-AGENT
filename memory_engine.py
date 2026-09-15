"""Closed-loop Memory Curator for KI-SOCIAL-AGENT.

Turns durable evidence into a small, auditable context packet. It never publishes,
never invents missing metrics, and never promotes weak correlations as facts.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path('.')
MEM = ROOT / 'memory'
EVENTS = MEM / 'MEMORY_EVENTS.jsonl'
RULES = MEM / 'LEARNED_RULES.md'
CONTEXT = MEM / 'MEMORY_CONTEXT.md'
HEALTH = MEM / 'MEMORY_HEALTH.md'
PERFORMANCE = MEM / 'PERFORMANCE.md'
POST_HISTORY = MEM / 'POST_HISTORY.md'
PUBLISHED = ROOT / 'content' / 'PUBLISHED.md'
DUPLICATES = MEM / 'PUBLICATION_DUPLICATES.md'
QUALITY = MEM / 'QUALITY_REPORT.md'
USER_PREFS = MEM / 'USER_PREFERENCES.md'

SEED_RULES = [
    ('editorial', 'Quelle ist Faktenbasis, niemals Textvorlage. Web-Metadaten, englische Rohtexte und Byline-Reste vor Social-Text entfernen.', 'user_correction_2026-09-15', 1.0),
    ('editorial', 'Social-Posts vollständig neu und natürlich auf Deutsch formulieren; keine Satz-für-Satz-Übersetzung oder lange Originalpassagen.', 'user_correction_2026-09-15', 1.0),
    ('editorial', 'Hooks und Community-Fragen müssen zum konkreten Thema passen; keine identische Dauerschablone.', 'user_correction_2026-09-15', 1.0),
    ('safety', 'Fehlende oder unklare Daten niemals schätzen. Schwache Evidenz bleibt Beobachtung und wird nicht als Lernregel befördert.', 'system_policy', 1.0),
    ('workflow', 'Eine explizite Telegram-Freigabe bleibt vor Social-Publishing erforderlich; Memory darf keine Freigabe ersetzen.', 'system_policy', 1.0),
]


def read(path: Path) -> str:
    return path.read_text(encoding='utf-8') if path.exists() else ''


def normalize(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip().casefold()


def event_key(event: dict) -> str:
    return '|'.join(str(event.get(k, '')) for k in ('type', 'source', 'subject', 'value'))


def load_events() -> list[dict]:
    events = []
    if EVENTS.exists():
        for line in EVENTS.read_text(encoding='utf-8').splitlines():
            try:
                obj = json.loads(line)
                if isinstance(obj, dict): events.append(obj)
            except json.JSONDecodeError:
                continue
    return events


def append_events(candidates: list[dict]) -> int:
    MEM.mkdir(parents=True, exist_ok=True)
    existing = {event_key(e) for e in load_events()}
    fresh = []
    for event in candidates:
        if event_key(event) in existing: continue
        event.setdefault('timestamp', datetime.now(timezone.utc).isoformat())
        fresh.append(event); existing.add(event_key(event))
    if fresh:
        with EVENTS.open('a', encoding='utf-8') as f:
            for event in fresh: f.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + '\n')
    return len(fresh)


def parse_performance() -> list[dict]:
    text = read(PERFORMANCE); rows = []
    pattern = r'^## Beitrag vom (\d{4}-\d{2}-\d{2}) - Plattform: (.+?) - Titel: (.*?)\n(.*?)(?=^## Beitrag vom |\Z)'
    for m in re.finditer(pattern, text, re.M | re.S):
        day, platform, title, body = m.groups()
        def n(label):
            x = re.search(rf'(?m)^{label}:\s*(\d+)', body); return int(x.group(1)) if x else 0
        reach=n('Reichweite'); engagement=sum(n(x) for x in ('Likes','Kommentare','Shares','Gespeichert'))
        rows.append({'date':day,'platform':platform.strip(),'title':title.strip(),'reach':reach,'engagement':engagement,'rate':engagement/reach if reach else None})
    return rows


def derive_events() -> list[dict]:
    out=[]
    # Published facts are strong operational evidence, not proof of content quality.
    pub=read(PUBLISHED)
    for m in re.finditer(r'^## (.+?) \[GEPOSTET ([^|\]]+)(?: \| ID: ([^\]]+))?\]', pub, re.M):
        platform, when, media_id=m.groups()
        out.append({'type':'published','source':'content/PUBLISHED.md','subject':platform.strip(),'value':media_id or when.strip(),'confidence':1.0})
    # Duplicate blocks are reliable failure events.
    dup=read(DUPLICATES)
    for m in re.finditer(r'(?m)^## ([^\n]+).*?^- Grund: ([^\n]+)', dup, re.S|re.M):
        out.append({'type':'failure','source':'memory/PUBLICATION_DUPLICATES.md','subject':'duplicate_content','value':normalize(m.group(2)), 'confidence':1.0})
    # Performance observations require reach > 0 and are stored as observations.
    rows=parse_performance()
    for r in rows:
        if r['rate'] is not None:
            out.append({'type':'performance','source':'memory/PERFORMANCE.md','subject':f"{r['platform']}::{r['title']}",'value':round(r['rate'],6),'reach':r['reach'],'engagement':r['engagement'],'confidence':1.0})
    # Repeated hooks in generated history are a deterministic anti-repetition signal.
    hooks=[normalize(x) for x in re.findall(r'(?m)^- Hook \d+:\s*(.+)$', read(POST_HISTORY)) if x.strip()]
    for hook,count in Counter(hooks).items():
        if count >= 2:
            out.append({'type':'failure','source':'memory/POST_HISTORY.md','subject':'repeated_hook','value':hook,'count':count,'confidence':1.0})
    return out


def performance_rules(rows: list[dict]) -> list[tuple[str,str,str,float]]:
    valid=[r for r in rows if r['rate'] is not None and r['reach'] >= 100]
    if len(valid) < 4: return []
    by_platform=defaultdict(list)
    for r in valid: by_platform[r['platform']].append(r)
    learned=[]
    for platform,items in by_platform.items():
        if len(items) < 3: continue
        ordered=sorted(items,key=lambda r:r['rate']); median=ordered[len(ordered)//2]['rate']
        best=max(items,key=lambda r:r['rate'])
        if best['rate'] >= median*1.25 and best['reach'] >= 100:
            learned.append(('performance', f"Auf {platform} ist '{best['title']}' aktuell ein überdurchschnittlicher Performer. Muster nur als Hypothese wiederverwenden, nicht den Text kopieren.", 'memory/PERFORMANCE.md', .8))
    return learned


def build_rules() -> list[tuple[str,str,str,float]]:
    rules=list(SEED_RULES)
    events=load_events()
    if any(e.get('subject')=='duplicate_content' for e in events):
        rules.append(('workflow','Vor Freigabe und Publication-Claim Textduplikate gegen bestehende/freigegebene Beiträge prüfen.', 'memory/PUBLICATION_DUPLICATES.md',1.0))
    if any(e.get('subject')=='repeated_hook' for e in events):
        rules.append(('editorial','Hooks innerhalb kurzer Zeit nicht wortgleich wiederverwenden; Thema und Hook müssen semantisch zusammenpassen.', 'memory/POST_HISTORY.md',1.0))
    rules += performance_rules(parse_performance())
    # Stable dedupe by normalized rule text.
    result=[]; seen=set()
    for rule in rules:
        key=normalize(rule[1])
        if key not in seen: seen.add(key); result.append(rule)
    return result


def write_outputs(new_events: int) -> None:
    now=datetime.now(timezone.utc); rules=build_rules(); events=load_events(); perf=parse_performance()
    lines=['# Learned Rules','',f'**Aktualisiert:** {now:%Y-%m-%d %H:%M UTC}','',
           'Nur Regeln mit klarer Evidenz werden hier eingespeist. Performance-Korrelationen bleiben als Hypothese markiert.','']
    for category,text,source,confidence in rules:
        lines += [f'- [{category.upper()} | Konfidenz {confidence:.2f}] {text}',f'  - Evidenz: `{source}`']
    RULES.write_text('\n'.join(lines)+'\n',encoding='utf-8')

    prefs=read(USER_PREFS)[-3500:]
    context=['# Memory Context Packet','',f'**Erzeugt:** {now:%Y-%m-%d %H:%M UTC}',
             '**Verwendung:** vor Content-Erstellung/Planung lesen; Regeln sind stärker als lose Beobachtungen.','',
             '## Aktive Lernregeln']
    context += [f'- {text}' for _,text,_,_ in rules]
    context += ['', '## Nutzerpräferenzen (dauerhaft)', prefs or '- keine Datei vorhanden', '',
                '## Datenlage', f'- Performance-Snapshots mit echter Reichweite: {sum(1 for r in perf if r["reach"]>0)}',
                f'- Audit-Events: {len(events)}', '- Fehlende Kennzahlen werden nicht geschätzt.',
                '- Externe Trenddaten sind Inspiration; eigene Performance + Nutzerfeedback haben Vorrang.','']
    CONTEXT.write_text('\n'.join(context),encoding='utf-8')

    quality=read(QUALITY)
    health=['# Memory Health','',f'**Stand:** {now:%Y-%m-%d %H:%M UTC}','',
            f'- Neue Events in diesem Lauf: {new_events}',f'- Events gesamt: {len(events)}',f'- Aktive Regeln: {len(rules)}',
            f'- Eigene Performance-Datensätze: {len(perf)}',f'- Mit Reichweite > 0: {sum(1 for r in perf if r["reach"]>0)}',
            f'- Quality-Status zuletzt: {"WARNUNG" if "Gesamtstatus: **WARNUNG**" in quality else "siehe QUALITY_REPORT"}',
            '- Schutz: keine Secrets, keine privaten Chats, keine automatische Freigabe, keine erfundenen Metriken.',
            '- Promotion: direkte Nutzerkorrektur/harte Systemregel sofort; Performance-Muster erst mit ausreichender Stichprobe.',
            '- Konflikte werden nicht still überschrieben; harte Sicherheits-/Freigaberegeln gewinnen.','']
    HEALTH.write_text('\n'.join(health),encoding='utf-8')


def get_context(max_chars: int=9000) -> str:
    if not CONTEXT.exists():
        new=append_events(derive_events()); write_outputs(new)
    return read(CONTEXT)[-max_chars:]


def main() -> None:
    new=append_events(derive_events()); write_outputs(new)
    print(f'Memory Curator: {new} neue Events, {len(load_events())} Events gesamt, Context Packet aktualisiert.')

if __name__ == '__main__': main()
