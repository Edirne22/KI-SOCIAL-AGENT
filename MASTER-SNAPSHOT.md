# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 15.09.2026  
**Version:** v5  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`

## Leitbild
Der KI-SOCIAL-AGENT recherchiert, prüft, formuliert, bereitet Medien vor und lernt aus Ergebnissen. Veröffentlichung bleibt hinter einer persönlichen Freigabe. Für MotoGP gilt jetzt: **eine Telegram-Freigabe pro ausgewähltem Content-Paket; danach darf die bestehende Publisher-Kette automatisch übernehmen.**

## Architektur
```
Web / MotoGP / Trends
        ↓
Quellenprüfung + Roster
        ↓
Content Agency / Creator / Strategist
        ↓
Profilformat + Quality + automatisches Rechte-Gate
        ↓
Telegram-Vorschau
        ↓
EINE Freigabe
        ↓
content/PUBLISHED.md = FREIGEGEBEN
        ↓
Instagram-/Facebook-Publisher
        ↓
Plattform-ID + Analytics + Learning
```

## MotoGP-Roster
- `motogp_roster_updater.py` prüft den aktiven 2026-Roster direkt gegen offizielle MotoGP-Seiten plus unabhängigen Crosscheck; keine Gemini-Abhängigkeit für den aktiven Roster.
- Erfolgreicher Real-Lauf am 15.09.2026: 22 Stammfahrer verifiziert und `content/MOTOGP_ROSTER.md` erzeugt.
- `memory/MOTOGP_ROSTER_LOG.md` dokumentiert die Prüfung.
- `content/MOTOGP_ROSTER_NEXT.md` führt bestätigte Meldungen zur nächsten Saison separat. Ein unvollständiger Zukunfts-Roster ersetzt niemals den aktiven Roster.
- Gerüchte, Wildcards, Test- und Ersatzfahrer werden nicht als reguläre Stammfahrer übernommen.

## Agent 13 – MotoGP Content Agency
Dateien: `agents/13_motogp_content_agency.md`, `motogp_content_agency.py`, `.github/workflows/motogp-content-agency.yml`.

Täglich:
- offizielle MotoGP-News und Rider-Market recherchieren;
- Fahrer-/Titel-/Renn-/Technik-/Transfer-Themen priorisieren;
- aktuellen Roster und Fahrerrotation berücksichtigen;
- Toprak/türkische Racer bei echtem Anlass priorisieren;
- bis zu 12 Themen analysieren und die stärksten 3 als Telegram-Pakete vorbereiten;
- eigenständige deutschsprachige Captions im Profilstil erzeugen;
- professionelle, thematische Hashtags ergänzen;
- offizielle Quelle pro Paket erhalten;
- Tagesbriefing und Archiv speichern;
- Next-Season-Meldungen getrennt fortschreiben.

## Rechte- und Quellen-Gate
Das Rechte-Gate läuft vor Telegram im Hintergrund und erzeugt keine routinemäßige zweite Nutzerabfrage:
- Fakten eigenständig zusammenfassen, keine längeren fremden Artikeltexte kopieren.
- Keine fremden Rennbilder/-videos ungeprüft als eigenes Medium verwenden.
- Bei unklaren Medienrechten automatisch sichere eigene/zulässige Medienalternative wählen.
- Facebook erhält die offizielle MotoGP-URL im Post, damit Meta – sofern von der Zielseite unterstützt – eine Link-Preview mit Vorschaubild/Titel/Domain erzeugen kann.
- Instagram verwendet eigenes/zulässiges Medium; Quelle bleibt dokumentiert. Story-Link kann genutzt werden, sobald/sofern der Story-Publisher Link-Sticker technisch unterstützt.

## MotoGP Telegram Approval
Dateien: `motogp_telegram_receive.py`, `.github/workflows/motogp-telegram-approval.yml`, `memory/MOTOGP_APPROVAL_SESSION.md`, `memory/MOTOGP_APPROVAL_STATE.md`.

Befehle:
- `motogp 1`, `motogp 2`, `motogp 3`
- `motogp alle`
- `motogp nein`

Nach Freigabe entstehen getrennte Instagram- und Facebook-Blöcke mit `Status: FREIGEGEBEN` in `content/PUBLISHED.md`. Die bestehenden Publisher dürfen danach automatisch veröffentlichen. Es gibt keine zweite routinemäßige Text-/Rechte-/Plattformfreigabe.

## Content-Regeln
- Ride With Me maximal 1x/Kalenderwoche.
- MotoGP-Fahrer stärker und einzeln fokussieren; Roster rotieren.
- Deutsch-türkische Motorrad-Community als Kernzielgruppe.
- Locker, per Du, wenige Emojis, kein Marketing-Sprech/Clickbait.
- Hashtags: Fahrer + Team/Hersteller + MotoGP/Event + Nische/Community; kein Spam.
- `POST_HISTORY`, `VIRAL_PATTERNS`, `HOOKS_THAT_WORK` für Wiederholungsvermeidung und Optimierung.

## Publisher
Vorhanden: Instagram Posts, Stories, Reels, Karussells sowie Facebook Posts/Karussells/Video. Alle Publisher bleiben an `FREIGEGEBEN` und Publication-Claims gebunden. Erfolgreiche Veröffentlichungen werden mit Zeitpunkt und Plattform-ID dokumentiert.

Facebook-Video-Pfad wurde am 15.09.2026 real erfolgreich bestätigt. Der Publisher erkennt `Video:` und darf einen fehlgeschlagenen Upload nicht als gepostet markieren.

## Medien & Musik
- Agnes-Medienpipeline für eigene/zulässige Bilder, optionale Videos und Karussells.
- KI-generierte Szenen dürfen nicht als echte Rennaufnahmen ausgegeben werden.
- Music Agent kann geeignete lokale Musik verarbeiten, veröffentlicht aber nicht selbst.

## Recherche & Learning
- Inspiration: Apify primär, Bright Data gezielter Fallback, weitere öffentliche Quellen quellengebunden.
- Analytics, Viral Patterns, Hooks, Growth/Funnel und Follow Analyzer liefern Learnings.
- Follow Analyzer untersucht konfigurierte öffentliche Profile, keine privaten Follower-/Likerlisten und führt keine Social-Interaktionen aus.

## Sicherheitsnetz
- Keine erfundenen Ergebnisse, Transfers, Quellen oder Trending-Behauptungen.
- Keine Veröffentlichung allein wegen eines Trends oder Roster-Updates.
- Telegram-Freigabe nur aus dem hinterlegten persönlichen Chat.
- Gemeinsame `published-plan-writers`-Concurrency schützt `content/PUBLISHED.md` vor konkurrierenden Schreibzugriffen.
- Secrets/Tokens ausschließlich in GitHub Secrets/Variables.
- Keine Käufe, Buchungen oder Anmeldungen durch Recherche-Agenten.

## Aktuelle Prioritäten
1. MotoGP Content Agency einmal real manuell testen: Recherche → Telegram → `motogp 1` → Publisher.
2. Link-Preview auf Facebook im Real-Post prüfen; sie hängt zusätzlich von den Open-Graph-Daten/Meta-Regeln der offiziellen Zielseite ab.
3. Instagram-Story-Link-Sticker als eigene Publisher-Funktion ergänzen/testen, bevor er als automatisch unterstützt gilt.
4. Next-Season-Roster weiter aus offiziellen Bestätigungen aufbauen und erst bei vollständigem Grid aktivieren.
5. `content/PUBLISHED.md`-Historie separat und verlustfrei reparieren.
6. Follow-Analyse-Anbieterfehler weiter stabilisieren.

## Leitbild
> **„Bülent entscheidet einmal. Das System recherchiert, prüft, formuliert und veröffentlicht danach kontrolliert über die bestehende Freigabekette.“**
