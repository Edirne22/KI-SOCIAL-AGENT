"""Ausschließlich öffentliche Quellen für Motorrad-Rennkalender."""

ALLOWED_SERIES = ["MotoGP", "WorldSBK", "WorldSSP", "WorldSPB"]

SOURCES = {
    "MotoGP": ["https://www.motogp.com/", "https://www.motorsport-magazin.com/motogp/"],
    "WorldSBK": ["https://www.worldsbk.com/", "https://www.servustv.com/sport/"],
    "WorldSSP": ["https://www.worldsbk.com/"],
    "WorldSPB": ["https://www.worldsbk.com/"],
}


def is_allowed_series(series: str) -> bool:
    allowed = str(series or "").strip() in ALLOWED_SERIES
    if not allowed:
        print(f"Event ignoriert: Serie {str(series or '').strip() or '-'} nicht erlaubt")
    return allowed
