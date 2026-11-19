import ezdxf
import pytest

from pafta.katman import katmanlari_listele, katman_tani
from pafta.isaret import (
    appid_tanimla,
    isaretle,
    ISARET_AKS,
    ISARET_KIRIS_EKSEN,
    ISARET_PERDE_EKSEN,
    ISARET_HATA,
)

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


def test_perde_eksen_katmani_kaynak_perde_sayilmaz(doc):
    doc.layers.add("PERDE_EKSEN")

    r = katman_tani(doc)

    assert "PERDE" in r.katmanlar["PERDE"]
    assert "PERDE_EKSEN" not in r.katmanlar["PERDE"]
    assert "PERDE_EKSEN" in r.tanimsiz


@pytest.mark.parametrize(
    "katman, etiket",
    [
        ("PERDE_EKSEN", ISARET_PERDE_EKSEN),
        ("KIRIS_EKSEN", ISARET_KIRIS_EKSEN),
        ("PAFTA_HATA", ISARET_HATA),
        ("AKS_URETILEN", ISARET_AKS),
    ],
)
def test_program_uretimi_katman_tanimsiz_raporlanmaz(
    doc, katman, etiket
):
    doc.layers.add(katman)
    appid_tanimla(doc)

    entity = doc.modelspace().add_line(
        (0, 0),
        (100, 0),
        dxfattribs={"layer": katman},
    )
    isaretle(entity, etiket)

    sonuc = katman_tani(doc)

    assert katman not in sonuc.tanimsiz


def test_kullanici_nesnesi_olan_uretilmis_katman_tanimsiz_kalir(doc):
    katman = "PERDE_EKSEN"
    doc.layers.add(katman)
    appid_tanimla(doc)

    uretilen = doc.modelspace().add_line(
        (0, 0),
        (100, 0),
        dxfattribs={"layer": katman},
    )
    isaretle(uretilen, ISARET_PERDE_EKSEN)

    # Aynı katmanda kullanıcının işaretsiz nesnesi bulunuyor.
    doc.modelspace().add_line(
        (0, 10),
        (100, 10),
        dxfattribs={"layer": katman},
    )

    sonuc = katman_tani(doc)

    assert katman in sonuc.tanimsiz


def test_bos_uretilmis_katman_tanimsiz_kalir(doc):
    doc.layers.add("PERDE_EKSEN")

    sonuc = katman_tani(doc)

    assert "PERDE_EKSEN" in sonuc.tanimsiz


def test_program_katmani_kullanici_tarafindan_secilebilir(doc):
    katman = "PERDE_EKSEN"
    doc.layers.add(katman)
    appid_tanimla(doc)

    entity = doc.modelspace().add_line(
        (0, 0),
        (100, 0),
        dxfattribs={"layer": katman},
    )
    isaretle(entity, ISARET_PERDE_EKSEN)

    sonuc = katman_tani(doc, {"PERDE": [katman]})

    assert katman in sonuc.katmanlar["PERDE"]
