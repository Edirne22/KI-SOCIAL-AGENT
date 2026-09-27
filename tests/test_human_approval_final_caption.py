"""Human approval must expose every complete final caption before commands."""
import motogp_content_agency_v2 as a

sent=[]
a.send_message=lambda msg: sent.append(msg)
a.series_for=lambda x: x.get("series","WorldSSP")
a.turkish_status=lambda items,qualified=None: "selected"
a.VALID_SERIES=("MotoGP","Moto2","Moto3","WorldSBK","WorldSSP","WorldSSP300")
a.VERSION="TEST"

items=[
 {"series":"WorldSSP","caption":"Mein vollständiger Redakteurstext Nummer eins.\n#WorldSSP","url":"https://example.test/1"},
 {"series":"MotoGP","caption":"Mein vollständiger Redakteurstext Nummer zwei.\n#MotoGP","url":"https://example.test/2"},
]
a.telegram_preview(items,True,items)
assert len(sent)==4,sent
assert "FINALER REDAKTEURS-TEXT" in sent[1]
assert items[0]["caption"] in sent[1]
assert items[1]["caption"] in sent[2]
assert "Freigabe: motogp 1–2" in sent[3]
assert all("Freigabe:" not in msg for msg in sent[:-1])
print("HUMAN APPROVAL FINAL CAPTION: PASS")
