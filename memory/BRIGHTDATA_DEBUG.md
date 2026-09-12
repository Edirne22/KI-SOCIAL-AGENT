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

