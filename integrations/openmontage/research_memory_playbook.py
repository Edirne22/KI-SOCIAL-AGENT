"""Reusable reviewed research-method lessons for the private OpenMontage agents.

Methodology is durable; facts and URLs must still be checked for each job.
"""
from __future__ import annotations

from integrations.agent_memory import append_experience, load_context
from integrations.openmontage.motorsport_source_catalog import source_catalog_memory_lesson

LESSONS = {
    "05_research_synthesist": [
        "Motorradtechnik: zuerst Hersteller-Handbücher und technische Herstellerseiten suchen (z.B. KTM Quickshifter+, BMW Schaltassistent Pro, Harley-Davidson Technik). Jede Behauptung mit der genauen Fundstelle verbinden; eine Hersteller-Domain allein ist kein Beweis.",
        "Bei Quickshifter zwischen Hochschalten mit kurzzeitiger Drehmomententlastung und Blipper-Funktion beim Herunterschalten unterscheiden; nicht jedes Motorrad kann beides. Fahrzeugspezifische Angaben nur aus dem passenden Handbuch übernehmen.",
        "Eigenständiger Rechercheauftrag: aus dem Telegram-Thema Suchbegriffe und konkrete Fragen ableiten; Hersteller- und Primärquellen live prüfen, URL und Datum speichern; keine vorbereitete Quickshifter-Geschichte als aktuelle Live-Recherche ausgeben.",
        "Pro Fakt mögliche Bilder und Videos als media_candidates mit Fund-URL, Medientyp, Themenbezug, Herkunft und ungeprüftem Rechte-Status notieren. Eine Webseite oder YouTube-URL ist noch keine direkte MP4-/Bilddatei. Keine Medien-URL erfinden.",
        "Bei leeren Treffern alternative Suchbegriffe und Quellen probieren, Duplikate entfernen und eine klare Fehlermeldung liefern statt fingierter Ergebnisse. YouTube- und Instagram-Scouts dürfen parallel Hinweise liefern, dürfen aber die Primärrecherche nicht blockieren.",
        "Aktuelle Renn-News: Datum und Rennen anhand offizieller MotoGP/WorldSBK-Ergebnisse verifizieren; ohne Veröffentlichungsdatum als needs_date_verification markieren. Evergreen-Technik braucht kein Newsdatum.",
    ],
    "creative_director": [
        "Bülent-Stil für Social-Posts: locker, flockig, entspannt, chillig und menschlich; natürliche kurze Sätze, passende Emojis, keine steife PR-Sprache und keine Hashtag-Wüste. 3D-Avatar ausdrücklich auf später verschieben.",
        "Aus belegten technischen Fakten eine eigenständige visuelle Geschichte bauen: Schaltimpuls, Sensor, Momententlastung, Gangwechsel, Blipper. Dauer nach Informationsdichte statt starrer 30/60-Sekunden-Vorgabe wählen.",
        "Für jede Szene echte Medienkandidaten nach Bildinhalt und Story-Relevanz bewerten; ein Clip muss die konkrete Aussage unterstützen. Keine beliebigen Motorradvideos als angeblich modellgenau darstellen. Fehlende Medien an den Rechercheagenten zur Nachsuche zurückgeben.",
        "Für Rennrückblicke nur bestätigte Platzierungen und Ereignisse verwenden. Reale Medien mit Quellen- und Lizenzstatus kennzeichnen; ungeklärte Rechte nicht als freigegeben darstellen. Veröffentlichung erst nach Owner-Approval.",
    ],
    "07_video_optimization": [
        "Vor dem Render pro Szene tatsächliche lokale Bild-/Videodatei, Dateiformat, Codec und Quellnachweis verlangen. Medienkandidaten und direkte Downloads unterscheiden; fehlende Dateien als Beschaffungsauftrag zurückmelden, nicht als erfolgreiches Realvideo markieren.",
        "Nach dem Render echte MP4 mit ffprobe auf Video, Dauer, 9:16 und technische Abspielbarkeit prüfen; synthetisches Bildmaterial nicht als echtes Rennmaterial ausgeben. Private Telegram-Vorschau vor jeder Veröffentlichung.",
    ],
}


def ensure_research_playbook(storage) -> dict:
    """Idempotently seed reviewed methodology in each role's R2 memory."""
    counts = {}
    for role, lessons in LESSONS.items():
        lessons = [*lessons, source_catalog_memory_lesson()] if role == "05_research_synthesist" else lessons
        existing = load_context(storage, role, limit=100)
        summaries = {entry.get("summary") for entry in existing["personal"] if entry.get("reviewed") is True}
        added = 0
        for lesson in lessons:
            if lesson not in summaries:
                append_experience(storage, role, kind="lesson", summary=lesson, reviewed=True)
                added += 1
        counts[role] = added
    return counts
