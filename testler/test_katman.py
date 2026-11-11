import ezdxf
import pytest

from pafta.katman import katmanlari_listele, katman_tani

ADLAR = [
    "KOLON",
    "SUTUNLAR",
    "COLUMN",
    "KIRIS",
    "BEAM",
    "AKS",
    "GRID",
    "PERDE",
    "SHEAR_WALL",
    "ANTET",
    "TARAMA",
]


@pytest.fixture
def doc():
    d = ezdxf.new()
    for ad in ADLAR:
        d.layers.add(ad)
    return d


def test_katmanlari_listele(doc):
    liste = katmanlari_listele(doc)
    assert "KOLON" in liste
    assert "ANTET" in liste


def test_otomatik_siniflandirma(doc):
    r = katman_tani(doc)

    assert "KOLON" in r.katmanlar["KOLON"]
    assert "SUTUNLAR" in r.katmanlar["KOLON"]
    assert "COLUMN" in r.katmanlar["KOLON"]

    assert "KIRIS" in r.katmanlar["KIRIS"]
    assert "BEAM" in r.katmanlar["KIRIS"]

    assert "AKS" in r.katmanlar["AKS"]
    assert "GRID" in r.katmanlar["AKS"]

    assert "PERDE" in r.katmanlar["PERDE"]
    assert "SHEAR_WALL" in r.katmanlar["PERDE"]

    assert "ANTET" in r.tanimsiz
    assert "TARAMA" in r.tanimsiz


def test_kullanici_secimi_otomatigi_gecersiz_kilar(doc):
    r = katman_tani(doc, {"KOLON": ["ANTET"]})
    assert "ANTET" in r.katmanlar["KOLON"]


def test_olmayan_katman_secilemez(doc):
    with pytest.raises(ValueError):
        katman_tani(doc, {"KOLON": ["OLMAYAN"]})
