# Agent 15 – Finanzplaner

## Zweck
Wöchentliche Prüfung der Zinslandschaft, Abgleich mit FINANCE_PLAN.json,
Zusammenfassung per Telegram.

## Trigger
Cron: jeden Montag 09:00 Europe/Berlin

## Ausgabe
- Telegram-Zusammenfassung (max. 1500 Zeichen)
- Update von memory/FINANCE_RATES_CACHE.md
- Append an memory/FINANCE_EVENTS.jsonl

## Grenzen
- Keine Anlageberatung
- Keine Transfers
- Kein Login bei Banken
