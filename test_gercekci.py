import math
import re
from types import SimpleNamespace

import ezdxf
import pytest

from ortak import EKSEN_KATMAN, katmandakiler, kolon_merkezleri


@pytest.fixture(scope="module")
def gercekci(tmp_path_factory, calistir):
    d = tmp_path_factory.mktemp("gercekci")
    calistir("uret_gercekci.py", d)
    cikti_t = calistir("temizle.py", d, "gercekci_kat.dxf", "gercekci_temiz.dxf")
    cikti_a = calistir("aks.py", d, "gercekci_temiz.dxf", "gercekci_aks.dxf")
    doc = ezdxf.readfile(d / "gercekci_temiz.dxf")
    return SimpleNamespace(cikti_t=cikti_t, cikti_a=cikti_a, doc=doc, msp=doc.modelspace())


def _sayilar(desen, metin):
    m = re.search(desen, metin)
    assert m, f"çıktıda {desen!r} bulunamadı:\n{metin}"
    return tuple(int(g) for g in m.groups())


# betik raporları
def test_kolon_adedi_poligon_ve_blok(gercekci):
    assert _sayilar(r"KOLON\s*:\s*(\d+) adet", gercekci.cikti_t) == (24,)


def test_kiris_adedi_cift_cizgiden(gercekci):
    assert _sayilar(r"KİRİŞ\s*:\s*(\d+) adet", gercekci.cikti_t) == (38,)


def test_dusey_aks(gercekci):
    dusey, _ = _sayilar(r"(\d+) düşey.*?(\d+) yatay", gercekci.cikti_a)
    assert dusey == 6


def test_yatay_aks(gercekci):
    _, yatay = _sayilar(r"(\d+) düşey.*?(\d+) yatay", gercekci.cikti_a)
    assert yatay == 4


def test_bos_aks_kesisimi(gercekci):
    assert _sayilar(r"boş kesişim:\s*(\d+)", gercekci.cikti_a) == (0,)


# çıktı dosyası
def test_kolon_merkezi_poligon_ve_blok(gercekci):
    assert len(kolon_merkezleri(gercekci.doc, gercekci.msp)) == 24


def test_kiris_ekseni(gercekci):
    assert len(katmandakiler(gercekci.msp, "LINE", [EKSEN_KATMAN])) == 38


def test_eksen_ucu_kolon_merkezinde(gercekci):
    merk = kolon_merkezleri(gercekci.doc, gercekci.msp)
    eks = katmandakiler(gercekci.msp, "LINE", [EKSEN_KATMAN])
    disarda = 0
    for l in eks:
        for p in ((l.dxf.start.x, l.dxf.start.y), (l.dxf.end.x, l.dxf.end.y)):
            if min(math.dist(c, p) for c in merk) > 1e-6:
                disarda += 1
    assert disarda == 0
