# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 13.09.2026  
**Version:** v3  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`

---

## Kurzbild

Der KI-SOCIAL-AGENT ist heute ein GitHub-Actions-basiertes System für Bülents deutsch-türkische Motorrad- und Reise-Community. Es erstellt, recherchiert, bewertet und bereitet Content vor. Veröffentlichungen bleiben an eine ausdrückliche menschliche Freigabe gebunden.

> **Grundsatz:** Die KI darf recherchieren, Vorschläge erstellen und prüfen. Sie veröffentlicht, kauft oder bucht nichts ohne klaren Auftrag und Freigabe.

---

## Architektur

```
Recherche & Trends ──┐
Content-Planung ─────┼──► Memory & Qualitätsprüfung ─► Telegram-Freigabe ─► Publisher
Medien-Erzeugung ────┘                                      │
                                                            └──► nur Status: FREIGEGEBEN
```

- **GitHub Actions** führt zeitgesteuerte und manuelle Abläufe aus.
- **Telegram** ist der persönliche Steuerungs- und Freigabekanal.
- **memory/** speichert nachvollziehbare Ergebnisse, Berichte und Lernstände.
- **content/PUBLISHED.md** ist der kontrollierte Freigabeplan.
- **GitHub Secrets/Variables** enthalten Zugangsdaten und Konfiguration; keine Schlüssel gehören in Dateien.

---

## Aktive Funktionsbereiche

### 1. Content-Pipeline

- Tägliche Content-Ideen und Wochenplanung
- Gemeinsamer Agenten-Kontext aus `agents/`
- Mediengenerierung mit Agnes: Bilder, optionale Hochformat-Videos und Karussellbilder
- Asset-Struktur unter `assets/`
- Morgen-Digest und Telegram-Freigabe
- Einträge bleiben Entwurf, bis Bülent ausdrücklich freigibt

### 2. Veröffentlichungs-Pipeline

Vorhandene Publisher für:

- Instagram-Posts
- Instagram-Stories
- Instagram-Reels
- Instagram-Karussells
- Facebook-Posts
- Facebook-Karussells

Die Publisher verarbeiten nur geeignete, freigegebene Blöcke in `content/PUBLISHED.md`. Erfolgreiche Posts werden mit Zeitpunkt und Plattform-ID dokumentiert.

### 3. Inspiration- und Recherche-Agent

Der Inspiration-Agent sammelt öffentliche Trend- und Social-Daten für konkrete Ideen.

- **Apify ist Hauptquelle** für Instagram, Facebook und YouTube
- Bright Data wird nur noch als gezielter Fallback genutzt; das Bright-Data-Konto war zuletzt ohne verfügbares Guthaben bzw. nicht aktiv
- Gemini fasst belegte öffentliche Daten in Themen und Ideen zusammen
- Ergebnisse: `memory/INSPIRATION_IDEAS.md`
- Apify-Social-Rohdaten und Diagnose: `memory/INSPIRATION_APIFY.md`, `memory/INSPIRATION_APIFY_DEBUG.md`
- YouTube-Rohdaten und Diagnose: `memory/INSPIRATION_YOUTUBE_APIFY.md`, `memory/INSPIRATION_YOUTUBE_APIFY_DEBUG.md`
- Daily Ideas übernimmt jetzt zu mindestens einer Idee die konkrete Inspirationsquelle, wenn eine aktuelle Quelle verfügbar ist

**Letzter bestätigter Stand:** Instagram und YouTube lieferten erfolgreich öffentliche Datensätze. Facebook scheiterte im letzten Lauf noch mit dem alten Actor (HTTP 400). Der neue Facebook-Actor ist auf maximal zehn Ergebnisse pro Lauf begrenzt und muss noch einmal manuell getestet werden.

### 4. Analytics, Viral Learning und Growth

- Instagram-/Facebook-Insights werden nach veröffentlichten Beiträgen gespeichert
- Performance-Berichte und Telegram-Zusammenfassungen
- Mustererkennung, Experimente, Funnel- und Growth-Auswertung
- Wettbewerber- und Follow-Analyse auf Basis öffentlicher Daten

Wichtig: Datenbasierte Empfehlungen sind Vorschläge, keine automatische Strategie- oder Veröffentlichungsentscheidung.

### 5. Deal-Hunter und Preis-Tracking

- Telegram-Kommandos für einmalige öffentliche Produktsuche
- Watchlist mit Preisverlauf und Benachrichtigung bei Änderungen
- Auto-Track kann ein- und ausgeschaltet werden
- Kein Kauf, keine Anmeldung und kein Testen nichtöffentlicher Gutscheincodes

### 6. Race- und Community-Funktionen

- Rennkalender und Poster-Entwürfe
- `race` erstellt nur einen Entwurf
- `go` ist eine ausdrückliche Freigabe, keine automatische Veröffentlichung
- Karussell-Entwürfe können per Telegram angelegt werden

---

## Agenten-Bibliothek

In `agents/` liegen aktuell zehn dokumentierte Spezialrollen:

1. Content Creator
2. Instagram Curator
3. TikTok Strategist
4. Social Media Strategist
5. Research Synthesist
6. Reddit Community Builder
7. Video Optimization
8. Paid Social Strategist
9. Quality Agent
10. Follow Analysis Agent

`agents/AGENTS_INDEX.md` beschreibt Rolle, Aktivierung und Einsatzgebiet. Nicht jede dokumentierte Rolle ist bereits ein vollständig automatisierter Workflow.

---

## Qualitäts- und Sicherheitsnetz

Der Qualitäts-Agent prüft täglich bzw. manuell:

- Vorhandensein zentraler Content- und Memory-Dateien
- Inspirationsreport: Quellen und Anzahl konkreter Ideen
- YouTube-Apify-Fallback: Datensätze, Duplikate und Quellenmix
- doppelte Quellen-URLs und fehlende Belege
- Datenalter der Recherche
- Bright-Data- und Gemini-Diagnosen
- typische versehentlich eingecheckte Zugangsschlüssel
- Status ausgewählter GitHub-Workflows

Er erzeugt `memory/QUALITY_REPORT.md` und `memory/QUALITY_HISTORY.md`.

**Garantien des Qualitäts-Agenten:**

- startet keine Workflows neu
- veröffentlicht nichts
- verändert keinen Content
- meldet Warnungen nachvollziehbar statt still etwas zu reparieren

---

## Freigabe- und Sicherheitsprinzip

```
Idee / Recherche
  → Entwurf
  → Telegram-Nachricht an Bülent
  → ausdrückliche Freigabe
  → Status: FREIGEGEBEN
  → passender Publisher
  → Post-ID und Analytics
```

- Keine automatische Veröffentlichung aus Ideen, Trends oder Analysen
- Alle Medien-Generatoren und Publisher verlangen technisch `Status: FREIGEGEBEN`
- Jeder Plattform-Post wird vor dem externen Aufruf als eindeutiger Veröffentlichungs-Claim in Git gespeichert
- Ein unklar abgebrochener Claim wird nicht automatisch erneut gesendet; das verhindert Doppelposts
- Gleiche freigegebene Inhalte werden in `memory/PUBLICATION_DUPLICATES.md` markiert und nicht automatisch veröffentlicht
- Alle Workflows, die `content/PUBLISHED.md` verändern, teilen eine gemeinsame GitHub-Actions-Sperre
- Kein Kauf, keine Buchung, keine Anmeldung durch Deal- oder spätere Reise-Agenten
- Telegram akzeptiert nur den konfigurierten persönlichen Chat
- API-Keys, Tokens und Chat-IDs bleiben GitHub Secrets

---

## Wichtige Speicherorte

| Bereich | Dateien/Ordner |
| --- | --- |
| Freigabeplan | `content/PUBLISHED.md` |
| Ideenpool | `content/CONTENT_PLAN.md` |
| Agentenrollen | `agents/` |
| Regeln | `rules/BRAND_RULES.md`, `rules/SAFETY_RULES.md` |
| Gedächtnis und Reports | `memory/` |
| Medien | `assets/images/`, `assets/videos/`, `assets/published/` |
| Workflow-Automationen | `.github/workflows/` |

---

## Aktuelle offene Prioritäten

1. **Facebook-Apify einmal manuell testen**  
   Der neue Facebook-Actor mit echtem `resultsLimit: 10` muss einen Lauf mit aktuellem Code abschließen. Im Apify-Dashboard muss danach „Facebook Posts Scraper“ erscheinen, nicht mehr der alte Profile-&-Posts-Actor.

2. **Apify-Kosten beobachten**  
   Der Free-Plan liegt aktuell bei einem $5-Monatslimit. Keine Upgrades oder Overages aktivieren; nur wenige manuelle Testläufe durchführen. Nach mehreren regulären Läufen den tatsächlichen Monatsdurchschnitt in Apify Billing prüfen.

3. **Qualitäts-Agent einmal manuell testen**  
   Der neue Check für YouTube-Fallback, Quellenqualität und Datenalter soll einen ersten echten Report erstellen.

4. **System-Neustart-Agent planen**  
   Ein zukünftiger, rein technischer Wächter soll festgefahrene Workflows erkennen und zeitversetzt neu anstoßen. Er darf keine Inhalte veröffentlichen.

5. **Stabilisieren vor Ausbau**  
   Mehrere Tage echte Reports, Telegram-Freigaben und Publisher-Ergebnisse prüfen, bevor weitere große Funktionen dazukommen.

---

## Geplante Ausbaustufen

### Nächste Stufe

- System-Neustart-Agent
- Aktualisierte Projektdokumentation und konsolidierte Secrets-Dokumentation
- Optional: VPS-Umzug für zuverlässigeren 24/7-Betrieb
- Optional: SearXNG als konfigurierbarer Recherche-Fallback
- Optional: zentraler Model Router / OmniRouter, erst nach Stabilisierung

### Spätere Reise-Zentrale

Ein Hauptagent koordiniert spezialisierte Agenten für:

- Flugrecherche
- Hotels
- Mietwagen
- Routen und Aktivitäten
- Budget- und Terminvergleich

Auch dort gilt: Recherche und Vorschläge automatisieren, Buchung erst nach Bülents ausdrücklicher Freigabe.

---

## Was nicht behauptet wird

- Nicht jede Plattformdatenquelle liefert jederzeit gleich gute oder vollständige Daten.
- Ein erfolgreiches Workflow-Grün ersetzt keine inhaltliche Quellenprüfung.
- Dokumentierte Agentenrollen sind nicht automatisch gleichbedeutend mit vollständig autonomen Agenten.
- GitHub Actions und externe APIs können zeitweise verzögert oder nicht erreichbar sein.

---

## Leitbild

> **„Bülent entscheidet. Das System recherchiert, organisiert, prüft und bereitet sauber vor.“**

