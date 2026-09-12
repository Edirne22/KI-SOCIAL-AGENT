"""Erstellt strukturierte, quellengebundene Inspirationsreports ohne erfundene Fakten."""
from __future__ import annotations

import re
from datetime import datetime


def evidence_count(reports: dict[str, str]) -> int:
    return sum(len(re.findall(r"(?m)^### Datensatz \d+", report)) for report in reports.values())


def build_evidence_text(reports: dict[str, str], limit_per_provider: int | None = None) -> str:
    sections = []
    for name, report in reports.items():
        source = report.strip()
        if limit_per_provider is not None and len(source) > limit_per_provider:
            source = source[:limit_per_provider] + "\n[Weitere Rohdaten wegen Prompt-Limit ausgelassen.]"
        sections.append(f"## Datenquelle: {name}\n{source}")
    return "\n\n".join(sections)


def build(provider_reports: dict[str, str]) -> str:
    count = evidence_count(provider_reports)
    lines = [
        "# Inspiration-Ideen",
        f"Stand: {datetime.now():%Y-%m-%d %H:%M}",
        "",
        "## Datenstatus",
        f"- Konkrete öffentliche Datensätze: {count}",
    ]
    for name, report in provider_reports.items():
        if re.search(r"(?m)^### Datensatz \d+", report):
            lines.append(f"- {name}: konkrete Daten vorhanden")
        else:
            lines.append(f"- {name}: keine konkreten Daten")
    lines += ["", "## Report"]
    if count == 0:
        lines.append("Report eingeschränkt – keine konkreten öffentlichen Themen, URLs oder Engagement-Zahlen verfügbar. Es werden keine Fakten oder Ideen mit erfundenen Quellen ausgegeben.")
    else:
        lines.append("Strukturierte Rohdaten liegen vor. Für die detaillierte Auswertung ist Gemini-Zusammenfassung vorgesehen.")
    return "\n".join(lines) + "\n"
