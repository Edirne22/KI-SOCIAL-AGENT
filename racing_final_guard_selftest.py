"""Offline regression tests for title-first Final-Guard classification."""
import unittest
from racing_final_guard import expected_series, review

class TitleSeriesTests(unittest.TestCase):
 def test_agius_motogp_debut_passes_final_guard(self):
  x={'title':'Tech3 signs Agius for MotoGP debut from 2027',
     'summary':'Agius moves from Moto2.','source_series':'Moto2','series':'MotoGP'}
  self.assertEqual(expected_series(x),'MotoGP')
  self.assertEqual(review(x,'Agius startet ab 2027 bei Tech3 in der MotoGP. #MotoGP'),(True,[]))
 def test_agius_profile_is_motogp(self):
  x={'title':"Who is Senna Agius? Meet Australia's new MotoGP star",
     'summary':'Agius raced in Moto2.','series':'MotoGP','source_series':'Moto2'}
  self.assertEqual(review(x,'Senna Agius im Porträt. #MotoGP'),(True,[]))
 def test_title_wins_over_conflicting_metadata(self):
  x={'title':'Agius MotoGP debut','summary':'Moto2 rider','series':'Moto2'}
  self.assertEqual(expected_series(x),'MotoGP')
  passed, errors=review(x,'Agius #Moto2')
  self.assertFalse(passed)
  self.assertTrue(any('Metadatum' in e for e in errors))
 def test_explicit_lower_class_still_wins(self):
  for series in ('Moto2','Moto3'):
   with self.subTest(series=series):
    self.assertEqual(expected_series({'title':f'Agius takes {series} pole',
     'summary':'The Official Home of MotoGP','series':'MotoGP'}),series)
 def test_generic_summary_does_not_promote_rider(self):
  self.assertEqual(expected_series({'title':'Agius takes pole',
   'summary':'The Official Home of MotoGP','series':'Moto2'}),'Moto2')
 def test_other_explicit_series(self):
  for series in ('WorldSBK','WorldSSP','WorldSSP300','WorldWCR'):
   with self.subTest(series=series):
    self.assertEqual(expected_series({'title':f'Agius joins {series}',
     'summary':'Moto2 background','series':'Moto2'}),series)
 def test_ambiguous_title_does_not_guess_motogp(self):
  self.assertEqual(expected_series({'title':'MotoGP and Moto2 news',
    'summary':'Agius','series':'Moto2'}),'Moto2')
 def test_existing_safety_guards_remain(self):
  for x, caption in [
   ({'title':'Behind the scenes with MotoGP','series':'MotoGP'},'Vlog #MotoGP'),
   ({'title':'WorldWCR race','series':'WorldWCR'},'Race #WorldWCR'),
   ({'title':'Agius MotoGP debut','series':'MotoGP'},'Agius #Moto2'),
   ({'title':'Razgatlioglu MotoGP test','series':'MotoGP'},'Rahil Etgar Razgatlioglu #MotoGP')]:
   with self.subTest(x=x):
    self.assertFalse(review(x,caption)[0])

if __name__=='__main__':unittest.main(verbosity=2)
