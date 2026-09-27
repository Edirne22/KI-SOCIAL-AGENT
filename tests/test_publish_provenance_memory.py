import json
import tempfile
from pathlib import Path

import memory_engine as me

sample = """## Instagram [GEPOSTET 2026-09-27 12:00 | ID: 17890001]
Status: GEPOSTET
Text: Test
Bild: assets/generated/test.jpg
Quelle: https://example.com/source
Publish-Provenienz: {"generator":"generate_agnes_media.py","media_kind":"image","media_path":"assets/generated/test.jpg","origin":"agnes-ai","platform":"instagram","post_id":"17890001","source_lineage":{"origin":"MotoParkTv","original_wording_reuse":false},"source_url":"https://example.com/source","synthetic":true}

## Facebook [GEPOSTET 2026-09-27 12:01 | ID: 998877]
Status: GEPOSTET
Text: Legacy ohne Provenienz
"""

with tempfile.TemporaryDirectory() as tmp:
    old = me.PUBLISHED
    try:
        me.PUBLISHED = Path(tmp) / "PUBLISHED.md"
        me.PUBLISHED.write_text(sample, encoding="utf-8")
        events = [e for e in me.derive_events() if e["type"] == "published"]
    finally:
        me.PUBLISHED = old

assert len(events) == 2
ig = next(e for e in events if e["subject"] == "Instagram")
assert ig["value"] == "17890001"
assert ig["post_id"] == "17890001"
assert ig["media_kind"] == "image"
assert ig["media_path"] == "assets/generated/test.jpg"
assert ig["source_url"] == "https://example.com/source"
assert ig["source_lineage"]["origin"] == "MotoParkTv"
assert ig["source_lineage"]["original_wording_reuse"] is False
assert ig["publish_provenance"]["origin"] == "agnes-ai"
fb = next(e for e in events if e["subject"] == "Facebook")
assert fb["value"] == "998877"
assert "publish_provenance" not in fb
print("PUBLISH PROVENANCE MEMORY: PASS")
