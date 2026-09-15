# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 15.09.2026  
**Version:** v6  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`

## Leitbild
Der KI-SOCIAL-AGENT recherchiert, prüft, formuliert, bereitet Medien vor, veröffentlicht nur nach persönlicher Freigabe und lernt anschließend aus Nutzerentscheidungen, eigenen Ergebnissen und technischen Fehlern. **Neu in v6: geschlossenes selbstlernendes Feedback-Memory mit Audit-Trail und Konfidenzregeln.**

## Architektur
```
Web / MotoGP / Trends
        ↓
Quellenprüfung + Roster
        ↓
MEMORY_CONTEXT + Creator / Strategist / MotoGP Agency
        ↓
Profilformat + Quality + Rechte-Gate
        ↓
Telegram-Vorschau → EINE Freigabe
        ↓
PUBLISHED.md = FREIGEGEBEN → Publisher
        ↓
Plattform-ID + Analytics + Quality + Fehler/Duplikate
        ↓
Agent 14 Memory Curator
        ↓
MEMORY_EVENTS → LEARNED_RULES → MEMORY_CONTEXT
        └──────────────────────────────► nächster Content-Lauf
```

## Agent 14 – Closed-Loop Memory Curator
Dateien: `agents/14_memory_curator.md`, `memory_engine.py`, `.github/workflows/memory-learning.yml`.

### Vier Memory-Schichten
- `memory/MEMORY_EVENTS.jsonl`: append-only Audit-Ereignisse (Nutzerkorrekturen, Publishing, Performance, Fehler, Wiederholungen).
- `memory/LEARNED_RULES.md`: kuratierte Regeln mit Evidenz/Konfidenz.
- `memory/MEMORY_CONTEXT.md`: kompaktes aktives Kontextpaket, das Content-Agenten vor der Erstellung lesen.
- `memory/MEMORY_HEALTH.md`: Datenlage, Regel-/Eventstatus und Schutzprüfung.

Bestehende Spezial-Memories wie `PERFORMANCE`, `POST_HISTORY`, `VIRAL_PATTERNS`, `HOOKS_THAT_WORK`, `USER_PREFERENCES`, `QUALITY_*`, `EXPERIMENTS` bleiben erhalten und dienen als Evidenzquellen.

### Evidenz-/Lernregeln
- Direkte Nutzerkorrektur und harte Sicherheits-/Freigaberegel: hohe Konfidenz, sofort nutzbar.
- Eindeutig dokumentierter technischer Fehler/Duplikat: präventive Workflow-Regel.
- Eigene Performance: nur mit echter Reichweite und mehreren vergleichbaren Datensätzen; Korrelation bleibt Hypothese, keine Kausalitätsbehauptung.
- Externe Trends/Engagement: Inspiration, niemals automatisch persönliche Präferenz.
- Fehlende Daten werden nicht geschätzt.
- Konflikte werden nicht still überschrieben; Safety/Brand/Freigabe haben Vorrang.
- Memory darf niemals `FREIGEGEBEN` setzen oder Publisher starten.

### Aktuelle Bootstrap-Learnings
Der erste MotoGP-Agency-Test vom 15.09.2026 hat bereits als direkte Nutzerkorrektur gelernt: Quelle ist Faktenbasis, nie Textvorlage; englische Rohtexte/Web-Metadaten entfernen; Social-Text komplett neu/natürlich auf Deutsch; keine Standard-Hook-/CTA-Dauerschablone. Zusätzlich wurden dokumentierte Textduplikate und wiederholte Hooks als präventive Regeln übernommen.

## Content Creator / Strategist
`generate_ideas.py` und `weekly_plan.py` lesen jetzt das Closed-Loop `MEMORY_CONTEXT`. Tagesideen lesen zusätzlich `memory/MOTOGP_DAILY_CONTENT.md`. Priorität: Safety/Brand/Quellen > Nutzerkorrektur > eigene kuratierte Performance > externe Inspiration. Wiederholte Hooks und Themen werden gegen POST_HISTORY geprüft; Performance wird nicht erfunden.

## MotoGP-Roster
- `motogp_roster_updater.py` prüft den aktiven 2026-Roster gegen offizielle MotoGP-Seiten plus Crosscheck.
- Erfolgreicher Real-Lauf 15.09.2026: 22 Stammfahrer verifiziert; `content/MOTOGP_ROSTER.md` erzeugt.
- `MOTOGP_ROSTER_NEXT.md` bleibt separate Zukunftsvorschau; unvollständig ersetzt nie den aktiven Roster.
- Gerüchte/Wildcards/Test-/Ersatzfahrer werden nicht als reguläre Stammfahrer übernommen.

## Agent 13 – MotoGP Content Agency
Die Agency liest jetzt `MEMORY_CONTEXT`, berücksichtigt jüngste Fahrer-/Themenhäufigkeit als Rotationssignal und besitzt ein zusätzliches Text-Qualitäts-Gate. Aktualität kann Rotation überstimmen. Quelle bleibt Faktenbasis; fertige Telegram-Texte müssen eigenständig deutsch sein.

Täglich: offizielle MotoGP-News/Rider Market → Roster/Memory/Rotation → bis 12 Themen analysieren → stärkste 3 sauber redigieren → Quellen-/Rechte-Gate → Telegram → eine Freigabe → Publisher.

## Rechte-/Quellen-Gate
Keine routinemäßige zweite Nutzerabfrage. Fakten eigenständig formulieren; fremde Rennmedien nicht ungeprüft übernehmen. Facebook nutzt bevorzugt offiziellen Link/Link-Preview; Instagram eigenes/zulässiges Medium. Unklare Medienrechte → sichere Alternative.

## Telegram / Publisher
MotoGP: `motogp 1`, `motogp 2`, `motogp 3`, `motogp alle`, `motogp nein`. Nach Freigabe entstehen getrennte Instagram-/Facebook-Blöcke `FREIGEGEBEN`. Bestehende Publisher bleiben an Freigabe + Publication-Claims gebunden. Erfolgreiche Veröffentlichungen werden mit Plattform-ID dokumentiert.

## Content-Regeln
- Ride With Me max. 1x/Kalenderwoche.
- MotoGP-Fahrer einzeln fokussieren und Roster rotieren.
- Locker, menschlich, per Du; Deutsch als Basis, Türkisch gezielt.
- Keine Nachrichtenagentur-/KI-Schablonensprache.
- Professionelle relevante Hashtags; kein Spam.
- Keine erfundenen Fakten, Ergebnisse, Transfers, Zitate, Trends oder Quellen.

## Automatisches Learning-Timing
`Closed Loop Memory Learning` läuft täglich um 17:45 UTC nach den vorgesehenen Analytics-/Viral-Reports und ist zusätzlich manuell startbar. Er verändert ausschließlich Memory-Dateien, nicht Freigaben oder Publisher.

## Sicherheitsnetz
Keine selbstmodifizierenden Safety-Regeln. Keine Secrets/private Chats im Learning-Memory. Keine automatische Veröffentlichung aus einem Lernsignal. Keine Käufe/Buchungen/Anmeldungen durch Recherche-Agenten. Externe Inhalte werden nicht kopiert.

## Aktuelle Prioritäten
1. Closed-Loop Memory ersten echten Workflow-Lauf prüfen und Event-/Regel-/Context-Ausgabe gegen Quellen validieren.
2. Zweiten MotoGP-Agency-Test nach Redaktions- und Memory-Update durchführen.
3. Eigene Analytics-Daten stabil befüllen; erst dann Performance-Hypothesen automatisch befördern.
4. Telegram-Ablehnungen künftig noch feiner als explizite Feedback-Events mit Grund erfassen, sofern Nutzer einen Grund mitsendet.
5. Facebook-Link-Preview im Real-Post prüfen.
6. `content/PUBLISHED.md`-Historie separat verlustfrei reparieren.
7. Follow-Analyse-Anbieterfehler stabilisieren.

## Leitbild
> **„Bülent entscheidet. Das System merkt sich belegte Entscheidungen und Ergebnisse, lernt kontrolliert daraus und nutzt dieses Wissen beim nächsten Lauf – ohne Sicherheits- oder Freigaberegeln selbst abzuschwächen.“**
