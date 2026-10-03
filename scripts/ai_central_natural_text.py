"""Conservative natural text intake. Publishing/approval never inferred."""
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Decision:
    kind: str
    message: str = ""

RESERVED = re.compile(r"(?i)\b(?:posten|veröffentlichen|veroeffentlichen|freigeben|löschen|loeschen|antwort\s+(?:ig|fb)-|t[1-5]|motogp|turkish|racing|toprak|worldsbk|worldssp|moto[23])\b")
EXPLICIT = re.compile(r"(?is)^\s*(?:ki|ki-zentrale|zentrale)\s*[:;,]\s*(.+?)\s*$")
COMMAND = re.compile(r"(?i)^\s*(?:/|alle$|liste$|hilfe$|help$|watchlist$|race$|inspiration$|follow-analyse$|ok$|neu$|ja$|nein$|bild\b)")

def classify_natural_text(text):
    if not isinstance(text,str):return Decision("ignore")
    value=text.strip()
    if not value or COMMAND.search(value):return Decision("ignore")
    explicit=EXPLICIT.fullmatch(value)
    message=explicit.group(1).strip() if explicit else value
    if RESERVED.search(message):return Decision("clarify")
    if len(message)<3 or len(message)>2500:return Decision("ignore")
    # Explicitly addressed requests are drafts; casual chatter is not silently sent to models.
    if explicit:return Decision("draft",message)
    if re.match(r"(?i)^(?:erstelle|mach(?:e)?|schreib(?:e)?|such(?:e)?|find(?:e)?|analysier(?:e)?|plane|prüf(?:e)?|vergleich(?:e)?|bearbeite|kannst du)\b",message):
        return Decision("draft",message)
    return Decision("clarify")
