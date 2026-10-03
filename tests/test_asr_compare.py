import unittest
from tools.asr_compare import alignment, compare, contains_phrase

class ASRCompareTests(unittest.TestCase):
    def test_unicode(self):
        self.assertTrue(contains_phrase("Can Öncü fährt.", "Öncü"))
        self.assertFalse(contains_phrase("Can Oncu fährt.", "Öncü"))

    def test_insertions(self):
        self.assertEqual(alignment("Merhaba Bülent", "Merhaba Bülent Toprak"), (0, 0, 1))

    def test_deletions(self):
        self.assertEqual(alignment("BMW M 1000 R", "BMW M R"), (0, 1, 0))

    def test_unprompted_name(self):
        result = compare([{"language": "tr", "reference": "Merhaba Bülent",
                           "baseline": "Merhaba Bülent Toprak",
                           "candidate": "Merhaba Bülent", "names": ["Bülent", "Toprak"]}])
        self.assertEqual(result["tr"]["baseline"]["insertions"], 1)
        self.assertEqual(result["tr"]["candidate"]["insertions"], 0)
        self.assertEqual(result["tr"]["baseline"]["unprompted_names"], ["Toprak"])

if __name__ == "__main__":
    unittest.main()
