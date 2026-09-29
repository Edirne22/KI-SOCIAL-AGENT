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
