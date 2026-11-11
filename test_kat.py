import math

import ezdxf
import pytest

from ortak import (AKS_KATMAN, KIRIS_KATMAN, KOLON_KATMAN, katmandakiler,
                   kose_listesi, merkez)


@pytest.fixture(scope="module")
def kat_dizini(tmp_path_factory, calistir):
    d = tmp_path_factory.mktemp("kat")
    for betik in ("uret_kat.py", "boz.py", "temizle.py", "aks.py"):
        calistir(betik, d)
    return d


def _oku(dizin, ad):
    return ezdxf.readfile(dizin / ad).modelspace()


@pytest.fixture(scope="module")
def bozuk(kat_dizini):
    return _oku(kat_dizini, "bozuk_kat.dxf")


@pytest.fixture(scope="module")
def temiz(kat_dizini):
    msp = _oku(kat_dizini, "temiz_kat.dxf")
    kolonlar = katmandakiler(msp, "LWPOLYLINE", KOLON_KATMAN)
    kirisler = katmandakiler(msp, "LINE", KIRIS_KATMAN)
    merk = [merkez(kose_listesi(p)) for p in kolonlar]
    return kolonlar, kirisler, merk


@pytest.fixture(scope="module")
def aks(kat_dizini):
    return _oku(kat_dizini, "aks_kat.dxf")


# bozuk dosya
def test_bozuk_acik_kolon(bozuk):
    acik = sum(1 for p in katmandakiler(bozuk, "LWPOLYLINE", KOLON_KATMAN) if not p.closed)
    assert acik == 2


def test_bozuk_kiris_cakisik_dahil(bozuk):
    assert len(katmandakiler(bozuk, "LINE", KIRIS_KATMAN)) == 41


# temiz dosya
def test_temiz_kolon(temiz):
    kolonlar, _, _ = temiz
    assert len(kolonlar) == 24


def test_temiz_acik_kolon(temiz):
    kolonlar, _, _ = temiz
    assert sum(1 for p in kolonlar if not p.closed) == 0


def test_temiz_kiris(temiz):
    _, kirisler, _ = temiz
    assert len(kirisler) == 38


def test_temiz_kiris_ucu_kolon_merkezinde(temiz):
    _, kirisler, merk = temiz
    disarda = 0
    for l in kirisler:
        for p in ((l.dxf.start.x, l.dxf.start.y), (l.dxf.end.x, l.dxf.end.y)):
            if min(math.dist(c, p) for c in merk) > 1e-6:
                disarda += 1
    assert disarda == 0


def test_temiz_cakisik_kiris(temiz):
    _, kirisler, _ = temiz
    anahtarlar = set()
    for l in kirisler:
        s = (l.dxf.start.x, l.dxf.start.y)
        e = (l.dxf.end.x, l.dxf.end.y)
        anahtarlar.add(frozenset([(round(s[0], 1), round(s[1], 1)),
                                  (round(e[0], 1), round(e[1], 1))]))
    assert len(kirisler) - len(anahtarlar) == 0


# aks dosyası
def test_aks_cizgisi(aks):
    assert len(katmandakiler(aks, "LINE", [AKS_KATMAN])) == 10


def test_aks_balonu(aks):
    assert len(katmandakiler(aks, "CIRCLE", [AKS_KATMAN])) == 10


def test_aks_yazisi(aks):
    assert len(katmandakiler(aks, "TEXT", [AKS_KATMAN])) == 10


def test_aks_dosyasinda_kolon(aks):
    assert len(katmandakiler(aks, "LWPOLYLINE", KOLON_KATMAN)) == 24


def test_aks_dosyasinda_kiris(aks):
    assert len(katmandakiler(aks, "LINE", KIRIS_KATMAN)) == 38
