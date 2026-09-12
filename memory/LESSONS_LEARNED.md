# Lessons Learned

## Zweck
Was der Agent aus Fehlern und Erfahrungen gelernt hat.

## Sicherheit
- API-Keys niemals in Markdown-Dateien speichern
- Filter für `AIza`, `AQ.`, `sk-` in allen Skripten aktiv
- GitHub Secrets für alle Zugangsdaten
- GitGuardian-Meldungen sofort prüfen

## Technik
- Gemini-Bildmodelle brauchen Billing (Fehler 429)
- Facebook-Seiten-Token aus Graph API Explorer läuft nach 1 Tag ab
- Instagram-API hat gelegentlich "transient errors" (Retry hilft)
- Dateinamen: nur Kleinbuchstaben, keine Umlaute
- Modell-Fallback nötig (mehrere Gemini-Modelle in Schleife)

## Content
- Renn-Content braucht aktuelle Racer-Namen
- Hook in den ersten 3 Sekunden entscheidend
- Zweisprachige Captions laufen besser
- Community-Themen (Turkbirler etc.) sind Gold

## Workflow
- Workflow-Dateien ohne Doppelpunkt am Dateinamen-Ende
- Nach jedem Update: 30 Sek. warten, dann Actions neu laden
- Bei Fehler immer Log im betroffenen Schritt prüfen

- 2026-09-12: Viral-, Funnel- und Experiment-Learning aktualisiert.
