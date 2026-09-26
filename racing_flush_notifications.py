"""Flush deferred Racing Telegram messages only after durable Git persistence."""
from pathlib import Path
import json
from telegram_bot import send_message

OUTBOX=Path('/tmp/racing_telegram_outbox.jsonl')

def main():
    if not OUTBOX.exists():
        print('Keine deferred Racing-Telegram-Nachricht')
        return 0
    messages=[]
    for line in OUTBOX.read_text(encoding='utf-8').splitlines():
        if line.strip():
            messages.append(json.loads(line))
    for message in messages:
        send_message(message)
    print(f'Racing Telegram nach Persistenz gesendet: {len(messages)}')
    OUTBOX.unlink(missing_ok=True)
    return 0

if __name__=='__main__':
    raise SystemExit(main())
