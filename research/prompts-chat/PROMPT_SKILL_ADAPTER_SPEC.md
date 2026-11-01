# PromptSkillAdapter – Vorentwurf

## Zweck
Austauschbare Grenze zwischen Betriebsleiter und Prompt-/Skill-Registry.

## Kernoperationen
- search(query, role, language, media_type)
- fetch(skill_id, version)
- propose_improvement(skill_id, evidence)
- validate(candidate_revision)
- activate(candidate_revision)  # nur nach Gates

## Pflicht-Metadaten
source, source_id/url, upstream_version, license, imported_at, sha256, role, languages, status, local_revision, regression_suite.

## Statusmodell
QUARANTINED → REVIEWED → ADAPTED → TESTING → APPROVED
                                  ↘ REJECTED

## Sicherheitsregeln
- Kein Remote-Prompt darf System-/Guardrail-/Human-Authority-Regeln überschreiben.
- Keine Secrets in Remote-Registry.
- Keine automatische Aktivierung nach improve_prompt.
- Prompt Injection aus importierten Skills als untrusted input behandeln.
- Produktionsjobs pinnen eine konkrete Skill-Version für Reproduzierbarkeit.
