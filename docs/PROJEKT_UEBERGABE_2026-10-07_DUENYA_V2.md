# CHAT-/PROJEKTÜBERGABE – DÜNYA LEVEL 12 V2

**Stand:** 07.10.2026 – V1 live produziert, V2 Creative-Chain-Reparatur noch nicht gestartet
**Repo:** Edirne22/KI-SOCIAL-AGENT
**Task-ID:** `f6f50c9f4c2690e4eb1fe978`
**Arbeitsbranch:** `fix/duenya-v2-creative-chain-20261007`

## MASTER-PROMPT FÜR EINEN NEUEN CHAT
Lies zuerst `PROJECT_GUARDRAILS.md`, `SELBSTSTAENDIG_BIS_ZUM_ENDE_3.md`, `AGENTS.md`, diese Datei und `docs/AGENCY_ORG_AND_HANDOFF.md`. Arbeite danach unter /BLOCKRUN selbstständig weiter. Eine Statusmeldung ist kein Stoppsignal. Keine neuen Kosten, keine Social-Veröffentlichung und keine Offenlegung privater Medien/Prompts/Secrets. Bülent hat technische Bau-/PR-/Merge-/Deploy-Vollmacht für diese Aufgabe erteilt.

Hauptauftrag: private Geburtstagsproduktion **„Dünya – Level 12“**, ca. 300 s, 9:16, emotional/kreativ, aus vorhandenen privaten R2-Fotos/-Videos. Der Originalauftrag bleibt im privaten Dashboard-/R2-Posteingang und MUSS zur Laufzeit anhand der Task-ID geladen werden; Prompttext nicht ins Repo kopieren.

## BEWIESENER STAND
V1 wurde real technisch produziert und privat via Telegram zugestellt. Damit ist R2-Medien → FFmpeg → Musik/Audio → 5-Minuten-MP4 → privates R2 → Telegram bewiesen. V1 ist jedoch **TECHNICAL PASS / CREATIVE FAIL**: Ergebnis im Wesentlichen gleichförmige Slideshow statt geforderter kreativer Szenen-/Effektproduktion.

### Root Causes
1. `load_private_prompt()` löst den exakten privaten Inbox-Prompt auf; `infra/private-asr/service.py::_run_video` gibt denselben Prompt an `build_plan(task_id,prompt,assets)`. Production Lead und Creative erhalten den Auftrag.
2. `PrivateCreativeDirector.create()` erzeugt `story_style=emotional-modern-memory-story`, `motion=ken-burns-pan-zoom`, `transitions=soft-cinematic`. Der aktuelle `PrivateVideoPlan` übernimmt motion/transitions nicht. Creative-Information geht bei Creative → Renderplan verloren.
3. `scripts/private_birthday_first_production.py::render_segment()` nutzt für alle Medien denselben Scale/Crop/FPS/Fade-Filter. Keine per-Szene Effektwahl.
4. `PrivateQM.checks()` akzeptiert vorhandene Overlays als Creative-Nachweis. Dadurch konnte V1 trotz fehlender realer Motion-/Transition-Ausführung Creative-QM bestehen.

## V2-REPARATURVERTRAG
Die bewiesene Maschinen-/Transportkette NICHT neu bauen. Drei Schnittstellen schließen:
- **Creative → Scene Plan:** expliziter Szenen-/Effektplan mit Story-Beats, Motion, Transition, Layout/Rhythmus und Overlays.
- **Scene Plan → FFmpeg:** konkrete Varianten pro Asset/Szene wirklich rendern; mehrere Pan/Zoom-/Bewegungsvarianten und sichtbare kreative Übergänge; Render-Evidence/Manifest erzeugen.
- **Render Evidence → QM:** Creative PASS nur bei nachgewiesener Soll/Ist-Umsetzung. Overlays allein reichen nie mehr.

## VERANTWORTUNGSKETTE
- Production Lead: exakten Inbox-Auftrag, Ziel/Dauer/9:16/privacy und Kette festlegen.
- Private Creative Director: echten Scene Plan erzeugen.
- Media/Story: private Assets Story-Beats/Szenen zuordnen, Rhythmus/Medientyp berücksichtigen.
- Music/Audio: Track + Source-Audio-Regeln.
- Video Editor/FFmpeg: Scene Plan ausführen + Render-Evidence.
- Private QM: technische UND kreative Soll/Ist-Prüfung, fail-closed.
- Private Preview: erst nach QM PASS READY_FOR_HUMAN, ausschließlich privat.
- Agent 21: technische Diagnose/Fix/Regression bei Fehlern; ersetzt Creative nicht.
- Agent 11: Runtime/Container-Recovery nur nach validiertem Handoff; kein Renderer.

Nicht alle Agenten künstlich ausführen. Alle Definitionen/Wiring auditieren, aber nur fachlich notwendige Rollen aktivieren. AGENTS_INDEX-Eintrag ist kein Live-Nachweis.

## V1-EVIDENCE
- Erfolgreicher Recovery-Run `37584085667`, rerun job `112694685062`, Produktion/QM/private Preview SUCCESS.
- V1 lief explizit mit „Agent 11 is bypassed“; Agent 11 nicht als V1-Produzent darstellen.
- PR #464 merge `b68bf4f12106553b6275921eaa14a721cf4eaf46`: FFmpeg mixed-media timebase/timeline.
- PR #465 merge `9399a7fc9ea5e1b6d57dc64caa3383fcd8d6d381`: Deploy runtime revision gate.
- PR #466 merge `131248cc938809c8222ef616ab799a5b86f40c07`: FFmpeg diagnostics wrapper.
- PR #467 / Ausgangs-main vor V2: `89ecf3c604e1a124c7ddcc3e32908ade4f09f6b6`.

## RELEVANTE DATEIEN
`content_factory_private_video_orchestrator.py`
`scripts/private_birthday_first_production.py`
`infra/private-asr/service.py`
`tests/test_content_factory_private_video_orchestrator.py`
`tests/test_private_birthday_timeline.py`
`.github/workflows/private-birthday-first-production.yml`
`.github/workflows/private-asr-cloudflare-deploy.yml`
`.github/workflows/recover-duenya-after-agent21.yml`
`scripts/watch_duenya_level12_production.py`
`agents/AGENTS_INDEX.md`
`agents/11_system_restart_agent.md`
`agents/21_instandhaltungsagent.md`

## NÄCHSTE SCHRITTE – OHNE NEUANALYSE-LOOP
1. main/Branch einmal verifizieren.
2. Orchestrator: echter Scene Plan + Render-Evidence-Vertrag.
3. FFmpeg: reale Effektvarianten; bewiesene V1-Timeline/Delivery erhalten.
4. QM: Soll/Ist-Creative-Evidence fail-closed.
5. Tests/echte synthetische FFmpeg-Regressionen, CI grün.
6. Runtime-Revision erhöhen; Deploy garantiert neuen Renderer.
7. PR prüfen/mergen; Deploy verifizieren.
8. Erst dann denselben privaten Task als **V2** starten.
9. V2 nur als gestartet melden, wenn die reparierte Runtime ihn wirklich angenommen hat; GitHub-Actions-Live-Link an Bülent.
10. Bis private Preview/QM verfolgen und tatsächliche Creative-Evidence prüfen.

**Checkpoint-Wahrheit:** V2 ist bei Erstellung dieser Datei NOCH NICHT gestartet.
