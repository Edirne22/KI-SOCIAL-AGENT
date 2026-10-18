"""DST-aware Berlin daily 08:00 gate; never infer a successful production."""
from datetime import datetime
from zoneinfo import ZoneInfo


def is_berlin_daily_slot(now_utc: datetime) -> bool:
    if now_utc.tzinfo is None:
        raise ValueError("Timezone-aware datetime required")
    local = now_utc.astimezone(ZoneInfo("Europe/Berlin"))
    return local.hour == 8 and local.minute < 30


if __name__ == "__main__":
    from datetime import timezone
    import os
    local = datetime.now(timezone.utc).astimezone(ZoneInfo("Europe/Berlin"))
    allowed = is_berlin_daily_slot(datetime.now(timezone.utc))
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as out:
        out.write(f"due={str(allowed).lower()}\\n")
    print(f"Berlin local time: {local.isoformat()}; scheduled slot: {allowed}")
