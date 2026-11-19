import ezdxf
import pytest

from pafta.aks import akslari_isle
from pafta.birim import Ayar
from pafta.kiris import kirisleri_isle
from pafta.kolon import kolonlari_isle


def _kolonlari_isle(doc, duzelt=True):
    return kolonlari_isle(
        doc, doc.modelspace(), ["KOLON"], Ayar.olustur("cm"), duzelt=duzelt
    )


def test_kapali_ve_tolerans_icindeki_acik_kolonlar_islenmeye_devam_eder():
    doc = ezdxf.new()
    msp = doc.modelspace()
    msp.add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    yakin = msp.add_lwpolyline(
        [(100, 0), (130, 0), (130, 60), (100, 60), (100.2, 0)],
        close=False,
        dxfattribs={"layer": "KOLON"},
    )

    sonuc = _kolonlari_isle(doc)

    assert len(sonuc.kolonlar) == 2
    assert len(sonuc.merkezler) == 2
    assert sonuc.acik_kapatilan == 1
    assert yakin.closed is True
    assert len(list(yakin.get_points())) == 5
    assert list(yakin.get_points("xy"))[-1] == pytest.approx((100.2, 0.0))


def test_tolerans_disi_acik_kolon_uyarilir_ve_diger_analizlere_aktarilmaz():
    doc = ezdxf.new()
    msp = doc.modelspace()
    for cx, cy in ((200, 200), (400, 400)):
        msp.add_lwpolyline(
            [
                (cx - 15, cy - 15),
                (cx + 15, cy - 15),
                (cx + 15, cy + 15),
                (cx - 15, cy + 15),
            ],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    acik = msp.add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=False,
        dxfattribs={"layer": "KOLON"},
    )
    beam = msp.add_line((15.4, 30), (100, 30), dxfattribs={"layer": "KIRIS"})

    kolon_sonuc = _kolonlari_isle(doc)

    assert acik.closed is False
    assert len(kolon_sonuc.kolonlar) == 2
    assert len(kolon_sonuc.merkezler) == 2
    assert all(abs(x) > 1 or abs(y) > 1 for x, y in kolon_sonuc.merkezler)
    assert any(b.kod == "KOLON_ACIK_KAPATILAMADI" for b in kolon_sonuc.bulgular)

    ayar = Ayar.olustur("cm")
    kiris_sonuc = kirisleri_isle(
        doc, msp, ["KIRIS"], kolon_sonuc.merkezler, ayar,
        duzelt=False, eksen_uret=False,
    )
    assert kiris_sonuc.cizgiler[0][0] == (15.4, 30.0)
    assert (beam.dxf.start.x, beam.dxf.start.y) == (15.4, 30.0)

    aks_sonuc = akslari_isle(doc, msp, kolon_sonuc.merkezler, ayar, duzelt=False)
    assert 15.0 not in aks_sonuc.xs
    assert 30.0 not in aks_sonuc.ys


@pytest.mark.parametrize("duzelt", [True, False])
@pytest.mark.parametrize("bulge", [False, True], ids=["duz", "bulge"])
def test_iki_koseli_gecersiz_polyline_silinmaz_ve_kolon_analizina_girmez(duzelt, bulge):
    doc = ezdxf.new()
    msp = doc.modelspace()
    if bulge:
        pl = msp.add_lwpolyline(
            [(0, 0, 0, 0, 0.5), (30, 0)],
            close=False,
            dxfattribs={"layer": "KOLON"},
        )
    else:
        pl = msp.add_lwpolyline(
            [(0, 0), (30, 0)], close=False, dxfattribs={"layer": "KOLON"}
        )
    original_points = list(pl.get_points("xyb"))

    sonuc = _kolonlari_isle(doc, duzelt=duzelt)

    assert pl in msp
    assert pl.closed is False
    assert list(pl.get_points("xyb")) == original_points
    assert sonuc.gecersiz_sayisi == 1
    assert sonuc.kolonlar == []
    assert sonuc.merkezler == []
    assert [b.kod for b in sonuc.bulgular] == ["KOLON_GECERSIZ"]
    assert "analiz dışında bırakıldı" in sonuc.bulgular[0].mesaj



def test_kiris_analizi_duzelt_false_katman_tablosunu_degistirmez():
    """Salt analiz modunda KIRIS_EKSEN katmanı oluşturulmamalıdır."""
    doc = ezdxf.new()
    msp = doc.modelspace()

    assert "KIRIS_EKSEN" not in doc.layers

    kirisleri_isle(
        doc,
        msp,
        ["KIRIS"],
        [],
        Ayar.olustur("cm"),
        duzelt=False,
        eksen_uret=False,
    )

    assert "KIRIS_EKSEN" not in doc.layers
