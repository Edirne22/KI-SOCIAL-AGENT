# MASTER-SNAPSHOT – KI-SOCIAL-AGENT

**Stand:** 15.09.2026  
**Version:** v4  
**Repository:** `Edirne22/KI-SOCIAL-AGENT`

---

## Kurzbild

Der KI-SOCIAL-AGENT ist ein GitHub-Actions-basiertes System für Bülents deutsch-türkische Motorrad- und Reise-Community. Es recherchiert öffentliche Quellen, erstellt und bewertet Content, bereitet Medien vor und veröffentlicht ausschließlich ausdrücklich freigegebene Inhalte.

> **Grundsatz:** Bülent entscheidet. Das System recherchiert, organisiert, prüft und bereitet sauber vor.

---

## Architektur

```
Web-Recherche & Trends ─────┐
MotoGP-Roster-Verifikation ─┼─► Content/Agenten ─► Qualität ─► Telegram-Freigabe ─► Publisher
Viral-/Performance-Memory ──┘                                            │
                                                                        └─► nur FREIGEGEBEN
```

- GitHub Actions führt geplante/manuelle Abläufe aus.
- Telegram ist Steuerungs- und Freigabekanal.
- `memory/` speichert Berichte, Logs und bestätigte Learnings.
- `content/PUBLISHED.md` bleibt Freigabe-/Publikationsplan.
- Secrets und Tokens bleiben in GitHub Secrets/Variables.

---

## 1. Content-Pipeline

- Tägliche Content-Ideen und Wochenplanung.
- Content Creator + Social Media Strategist verwenden Memory, Viral-Muster und Post-History.
- Ride With Me ist auf maximal **einen Content-Schwerpunkt pro Kalenderwoche** reduziert.
- MotoGP erhält höheren Schwerpunkt: bevorzugt ein einzelner Fahrer pro Idee statt oberflächlicher Sammelposts.
- Fahrer werden über die aktuelle zentrale Datei `content/MOTOGP_ROSTER.md` bezogen.
- Professionelle Hashtag-Strategie: Fahrer, Team/Hersteller, MotoGP/GP plus passende Nischen-/Community-Tags; kein Hashtag-Spam und keine erfundenen Trends.
- Türkische Racer bleiben bei starken aktuellen Anlässen Prio 1.
- `POST_HISTORY`, `VIRAL_PATTERNS` und `HOOKS_THAT_WORK` dienen der Rotation und Optimierung auf relevante Interaktionen.

---

## 2. Neuer autonomer MotoGP-Roster-Updater

**Neu in v4:** `motogp_roster_updater.py` + `.github/workflows/motogp-roster-update.yml`.

Zweck: Die Fahrer-/Teamaufstellung ist nicht mehr dauerhaft auf „2026“ fest verdrahtet. Das System erkennt das aktuelle Kalenderjahr bzw. kann bei manuellem Lauf ein Saisonjahr erhalten und recherchiert die entsprechende MotoGP-Aufstellung im öffentlichen Web.

### Ablauf

1. Wöchentlicher Lauf montags über GitHub Actions; zusätzlich manuell startbar.
2. Recherche mit Gemini Google Search Grounding.
3. Offizielle MotoGP-Quellen werden bevorzugt.
4. Mindestens eine zweite unterschiedliche Web-Domain muss den Roster crosschecken.
5. Nur eine explizit als vollständig bestätigt erkannte Saison wird übernommen.
6. Plausibilitätsprüfung auf mindestens 8 Teams und 18 Fahrer.
7. Unbestätigte Transfers, Gerüchte, Test-/Ersatzfahrer werden nicht automatisch als Stamm-Roster übernommen.
8. Social-Handles werden niemals geraten. Vorhandene Handles werden nur bei eindeutigem Namensmatch weiterverwendet.
9. Bei unvollständiger oder widersprüchlicher Quellenlage bleibt der letzte bestätigte Roster unverändert.
10. Ergebnis: `content/MOTOGP_ROSTER.md`; Audit-Log: `memory/MOTOGP_ROSTER_LOG.md`.

Damit kann das System beim Jahreswechsel 2026 → 2027 und in späteren Jahren selbstständig auf bestätigte Fahrer- und Teamwechsel reagieren, ohne dass Content-Prompts jährlich manuell umgeschrieben werden müssen.

---

## 3. Recherche & Inspiration

- Apify ist Hauptquelle für Instagram/Facebook/YouTube-Social-Recherche.
- Bright Data bleibt gezielter Fallback für fehlende/nicht unterstützte Quellen.
- Gemini fasst quellengebundene Daten zusammen.
- Bei zu wenig Social-Evidenz kann Google Search Grounding öffentliche Quellen ergänzen.
- Ergebnisse: `memory/INSPIRATION_IDEAS.md` plus Archive/Debug-Dateien.
- Reale Fahrer-, Team- und Rennbehauptungen benötigen belegbare Quellen; keine erfundenen URLs/Zahlen.

---

## 4. Veröffentlichungs-Pipeline

Publisher vorhanden für Instagram Posts, Stories, Reels, Karussells sowie Facebook Posts/Karussells.

**Facebook-Video-Fix 15.09.2026:** Der Facebook-Publisher erkennt jetzt freigegebene `Video:`-Medien und lädt sie als echtes Facebook-Video hoch, statt bei vorhandenem Video versehentlich nur einen Text-Feed-Post zu erzeugen. Ein fehlgeschlagener Video-Upload darf nicht als `[GEPOSTET]` markiert werden. Der korrigierte Pfad wurde mit dem Red-Bull-Ring-MP4 erfolgreich bestätigt; Video-ID `1061438430139436`.

Alle Publisher bleiben an `Status: FREIGEGEBEN` und Publication-Claims gebunden. Erfolgreiche Veröffentlichungen werden mit Zeitpunkt und Plattform-ID dokumentiert.

---

## 5. Medien & Musik

- Agnes-Medienpipeline für Bilder/optionale Videos/Karussells.
- Reale Rennfahrer und Rennszenen dürfen nicht als vermeintlich echte KI-Aufnahmen ausgegeben werden.
- Music Agent mischt freigegebene Reel-/Story-Videos mit geeigneter lokaler Musik, validiert Video+Audio und veröffentlicht selbst nichts.
- Gemischte Medien werden erst durch den jeweiligen Plattform-Publisher veröffentlicht.

---

## 6. Analytics, Viral Learning & Follow-Analyse

- Instagram-/Facebook-Insights und Performance-Berichte.
- Viral Patterns, Hooks, Growth- und Funnel-Auswertung.
- Follow Analyzer untersucht ausschließlich konfigurierte öffentliche Profile; keine privaten Follower-/Likerlisten und keine Interaktionen.
- Erkenntnisse dürfen Content priorisieren, aber keine Veröffentlichung selbst freigeben.

---

## 7. Sicherheits- und Freigabenetz

```
Recherche / Idee
→ Entwurf
→ Telegram
→ ausdrückliche Freigabe
→ FREIGEGEBEN
→ Publication-Claim
→ Publisher
→ Plattform-ID / Analytics
```

- Keine automatische Veröffentlichung allein aufgrund von Trends, Roster-Updates oder Agentenempfehlungen.
- Keine erfundenen Transfers oder Fahrerlisten.
- Ein unklar abgebrochener Publication-Claim wird nicht blind erneut gesendet.
- Gemeinsame GitHub-Actions-Sperren schützen Publikationsdateien vor konkurrierenden Schreibzugriffen.
- Keine Käufe, Buchungen oder Anmeldungen durch Recherche-Agenten.
- Zugangsdaten ausschließlich als Secrets.

---

## Wichtige Dateien

| Bereich | Datei/Ordner |
| --- | --- |
| Freigabeplan | `content/PUBLISHED.md` |
| Daily Ideas | `generate_ideas.py`, `content/CONTENT_PLAN.md` |
| Wochenplan | `weekly_plan.py`, `content/WOCHENPLAN.md` |
| MotoGP-Roster | `content/MOTOGP_ROSTER.md` |
| Roster-Updater | `motogp_roster_updater.py` |
| Roster-Workflow | `.github/workflows/motogp-roster-update.yml` |
| Roster-Audit | `memory/MOTOGP_ROSTER_LOG.md` |
| Agenten | `agents/` |
| Inspiration | `inspiration/`, `memory/INSPIRATION_IDEAS.md` |
| Regeln | `rules/` |
| Medien | `assets/` |
| Workflows | `.github/workflows/` |

---

## Aktuelle technische Prioritäten

1. Ersten echten Lauf des neuen MotoGP-Roster-Updaters prüfen und `content/MOTOGP_ROSTER.md` erzeugen lassen.
2. Bei Saisonübergängen besonders beobachten, ob die offizielle vollständige Aufstellung bereits bestätigt ist; bis dahin muss der alte bestätigte Roster erhalten bleiben.
3. Follow-Analyse-Anbieterfehler weiter stabilisieren.
4. Qualität und Kosten der externen Recherchequellen beobachten.
5. `content/PUBLISHED.md`-Historie separat auf Vollständigkeit prüfen/reparieren, ohne aktuelle Publication-Claims oder neue Einträge zu verlieren.

---

## Was bewusst nicht behauptet wird

- Webquellen sind nicht immer gleichzeitig aktuell; deshalb Crosscheck und Fail-closed-Verhalten.
- Ein Transfergerücht reicht niemals für eine automatische Roster-Änderung.
- Ein grüner Workflow ersetzt keine Quellenqualität.
- Roster-Aktualisierung bedeutet nicht automatische Veröffentlichung.
- Social-Media-Reichweite und Likes können optimiert, aber nicht garantiert werden.

---

## Leitbild

> **„Bülent entscheidet. Das System hält Wissen aktuell, recherchiert selbstständig, lernt aus belegten Ergebnissen und veröffentlicht nur nach Freigabe.“**
