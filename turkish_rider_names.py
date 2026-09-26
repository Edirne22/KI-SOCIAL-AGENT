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

# Current public racing context. Keep identity separate from article facts: the scout
# fetches fresh context from these official championship pages on every run.
RIDER_CONTEXT={
 "Toprak Razgatlıoğlu":{"series":"MotoGP","official_sources":("https://www.motogp.com/en/riders/toprak-razgatlioglu/c883a3b8-17ce-419d-b71b-32c252f6fc7e","https://www.motogp.com/en/news")},
 "Deniz Öncü":{"series":"Moto2","official_sources":("https://www.motogp.com/en/riders/-/7f2593e1-d17e-4a83-9890-d9c383b29898","https://www.motogp.com/en/news/Moto2")},
 "Can Öncü":{"series":"WorldSSP","official_sources":("https://www.worldsbk.com/en/riders/can-oncu/8482","https://www.worldsbk.com/en/news/ssp")},
 "Bahattin Sofuoğlu":{"series":"WorldSSP","official_sources":("https://www.worldsbk.com/en/riders/bahattin-sofuoglu/8467","https://www.worldsbk.com/en/news/ssp")},
}

def context_for(rider):
 return RIDER_CONTEXT.get(rider,{})

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
