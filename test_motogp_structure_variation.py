import json
import random
import unittest

import motogp_content_agency_v2 as agency


class MotoGPStructureVariationTests(unittest.TestCase):
    def test_all_six_variants_can_be_parsed(self):
        samples = {
            "HOOK_BODY_QUESTION": {"hook": "Starker Auftakt.", "body": "Das Rennen bleibt eng.", "question": "Wie seht ihr das?"},
            "BODY_QUESTION": {"body": "Das Rennen bleibt eng. Der Fahrer hält den Druck hoch.", "question": "Wie seht ihr das?"},
            "STORY_QUESTION": {"story": "Am Anfang war alles offen. Dann fiel die Entscheidung.", "question": "Wie seht ihr das?"},
            "FACT_FACT_FACT": {"facts": ["Fakt eins.", "Fakt zwei.", "Fakt drei."], "cta": "Mehr Racing folgt."},
            "QUESTION_HOOK_BODY": {"question": "Wie seht ihr das?", "body": "Das Rennen bleibt eng. Der Fahrer hält den Druck hoch."},
            "ZITAT_BODY": {"quote": "Das war ein hartes Rennen.", "body": "Der Satz stammt aus der gelieferten Quelle. Danach folgte der Kontext.", "question": "Wie seht ihr das?"},
        }
        self.assertEqual(set(samples), set(agency.STRUCTURE_VARIANTS))
        for variant, payload in samples.items():
            with self.subTest(variant=variant):
                parts = agency._parse_editor_json(json.dumps(payload), variant)
                self.assertTrue(parts)
                self.assertGreaterEqual(len(parts), 2)

    def test_each_variant_requests_its_own_schema(self):
        item = {"title": "MotoGP rider completes a demanding race weekend", "summary": "Verified source summary.", "series": "MotoGP"}
        for variant, (schema, _) in agency.STRUCTURE_VARIANTS.items():
            with self.subTest(variant=variant):
                prompt = agency._editor_prompt(item.copy(), structure_variant=variant)
                self.assertIn(f"STRUKTUR-VARIANTE: {variant}", prompt)
                self.assertIn(schema, prompt)

    def test_random_choice_varies_within_ten_runs(self):
        state = random.getstate()
        try:
            random.seed(20260924)
            choices = [agency.choose_structure_variant() for _ in range(10)]
        finally:
            random.setstate(state)
        self.assertGreaterEqual(len(set(choices)), 2)
        self.assertTrue(set(choices).issubset(agency.STRUCTURE_VARIANTS))


if __name__ == "__main__":
    unittest.main()
