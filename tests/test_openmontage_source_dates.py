import unittest
from scripts.openmontage_source_dates import extract_publication_date

class SourceDateTests(unittest.TestCase):
    def test_article_meta(self):
        self.assertEqual(extract_publication_date(
            '<meta property="article:published_time" content="2026-10-18T09:00:00+00:00">'),
            "2026-10-18T09:00:00+00:00")

    def test_json_ld(self):
        html = '<script type="application/ld+json">{"@type":"NewsArticle","datePublished":"2026-10-17T09:00:00Z"}</script>'
        self.assertEqual(extract_publication_date(html), "2026-10-17T09:00:00Z")

    def test_no_metadata_does_not_invent_date(self):
        self.assertEqual(extract_publication_date("<p>Today was a race</p>"), "")

    def test_invalid_date_rejected(self):
        self.assertEqual(extract_publication_date(
            '<meta name="pubdate" content="not-a-date">'), "")
