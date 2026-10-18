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
        "Aktuelle Renn-News: Datum und Rennen anhand offizieller MotoGP/WorldSBK-Ergebnisse verifizieren; ohne Veröffentlichungsdatum als needs_date_verification markieren. Evergreen-Technik braucht kein Newsdatum.",
    ],
    "creative_director": [
        "Aus belegten technischen Fakten eine eigenständige visuelle Geschichte bauen: Schaltimpuls, Sensor, Momententlastung, Gangwechsel, Blipper. Dauer nach Informationsdichte statt starrer 30/60-Sekunden-Vorgabe wählen.",
        "Für Rennrückblicke nur bestätigte Platzierungen und Ereignisse verwenden. Reale Medien mit Quellen- und Lizenzstatus kennzeichnen; ungeklärte Rechte nicht als freigegeben darstellen. Veröffentlichung erst nach Owner-Approval.",
    ],
    "07_video_optimization": [
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
