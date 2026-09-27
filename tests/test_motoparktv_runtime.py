import json,tempfile
from pathlib import Path
import motoparktv_runtime as rt
import motoparktv_video_ingest as ingest_mod
import turkish_rider_memory as mem

assert rt._published({'upload_date':'20260927'}).startswith('2026-09-27T')

with tempfile.TemporaryDirectory() as td:
 root=Path(td)
 old_run=rt._run;old_audio=rt.audio;old_whisper=rt.whisper
 old_memory=mem.MEMORY_PATH
 old_video_memory=Path("memory/MOTOPARKTV_VIDEO_MEMORY.json")
 try:
  def fake_run(args,timeout=1800):
   if args[0]=='yt-dlp' and '--dump-single-json' in args:
    return json.dumps({'webpage_url':'https://www.youtube.com/watch?v=abcdefghijk',
      'title':'Toprak ve Can pistte','description':'Can Oncu WorldSSP antrenman',
      'upload_date':'20260927'})
   return ''
  rt._run=fake_run
  assert rt.metadata('x')['title']=='Toprak ve Can pistte'

  # Provider-free E2E contract: metadata -> local audio -> local Whisper -> ingest
  # -> rider recognition -> lineage -> dedicated video memory.
  rt.audio=lambda url,outdir: root/'abcdefghijk.mp3'
  (root/'abcdefghijk.mp3').write_bytes(b'audio')
  rt.whisper=lambda audio_path,model='small':'Can Oncu WorldSSP pistte calisiyor.'
  video_memory=root/'MOTOPARKTV_VIDEO_MEMORY.json'
  original_remember=ingest_mod.remember_video
  def remember_local(row):
   try:data=json.loads(video_memory.read_text(encoding='utf-8')) if video_memory.exists() else {'version':1,'videos':[]}
   except Exception:data={'version':1,'videos':[]}
   safe={k:v for k,v in row.items() if k!='transcript'}
   safe['transcript_excerpt']=str(row.get('transcript',''))[:4000]
   data['videos']=[safe];video_memory.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
   return safe
  ingest_mod.remember_video=remember_local
  row=rt.video_candidate('https://www.youtube.com/watch?v=abcdefghijk')
  assert row['source_url']==row['url']
  assert 'Can Öncü' in row['riders']
  assert row['video_transcript'].startswith('Can Oncu')
  lineage=row['source_lineage']
  assert lineage['origin']=='MotoParkTv'
  assert lineage['source_url']==row['source_url']
  assert lineage['transcription']=='local-whisper'
  assert lineage['evidence_fields']==['title','summary','video_transcript']
  assert lineage['original_wording_reuse'] is False
  saved=json.loads(video_memory.read_text(encoding='utf-8'))['videos'][0]
  assert saved['source_lineage']==lineage
  assert saved['transcript_excerpt'].startswith('Can Oncu')
 finally:
  rt._run=old_run;rt.audio=old_audio;rt.whisper=old_whisper
  ingest_mod.remember_video=original_remember
  mem.MEMORY_PATH=old_memory

print('TEST – MotoParkTv Runtime + Lineage E2E: PASS')
