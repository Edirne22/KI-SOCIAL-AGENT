# Seed-Kandidaten

## Direkt relevant
- prompts.chat Prompt Builder Agent: Muster „erst ähnliche Beispiele suchen, dann neuen Prompt bauen“; für unsere Candidate-Revision-Pipeline interessant.
- prompts.chat skill-lookup: Registry-Suche → Skill vollständig holen → Dateien prüfen/installieren; Vorlage für PromptSkillAdapter.
- Evidence-first verification / Research-Claims-Source-Quality: für Racing Fact-QM.
- Modular delivery / stable fit points: für unsere Adapter-/Handoff-Architektur.
- Chained execution: Ziel → zerlegen → ausführen → verifizieren → fortsetzen; passt zum Staffellauf.
- Context handoff: Entscheidungen/Constraints/Risiken verlustarm zwischen Agenten übergeben.
- Guardrail workflow: Grenzen/Risiken/Scope während mehrstufiger Jobs explizit halten.
- Signal review: unstrukturierte Inputs in nächste Aktion überführen; DiscoveryAgent.

## Zweite Suchwelle
- social media hooks/captions
- video storyboard
- image/video generation prompts
- code review/testing automation
- API integration/retry/recovery
- documentation/handover

Die Kandidaten sind Research-Material, keine produktiven Skills.


## Externer Skill-Fund: linkedin-agent-skill (MIT) – 30.09.2026

Quelle/Upstream: `Jakeschincariol/linkedin-agent-skill`.
Nicht als LinkedIn-Lösung übernehmen, sondern folgende vier Muster gegen unsere bestehenden Agenten evaluieren:

### 1. Bülent Voice Profile
- Prinzip aus `templates/voice.md`: eigene Beispieltexte → Ton, Satzlänge, typische Wörter, No-Gos.
- Ziel: versioniertes gemeinsames Style-Profil für Writing, Captions, Replies und später Voice/Avatar-Moderator.
- Bestehenden Bülent-/Edirne-22-Stil nicht ersetzen, sondern strukturieren und messbarer machen.

### 2. Writing Finalizer / Humanizer-QM
- AI-Floskeln, untypische Formulierungen und Formatierungsartefakte vor Preview erkennen.
- Gegen Bülent Voice Profile prüfen.
- Keine behauptete „AI-Erkennungsquote“ als Qualitätswahrheit verwenden.
- Darf Fakten nicht umschreiben oder neue Fakten erfinden.

### 3. Repurpose Agent
- Ein verifiziertes Fakten-/Content-Paket in mehrere Formate ableiten.
- Beispiel: Racing-Story → Reel + IG/FB-Post + Carousel + Story + YouTube Short + X-Variante.
- Alle Ableitungen referenzieren dasselbe geprüfte Faktenpaket; kein erneutes freies Erfinden pro Plattform.

### 4. Plan + Audit
- Editoriale Planung mit späterer Performance-Auswertung verbinden.
- Anschluss an geplanten `InstagramInsightsAdapter → PerformanceLearningAgent → EditorialMemory`.
- Performance erzeugt Hypothesen/Candidate Skill Revisions, aber keine stille Selbstmutation produktiver Prompts.

### Gate
Upstream-Dateien vor echter Übernahme einzeln auf Inhalt, Lizenz, Prompt-Injection-/Guardrail-Risiken und Überschneidungen mit vorhandenen Edirne-22-Agenten prüfen. Nur nach Adapter-/Skill-Anpassung + Regression + Red-Team + Positive Control freigeben.


## Guide-Kollektion – Triage 30.09.2026

### A – hoher Nutzen / in Skill-Radar aufnehmen

#### YouTube Agent Skills – Jakeschincariol/youtube-agent-skill (MIT laut Guide)
Interessante Muster:
- `yt-script`: Idee → mehrere Hooks → bewertetes Skript.
- `yt-package`: Titel + Thumbnail als gemeinsames Paket prüfen.
- `yt-edit`: Transkript → Schnittliste/Timecodes/Füllwörter.
- `yt-retention`: Retention-Daten → konkrete Drop-off-Stellen.
- `yt-shorts`: Longform → bereits enthaltene Short-Kandidaten.
- `yt-viral`: Erfolg relativ zum eigenen Kanal statt pauschaler Viral-Behauptungen.
- `yt-audit`: Kanalprüfung mit priorisiertem nächsten Fix.
Edirne-22-Zuordnung: Blocks 5/6/9 + PerformanceLearning. Gegen SupoClip/OpenChatCut/unsere Writing- und Learning-Agenten vergleichen, keine Doppelentwicklung.

#### Instagram Skills – sergebulaev/instagram-skills (MIT laut Guide)
Kandidaten:
- Caption Writer
- Carousel Planner
- Hook Extractor
- Humanizer audit
- Content Planner
Hashtag Strategist nur als Vergleich; bestehende Racing-/Series-Hashtag-Regeln bleiben übergeordnet.
Edirne-22-Zuordnung: Block 5 Creative Director/Writing + Block 8 End-QM + Block 9 Planung.
Publora nicht automatisch übernehmen; bestehender Publisher bleibt führend.

#### Playbook-Prinzip
Muster: Ablauf + Artefaktablage + überprüfbare Definition-of-Done-Checkliste.
Fehler werden dauerhaft im Playbook/Skill korrigiert statt nur im Chat.
Edirne-22-Zuordnung: Querschnitt über alle Blocks. Sehr kompatibel mit PROJECT_GUARDRAILS + Staffellauf + versionierter Skill-Registry.
Wichtig: Änderungen als Candidate Revision, nicht unkontrollierte Selbstmutation.

#### LUPE / Evidence Guard
Nützliche Regeln: keine erfundenen Quellen/Zahlen/Zitate, Unsicherheit lokal kennzeichnen, Aktualität nachschlagen, belegkritischer Selbstcheck, falschen Nutzerannahmen widersprechen.
Edirne-22-Zuordnung: Block 4 Research/Facts + End-QM.
Nicht als bloßen Prompt behandeln: soweit möglich deterministische Source-Fact-Contracts, Claim-Evidence-Coverage und Regression beibehalten. LLM-Selbstcheck ist nur zusätzliche Schicht.

#### Scrapling – Web Discovery Kandidat
Open-Source-Web-Extraction/MCP laut Guide; öffentliche Webseiten strukturiert auslesen.
Edirne-22-Zuordnung: Block 3 Discovery als möglicher `WebExtractionAdapter`.
PoC gegen bestehende Apify/RSS/API-Wege: Stabilität, JS-Seiten, Rate Limits, ToS/robots, Ressourcenbedarf, Retry/Recovery, Datenqualität.
Kein Einsatz zum Umgehen von Logins/Zugriffskontrollen oder zum Sammeln personenbezogener Daten.

### B – sinnvoll, aber größtenteils bereits abgedeckt
- prompts.chat: bereits eigener PromptSkillAdapter-/Registry-Seed in diesem PR.
- Social/Composio: bereits im IDEA_POOL als möglicher Insights-/Meta-Adapter + PerformanceLearning vorgemerkt.
- LinkedIn Skills: Voice/Humanizer/Repurpose/Plan/Audit bereits als übertragbare Muster aufgenommen; LinkedIn-spezifische Funktionen derzeit keine MVP-Priorität.
- ADHS-Skill: UX-Prinzip „Handlung zuerst, konkreter nächster Schritt“ interessant für Betriebsleiter-/Statusausgaben, aber kein eigener Produktionsagent nötig.

### C – WATCH / separat verifizieren
- Experiential Labs / behauptete Promo-Modelle: nur Provider-Radar. Preise, Modellnamen, Verfügbarkeit, Datenschutz und Anbieterherkunft live verifizieren, bevor LLMRouterAdapter geändert wird. Keine Architekturabhängigkeit aufgrund einer Gratisaktion.

### Cross-Guide-Erkenntnis
Mehrere unabhängige Skill-Pakete wiederholen dieselben Rollen: Voice Profile, Hook, Humanizer, Planner, Repurpose, Audit/Performance, Comment/Reply. Diese Rollen deshalb nicht pro Plattform duplizieren. Ziel sind **plattformneutrale Edirne-22 Core Skills** plus dünne Plattformprofile/Adapter.
