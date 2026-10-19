# KI-SOCIAL-AGENT – Codespaces-Testwerkstatt

Dieser Branch ist eine isolierte Testumgebung auf Basis von PR #663. Kein Merge und kein Publishing.

## Start
1. Repository öffnen und Branch `setup/codespaces-testwerkstatt-20261019` auswählen.
2. **Code → Codespaces → Create codespace on ...** auswählen. Wenn möglich **2 cores** verwenden.
3. Im Terminal ausführen:

```bash
python --version
ffmpeg -version | head -n 1
python -m pytest -q tests/test_hermes_dynamic_claims_count.py tests/test_hermes_toprak_factcheck_regression.py
```

## Regeln
- **Keine** GitHub Actions zum Testen starten; diese Tests laufen im Codespace-Terminal.
- Keine automatischen Publikationen, Telegram-Sends, R2-Uploads oder Merges.
- Live-Secrets aus GitHub Actions werden **nicht automatisch** als Codespaces-Secrets übernommen. Keine Secrets in Dateien, Logs oder Chats kopieren.
- Für echten FFmpeg-End-to-End-Test zuerst Abhängigkeiten, Ressourcen und Aufrufparameter gezielt prüfen; reale Medien-/API-Integration gesondert abnehmen.
- Codespace nach Nutzung **Stop codespace**; Speicher kann bis zum Löschen weiter auf das Codespaces-Kontingent angerechnet werden.

## Wichtig
Ein bestandener synthetischer Test beweist noch keine echte Toprak-News-/Instagram-/YouTube-/Telegram-Produktionskette. Erst stufenweise nachweisen.
