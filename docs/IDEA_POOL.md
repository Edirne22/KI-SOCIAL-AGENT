# 💡 MASTER-IDEENPOOL – KI-SOCIAL-AGENT

**Version:** 2.0  
**Stand:** 2026-09-29  
**Zweck:** Eine einzige lebende Roadmap für Ideen, Ausbau, Experimente und bereits erledigte Vorhaben.

> **Pflegeregel:** Vor jeder größeren neuen Ausbaustufe diesen Master-Ideenpool prüfen. Neue Funde hier einordnen statt neue Ideenpool-Dateien anzulegen. Erledigte Punkte abhaken/ins Archiv verschieben; verworfene Ideen mit Grund markieren. Der Pool ist Werkzeugkasten und Projektgedächtnis, kein Zwang.

> **Guardrail:** `PROJECT_GUARDRAILS.md` bleibt für produktive Änderungen bindend. Externe Frameworks dürfen Racing-/Source-Fact-/Semantic-/Writing-/Chief-QM nicht umgehen oder abschwächen.

## Status-Legende
- 🔴 **P0** = aktueller Produktions-/Qualitätsblocker
- 🟠 **P1** = als Nächstes untersuchen/bauen
- 🟡 **P2** = geplant nach P1/Stabilisierung
- 🟢 **P3** = später / nach VPS
- ✅ = erledigt bzw. bereits produktiv vorhanden
- ⏸️ = bewusst pausiert
- ❌ = verworfen/nicht relevant

---

# 1. SCHLACHTPLAN

## 🔴 P0 – Racing-Produktion wasserdicht halten

**Aktueller Stand 29.09.2026:** Racing-Pipeline V8.5.x wurde seit dem alten Pool massiv gehärtet. Source-Fact-Contract, Series-/Session-/Entity-/Claim-Strength-Gates, Human-Writing-Gate, Semantic DEGRADED-PASS, Final Guard, Quality Lab, Red-Team und Positivkontrollen sind vorhanden.

- [x] Source-Fact-Contract / claim-basierte Faktenprüfung
- [x] Series-/Session-Locks und Final Guard
- [x] Claim-Strength-Schutz gegen Unsicherheit → falsche Gewissheit
- [x] Human-Writing-Gates für bekannte schlechte Formulierungen
- [x] Quality Lab + Production Adapter + Red-Team/Positive Controls
- [x] Türkische Rider T1–T5 mit eigener Relevanzschicht
- [x] Telegram natürliche Racing-Archivabfragen inkl. Alias-/Tippfehlerarbeit
- [ ] Aktuelle Produktions-Abnahme vollständig abschließen (Run #144, MIT HAKEN)
- [ ] Weiterhin: jeder neu gefundene Halluzinations-/Sprachfehler wird permanente Regression
- [ ] Telegram-QM-Transparenz prüfen: PASS vs Semantic DEGRADED-PASS sichtbar unterscheiden

## 🟠 P1 – Audio/Voice + Publishing nicht neu erfinden

### P1A – Pipecat: Audio-/Sprachstufe
**Repo:** `pipecat-ai/pipecat`  
**Ziel:** Prüfen, ob Pipecat die Infrastruktur für unsere geplante Audio-/Voice-Stufe liefert.

Geplante Kette:
`Telegram Voice / Video / Interview → Audio-Ingest → Pipecat/STT → Transkript → Rider/Themen-Erkennung → bestehender Racing/Research-Stack → bestehende QM`

Zu untersuchen:
- [ ] STT/TTS-Provider und lokale/self-hosted Optionen gegen Nemotron ASR / Magpie TTS vergleichen
- [ ] WebSocket/WebRTC/Streaming nur dort einsetzen, wo Echtzeit echten Mehrwert hat
- [ ] Telegram-Sprachnachricht als erster kleiner Spike
- [ ] YouTube/Interview-Audio → Transkript → Zeitmarken → relevante Racing-Passagen
- [ ] Multi-Agent/Parallel-Pipeline-Patterns prüfen
- [ ] Failure Modes: unverständliches Audio, falsche Sprache, Rider-Verwechslung, Halluzinationsrisiko aus Transkript
- [ ] Lizenz-/Update-Strategie dokumentieren
- [ ] Kein Ersatz der Racing-QM: Transkript ist Quelleingang, nicht Wahrheit

### P1B – Postiz: Publisher/Scheduling
**Repo:** `gitroomhq/postiz-app`  
**Ziel:** Prüfen, ob Postiz als getrenntes Self-Hosted Publishing-Backend Monate Eigenentwicklung spart.

Zielarchitektur:
`Edirne-22 Content/QM → Telegram-Freigabe → dünner Postiz-Adapter → Instagram / Facebook / TikTok / später weitere Plattformen`

Zu untersuchen:
- [ ] Public API und Webhooks
- [ ] Instagram-/Facebook-/TikTok-Provider gegen unsere vorhandenen Adapter vergleichen
- [ ] Scheduling/Kalender/Queue/Retry/Token-Refresh analysieren
- [ ] Analytics-Rückkanal prüfen
- [ ] Fehler- und Idempotenzverhalten beim Publishing vergleichen
- [ ] Self-Hosted VPS-Ressourcen/Kosten prüfen
- [ ] **AGPL-3.0 beachten:** bevorzugt getrennte Instanz + API-Adapter; keinen Postiz-Code blind in dieses Repo kopieren
- [ ] Proof-of-Concept erst nach Architektur-/Lizenzvergleich

---

## 🛡️ P1 ISOLIERTER ARCHITEKTUR-/RED-TEAM-ABNAHMEVERTRAG

**Zweck:** Pipecat/Postiz werden erst produktiv verdrahtet, wenn ein isolierter Spike diese Angriffe und Positivkontrollen nachweisbar besteht. Externe Frameworks sind Transport/Orchestrierung, niemals Wahrheitsinstanz.

### Muss-PASS – Positivkontrollen
- [ ] **Audio Happy Path:** verständliche DE/TR-Sprachnachricht → korrektes Transkript mit Sprache/Zeit/Quelle → bestehende QM → Telegram-Freigabe.
- [ ] **Publisher Happy Path:** bereits freigegebener Post → genau einmal geplant/veröffentlicht → externe Post-ID + interner Status nachvollziehbar.
- [ ] **Restart/Retry:** Neustart zwischen Freigabe und Publish erzeugt keinen Doppelpost.

### Muss-BLOCK/FAIL-CLOSED – Red-Team
- [ ] **Transkript-Manipulation:** erfundener Rider, Team, Zahl, Ort, Serie oder Vertragsstatus darf aus Audio nicht zur Tatsache werden.
- [ ] **Unsicheres Audio:** niedrige STT-Konfidenz/unklare Passage darf nicht stillschweigend geglättet oder erfunden werden; markiert/erneut transkribiert/manuell geprüft.
- [ ] **Cross-Language:** DE/TR/EN-Fragmente dürfen Namen, türkische Diakritika oder Claim-Stärke nicht verändern.
- [ ] **Provenienzverlust:** kein Racing-Claim ohne rückverfolgbare Quelle/Audio-ID/Zeitraum bzw. vorhandenen Source-Fact-Beleg.
- [ ] **QM-Bypass:** weder Pipecat noch Postiz dürfen direkt von Discovery/Transkript zu Publish springen.
- [ ] **Approval-Bypass:** ohne gültige Telegram-/Approval-Freigabe kein Publish.
- [ ] **Replay/Double-Publish:** identischer Approval-/Webhook-/Retry-Event darf höchstens einmal extern publizieren; Idempotency-Key/External-ID erforderlich.
- [ ] **Wrong Destination:** IG-Inhalt darf nicht durch Mapping-/Retry-Fehler auf falschem Account/Netzwerk landen; Zielkonto ist Teil des Approval-Vertrags.
- [ ] **Token/API-Ausfall:** 401/429/5xx/Timeout → kontrollierter Retry/Block, niemals künstliches SUCCESS.
- [ ] **Partial Success:** Plattform A erfolgreich, B fehlgeschlagen → Status pro Plattform; kein globales falsches PASS und kein Doppelpost auf A beim Retry.
- [ ] **Webhook Spoof/Replay:** eingehende Webhooks authentisieren/verifizieren und Replay-Schutz vorsehen.
- [ ] **Framework-Ausfall:** Pipecat/Postiz down → bestehende Racing-QM bleibt intakt; keine Fakten-/Freigabe-Abkürzung als Fallback.
- [ ] **Lizenzgrenze:** Postiz bleibt getrennte AGPL-Komponente/API-Grenze, bis eine bewusste Lizenzentscheidung dokumentiert ist; keine versehentliche Codekopie.

### Evidence / Release Gate
Für einen P1-POC müssen mindestens diese Evidenzen **PASS** sein:
`architecture_contract`, `positive_control`, `hallucination_attack`, `provenance`, `approval_gate`, `idempotency`, `provider_outage`, `partial_failure`, `security_webhook`, `license_boundary`, `runtime_e2e`.

Fehlende Evidenz zählt als **BLOCK**, nicht als PASS. Jeder im Spike gefundene neue Fehler wird als permanente Regression aufgenommen. Erst danach darf eine produktive Integration zur Merge-Freigabe vorgelegt werden.

# 2. P2 – MEMORY, ORCHESTRIERUNG UND ENTWICKLUNG

## 🟡 AnythingLLM – Memory/RAG-Kandidat
**Repo:** `Mintplex-Labs/anything-llm`
- [ ] Gegen heutiges Memory, OpenViking und Nemotron Embeddings vergleichen
- [ ] Rider/Event/Source/Community-Memory evaluieren
- [ ] Nutzen für natürliche Abfragen wie „letzte 14 Tage über Toprak/Ai Ogura/Alex Rins“ messen
- [ ] Dokument-/Knowledge-Ingestion und lokale Modelle prüfen
- [ ] Keine Migration ohne messbaren Retrieval-Vorteil

## 🟡 CrewAI – Orchestrierungs-Referenz
**Repo:** `crewAIInc/crewAI`
- [ ] Handoffs, parallele Agenten, Retry/State/Observability untersuchen
- [ ] Gegen bestehende Kette Scout → Research → Fact-QM → Editor → Chief-QM → Publisher → Engagement vergleichen
- [ ] Nur Patterns übernehmen; funktionierenden Racing-Stack nicht ohne Nutzenbeweis migrieren

## 🟡 Cline – Entwicklungswerkzeug
**Repo:** `cline/cline`
- [ ] Als CLI/IDE-Agent für Laptop/VPS prüfen
- [ ] Gegen vorhandenen Claude/Codex/GitHub-Workflow vergleichen
- [ ] Kein Runtime-Baustein des Racing-Agenten

---

# 3. DISCOVERY-/RESEARCH-SCHICHT

## Bereits bekannte Fundgrube
- [ ] `browser-use/browser-use`: Browser-Automation nur für zulässige externe Recherche; **nicht** als Meta-Bot
- [ ] `yenanjing/awesome-harness-engineering`: Production-Agent-Patterns als Referenz
- [ ] `Threesided-Studios/Agent-Memory`: Memory-Inspiration
- [ ] `volcengine/OpenViking`: Memory + Knowledge + Skills nach VPS vergleichen
- [ ] `cathrynlavery/diagram-design`: Nice-to-have für Architekturdiagramme
- [x] Godmode-Patterns selektiv ausgewertet: Root-Cause-Debugging, Completion Verification, Agent Evaluation, Behavior Validation, Evidence Map, Mutation/Red-Team – passende Konzepte bereits in Quality-Lab/Arbeitsweise übernommen

## Social-/Realtime-Discovery
- [ ] **RSS-first:** Racing-RSS vor HTML-Crawling nutzen
- [ ] Strukturierte MotoGP-/WorldSBK-Ergebnis-/Timing-Daten prüfen
- [ ] Telegram: türkische Racing-News-/Fan-Kanäle als zusätzliche Discovery-Quelle evaluieren
- [ ] X/Twitter: nur optionale Discovery-Schicht; keine Primär-Faktenquelle
- [ ] Instagram: offizielle Schnittstellen bevorzugen; Apify/RapidAPI nur optional nach Kosten/Zuverlässigkeit/Datenschutz
- [ ] Event-Klassifizierung: CRITICAL / RESULT / SESSION / CAREER / DISCOVERY / GENERAL
- [ ] Racer Registry ausbauen: Startnummer, Serie/Team, Historie, Aliase, Quellenbeleg, `verified_at`
- [ ] 1–2 Wochen Produktionsdaten als Grundlage für neue Discovery-Entscheidungen sammeln

---

# 4. MEMORY / MULTI-KI / QUALITY

## Multi-KI Cross-Check
Ursprüngliche Kandidaten: `claudelink-bridge`, `ai-relay`, `clipboard-ai-mcp`, `llm-council-no-api`, `cross-review`, `codeagora`, `Triumvirate`, `llm-panel`.

- [x] Multi-Modell-Prinzip inzwischen teilweise produktiv: Agnes → Gemini/NVIDIA Provider-Fallback; Quality Lab / advisory Jury vorhanden
- [ ] Echte providergebundene 3-Modell-Jury später kontrolliert live verdrahten; deterministische Gates bleiben vorrangig
- [ ] Browser↔lokaler Coding-Workflow nur weiterverfolgen, wenn er gegenüber GitHub/Codex/Claude real Zeit spart

## Memory
- [x] Community-/Racing-Memory-Grundlagen vorhanden
- [ ] Expert Agent Memory weiter ausbauen
- [ ] Memory Embedding mit Nemotron prüfen
- [ ] AnythingLLM ↔ OpenViking ↔ Eigenbau ↔ Embeddings benchmarken
- [ ] Source-Memory mit Provenienz und Alter/verified_at stärker strukturieren

---

# 5. SOCIAL / ENGAGEMENT / PUBLISHER

## Instagram
- [x] Reply Adapter vorhanden
- [x] `reply_draft` beim ingest() inzwischen umgesetzt
- [x] Telegram-Freigabe vor Antworten
- [ ] Echte Tickets weiter gegen info → memory → antwort/ändern prüfen
- [ ] Erwähnungen über Webhooks/VPS
- [ ] Story Replies separat testen
- [ ] Tagged Media nur bei messbarem Nutzen

## Facebook
- ⏸️ Engagement wegen Berechtigungs-/Token-Thema pausiert; bei Postiz/Meta-Neubewertung erneut prüfen

## DM-Automation – nach VPS
Nur offizielle Meta API / Business/Creator + OAuth.
1. Kommentar-Trigger → DM
2. FAQ-DM-Assistent
3. Content-Analytics
4. Lead-Magnet
- [ ] 24h-Regel und Webhook-Echtzeit sauber abbilden

## Publisher
- [x] Eigener Publisher grundsätzlich vorhanden
- [ ] Statusmodell READY_FOR_APPROVAL vs FREIGEGEBEN weiter konsistent halten
- [ ] Postiz P1-Vergleich entscheidet: Eigenbau behalten, Hybrid oder Postiz-Backend

---

# 6. CONTENT- UND CREATOR-AUSBAU

## Bereits erledigt
- [x] MotoGP-Reel gepostet (22.09.)
- [x] MotoGP-Karussell 12 Slides gepostet (22.09.)
- [x] BMW-App-Karussell gepostet (23.09.)
- [x] Comment Reply Assistant vorhanden
- [x] Content Quality Reviewer / Chief-QM vorhanden
- [x] Multi-Platform Caption Writer vorhanden
- [x] Daily Racing News Scanner vorhanden

## Content-Backlog
- [ ] Bikertreff-Reel Radevormwald + Biggesee
- [ ] Hagen-Biker-Treff-Reel
- [ ] M1000R-Realität-Reel
- [ ] Instagram-Patterns weiter sammeln
- [ ] TÜRKBiR beobachten
- [ ] Calimoto/Biker-App-Karussell

## Pattern-/Generator-Ideen
- [ ] Pattern 18: Content → DM → Conversion
- [ ] Pattern 19: Sicher vs Riskant
- [ ] Ziel: 20 belastbare Patterns
- [ ] Viral Hook Generator: 3–5 Varianten, erst nach stabilem Flow
- [ ] Headline A/B Generator für Karussell/Telegram
- [ ] „15 Fragen an KI vor Motorrad-Kauf“ als DE/TR-Karussell

---

# 7. AUDIO / VIDEO / MEDIA

## Vorhanden
- [x] FFmpeg-Skript für Reels
- [x] Video-/Audio-Ingestion als Projektziel und erste Runtime-Bausteine vorhanden
- [x] yt-dlp/Transkriptionsrichtung in Racing-/Video-Roadmap aufgenommen

## Kandidaten
- [ ] Pipecat – **P1, siehe Schlachtplan**
- [ ] MiniMax Audio – Voiceover
- [ ] Wan – Video-Generator evaluieren
- [ ] SadTalker – Avatar nur bei echtem Content-Nutzen
- [ ] CutAI – Agent-Videoeditor testen
- [ ] Remotion + AI Video Toolkit – nach VPS
- [ ] Cosmos/NVIDIA Video-Router nur nach Hardware-/Kostencheck

---

# 8. VPS / INFRASTRUKTUR

- [ ] VPS auswählen/einrichten; x86 bevorzugt
- [ ] SearXNG installieren
- [ ] OmniRoute auf VPS
- [ ] Audio/Voice-Layer: Pipecat vs eigener `speech_router.py`
- [ ] Video-Pipeline/Remotion
- [ ] Meta Webhooks statt Polling
- [ ] Postiz Self-Hosted POC, falls P1-Analyse positiv
- [ ] n8n nur als Workflow-Alternative benchmarken, nicht zusätzlich ohne Nutzen
- [ ] Security-Audit/Trail of Bits Skills nach VPS

---

# 9. TOOLS / SKILLS – MERKLISTE

## Bereits vorhanden
- [x] OmniRoute lokal
- [x] Planning with Files
- [x] `turkish-native`
- [x] Human Writing Protocol / Pattern Library
- [x] API-/Engagement-/Media-Dokumentation

## Prüfen
- [ ] Marketing Skills
- [ ] Stop Slop
- [ ] Context Engineering
- [ ] Superpowers – nach VPS
- [ ] Anthropic Skills für Dokumentarbeit bei Bedarf
- [ ] Expert Agent Training / yt-analysis-mcp
- [ ] YouMind / PromptCreek nur als Inspirationsquelle

## Nicht relevant / verworfen
- [x] gptcc: ChatGPT-Plus-Konstellation nicht nutzbar
- ❌ UI UX Pro Max / Impeccable
- ❌ Vercel Agent Skills
- ❌ Supabase Agent Skills
- ❌ Scientific-Agent-Skills
- ❌ Cybersecurity-Skill-Sammlung als Kernfeature
- ❌ allgemeiner Marketing Consultant / Blog SEO / LinkedIn Finder

---

# 10. OFFENE ALTPUNKTE, DIE NICHT VERGESSEN WERDEN

- [ ] Follow-Analyzer: historische 0/8-Auswertbarkeit erneut prüfen, bevor weitergebaut wird
- [ ] Community-Fallback/Fallback-Kennzeichnung gegen aktuellen Codezustand verifizieren; alte Notiz nicht ungeprüft als noch offenen Bug behandeln
- [ ] Kaestral nur bei klarem Modell-/Kostenmehrwert reaktivieren
- [ ] Router-Erweiterungen nur benchmarkbasiert
- [ ] Safety-Modell als zusätzliche Schicht prüfen, niemals als Ersatz der deterministischen Racing-Gates

---

# 11. ERLEDIGT / HISTORISCHER STAND

## 29.09.2026
- [x] PROJECT_GUARDRAILS.md als verbindliche Arbeitsregeln etabliert
- [x] Racing Quality Lab + Production Adapter + Red-Team/Positivkontrollen
- [x] Source-Fact-/Session-/Series-/Entity-/Claim-Strength-/Human-Writing-Hardening
- [x] Agius False-Positive behoben (#209)
- [x] Source-Fact-Preflight an deterministisches Fail-Closed angepasst (#210)
- [x] Pipecat, Postiz, AnythingLLM, CrewAI und Cline als neue Open-Source-Kandidaten aufgenommen
- [x] Zwei konkurrierende Ideenpools zu diesem Master zusammengeführt

## 24.09.2026 und früher
- [x] PR #78–#94 damalige Racing-Stabilisierungen
- [x] Instagram Reply Adapter
- [x] HUMAN_WRITING_PROTOCOL
- [x] docs/ENGAGEMENT_AGENTS.md
- [x] Pattern Library / Free Tools / API Referenz
- [x] Telegram Parsing-/Batch-Bugs
- [x] Approval Dashboard Stufe 2
- [x] Repo-Backup / public-apis
- [x] Wetter-/Instagram-Zwei-Stufen-Freigabe

---

# 12. VERBINDLICHE ARBEITSREGELN / NICHT VERGESSEN

1. Vor größeren neuen Features **zuerst diesen Master-Ideenpool und PROJECT_GUARDRAILS.md prüfen**.
2. Neue Ideen nicht in separaten Pool-Dateien verteilen.
3. Bei Umsetzung Status hier aktualisieren: offen → aktiv → erledigt/verworfen.
4. Externe Repos zuerst zerlegen: Lizenz, API, Failure Modes, Wartung, Ressourcen, Nutzen gegen Eigenbau.
5. Fremdcode nicht blind kopieren; Adapter/saubere Trennung bevorzugen.
6. Racing-QM bleibt unabhängig von Discovery-, Audio-, Memory- und Publisher-Frameworks.
7. Produktive Änderungen folgen immer dem Guardrail-Finish:
   **BUILD → REGRESSION → CI → RED-TEAM → POSITIVE CONTROL → ROOT-CAUSE/FIX → ATTACK AGAIN → CI GREEN → Merge-Freigabe.**
8. Der Ideenpool wird bei Projekt-Handover/Snapshot mit geprüft, damit alte gute Ideen nicht erneut vergessen werden.

**Nächster strategischer Fokus:** Produktions-Abnahme Racing abschließen → Pipecat technisch zerlegen → Postiz gegen bestehenden Publisher/API/Webhooks/Scheduling benchmarken → daraus P1-POC entscheiden.
