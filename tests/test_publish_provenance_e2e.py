import json,re
import instagram_publish as ig
import facebook_publish as fb
from publish_provenance import media_origin

BASE="""## {platform}
Status: FREIGEGEBEN
Publication-Claim: IN_BEARBEITUNG token-1
Titel: Test
Text:
Neu formulierte Caption.
Bild: assets/generated/test.jpg
Quelle: https://www.youtube.com/watch?v=abcdefghijk
Medienstatus: EIGENE_KI_EDITORIALGRAFIK
Nutzungsrecht: eigene KI-Editorialgrafik
Quellen-Lineage: {"origin":"MotoParkTv","source_url":"https://www.youtube.com/watch?v=abcdefghijk","transcription":"local-whisper","original_wording_reuse":false}
"""

ig_block=BASE.format(platform="Instagram")
ig_out=ig.mark_block(ig_block,ig_block,"IG-POST-123")
assert "Status: GEPOSTET" in ig_out
assert "Publication-Claim:" not in ig_out
m=re.search(r"(?m)^Publish-Provenienz: (.+)$",ig_out);assert m
p=json.loads(m.group(1))
assert p["platform"]=="instagram" and p["post_id"]=="IG-POST-123"
assert p["media_kind"]=="image" and p["media_path"]=="assets/generated/test.jpg"
assert p["source_url"].startswith("https://www.youtube.com/")
assert p["source_lineage"]["origin"]=="MotoParkTv"
assert p["source_lineage"]["transcription"]=="local-whisper"
assert p["source_lineage"]["original_wording_reuse"] is False

fb_block=BASE.format(platform="Facebook")
fb_out=fb.mark_block(fb_block,fb_block,"FB-POST-456")
assert "Status: GEPOSTET" in fb_out
assert "Publication-Claim:" not in fb_out
m=re.search(r"(?m)^Publish-Provenienz: (.+)$",fb_out);assert m
p=json.loads(m.group(1))
assert p["platform"]=="facebook" and p["post_id"]=="FB-POST-456"
assert p["media_status"]=="EIGENE_KI_EDITORIALGRAFIK"
assert p["source_lineage"]["source_url"]==p["source_url"]

print("TEST – Publish Provenance E2E: PASS")
