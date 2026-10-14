"""Öffentliche Primär- und Sekundärquellen für Motorrad-Rennkalender."""

ALLOWED_SERIES = ["MotoGP", "WorldSBK", "WorldSSP", "WorldSPB"]

# Kalenderseiten werden vom Wochenkalender-Agenten tatsächlich abgerufen.
# Sekundärquellen ergänzen Kontext; Termine und Uhrzeiten müssen aus der
# offiziellen Veranstalterquelle stammen.
CALENDAR_SOURCES = {
    "MotoGP": [
        {"role": "official", "url": "https://www.motogp.com/en/calendar"},
        {"role": "secondary", "url": "https://motoetkinlik.com/motogp-yaris-takvimi/"},
        {"role": "secondary", "url": "https://trf1.net/motor-sporlari/motogp/"},
    ],
    "WorldSBK": [
        {"role": "official", "url": "https://www.worldsbk.com/en/calendar"},
        {"role": "secondary", "url": "https://motoetkinlik.com/kategori/wsbk/"},
    ],
    "WorldSSP": [
        {"role": "official", "url": "https://www.worldsbk.com/en/calendar"},
        {"role": "secondary", "url": "https://motoetkinlik.com/kategori/worldssp/"},
    ],
    "WorldSPB": [
        {"role": "official", "url": "https://www.worldsbk.com/en/calendar"},
        {"role": "secondary", "url": "https://motoetkinlik.com/kategori/yaris/"},
    ],
}

SOURCES = {
    "MotoGP": [
        "https://www.motogp.com/en/calendar",
        "https://motoetkinlik.com/motogp-yaris-takvimi/",
        "https://trf1.net/motor-sporlari/motogp/",
        "https://www.motorsport-magazin.com/motogp/",
    ],
    "WorldSBK": [
        "https://www.worldsbk.com/en/calendar",
        "https://motoetkinlik.com/kategori/wsbk/",
        "https://www.servustv.com/sport/",
    ],
    "WorldSSP": [
        "https://www.worldsbk.com/en/calendar",
        "https://motoetkinlik.com/kategori/worldssp/",
    ],
    "WorldSPB": [
        "https://www.worldsbk.com/en/calendar",
        "https://motoetkinlik.com/kategori/yaris/",
    ],
}


def is_allowed_series(series: str) -> bool:
    allowed = str(series or "").strip() in ALLOWED_SERIES
    if not allowed:
        print(f"Event ignoriert: Serie {str(series or '').strip() or '-'} nicht erlaubt")
    return allowed
