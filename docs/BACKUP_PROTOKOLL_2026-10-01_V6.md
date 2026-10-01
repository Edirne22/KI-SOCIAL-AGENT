# BACKUP-PROTOKOLL V6 – 01.10.2026
## VERBINDLICHE PROJEKTREGELN / NICHT VERGESSEN
`PROJECT_GUARDRAILS.md` vor jeder Arbeit lesen; Merge nur nach Bülents Freigabe, keine ungeprüften Live-Behauptungen.
**Gesicherter Git-Code-HEAD vor Beginn:** `e1ebc471f22b8ad1512ac42dd30080478590413c`.
**Wiederherstellungsbranch:** `backup/2026-10-01-ai-central-vision-pre-stage2-v6` genau von diesem Commit erstellt.
**Separater Doku-Branch:** `feature/project-handover-v6-ai-company-roadmap`. Änderungen nur Dokumentation; PR erfordert Bülents ausdrückliches Merge.
**Vorgänger-Sicherung:** `backup/2026-10-01-ai-central-live-v5` bei `efad1f9e7000864a20fc235b5b235be4760d2e06`; V5-Übergabe historisch in offenem DRAFT-PR #286, noch nicht in main; alle drei V5-Dokumente wurden zur selbstständigen Wiederherstellung zusätzlich auf diesen V6-Branch kopiert.
**V6-Artefakte:** `docs/PROJEKT_UEBERGABE_6_2026-10-01_KI_UNTERNEHMEN.md`, `snapshots/SNAPSHOT_2026-10-01_KI_UNTERNEHMEN_PRE_STEP1_V6.md`, dieses Sicherungsprotokoll und aktualisierter `MASTER-SNAPSHOT.md` auf dem Doku-Branch.

## Umfang und Lücken
Git-Branch enthält alle zum Sicherungszeitpunkt getrackten Code-, Workflow- und alten Dokumentdateien auf main, keine uncommitted Dateien, User-Chat-Inhalte außerhalb der hier geschriebenen V6-Übergabe, keine GitHub/Cloudflare Secrets, Cloudflare-Container-Laufzeitzustände, private R2-Daten, Modell-Dateien oder externe Konten. Gewöhnliche Git-Branches können ohne Protection verändert werden; für wirklich unveränderlichen/off-site Disaster-Recovery später zusätzlich extern archivieren.
Aktueller main kann durch automatisierte Publisher/Memory/Quality-Workflows rasch wechseln. Vor jedem Wiederherstellen Snapshot-SHA mit dem Branch prüfen und niemals main unbeaufsichtigt hart zurücksetzen.
**Live-Beweiskette:** PR #287 gemergt; manueller Nvidia-Free-Test #36903543954 Nemotron ANSWER, Kimi ANSWER, OpenRouter-Challenge UNAVAILABLE, separates OmniRoute-Job FAILURE; Telegram-Poller erfolgreich aber keine belegte End-to-End-Ergebnisantwort. Kein unbekannter Gemini-/Groq-Kostenstatus als kostenlos darstellen.
**Nicht enthalten:** V5 original vorheriger Übergabe Nr.4 als nachweislich identische Archivkopie; V5 enthält dokumentierte Archivlücke.

## Sicherer Wiederanlauf
1. Aktuellen main, PRs und Actions prüfen. V6-Handover und V6-Snapshot lesen; V5-Archivdokumente liegen jetzt auch im V6-Branch; historischer V5-PR #286 bleibt separat offen.
2. Separaten Schritt-1-Branch identifizieren oder nur falls fehlend neu anlegen. Keine zweite parallele KI-Zentrale.
3. Direkte NVIDIA-Route erhält Vorrang. Kosten-Guard für Gemini/Groq, echten begrenzten Live-Nachweis und R2/Dashboard/Telegram-Staffel erst später produktiv schalten.
4. OmniRoute ausdrücklich PAUSIERT; OpenChatCut #271/#278 unangetastet bis separate Freigabe. Kein autonomer Publisher.
