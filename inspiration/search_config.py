"""Zentrale, priorisierte Suchbegriffe und sichere Anbieter-Konfiguration."""
SEARCH_PRIORITIES = [
    ("Türkische Racer", ["toprak", "razgatlioglu", "öncü", "oncu", "sofuoglu", "türkische rennfahrer", "turkish riders motogp"]),
    ("MotoGP", ["motogp top 10", "motogp standings", "motogp news"]),
    ("WorldSBK", ["worldsbk", "superbike wm", "worldsbk standings"]),
    ("Formel 1", ["formel 1", "formula 1", "f1 race weekend", "f1 news"]),
    ("KI-Prompting", ["ai prompting trends", "ki content creation", "gemini prompts", "claude prompts"]),
    ("Motorrad & Reisen", ["motorrad trending", "biker content", "motorrad türkei", "türkische biker"]),
    ("Ride With Me", ["ride with me app", "ridewithme motorcycle"]),
]
PLATFORMS = ("instagram", "facebook", "youtube")
MAX_REQUESTS_PER_PLATFORM = 10
APIFY_ACTORS = {"instagram": "apify/instagram-hashtag-scraper", "facebook": "scrapier/facebook-pages-scraper", "youtube": "mighty_monk/youtube-channel-scraper"}
# Bright-Data-IDs für Facebook/YouTube werden bewusst erst verwendet, wenn sie als Secret gesetzt sind.
BRIGHTDATA_DATASETS = {"instagram": "gd_l1vikfch901nx3by4", "facebook": "", "youtube": ""}
