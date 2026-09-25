import pytest
from turkish_rider_names import canonical_rider, fold
from turkish_riders_scout import rider_for

@pytest.mark.parametrize("variant,expected",[
 ("Toprak Razgatlıoğlu","Toprak Razgatlıoğlu"),
 ("Toprak Razgatlioglu","Toprak Razgatlıoğlu"),
 ("Toprak Razgatlıoglu","Toprak Razgatlıoğlu"),
 ("Toprak Razgatliğlu","Toprak Razgatlıoğlu"),
 ("Can Öncü","Can Öncü"),("Can Oncu","Can Öncü"),("C. Öncü","Can Öncü"),("C. Oncu","Can Öncü"),
 ("Deniz Öncü","Deniz Öncü"),("Deniz Oncu","Deniz Öncü"),("D. Öncü","Deniz Öncü"),("D. Oncu","Deniz Öncü"),
 ("Bahattin Sofuoğlu","Bahattin Sofuoğlu"),("Bahattin Sofuoglu","Bahattin Sofuoğlu"),("Bahattin Sofouglu","Bahattin Sofuoğlu"),
 ("B. Sofuoğlu","Bahattin Sofuoğlu"),("B. Sofouglu","Bahattin Sofuoğlu"),
 ("Zayn Sofuoğlu","Zayn Sofuoğlu"),("Zayn Sofuoglu","Zayn Sofuoğlu"),("Z. Sofuoğlu","Zayn Sofuoğlu"),
])
def test_all_mixed_spellings(variant,expected):
 assert canonical_rider("News: "+variant+" confirmed")==expected
 assert rider_for("News: "+variant+" confirmed")==expected

def test_combining_unicode_is_normalized():
 assert canonical_rider("Deniz O\u0308ncu\u0308 wins")=="Deniz Öncü"

def test_dotless_i_and_g_breve_collapse():
 assert fold("Razgatlıoğlu")==fold("Razgatlioglu")

def test_ambiguous_oncu_surname_is_not_guessed():
 assert canonical_rider("Öncü wins the race")==""
 assert rider_for("Oncu wins the race")==""

def test_ambiguous_sofuoglu_surname_is_not_guessed():
 assert canonical_rider("Sofuoğlu joins a team")==""
