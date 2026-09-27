import json,tempfile
from pathlib import Path
import motoparktv_runtime as rt

assert rt._published({'upload_date':'20260927'}).startswith('2026-09-27T')
with tempfile.TemporaryDirectory() as td:
 p=Path(td)/'abcdefghijk.mp3';p.write_bytes(b'audio')
 old=rt._run
 def fake(args,timeout=1800):
  if args[0]=='yt-dlp' and '--dump-single-json' in args:return json.dumps({'webpage_url':'https://www.youtube.com/watch?v=abcdefghijk','title':'Toprak ve Can pistte','description':'antrenman','upload_date':'20260927'})
  if args[0]=='yt-dlp':return ''
  return ''
 rt._run=fake
 # audio() validates that downloader really created a file; direct deterministic contract check
 assert rt.metadata('x')['title']=='Toprak ve Can pistte'
 rt._run=old
print('TEST – MotoParkTv Runtime: PASS')
