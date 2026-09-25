"""Canonical Turkish racing rider identity normalization.

All discovery/QM stages should consume the same Unicode/ASCII matching rules.
"""
import re, unicodedata

CANONICAL_ALIASES={
 "Toprak Razgatlıoğlu":("Toprak Razgatlıoğlu","Toprak Razgatlioglu","Toprak Razgatlıoglu","Toprak Razgatliğlu"),
 "Can Öncü":("Can Öncü","Can Oncu","C. Öncü","C. Oncu"),
 "Deniz Öncü":("Deniz Öncü","Deniz Oncu","D. Öncü","D. Oncu"),
 "Bahattin Sofuoğlu":("Bahattin Sofuoğlu","Bahattin Sofuoglu","Bahattin Sofouglu","B. Sofuoğlu","B. Sofuoglu","B. Sofouglu"),
 "Zayn Sofuoğlu":("Zayn Sofuoğlu","Zayn Sofuoglu","Z. Sofuoğlu","Z. Sofuoglu"),
}

def fold(value):
 s=unicodedata.normalize("NFKD",str(value or "").casefold()).replace("ı","i")
 return "".join(ch for ch in s if not unicodedata.combining(ch)).replace("ğ","g").replace("ü","u").replace("ö","o").replace("ş","s").replace("ç","c")

def canonical_rider(text):
 low=fold(text)
 for rider,aliases in CANONICAL_ALIASES.items():
  for alias in aliases:
   a=fold(alias)
   if re.search(r"(?<![a-z])"+re.escape(a)+r"(?![a-z])",low):
    return rider
 return ""

def aliases_for(rider):
 return CANONICAL_ALIASES.get(rider,())
