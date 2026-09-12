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

## Diagnose Instagram (2026-09-13 00:42)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 377 Zeichen
- Snapshot-ID: sd_mtyyxlopq13cbhj13
- Polling-Versuche: 5
- Letzter Status: ready
- Wartezeit: 41 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.instagram.com/p/DdLv2MDiJdc/","user_posted":"motogp","description":"It’s going to be a red-hot #TissotSprint 🔥\n\n#SanMarinoGP 🇸🇲 #MotoGP","hashtags":["#TissotSprint","#SanMarinoGP","#MotoGP"],"num_comments":126,"date_posted":"2026-09-12T10:14:52.000Z","likes":29125,"photos":["https://scontent-muc2-1.cdninstagram.com/v/t51.82787-15/806159997_18637538671027895_3601682347454655251_n.jpg?stp=dst-jpg_e35_s640x640_tt6&_nc_cat=102&ccb=7-5&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiQ0FST1VT

## Diagnose Facebook (2026-09-13 00:43)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 377 Zeichen
- Snapshot-ID: sd_mtyyztnsj9p03wbqx
- Polling-Versuche: 5
- Letzter Status: ready
- Wartezeit: 41 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.facebook.com/MotoGP/posts/pfbid02rqrwkfVuU19enc5hVGFWjdBpFK8uXqfhDZLwuLm6rvRz7W8R12XxbVQcxnqbfNmZl","post_id":"1530570235770823","user_url":"https://www.facebook.com/MotoGP","user_username_raw":"MotoGP","content":"The best way to finish Super Saturday, with the best fans of the world! ❤️\n\n#SanMarinoGP🇸🇲 #MotoGP","date_posted":"2026-09-12T19:30:10.000Z","hashtags":["sanmarinogp","motogp"],"num_comments":7,"num_shares":12,"num_likes_type":{"type":"Like","num":355},"page_name"

## Diagnose YouTube (2026-09-13 00:43)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword
- HTTP-Status: 200
- Records: 0
- Fehler: Leere Antwort – Plattform nicht verfügbar
- Body-Länge: 0 Zeichen
- Antwort (max. 500 Zeichen):

## Diagnose TikTok (2026-09-13 00:49)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 378 Zeichen
- Snapshot-ID: sd_mtyz25sv1beopch6gc
- Polling-Versuche: 18
- Letzter Status: ready
- Wartezeit: 259 Sekunden
- Antwort (max. 500 Zeichen): {"timestamp":"2026-09-12T22:44:29.577Z","input":{"url":"https://www.tiktok.com/search?lang=en&q=motogp&t=1789253034862","num_of_posts":10,"country":""},"error":"Couldn't find this hashtag","error_code":"dead_page"}
{"url":"https://www.tiktok.com/@motogp/video/7684273737302035734","post_id":"7684273737302035734","description":"Spotted in Misano 👀 #SanMarinoGP 🇸🇲 #MotoGP #SportsOnTikTok ","create_time":"2026-09-11T13:46:47.000Z","digg_count":57300,"share_count":"4676","collect_count":2939,"comment

## Diagnose X (2026-09-13 00:49)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url
- HTTP-Status: 200
- Records: 10
- Fehler: keine
- Body-Länge: 14258 Zeichen
- Erste URL: https://x.com/worldsbk/status/2098732943917158803
- Antwort (max. 500 Zeichen): {"id":"2098732943917158803","user_posted":"WorldSBK","name":"WorldSBK","description":"Summer was great. But we missed this 🥹🏁 \n\nWhat did you miss the most? 💭\n\n#FrenchWorldSBK 🇫🇷 #WorldSBK","date_posted":"2026-09-12T11:18:21.000Z","photos":["https://pbs.twimg.com/media/HSAyc_pW8AYfhHx.jpg","https://pbs.twimg.com/media/HSAydASawAAMV4A.jpg","https://pbs.twimg.com/media/HSAyc_2XoAACUIo.jpg","https://pbs.twimg.com/media/HSAydANakAEIBFj.jpg"],"url":"https://x.com/worldsbk/status/209873294391715880

## Diagnose Instagram (2026-09-13 00:53)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 378 Zeichen
- Snapshot-ID: sd_mtyzd2ay28ou3jzjx8
- Polling-Versuche: 3
- Letzter Status: ready
- Wartezeit: 20 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.instagram.com/p/Dc-oelwiEUf/","user_posted":"motogp","description":"Save this one if you want to keep up with all the action 😉⏰\n\n#SanMarinoGP 🇸🇲 #MotoGP","hashtags":["#SanMarinoGP","#MotoGP"],"num_comments":38,"date_posted":"2026-09-07T08:00:02.000Z","likes":18041,"photos":["https://scontent-sjc6-1.cdninstagram.com/v/t51.82787-15/793244879_18634751131027895_2707803452069001692_n.jpg?stp=dst-jpg_e35_s640x640_tt6&_nc_cat=107&ccb=7-5&_nc_sid=18de74&efg=eyJlZmdfdGFnIjoiRkVFRC5i

## Diagnose Facebook (2026-09-13 00:56)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 377 Zeichen
- Snapshot-ID: sd_mtyzesjoff1z89px0
- Polling-Versuche: 9
- Letzter Status: ready
- Wartezeit: 80 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.facebook.com/MotoGP/posts/pfbid02rqrwkfVuU19enc5hVGFWjdBpFK8uXqfhDZLwuLm6rvRz7W8R12XxbVQcxnqbfNmZl","post_id":"1530570235770823","user_url":"https://www.facebook.com/MotoGP","user_username_raw":"MotoGP","content":"The best way to finish Super Saturday, with the best fans of the world! ❤️\n\n#SanMarinoGP🇸🇲 #MotoGP","date_posted":"2026-09-12T19:30:10.000Z","hashtags":["sanmarinogp","motogp"],"num_comments":7,"num_shares":12,"num_likes_type":{"type":"Like","num":368},"page_name"

## Diagnose YouTube (2026-09-13 00:56)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword
- HTTP-Status: 200
- Records: 0
- Fehler: Leere Antwort – Plattform nicht verfügbar
- Body-Länge: 0 Zeichen
- Antwort (max. 500 Zeichen):

## Diagnose TikTok (2026-09-13 00:59)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: keine
- Body-Länge: 378 Zeichen
- Snapshot-ID: sd_mtyzhz8o1bbkf7dlku
- Polling-Versuche: 11
- Letzter Status: ready
- Wartezeit: 150 Sekunden
- Antwort (max. 500 Zeichen): {"url":"https://www.tiktok.com/@motogp/video/7684273737302035734","post_id":"7684273737302035734","description":"Spotted in Misano 👀 #SanMarinoGP 🇸🇲 #MotoGP #SportsOnTikTok ","create_time":"2026-09-11T13:46:47.000Z","digg_count":57400,"share_count":"4678","collect_count":2941,"comment_count":1101,"play_count":551700,"video_duration":8,"hashtags":["sanmarinogp","motogp","sportsontiktok"],"original_sound":"Plantdaddy55: Ed bassmaster","profile_id":"6690198746083673094","profile_username":"MotoGP™"

## Diagnose X (2026-09-13 01:00)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url
- HTTP-Status: 200
- Records: 10
- Fehler: keine
- Body-Länge: 14258 Zeichen
- Erste URL: https://x.com/worldsbk/status/2098305043715789037
- Antwort (max. 500 Zeichen): {"id":"2098305043715789037","user_posted":"WorldSBK","name":"WorldSBK","description":"What better #FridayFeeling than celebrating an 11th career hat-trick? 🏆🔥\n\n#FrenchWorldSBK 🇮🇹 #WorldSBK","date_posted":"2026-09-11T06:58:01.000Z","photos":null,"url":"https://x.com/worldsbk/status/2098305043715789037","quoted_post":{"photos":null,"videos":null},"tagged_users":null,"replies":0,"reposts":2,"likes":100,"views":6947,"external_url":null,"hashtags":["FridayFeeling","FrenchWorldSBK","WorldSBK"],"foll

## Diagnose Instagram (2026-09-13 01:23)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk5ns7kz21pck8jpis&notify=false&include_errors=true&type=discover_new&discover_by=url
- HTTP-Status: 202 (asynchron)
- Records: 22
- Fehler: keine
- Body-Länge: 378 Zeichen
- Snapshot-ID: sd_mtz0fb1n2i3ek6xad9
- Polling-Versuche: 5
- Letzter Status: ready
- Wartezeit: 41 Sekunden
- Erste URL: https://www.instagram.com/p/DdJ7mqdCADq/
- Antwort (max. 500 Zeichen): {"url":"https://www.instagram.com/p/DdJ7mqdCADq/","user_posted":"pramacracing","description":"@toprakrazgatlioglu7 - P21 💬\nSanMarinoGP - PRACTICE 🇸🇲\n\nToday was a very strange day. This morning, with the medium tyre, the bike felt really good and I was feeling very positive. I did my best lap time on a used medium tyre, so I was expecting to make a big step with the soft. Instead, when we put the soft tyre on, the bike completely changed. It felt almost like I was riding a rental bike! I was r

## Diagnose Facebook (2026-09-13 01:25)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lkaxegm826bjpoo9m5&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 141
- Fehler: keine
- Body-Länge: 377 Zeichen
- Snapshot-ID: sd_mtz0hiqn2xllbk1y9
- Polling-Versuche: 5
- Letzter Status: ready
- Wartezeit: 41 Sekunden
- Erste URL: https://www.facebook.com/MotoGP/posts/pfbid02rqrwkfVuU19enc5hVGFWjdBpFK8uXqfhDZLwuLm6rvRz7W8R12XxbVQcxnqbfNmZl
- Antwort (max. 500 Zeichen): {"url":"https://www.facebook.com/MotoGP/posts/pfbid02rqrwkfVuU19enc5hVGFWjdBpFK8uXqfhDZLwuLm6rvRz7W8R12XxbVQcxnqbfNmZl","post_id":"1530570235770823","user_url":"https://www.facebook.com/MotoGP","user_username_raw":"MotoGP","content":"The best way to finish Super Saturday, with the best fans of the world! ❤️\n\n#SanMarinoGP🇸🇲 #MotoGP","date_posted":"2026-09-12T19:30:10.000Z","hashtags":["sanmarinogp","motogp"],"num_comments":8,"num_shares":12,"num_likes_type":{"type":"Like","num":385},"page_name"

## Diagnose YouTube (2026-09-13 01:25)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lk56epmy2i5g7lzu0k&notify=false&include_errors=true&type=discover_new&discover_by=keyword
- HTTP-Status: 200
- Records: 0
- Fehler: Leere Antwort – Plattform nicht verfügbar
- Body-Länge: 0 Zeichen
- Antwort (max. 500 Zeichen):

## Diagnose TikTok (2026-09-13 01:31)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_m7n5ixlw1gc4no56kx&notify=false&include_errors=true
- HTTP-Status: 202 (asynchron)
- Records: 0
- Fehler: Snapshot-Timeout nach 5 Minuten
- Body-Länge: 377 Zeichen
- Snapshot-ID: sd_mtz0jw9vss162ep06
- Polling-Versuche: 20
- Letzter Status: running
- Wartezeit: 300 Sekunden
- Antwort (max. 500 Zeichen): {"status":"running","snapshot_id":"sd_mtz0jw9vss162ep06","dataset_id":"gd_m7n5ixlw1gc4no56kx","running_time":349672}

## Diagnose X (2026-09-13 01:32)
- Endpoint: https://api.brightdata.com/datasets/v3/scrape?dataset_id=gd_lwxkxvnf1cynvib9co&notify=false&include_errors=true&type=discover_new&discover_by=profile_url
- HTTP-Status: 200
- Records: 10
- Fehler: keine
- Body-Länge: 14258 Zeichen
- Erste URL: https://x.com/worldsbk/status/2098381043334000720
- Antwort (max. 500 Zeichen): {"id":"2098381043334000720","user_posted":"WorldSBK","name":"WorldSBK","description":"Early drama! 💥 \n\nJorge Navarro was pushing hard at the front when it all came undone 😬\n\n#FrenchWorldSBK 🇫🇷 #WorldSBK","date_posted":"2026-09-11T12:00:01.000Z","photos":null,"url":"https://x.com/worldsbk/status/2098381043334000720","quoted_post":{"photos":null,"videos":null},"tagged_users":null,"replies":0,"reposts":4,"likes":89,"views":11263,"external_url":null,"hashtags":["FrenchWorldSBK","WorldSBK"],"foll
