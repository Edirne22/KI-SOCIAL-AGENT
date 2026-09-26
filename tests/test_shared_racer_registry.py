from turkish_rider_names import canonical_rider, context_for, CANONICAL_ALIASES
import motogp_content_agency_v2 as agency

cases={
 'Oğuz Taşhan wins': 'Oğuz Taşhan',
 'Oguz Tashan podium': 'Oğuz Taşhan',
 'Hasan Huseyin Bas podium': 'Hasan Hüseyin Baş',
 'Can Oncu WorldSSP': 'Can Öncü',
 'Toprak Razgatlioglu MotoGP': 'Toprak Razgatlıoğlu',
}
for text,expected in cases.items():
 assert canonical_rider(text)==expected,(text,canonical_rider(text),expected)
 assert agency.detect_turkish_rider({'title':text,'summary':'','url':''})==expected
 assert context_for(expected),expected
assert len(CANONICAL_ALIASES)>=13
print('TEST – Shared Racer Registry: PASS')
