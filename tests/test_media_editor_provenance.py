import json
from publish_provenance import append_media_provenance, append_publish_provenance

def field(block,label):
    for line in block.splitlines():
        if line.startswith(label+":"):
            return json.loads(line.split(":",1)[1].strip())
    raise AssertionError(label)

base="""## Instagram
Status: FREIGEGEBEN
Text: Neutraler Motorrad-Reisebeitrag
Bild: assets/generated/test.jpg
Quelle: https://example.com/source
Quellen-Lineage: {"origin":"MotoParkTv","original_wording_reuse":false}
Medienstatus: FREIGEGEBEN
"""
media={"version":1,"media_kind":"image","media_path":"assets/generated/test.jpg",
       "origin":"agnes-ai","generator":"generate_agnes_media.py",
       "model":"agnes-image-2.1-flash","synthetic":True,"real_racer_generation":False}
edited=append_media_provenance(base,media)
assert field(edited,"Media-Provenienz")==media
published=append_publish_provenance(edited,"instagram","17890001")
prov=field(published,"Publish-Provenienz")
assert prov["origin"]=="agnes-ai"
assert prov["generator"]=="generate_agnes_media.py"
assert prov["model"]=="agnes-image-2.1-flash"
assert prov["synthetic"] is True
assert prov["real_racer_generation"] is False
assert prov["media_kind"]=="image"
assert prov["media_path"]=="assets/generated/test.jpg"
assert prov["source_url"]=="https://example.com/source"
assert prov["platform"]=="instagram"
assert prov["post_id"]=="17890001"
assert prov["source_lineage"]["origin"]=="MotoParkTv"
assert prov["source_lineage"]["original_wording_reuse"] is False
print("MEDIA PROVENANCE E2E: PASS")
