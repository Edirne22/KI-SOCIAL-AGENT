from datetime import datetime, timezone, timedelta
import motogp_content_agency_v2 as agency

now=datetime(2026,9,26,12,0,tzinfo=timezone.utc)

def item(title,days,kind='news'):
    return {
        'title':title,
        'summary':'Can Oncu is explicitly supported by the official source.',
        'url':'https://www.worldsbk.com/en/news/2026/09/25/example/1',
        'turkish_rider':'Can Oncu',
        'kind':kind,
        'published_at':(now-timedelta(days=days)).isoformat(),
        'series':'WorldSSP','source_series':'WorldSSP','series_locked':True,
    }

# Turkish candidate gate is intentionally independent from the normal Racing
# relevance/feature gate, but freshness and identity remain mandatory.
fresh=item('A supported Turkish rider update',3)
assert agency.turkish_candidate_gate(fresh,now,7)
assert agency.turkish_candidate_reason(fresh,now,7)=='PASS'
assert not agency.turkish_candidate_gate(item('Old supported rider update',11),now,10)
assert agency.turkish_candidate_reason(item('Old supported rider update',11),now,10)=='older-than-window'
assert not agency.turkish_candidate_gate(item('Rider profile',0,'profile'),now,10)
missing=item('Missing date',0); missing.pop('published_at'); missing['url']='https://www.worldsbk.com/en/news/example-undated'
assert not agency.turkish_candidate_gate(missing,now,10)
assert agency.turkish_candidate_reason(missing,now,10)=='missing-date'
no_rider=item('No rider',0); no_rider['turkish_rider']=''; no_rider['summary']='generic racing update'
assert not agency.turkish_candidate_gate(no_rider,now,10)
print('TEST – Turkish Candidate Gate: PASS')
