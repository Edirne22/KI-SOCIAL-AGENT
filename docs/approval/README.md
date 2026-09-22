# KI Social Agent – Freigabe-Oberfläche (Stufe 2)

Diese statische Web-Oberfläche dient zur manuellen Vorschau, Freigabe und Ablehnung von generierten Social-Media-Inhalten.

## Übersicht

- **Ziel-URL (GitHub Pages):** `https://edirne22.github.io/KI-SOCIAL-AGENT/`
- **Technologie:** Reines Vanilla JavaScript + HTML5 + CSS3 (ohne externe Frameworks, ohne Backend, ohne Login).

## Datenquelle & Funktionsweise

> **Hinweis zur Datenquelle:**
> `queue.json` enthält aktuell Beispieldaten (Mock) und wird später automatisiert vom Instagram-Publisher-Workflow befüllt.

- **Status-Optionen:** `offen`, `freigegeben`, `abgelehnt`
- **Filter:** Alle, Offen, Freigegeben, Abgelehnt
- **Lokaler Zustand:** Beim Klick auf "Freigeben" oder "Ablehnen" wird der Status im `localStorage` des Browsers gesichert. Beim Neuladen der Seite bleibt der Zustand erhalten. Es werden keine Netzwerk-Requests oder Backend-Aufrufe ausgeführt.

## Ausblick (Stufe 3)

In Stufe 3 wird die Entscheidung (Freigeben/Ablehnen) an die Automatisierungs-Pipeline (GitHub Actions / Telegram-Bot) übermittelt.
