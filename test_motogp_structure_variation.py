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


def test_racing_qm_accepts_variant_structure_contracts():
 from motogp_quality_manager import review
 base={'title':'Marc Marquez gewinnt MotoGP Rennen','summary':'Marc Marquez gewinnt das MotoGP Rennen.','series':'MotoGP'}
 samples={
  'HOOK_BODY_QUESTION':'Hook.\n\nFakt zum Rennen.\n\nWas meinst du?\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
  'BODY_QUESTION':'Fakt zum Rennen.\n\nWas meinst du?\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
  'STORY_QUESTION':'Marc Marquez gewinnt das Rennen.\n\nWie siehst du das?\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
  'FACT_FACT_FACT':'Marc Marquez gewinnt.\n\nMotoGP Rennen entschieden.\n\nMarquez steht als Sieger fest.\n\nMehr Racing bei Buelents Bike Life.\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
  'QUESTION_HOOK_BODY':'Was meinst du?\n\nMarc Marquez gewinnt das MotoGP Rennen.\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
  'ZITAT_BODY':'Marc Marquez gewinnt.\n\nDer MotoGP-Sieg steht fest.\n\nWie siehst du das?\n\n#MotoGP #MarcMarquez #MotorradRacing #BuelentsBikeLife',
 }
 for variant,caption in samples.items():
  item=dict(base,structure_variant=variant)
  ok_,errors=review(item,caption)
  assert ok_,(variant,errors)
