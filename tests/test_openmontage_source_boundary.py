import unittest
from openmontage_research import _detect_source_status


class OpenMontageSourceBoundaryTests(unittest.TestCase):
    def test_exact_official_host(self):
        self.assertEqual(_detect_source_status("https://motogp.com/news", "result"), "official")

    def test_official_subdomain(self):
        self.assertEqual(_detect_source_status("https://www.worldsbk.com/news", "result"), "official")

    def test_spoofed_host_is_not_official(self):
        for url in ("https://motogp.com.evil.example/news",
                    "https://notmotogp.com/news",
                    "https://evil.example/path/motogp.com"):
            with self.subTest(url=url):
                self.assertEqual(_detect_source_status(url, "result"), "journalistic")

    def test_rumor_even_on_official_host(self):
        self.assertEqual(_detect_source_status("https://motogp.com/news", "rumor"), "rumor")


if __name__ == "__main__":
    unittest.main()
