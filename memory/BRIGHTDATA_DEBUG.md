# Bright Data Debug

Noch keine API-Aufrufe protokolliert.
## 2026-09-12 17:07
- Endpunkt: https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1vikfch901nx3by4
- Status: 200
- Antwort (max. 500 Zeichen): {"snapshot_id":"sd_mtyn1x2jxpdkglu70"}
## 2026-09-12 17:07
- Endpunkt: https://api.brightdata.com/datasets/v3/progress/sd_mtyn1x2jxpdkglu70
- Status: 200
- Antwort (max. 500 Zeichen): {"status":"running","snapshot_id":"sd_mtyn1x2jxpdkglu70","dataset_id":"gd_l1vikfch901nx3by4","running_time":291}
## 2026-09-12 17:07
- Endpunkt: https://api.brightdata.com/datasets/v3/progress/sd_mtyn1x2jxpdkglu70
- Status: 200
- Antwort (max. 500 Zeichen): {"status":"ready","snapshot_id":"sd_mtyn1x2jxpdkglu70","dataset_id":"gd_l1vikfch901nx3by4","error_codes":{"dead_page":1},"records":0,"errors":1,"collection_duration":1547,"avg_duration_per_input":1547}
## 2026-09-12 17:07
- Endpunkt: https://api.brightdata.com/datasets/v3/snapshot/sd_mtyn1x2jxpdkglu70
- Status: 200
- Antwort (max. 500 Zeichen): []
## 2026-09-12 17:34
- Endpunkt: https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_...
- HTTP-Status: 404
- Antwort (max. 500 Zeichen): dataset does not exist
- Snapshot-ID: nicht verfügbar
- Snapshot-Status: nicht verfügbar
- Records: 0
- Errors: 0
- Error-Codes: {}
## 2026-09-12 17:34
- Endpunkt: https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_...
- HTTP-Status: 404
- Antwort (max. 500 Zeichen): dataset does not exist
- Snapshot-ID: nicht verfügbar
- Snapshot-Status: nicht verfügbar
- Records: 0
- Errors: 0
- Error-Codes: {}
## 2026-09-12 17:34
- Endpunkt: https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_...
- HTTP-Status: 404
- Antwort (max. 500 Zeichen): dataset does not exist
- Snapshot-ID: nicht verfügbar
- Snapshot-Status: nicht verfügbar
- Records: 0
- Errors: 0
- Error-Codes: {}
## Diagnose Instagram (2026-09-12 23:49)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url
- HTTP-Status: 400
- Records: 0
- Fehler: Invalid input provided, ['url', 'Value should match pattern ^https://(www.)?instagram.com/[a-zA-Z0-9._-]+(/?[a-zA-Z0-9._-]+/?)?$']
- Antwort (max. 500 Zeichen): {"error":"Invalid input provided","code":"validation_error","type":"validation","line":"{\"url\":\"https://www.instagram.com/explore/tags/motogp/\",\"start_date\":\"09-05-2026\",\"end_date\":\"09-11-2026\",\"post_type\":\"\"}","index":1,"errors":[["url","Value should match pattern ^https://(www.)?instagram.com/[a-zA-Z0-9._-]+(/?[a-zA-Z0-9._-]+/?)?$"]]}
## Diagnose Facebook (2026-09-12 23:51)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true
- HTTP-Status: 202
- Records: 0
- Fehler: HTTP 202
- Antwort (max. 500 Zeichen): {"snapshot_id":"sd_mtyx4u4p1kml9j3ncb","message":"Your request is still in progress and cannot be retrieved in this call. Use the provided Snapshot ID to track progress via the Monitor Snapshot endpoint and download it once ready via the Download Snapshot endpoint. More information on https://docs.brightdata.com/api-reference/web-scraper-api/management-apis/monitor-progress"}
## Diagnose YouTube (2026-09-12 23:51)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword
- HTTP-Status: 200
- Records: 0
- Fehler: keine
- Antwort (max. 500 Zeichen):
## Diagnose TikTok (2026-09-12 23:52)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true
- HTTP-Status: 202
- Records: 0
- Fehler: HTTP 202
- Antwort (max. 500 Zeichen): {"snapshot_id":"sd_mtyx6bwatd1vxy8gl","message":"Your request is still in progress and cannot be retrieved in this call. Use the provided Snapshot ID to track progress via the Monitor Snapshot endpoint and download it once ready via the Download Snapshot endpoint. More information on https://docs.brightdata.com/api-reference/web-scraper-api/management-apis/monitor-progress"}
## Diagnose X (2026-09-12 23:52)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url
- HTTP-Status: 200
- Records: 0
- Fehler: keine
- Antwort (max. 500 Zeichen): {"timestamp":"2026-09-12T21:52:15.691Z","input":{"url":"https://x.com/toprakrazgatlioglu","start_date":"2026-09-05","end_date":"2026-09-11"},"error":"The navigation resulted in a dead page (404 status code)","error_code":"dead_page"}
{"timestamp":"2026-09-12T21:52:20.874Z","input":{"url":"https://x.com/MotoGP","start_date":"2026-09-05","end_date":"2026-09-11"},"error":"No public posts were found in the profile for the specified period.","error_code":"dead_page"}

## Diagnose Instagram (2026-09-13 00:04)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url
- HTTP-Status: 202
- Records: 0
- Fehler: Unerwartetes asynchrones Ergebnis für synchronen Scraper
- Antwort (max. 500 Zeichen): {"snapshot_id":"sd_mtyxln0x4oxzd7pyd","message":"Your request is still in progress and cannot be retrieved in this call. Use the provided Snapshot ID to track progress via the Monitor Snapshot endpoint and download it once ready via the Download Snapshot endpoint. More information on https://docs.brightdata.com/api-reference/web-scraper-api/management-apis/monitor-progress"}

## Diagnose Facebook (2026-09-13 00:07)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Snapshot-ID: sd_mtyxmxpk26xjp2kyvi
- Polling-Versuche: 15
- Letzter Status: ready
- Wartezeit: 144 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.facebook.com/MotoGP/posts/pfbid02rqrwkfVuU19enc5hVGFWjdBpFK8uXqfhDZLwuLm6rvRz7W8R12XxbVQcxnqbfNmZl","post_id":"1530570235770823","user_url":"https://www.facebook.com/MotoGP","user_username_raw":"MotoGP","content":"The best way to finish Super Saturday, with the best fans of the world! ❤️\n\n#SanMarinoGP🇸🇲 #MotoGP","date_posted":"2026-09-12T19:30:10.000Z","hashtags":["sanmarinogp","motogp"],"num_comments":7,"num_shares":11,"num_likes_type":{"type":"Like","num":323},"page_name"

## Diagnose YouTube (2026-09-13 00:07)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword
- HTTP-Status: 200
- Records: 0
- Fehler: keine
- Antwort (max. 500 Zeichen):

## Diagnose TikTok (2026-09-13 00:11)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: Snapshot-Timeout nach 3 Minuten
- Snapshot-ID: sd_mtyxrhwa149kagzu2d
- Polling-Versuche: 18
- Letzter Status: running
- Wartezeit: 180 Sekunden
- Antwort (max. 500 Zeichen): {"status":"running","snapshot_id":"sd_mtyxrhwa149kagzu2d","dataset_id":"gd_m7n5ixlw1gc4no56kx","running_time":233878}

## Diagnose X (2026-09-13 00:12)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url
- HTTP-Status: 200
- Records: 0
- Fehler: keine
- Antwort (max. 500 Zeichen): {"id":"2098828989867376993","user_posted":"MotoGP","name":"MotoGP™🏁","description":"You can't miss what the riders said after today's intense Sprint at Misano! 👀\n\n#SanMarinoGP🇸🇲\n","date_posted":"2026-09-12T17:40:00.000Z","photos":null,"url":"https://x.com/motogp/status/2098828989867376993","quoted_post":{"photos":null,"videos":null},"tagged_users":null,"replies":1,"reposts":4,"likes":33,"views":15800,"external_url":"https://www.motogp.com/en/videos/2026/09/12/word-on-the-grid-a-super-saturday
