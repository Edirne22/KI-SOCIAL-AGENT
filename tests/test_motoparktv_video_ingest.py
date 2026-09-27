import tempfile
from pathlib import Path
import motoparktv_video_ingest as v
import turkish_rider_memory as mem
import turkish_editor_qm as ed

assert v.freshness_score(16)==100
assert v.freshness_score(48)==75
assert 'Toprak Razgatlıoğlu' in v.riders_in('Bugün Toprak Razgatlıoğlu ile pistteydik.')
assert 'Can Öncü' in v.riders_in('WorldSSP tarafında Can Öncü ile konuştuk.')
assert v.riders_in('Toprak Razgatlıoğlu ve Can Öncü birlikte pistteydi.')==['Toprak Razgatlıoğlu','Can Öncü']
remember=v.remember_video
v.remember_video=lambda row: row
x_video=v.ingest(
    'https://www.youtube.com/watch?v=abcdefghijk',
    'Pistten yeni görüntüler',
    'MotoParkTv özel çekimi',
    '2026-09-27T08:00:00Z',
    transcript='Can Öncü bugün motosikletin ayarlarını anlattı.',
)
v.remember_video=remember
assert x_video['url']==x_video['source_url']=='https://www.youtube.com/watch?v=abcdefghijk'
assert x_video['summary']=='MotoParkTv özel çekimi'
assert x_video['video_transcript']=='Can Öncü bugün motosikletin ayarlarını anlattı.'
x_video['turkish_rider']='Can Öncü'
assert ed._target_supported(x_video)
x={'title':'Toprak pistte antrenman yaptı','summary':'','video_transcript':'Toprak bugün yeni motosikletiyle uzun bir antrenman yaptı ve gün sonunda ekiple birlikte garaja geri döndü','url':'https://www.youtube.com/watch?v=abcdefghijk'}
assert ed._copied_source_phrase(x,'Toprak bugün yeni motosikletiyle uzun bir antrenman yaptı ve gün sonunda ekiple birlikte garaja geri döndü')
assert not ed._copied_source_phrase(x,'Toprak bugün pistte uzun süre çalıştı. Günün sonunda takımın yanına döndü.')
print('TEST – MotoParkTv Video Ingest: PASS')
