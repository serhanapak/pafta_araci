from pafta.hata import Bulgu, ozet

# Gecerli bulgu
b = Bulgu("TEST", "HATA", "Test mesaji")
assert b.kod == "TEST"

# Gecersiz siddet reddedilmeli
try:
    Bulgu("TEST", "KRITIK", "Hatali")
    raise AssertionError("Gecersiz siddet kabul edildi")
except ValueError:
    pass

# Ozet kontrolu
liste = [
    Bulgu("A", "HATA", "A"),
    Bulgu("B", "UYARI", "B"),
    Bulgu("C", "HATA", "C"),
]
assert ozet(liste) == {"BILGI": 0, "UYARI": 1, "HATA": 2}

print("HATA MODULU: BUTUN TESTLER GECTI")
