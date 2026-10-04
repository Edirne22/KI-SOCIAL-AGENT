# Claude-Instandhaltung

Dieser Ordner ist das dauerhafte GitHub-Protokoll fuer Code-Reparaturen von Agent 21 / Claude-Instandhaltung.

## Verbindliche Ablage

- `REPAIR_INDEX.md`: chronologischer Index der Code-Reparaturen.
- Pro Reparatur eine neue Datei `YYYY-MM-DD_REPAIR-<ID>.md`.
- Alte Reparaturberichte werden niemals ueberschrieben oder geloescht.
- Der zugehoerige Runtime-/Incident-Datensatz bleibt zusaetzlich unveraenderlich in privatem R2.

Jeder Bericht dokumentiert mindestens: Repair-ID, Zeit, Maschine/Tool, Task/Stage, Fehlerklasse, Root Cause, geaenderte Dateien, Commit/Diff, gezielte Tests, Deploy/Verify, kontrollierten Retry und Endzustand.

Keine Secrets, Tokens, privaten Rohmedien, privaten Prompts oder personenbezogenen Inhalte in diesem Ordner.

## Coding-Regel

Agent 21 darf fuer technische Reparaturen den freigegebenen Fast-Repair-Pfad benutzen. Schreibzugriff bedeutet keine unprotokollierten direkten Aenderungen an `main`: Patch und Nachweis muessen nachvollziehbar bleiben. `CLAUDE.md`, `PROJECT_GUARDRAILS.md` und die Privacy-/Kosten-/Publishing-Grenzen bleiben bindend.
