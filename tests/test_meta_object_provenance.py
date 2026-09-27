import json
import re
import instagram_publish as ig
import facebook_publish as fb

BASE = """Status: FREIGEGEBEN
Publication-Claim: IN_BEARBEITUNG token
Text: Test
Bild: media/test.jpg
Medienstatus: EIGENES_MATERIAL
Nutzungsrecht: eigen
"""

def provenance(block):
    m=re.search(r"(?m)^Publish-Provenienz: (.+)$", block)
    assert m
    return json.loads(m.group(1))

ig_block="## Instagram\n"+BASE
ig_out=ig.mark_block(ig_block, ig_block, "17890001", "creation-77")
ip=provenance(ig_out)
assert ip["post_id"]=="17890001"
assert ip["published_media_id"]=="17890001"
assert ip["creation_id"]=="creation-77"

fb_block="## Facebook\n"+BASE
fb_out=fb.mark_block(fb_block, fb_block, "998877", "bild")
fp=provenance(fb_out)
assert fp["post_id"]=="998877"
assert fp["object_id"]=="998877"
assert fp["object_type"]=="bild"
print("META OBJECT PROVENANCE: PASS")
