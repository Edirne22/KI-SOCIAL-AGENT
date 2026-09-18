# AGENTS.md – Arbeitsregeln für KI-Agenten

## Ausgabe-Regeln (i-have-adhd)

1. Erste Zeile: die nächste konkrete Aktion
2. Mehrstufige Aufgaben nummerieren (Schritt 1, 2, 3)
3. Letzte Zeile: ein konkreter nächster Schritt
4. Keine Einleitungen, keine Zusammenfassungen, keine Floskeln
5. Bei Fehlern: direkt Problem + Lösung nennen
6. Listen max. 5 Einträge
7. Bei mehrstufigen Aufgaben: Status wiederholen
8. Erfolge sichtbar machen (was ist erledigt?)

## Projekt-Regeln (KI-SOCIAL-AGENT)

- Sprache: Deutsch
- Kein Auto-Merge (immer PR erstellen, Nutzer entscheidet)
- Nicht anfassen: `debug/motogp-pipeline-output`
- Kein Schreiben in `memory/MEMORY_EVENTS.jsonl`
- Publisher nie automatisch starten
- Keine Secrets anlegen (nur im PR notieren)
- Fünfer-Batch-Regel nur mit expliziter Freigabe ändern
- Kein Push in andere Branches als `main` und `feature/*`
- Bei Testfehlern: nur Analyse + Kommentar, kein Auto-Fix

## Vision (Kurzfassung)

Ziel: Autonome Content-Fabrik. Agenten erstellen selbstständig Videos, Bilder und Texte aus einem Prompt. OmniRoute auf VPS als zentrales Gateway. Remotion + KI-Video-Modelle (LTX, Wan, Hunyuan). Kinocut als Video-Editor.
