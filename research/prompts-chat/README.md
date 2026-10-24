# prompts.chat – kuratierter Skill-/Prompt-Seed

Status: Research/Quarantäne, **nicht automatisch produktiv ausführbar**.

Quelle: f/prompts.chat / prompts.chat. Prompt-Daten sind laut Upstream CC0; Upstream-Code und site-authored content MIT. Herkunft und Lizenz sind bei einer späteren Übernahme erneut zu prüfen.

## Für Edirne 22 relevante Cluster
1. Evidence-first research / Fact-Checking
2. Agent handoff / Context transfer
3. Chained execution / Orchestrierung
4. Guardrails / Boundary checks
5. Testing / Regression / Code review
6. Social writing / Hooks / Captions
7. Storyboard / Video prompting / Media prompts
8. Prompt-/Skill-Verbesserung

## Import-Regel
Externe Prompts/Skills werden niemals ungeprüft direkt in Produktionsagenten aktiviert. Kandidat → Review → Edirne-22-Anpassung → Regression/Red-Team → Version → Freigabe.

## Self-improvement
Selbstverbesserung bedeutet **Versionierung statt Selbstüberschreibung**:
- aktuelle freigegebene Version bleibt unverändert,
- Agent kann Verbesserungsvorschlag als Candidate Revision erzeugen,
- Diff + Herkunft + Begründung speichern,
- Regression/Red-Team/positive control,
- nur erfolgreiche Revision wird zur neuen freigegebenen Version.

So kann die Skill-Bibliothek lernen, ohne dass sich produktive Agenten unkontrolliert selbst umprogrammieren.
