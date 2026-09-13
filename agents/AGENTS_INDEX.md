# Agenten-Bibliothek

Diese Bibliothek bündelt spezialisierte Arbeitsrollen für Bülents deutsch-türkische Motorrad- und Reise-Community. Die Rollen sind projektspezifisch formuliert und dienen als Arbeitsanweisung für künftige Automatisierungen oder manuelle Aufträge.

Die Struktur ist methodisch inspiriert von [Agency Agents](https://github.com/msitarzewski/agency-agents); das Referenzprojekt steht unter der [MIT-Lizenz](https://github.com/msitarzewski/agency-agents/blob/main/LICENSE).

## Agentenübersicht

| Datei | Rolle | Aktivierung |
| --- | --- | --- |
| [01_content_creator.md](01_content_creator.md) | Entwickelt neue Content-Ideen und produktionsreife Entwürfe. | Bei neuen Themen, täglichen Ideen und konkreten Beitragsentwürfen. |
| [02_instagram_curator.md](02_instagram_curator.md) | Passt Inhalte für Reels, Carousels, Stories und Instagram-Captions an. | Wenn Instagram das Ziel ist oder ein Format gewählt werden muss. |
| [03_tiktok_strategist.md](03_tiktok_strategist.md) | Entwickelt kurze TikTok-Konzepte mit Hook, Szenen und Untertiteln. | Bei TikTok-Ideen, Kurzvideo-Tests und vertikalen Storys. |
| [04_social_media_strategist.md](04_social_media_strategist.md) | Plant Themen, Plattform-Mix und realistische Redaktionsschritte. | Bei Wochenplänen, Kampagnen und Priorisierungsfragen. |
| [05_research_synthesist.md](05_research_synthesist.md) | Prüft Quellen und bereitet Fakten verständlich auf. | Vor externen Tatsachenbehauptungen, Reise-, Sicherheits- oder Plattforminformationen. |
| [06_reddit_community_builder.md](06_reddit_community_builder.md) | Entwirft hilfreiche, regelkonforme Reddit-Beiträge und Antworten. | Bei Reddit-Recherche, Community-Gesprächen und Antwortentwürfen. |
| [07_video_optimization.md](07_video_optimization.md) | Erstellt Schnitt-, Untertitel- und Produktionsbriefe für Kurzvideos. | Bei Reel-, TikTok-, Video- oder Agnes-Asset-Briefings. |
| [08_paid_social_strategist.md](08_paid_social_strategist.md) | Entwirft vorsichtige Paid-Social-Kampagnen und Messpläne. | Nur bei ausdrücklich gewünschter, bezahlter Reichweite. |
| [09_quality_agent.md](09_quality_agent.md) | Prüft Workflow-Ergebnisse, Datenqualität und Sicherheitswarnungen. | Täglich nach den Analyse-Workflows oder manuell vor größeren Änderungen. |
| [10_follow_analysis_agent.md](10_follow_analysis_agent.md) | Erkennt aus freigegebenen öffentlichen Instagram-Profilen Formate, Themen und Hook-Muster. | Geplanter Analyse-Lauf oder Telegram: \`follow-analyse\`; kein Zugriff auf eine private Follow-Liste. |

## Geplante Agenten

| Name | Zweck | Reihenfolge | Sicherheitsregel |
| --- | --- | --- | --- |
| System-Neustart-Agent | Prüft Workflow-Zustände, startet ausschließlich freigegebene Wartungs- und Analyse-Workflows zeitversetzt und meldet einen Gesamtstatus. | Nach dem Qualitäts-Agenten. | Publisher, Telegram-Empfang, Medienerzeugung, Migrationen und alle extern wirkenden Workflows bleiben gesperrt, bis Bülent sie ausdrücklich einzeln freigibt. |

## Aktivierungs-Logik

1. Ordne den Auftrag zuerst einem Hauptagenten zu. Aktiviere nur einen zweiten Agenten, wenn dessen Fachwissen wirklich nötig ist.
2. Bei neuen Beiträgen startet in der Regel der Content Creator. Danach übernimmt der Plattform-Spezialist oder Video-Optimization-Agent.
3. Der Research Synthesist wird vor allen aktuellen, externen oder sicherheitsrelevanten Behauptungen eingesetzt.
4. Der Social Media Strategist plant Reihenfolgen und Wochenziele; er ersetzt nicht die Erstellung einzelner Beiträge.
5. Der Paid Social Strategist erstellt ausschließlich Entwürfe. Er startet weder Anzeigen noch Ausgaben.
6. Der Reddit Community Builder erstellt nur Vorschläge. Beiträge, Kommentare und Nachrichten werden nie automatisch versendet.
7. Jeder Agent liest vor der Arbeit mindestens die passenden Informationen aus `memory/`, `content/` und den Regeln unter `rules/`.
8. Jeder Output ist ein Entwurf. Veröffentlichung, externe Kommunikation, Budgeteinsatz, Buchungen und Kontoveränderungen brauchen immer Bülents ausdrückliche Freigabe.

## Empfohlene Reihenfolgen

- **Tägliche Idee:** Content Creator → optional Research Synthesist → Instagram Curator oder TikTok Strategist.
- **Wochenplanung:** Social Media Strategist → Content Creator → jeweiliger Plattform-Agent.
- **Video:** Content Creator oder TikTok Strategist → Video Optimization → menschliche Freigabe.
- **Recherche-Post:** Research Synthesist → Content Creator → Plattform-Agent.
- **Follow-Analyse:** Follow-Analyse-Agent → Research Synthesist → Content Creator; Muster nur als Inspiration verwenden.
- **Bezahlte Kampagne:** Paid Social Strategist → menschliche Freigabe → manuelle Einrichtung.

## Technischer Status

Die Agenten-Bibliothek ist zunächst Dokumentation und Arbeitsgrundlage. Sie wird noch nicht automatisch durch `router.py`, `llm_client.py` oder GitHub Actions ausgeführt. Eine spätere Orchestrierung darf diese Dateien lesen, muss aber die Aktivierungs-Logik und die menschlichen Freigaben respektieren.
