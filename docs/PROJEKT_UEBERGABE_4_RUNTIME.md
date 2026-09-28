# RACING RUNTIME HARDENING – 27./28.09.2026

**Stand:** 2026-09-28 (18:20 Uhr)
**Repo:** `Edirne22/KI-SOCIAL-AGENT`
**Bereich:** Racing Agency V8.5.x – Runtime, NLU, Cross-Language-Dedupe
**Ergänzung zu:** `docs/PROJEKT_UEBERGABE.md` (Teil 1)

---

## 1. Projektstand

**Racing-Pipeline aktuell V8.5.x mit:**
- MotoGP / Moto2 / Moto3
- WorldSBK / WorldSSP
- separatem Turkish-Rider-Fokus
- Source-Fact-Contract
- Series-Lock
- Racing-QM
- Semantic-QM
- Chief-QM / Final Guard
- Human Approval über Telegram
- Archiv-/Memory-Suche
- Provider-Fallback und DEGRADED-PASS

**Unverhandelbare Regel:**
> Unsupported FACT bleibt HARD FAIL.
> Provider-Ausfälle dürfen über DEGRADED-PASS behandelt werden, echte Faktenfehler nicht.

---

## 2. Arbeiten vom 27.09.2026

Am 27.09. wurde die Racing-Pipeline in mehreren Stufen weiter gehärtet.

**Schwerpunkte:**
- Turkish Rider
- Deutsche Textqualität
- Serienzuordnung
- Retry-Verhalten
- Vorbereitung natürlicher Telegram-Abfragen

**Bearbeitete Bereiche:**
- Turkish-Web-Scout/Tiefensuche
- MotoEtkinlik und türkische Quellen
- Series-Lock
- Deutsch-/Writing-Editor-Gates
- WorldSSP/Moto2-Abgrenzung
- MotoParkTV-Vertrag
- Telegram-Ausgaben
- Instagram-False-Green
- Retry-Amplification
- Provider-Defer
- Balanced Racing Gates
- Turkish Candidate Gate
- Human Approval

**PR-Serie #163–#182:** schrittweise getestet bzw. vorbereitet.
**Später #184–#193:** Editor/QM, Final Gates, Archiv, natürliche Fahrerabfragen.

**Turkish Rider – Schreibweisen:**
- Ö, Ç, Ğ, ı
- ASCII-/Fehlschreibvarianten
- Alias-/Canonical-Rider-Logik

---

## 3. Natürliche Racing-Archivsuche

Die Telegram-Suche versteht jetzt natürliche Formulierungen, z. B.:

> „gib mir alles, was du in den letzten 48 Stunden über die türkischen Fahrer gefunden hast"

> „gib mir zu der letzten 14 Tage über Alex Renz und aiogura"

**Normalisierung funktioniert:**
- `Alex Renz` → `Alex Rins`
- `aiogura` → `Ai Ogura`
- Schreibvarianten über Alias-/Canonical-Rider-Logik

### Falsche Nulltreffer (Ursache gefunden)

**Vorher:** „Racing letzte 14 Tage · Alex Rins, Ai Ogura: keine gespeicherten Treffer"
**Vorher:** „Racing letzte 14 Tage · Toprak: keine gespeicherten Treffer"

**Toprak-Ursache:**
- Archiv enthielt mehere aktuelle Toprak Razgatlıoğlu-Artikel
- Problem lag **nicht** in der Speicherung
- Problem: **NLU-/Canonical-Rider-Auflösung** – der allein eingegebene Vorname „Toprak" wurde nicht auf den vollständigen Fahrernamen erweitert

**Lösung:**
- Eindeutige Vornamen wie **Toprak** werden auf vollständigen Namen erweitert
- Mehrdeutige Vornamen wie **Can** bleiben fail-closed

---

## 4. Run #136 – entscheidende Laufzeitanalyse

**MotoGP Content Agency Run #136**
**Run-ID:** `36423212562`

**Ergebnis:** erfolgreich, aber extrem langsam.
**Hauptschritt:** ca. **1:32:07 Stunden**

### Log-Statistik

| Ereignis | Anzahl |
|---|---|
| RACING-QM PASS | 76 |
| PRIORITY-REPAIR START | 28 |
| QM → RESEARCH → EDITOR retry | 22 |
| SEMANTIC-QM TECHNICAL DEFER | 36 |
| SEMANTIC-QM DEGRADED PASS | 36 |
| JSONDecodeError | 5 |
| Editor-Exceptions | 2 |
| SemanticContractError | 28 |
| ProviderUnavailableError | 3 |
| Rohkandidaten | ~320 |
| fresh | 46 |
| current-Q | 45 |
| finale Vorschläge | 5 |

### Zwei große Zeitblöcke

1. **Discovery/Enrichment:** ca. 10:26 Minuten ohne Logausgabe (nach `RACING SCOUT WorldSBK: 55 candidates`)
2. **Semantic Provider:** ca. 8:19 Minuten zwischen Racing-QM-PASS und Semantic-QM Technical Defer

**Gesamt:** Log-Lücken ≥60 Sekunden → **ca. 39,7 Minuten**

---

## 5. Doppelte Discovery entdeckt

Run #136 führte die Discovery **zweimal nahezu vollständig** durch.

**Erste Runde:** ca. 12:40:54–12:44:54 UTC
**Zweite Runde:** ca. 12:45:23–12:48:58 UTC

**Nahezu identische Crawls:**
- TMF: 34
- AnadoluAjansi: 16
- Motoron: 155
- TRMotoSports: 294

**Vorgabe von Bülent:**
> „Round 2 darf erst entfernt werden, wenn anhand der Result-Sets bewiesen ist, dass keine relevanten zusätzlichen Ergebnisse entstehen."

**Umsetzung:** Instrumentierung eingebaut, die Round 1 und Round 2 vergleicht.

---

## 6. PR #196 – Runtime-Hardening

**PR #196** – `perf: instrument and bound Racing runtime after run #136`
**Merge-Commit:** `d7f38790e94fdba36d6f5074075d9c54e077065e`
**Status:** ✅ gemergt (15/15 CI-Checks grün)

### Änderungen

**Semantic-QM begrenzt:**
- Timeout: 12 Sekunden
- Request-Retries: 0
- Textmodell-Limit: 1
- Providerkette: Agnes → Gemini → NVIDIA

→ Ein einzelner kaputter Provider kann nicht mehr minutenlang denselben Artikel blockieren.

**Circuit Breaker:**
- Runtime-State: `total`, `success`, `technical_defer`, `degraded_pass`, `consecutive_failures`, `breaker_open`
- Nach 3 aufeinanderfolgenden technischen Fehlern öffnet der Circuit Breaker
- Danach wird der Providerpfad nicht mehr sinnlos abgefahren

**DEGRADED-PASS bleibt erhalten:**
- Provider-Ausfall ≠ Faktenfehler
- Deterministische Faktenprüfungen sauber → DEGRADED-PASS erlaubt
- Unsupported FACT bleibt HARD FAIL

**Runtime-Instrumentierung (neu gemessen):**
- Discovery
- article_info
- Freshness
- Editor/QM
- Final Selection/Media
- Gesamtlaufzeit
- langsame article_info-Calls
- Semantic Runtime Summary
- DEGRADED-PASS-Anteil

**Early Prefilter:**
- Offensichtlich irrelevant: Formula 1, WEC, alte datierte URLs
- Filter bewusst konservativ

**Toprak-Fix:**
- Eindeutige Vornamensuche
- Toprak → Toprak Razgatlıoğlu
- Can bleibt fail-closed

---

## 7. PR #197 – Content-/QM-Optimierung

**PR #197** – `fix: targeted Racing format repair and cross-language event dedupe`

#197 wurde auf aktuellen main mit #196 gebracht.
**Konflikte in:** `motogp_content_agency_v2.py`, `racing_v855_hardening.py`
**Auflösung:** #196-Runtime-Änderungen erhalten, #197-Funktionen neu angewendet.

**Nach Kombination:** 14/14 CI- und Regression-Checks GRÜN.
**Merge-Commit:** `e77c67dc909c11602c22153552e863d2bbcbeb70`

**main enthält jetzt:** #196 + #197.

---

## 8. Targeted Hashtag Repair

**Problem:**
Editor → Racing-QM → kleiner Hashtagfehler → kompletter Research-/Editor-Zyklus.

**Lösung:**
Wenn Racing-QM **ausschließlich** einen deterministischen Hashtagfehler meldet (falsche Hashtaganzahl, fehlender Fahrer-Hashtag), wird nur der Hashtagblock deterministisch repariert. Racing-QM läuft erneut.

**Regression beweist für diesen Fall:**
- Editor: 1×
- Racing-QM: 2×
- Semantic-QM: 1×
- Research-Retry: 0×

**Wichtig:** Kein QM-Gate umgangen. Bei weiterhin inhaltlichem Fehler greift normale Research→Editor-Reparatur.

---

## 9. Cross-Language Event Dedupe

**Hintergrund:**
Gleiche Racing-Ereignisse aus verschiedenen Quellen/Sprachen.

**Beispiel:**
- Türkisch: Lecuona / Bulega / Cremona / Superpole
- Englisch (WorldSBK): Lecuona / Bulega / Cremona / Superpole

Beide können dasselbe reale Event beschreiben, obwohl URL, Titel, Caption unterschiedlich sind.

**Event-Fingerprint (konservativ):**
- Serie
- Session/Eventtyp
- Fahrer
- Strecke/Ort

Nur bei ausreichend starker Übereinstimmung wird dedupliziert.

**Wichtig:** `Superpole Qualifying` ≠ `Superpole Race` – dafür existiert ein Regressionstest.

---

## 10. Aktueller Stand – Run #137

**MotoGP Content Agency Run #137**
**Run-ID:** `36449946994`
**Start:** 28.09.2026 – 18:17:24 Uhr deutscher Zeit
**GitHub-Commit:** `e77c67dc909c11602c22153552e863d2bbcbeb70`
**Läuft mit:** #196 + #197
**Status zum Zeitpunkt der Übergabe:** IN PROGRESS

**Run #137 ist der entscheidende reale Vergleichslauf.**
**Referenz:** Run #136 = ca. 1:32:07 Hauptlaufzeit

---

## 11. Was nach Run #137 ausgewertet werden muss

Nach Abschluss nicht nur grün/rot prüfen. Messwerte gegen #136 vergleichen:

1. Gesamtlaufzeit
2. Discovery-Zeit
3. Round-1-/Round-2-Ergebnisse
4. `only_round2` und Überschneidung der URLs
5. Erklärung des früheren Unterschieds MotoGP 140 → 70 Kandidaten
6. `article_info`-Laufzeit
7. Anzahl Slow Calls
8. Freshness-Zeit
9. Editor-/QM-Zeit
10. Semantic-QM-Laufzeit
11. Semantic technical defers
12. DEGRADED-PASS-Anteil
13. Circuit-Breaker-Aktivierungen
14. Provider-Ausfälle
15. Anzahl Research→Editor-Retries
16. TARGETED HASHTAG REPAIR
17. Finale Anzahl Posts
18. Cross-Language-Dedupe
19. Telegram-Ausgabe
20. Persistence/Archiv

**Wichtig:** Round 2 erst entfernen, wenn Messdaten zeigen, dass keine relevanten neuen Racing-Inhalte verloren gehen.

---

## 12. Arbeitsregel für weitere Änderungen

**Vorgehensweise:**
Log-Beobachtung → Codepfad beweisen → Regression reproduziert Problem → Code ändern → CI/Regression → realer Vergleichslauf

**Keine Optimierung darf:**
- Tests umgehen
- künstliche PASS erzeugen
- Semantic-QM abschalten
- Chief-QM abschalten
- Series-Lock schwächen
- Source-Fact-Contract schwächen
- Unsupported FACT durchlassen

**Nächstes unmittelbares Ziel:** Keine neue Feature-Runde – zunächst vollständige Auswertung von Run #137 gegen Run #136.

---

📖 NÄCHSTER TEIL:
→ Falls weitere Dateien existieren: weiterlesen
→ Sonst: ✅ ENDE DER ÜBERGABE

Diese Datei ist Teil 4 von 4.
