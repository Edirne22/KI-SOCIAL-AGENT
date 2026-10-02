# AGENTS.md – Arbeitsregeln für KI-Agenten

**Verbindliche Priorität:** [PROJECT_GUARDRAILS.md](PROJECT_GUARDRAILS.md), danach aktueller tatsächlicher Code, [MASTER-SNAPSHOT.md](MASTER-SNAPSHOT.md) und aktuell ausdrücklich erteilte Bereichsfreigaben. Historische Übergaben oder diese kurze Agentenhilfe dürfen gültige neuere Regeln nicht aufheben. [Rollen und Hierarchie](docs/AGENCY_ORG_AND_HANDOFF.md); [Agentenindex](agents/AGENTS_INDEX.md).

## Ausgabe-Regeln (bestehende Arbeitspräferenz)

1. Die nächste konkrete Aktion erkennbar machen.
2. Mehrstufige Aufgaben mit nachvollziehbaren Schritten darstellen.
3. Fehler mit Ursache, Lösung und Nachweis berichten, statt auf wiederholte Startimpulse zu warten.
4. Fachlich wichtige Ergebnisse und tatsächliche Blocker klar kennzeichnen.
5. Übersichtlich bleiben; keine ungeprüften Erfolgs- oder Dauerbetriebsbehauptungen.

## Projekt-Regeln

- Sprache: Deutsch. Niemals Credentials, private Rohmedien oder Autorisierungstokens in Commits, Logs, öffentliche Issues oder ungenehmigte externe Dienste geben.
- Vor Änderungen aktuelle HEAD, relevante offene PRs, bestehende Komponenten, Guardrails und Zielverträge lesen. Kein doppelter Parallel-Branch für schon in Arbeit befindliche Funktionen.
- Branch/PR, CI, Regression, positive und negative Kontrollen, Red-Team und ggf. isolierter echter End-to-End-Test sind Pflicht. **Für ausdrücklich freigegebene Entwicklungsblöcke gilt die technische Build-/Merge-/Deploy-Vollmacht nach Guardrails; sonst muss die jeweils notwendige Freigabe vorliegen.** Kein direkter produktiver Eingriff allein aufgrund eines Modellvorschlags.
- Bei Tests rot: Logs → Root Cause → kleinster fachlich korrekter Fix → Regression → CI → Kontrolle. Keine Tests oder Source-Fact-/Security-Gates zur Erzeugung eines grünen Status umgehen. Für `/BLOCKRUN` keinen Zwischenstatus als freiwilliges Arbeitsende behandeln; keine angebliche Hintergrundarbeit ohne reale Ausführung.
- Kein eigenständiger Social-Publisher, keine aus Agententext abgeleitete Freigabe, keine neuen Ausgaben oder Verträge ohne Bülents ausdrücklich passende Erlaubnis. Private Fotos/Stimmen bleiben bis zum separat autorisierten sicheren Intake ausgeschlossen.
- Historisch besonders geschützte Projektbereiche wie `debug/motogp-pipeline-output` und `memory/MEMORY_EVENTS.jsonl` nicht beiläufig verändern. Die bestehende Fünfer-Batch-Regel nicht ohne ausdrückliche spezielle Freigabe ändern.

## Zielarchitektur

**Eine** KI-Zentrale koordiniert die 24/7-Content-Fabrik und die unabhängig beauftragbare universelle KI-Werkstatt. Der gemeinsame Produktionsleiter verteilt Aufträge über klare Job-/Revisions- und Maschinen-Handoff-Verträge; der deterministische Ressourcenmanager soll freigegebene Kapazitäten verwalten. Research, eigene Redaktion, tatsächlich getestete Media-/Audio-Adapter, unabhängiges QM, privates R2, Goldenes Tablett und Human Authority bleiben getrennte Stufen. Scout → Research/Security → Integrationsingenieur → unabhängige Abnahme → geprüftes Werkzeug-Memory ist der rückgekoppelte Verbesserungsprozess.

`OmniRoute` bleibt gegenwärtig PAUSED, **keine** zwingende VPS-/Gateway-Abhängigkeit. Vorhandenen funktionsfähigen FFmpeg-/direkten Provider-/R2-Weg nicht für ein ungeprüftes neues Tool blockieren. Ein Rollenpapier oder Modellkatalog beweist weder 24/7-Laufzeit noch kostenlos nutzbare Inferenz. Nur tatsächlich gemessene/abgenommene Fähigkeiten als LIVE ausweisen.
