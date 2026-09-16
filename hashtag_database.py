"""Context-aware hashtag catalog for MotoGP content.

Tags are selected only when the related rider/team/series is present in the
canonical fact object. This catalog is not a source of facts.
"""

HASHTAG_DATABASE = {
    "Johann Zarco": {"number": "5", "teams": ["Castrol Honda LCR"], "series": ["MotoGP"], "hashtags": ["#JohannZarco", "#Zarco", "#JZ5", "#Zarco5", "#CastrolHondaLCR", "#LCRHonda", "#MotoGP", "#MotoGP2026"]},
    "Toprak Razgatlioglu": {"number": "7", "teams": ["Prima Pramac Yamaha MotoGP"], "series": ["MotoGP"], "hashtags": ["#ToprakRazgatlioglu", "#Toprak", "#ElTurco", "#Razgatlioglu", "#TR07", "#07", "#PrimaPramac", "#PramacYamaha", "#YamahaM1", "#MotoGP", "#MotoGP2026"]},
    "Jack Miller": {"number": "43", "teams": ["Prima Pramac Yamaha MotoGP"], "series": ["MotoGP"], "hashtags": ["#JackMiller", "#Miller", "#JM43", "#43", "#JackMillerAus", "#PrimaPramac", "#PramacYamaha", "#YamahaM1", "#MotoGP", "#MotoGP2026"]},
    "Luca Marini": {"number": "10", "teams": ["Honda HRC Castrol"], "series": ["MotoGP"], "hashtags": ["#LucaMarini", "#Marini", "#LM10", "#10", "#HondaHRC", "#HRCCastrol", "#HondaRacing", "#MotoGP", "#MotoGP2026"]},
    "Joan Mir": {"number": "36", "teams": ["Honda HRC Castrol"], "series": ["MotoGP"], "hashtags": ["#JoanMir", "#Mir", "#JM36", "#36", "#HondaHRC", "#HRCCastrol", "#HondaRacing", "#MotoGP", "#MotoGP2026"]},
    "Ai Ogura": {"number": "79", "teams": ["SuperFile Trackhouse MotoGP Team"], "series": ["MotoGP"], "hashtags": ["#AiOgura", "#Ogura", "#AO79", "#79", "#Trackhouse", "#TrackhouseMotoGP", "#SuperFile", "#MotoGP", "#MotoGP2026"]},
    "Fabio Quartararo": {"number": "20", "teams": ["Monster Energy Yamaha MotoGP"], "series": ["MotoGP"], "hashtags": ["#FabioQuartararo", "#Quartararo", "#FQ20", "#20", "#MonsterYamaha", "#YamahaMotoGP", "#MotoGP", "#MotoGP2026"]},
    "Pedro Acosta": {"number": "37", "teams": ["Red Bull KTM Factory Racing"], "series": ["MotoGP"], "hashtags": ["#PedroAcosta", "#Acosta", "#PA37", "#37", "#RedBullKTM", "#KTMFactoryRacing", "#KTM", "#MotoGP", "#MotoGP2026"]},
    "Marc Marquez": {"number": "93", "teams": ["Ducati Lenovo Team"], "series": ["MotoGP"], "hashtags": ["#MarcMarquez", "#Marquez", "#MM93", "#93", "#DucatiLenovo", "#Ducati", "#ForzaDucati", "#MotoGP", "#MotoGP2026"]},
    "Francesco Bagnaia": {"number": "63", "teams": ["Ducati Lenovo Team"], "series": ["MotoGP"], "hashtags": ["#FrancescoBagnaia", "#Bagnaia", "#FB63", "#63", "#DucatiLenovo", "#Ducati", "#ForzaDucati", "#MotoGP", "#MotoGP2026"]},
    "Marco Bezzecchi": {"number": "72", "teams": ["Aprilia Racing"], "series": ["MotoGP"], "hashtags": ["#MarcoBezzecchi", "#Bezzecchi", "#MB72", "#72", "#Aprilia", "#ApriliaRacing", "#MotoGP", "#MotoGP2026"]},
    "Jorge Martin": {"number": "89", "teams": ["Aprilia Racing"], "series": ["MotoGP"], "hashtags": ["#JorgeMartin", "#Martin", "#JM89", "#89", "#Aprilia", "#ApriliaRacing", "#MotoGP", "#MotoGP2026"]},
}

GLOBAL_HASHTAGS = ("#MotorradRacing", "#RacingDeutschland", "#BuelentsBikeLife")


def _fold(value):
    return str(value or "").casefold().replace("ı", "i").replace("ğ", "g").replace("ü", "u").replace("ö", "o").replace("ş", "s").replace("ç", "c")


def _norm_tag(value):
    return _fold(value).replace("#", "")


def _cfo_text(cfo):
    return " ".join(str(cfo.get(section, "")) for section in ("source", "event", "session", "riders", "entities", "teams", "manufacturers", "locations", "claims"))


def contextual_hashtags(cfo, limit=7):
    text = _fold(_cfo_text(cfo))
    selected = []
    for rider, data in HASHTAG_DATABASE.items():
        if _fold(rider) not in text and not any(_fold(alias) in text for alias in rider.split()[-1:]):
            continue
        selected.extend(data["hashtags"][:4])
        selected.extend(tag for tag in data["hashtags"][4:] if _fold(tag.lstrip("#")) in text)
        break
    series = cfo.get("series")
    if series:
        series_tag = "#" + str(series)
        selected.insert(0, series_tag)
    selected.extend(GLOBAL_HASHTAGS)
    result, seen = [], set()
    for tag in selected:
        key = _norm_tag(tag)
        if key not in seen:
            seen.add(key); result.append(tag)
        if len(result) >= limit: break
    return result
