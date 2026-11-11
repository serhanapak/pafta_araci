import pytest

from pafta.hata import Bulgu, ozet


def test_gecerli_bulgu():
    b = Bulgu("TEST", "HATA", "Test mesaji")
    assert b.kod == "TEST"


def test_gecersiz_siddet_reddedilir():
    with pytest.raises(ValueError):
        Bulgu("TEST", "KRITIK", "Hatali")


def test_ozet():
    liste = [
        Bulgu("A", "HATA", "A"),
        Bulgu("B", "UYARI", "B"),
        Bulgu("C", "HATA", "C"),
    ]
    assert ozet(liste) == {"BILGI": 0, "UYARI": 1, "HATA": 2}
