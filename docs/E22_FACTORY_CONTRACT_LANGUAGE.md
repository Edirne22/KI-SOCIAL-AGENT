# E22-FCL – Edirne 22 Factory Contract Language

**Status:** verbindliche interne Fabriksprache  
**Version:** `E22-FCL-1.0`

## Zweck
Alle Agenten, Betriebs-/Produktionsleitung, QM-Rollen und Maschinenadapter lesen und schreiben denselben revisionsgebundenen JSON-Vertrag. Natürliche Sprache bleibt Nutzer-/Briefing-Eingang; rohe Tool-Kommandos sind ausschließlich Sache deterministischer Adapter.

```text
Menschensprache
→ Agent / Creative / Production
→ E22-FCL
→ validierter Maschinenadapter
→ FFmpeg | Remotion | Whisper | OpenCode | weitere freigegebene Maschine
→ Evidence in E22-FCL
→ QM
```

## Pflicht-Envelope
Jeder ausführbare Vertrag enthält mindestens:
- `schema: "E22-FCL-1.0"`
- `task_id`, `contract_revision`, `producer_role`, `consumer_role`
- `capability` und `machine_target`
- `inputs` mit autorisierten Referenzen/Hashes statt privaten Rohdaten in Logs
- `intent` / gewünschtes Ergebnis
- `constraints`: Format, Privacy, Kosten, Laufzeit/Timeout, Plattform/Seitenverhältnis soweit relevant
- `operations`: geordnete, typisierte Operationen mit IDs; keine freien Shell-Fragmente
- `expected_evidence`: prüfbare Sollnachweise
- `lifecycle`: `wake_required`, benötigte Ports/Readiness und Zielrevision soweit Containerarbeit nötig
- `failure_policy`: fail-closed, erlaubte sichere Readiness-Retries, keine blinden nicht-idempotenten Wiederholungen

Nicht relevante Felder sind explizit `N/A`/leer gemäß Schema, nicht durch versteckte Defaults ersetzt.

## Sprachregel
1. Agent↔Agent und Agent↔Betriebsleitung sprechen ausschließlich E22-FCL für ausführbare Aufträge.
2. Agent↔Maschine geht ausschließlich über einen freigegebenen Adapter.
3. Kein Fachagent erfindet rohe FFmpeg-CLI-, Remotion-JS-, Shell-, HTTP-, Whisper- oder OpenCode-Befehle als Übergabevertrag.
4. Adapter übersetzen deterministisch E22-FCL → Maschinensprache und Maschinenevidence → E22-FCL.
5. Unbekannte Operation/Feld/Version => `UNSUPPORTED_CONTRACT`; keine stille Interpretation.
6. Capability fehlt => `CAPABILITY_GAP`; Anforderung bleibt im Vertrag sichtbar.
7. Änderungen erzeugen neue `contract_revision`; keine Mischrevisionen.
8. QM prüft Sollvertrag gegen Adapter-/Render-Evidence derselben Revision.

## Medien-Vokabular
Medienverträge dürfen u. a. typisierte Felder verwenden: `scene`, `story_beat`, `asset_role`, `duration_policy`, `effect`, `transition`, `reframe`, `speed_policy`, `overlay`, `caption`, `keep_audio`, `dialogue_trim`, `music_cue`, `ducking`, `sfx_cue`, `look_target`, `continuity_group`, `variant_target`.

## Adapter
- **FFmpeg adapter:** E22-FCL-Medienoperationen → validierte Filter-/Codec-/Timeline-Argumente.
- **Remotion adapter:** E22-FCL-Szenen/Animationen → freigegebene Komponenten/Props.
- **Whisper/ASR adapter:** E22-FCL-ASR-Auftrag → festes Runtime-Requestschema; Transkript-Evidence zurück.
- **OpenCode adapter:** E22-FCL-Coding/Analyseauftrag → begrenzter freigegebener Executor-Vertrag.
- Weitere Maschinen benötigen vor Nutzung einen Adapter mit Positiv-/Negativ-/Regressionstest.

## Container-Lifecycle
Wenn `lifecycle.wake_required=true`: **Wake/Warmup → Port-Readiness → Dienst-/Zielrevisions-Health → Operation genau einmal**. Nach Deploy/Destroy/Restart erneut Wake. HTTP 200 ohne erwartete Readiness/Revision ist kein PASS.

## Mehrsprachigkeit
Agenten dürfen Nutzerbriefings in Deutsch, Türkisch oder anderen unterstützten Sprachen verstehen. Die **ausführbare Semantik** wird jedoch in E22-FCL normalisiert; Feldnamen, Enum-Werte und Operation-IDs bleiben sprachunabhängig und versionsstabil.
