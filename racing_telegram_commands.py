"""Pure Telegram command routing for the Racing approval lanes."""
import re


_SELECTION = r"(?:[1-9]|1[0-9]|20)(?:\s*[-–—]\s*(?:[1-9]|1[0-9]|20))?"
_SELECTION_LIST = rf"{_SELECTION}(?:\s*,\s*(?:t\s*)?{_SELECTION})*"


def _command(value):
    return re.sub(r"\s+", " ", str(value or "").strip().lower()).lstrip("/")


def is_turkish_approval(command):
    """Match documented Turkish selection commands, including T1,T3 and ranges."""
    value = _command(command)
    return bool(
        re.fullmatch(rf"turkish\s+(?:(?:t\s*)?{_SELECTION_LIST}|alle|nein|✅|❌)", value, re.I)
        or re.fullmatch(rf"t\s*(?:{_SELECTION_LIST}|alle|nein|✅|❌)", value, re.I)
    )


def is_turkish_human_action(command):
    """Match explicit per-item post/edit/drop actions without capturing plain selections."""
    value = _command(command)
    has_item = bool(re.search(rf"(?:^|[^a-z0-9])(?:t\s*|turkish\s+(?:t\s*)?){_SELECTION}(?=$|[^0-9])", value, re.I))
    has_action = bool(re.search(
        r"\b(?:post(?:en|e|et)?|veröffentlichen|veroeffentlichen|freigeben|ändern|aendern|überarbeiten|ueberarbeiten|umschreiben|bearbeiten|verwerfen|löschen|loeschen)\b|nicht\s+(?:posten|veröffentlichen|veroeffentlichen)",
        value,
        re.I,
    ))
    return has_item and has_action


def is_archive_select(command):
    """Only explicit archive choices belong to the archive path; T1 is Turkish approval."""
    return bool(re.fullmatch(r"(?:poste\s+|nimm\s+)\d+", _command(command), re.I))
