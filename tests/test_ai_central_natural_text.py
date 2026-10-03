import unittest
from scripts.ai_central_natural_text import classify_natural_text as route

class NaturalTelegramTest(unittest.TestCase):
    def test_explicit_private_request(self):
        self.assertEqual(route("KI: Erstelle einen privaten Geburtstagsclip").kind,"draft")
    def test_natural_private_request(self):
        self.assertEqual(route("Erstelle einen privaten Clip").kind,"draft")
    def test_legacy_and_short_ack_not_hijacked(self):
        for message in ("T1","T1,T3","motogp 2,4","racing top10","ok","ja","/zentrale status"):
            self.assertNotEqual(route(message).kind,"draft",message)
    def test_ambiguous_publish_never_becomes_task(self):
        for message in ("KI: Poste T1","Mach und veröffentlichen","Freigeben"):
            self.assertNotEqual(route(message).kind,"draft",message)
    def test_casual_text_not_auto_dispatched(self):
        self.assertEqual(route("Hallo, wie geht es dir?").kind,"clarify")

if __name__=="__main__":unittest.main()
