import math

import ezdxf
import pytest

from pafta.birim import Ayar
from pafta.geometri import dikdortgen_kenar_olculeri
from pafta.kolon import kolonlari_isle


def _donmus_dikdortgen(genislik, yukseklik, aci):
    radians = math.radians(aci)
    cos_a, sin_a = math.cos(radians), math.sin(radians)
    corners = [
        (-genislik / 2, -yukseklik / 2),
        (genislik / 2, -yukseklik / 2),
        (genislik / 2, yukseklik / 2),
        (-genislik / 2, yukseklik / 2),
    ]
    return [
        (x * cos_a - y * sin_a, x * sin_a + y * cos_a)
        for x, y in corners
    ]


def _analiz_et(polyline_points):
    doc = ezdxf.new()
    doc.modelspace().add_lwpolyline(
        polyline_points, close=True, dxfattribs={"layer": "KOLON"}
    )
    result = kolonlari_isle(
        doc, doc.modelspace(), ["KOLON"], Ayar.olustur("cm"), duzelt=False
    )
    assert len(result.kolonlar) == 1
    return result.kolonlar[0]


@pytest.mark.parametrize(
    "angle",
    [pytest.param(angle, id=f"{angle}-derece") for angle in (0, 15, 30, 45, 60, 90)],
)
def test_30x60_dikdortgen_kolon_gercek_kenar_olculerini_korur(angle):
    kolon = _analiz_et(_donmus_dikdortgen(30, 60, angle))

    assert kolon.kisa_kenar == pytest.approx(30.0, abs=1e-9)
    assert kolon.uzun_kenar == pytest.approx(60.0, abs=1e-9)


@pytest.mark.parametrize(
    "angle",
    [pytest.param(angle, id=f"{angle}-derece") for angle in (0, 15, 30, 45, 60, 90)],
)
def test_40x40_kare_kolon_donus_acisindan_bagimsizdir(angle):
    kolon = _analiz_et(_donmus_dikdortgen(40, 40, angle))

    assert kolon.kisa_kenar == pytest.approx(40.0, abs=1e-9)
    assert kolon.uzun_kenar == pytest.approx(40.0, abs=1e-9)


def test_dairesel_kolon_cap_olcusu_korunur():
    doc = ezdxf.new()
    doc.modelspace().add_circle((10, 20), radius=25, dxfattribs={"layer": "KOLON"})

    result = kolonlari_isle(
        doc, doc.modelspace(), ["KOLON"], Ayar.olustur("cm"), duzelt=False
    )

    assert len(result.kolonlar) == 1
    assert result.kolonlar[0].kisa_kenar == 50.0
    assert result.kolonlar[0].uzun_kenar == 50.0


def test_dikdortgen_olmayan_ve_bulge_icerikli_polyline_icin_kesin_olcu_verilmez():
    doc = ezdxf.new()
    msp = doc.modelspace()
    trapez = msp.add_lwpolyline(
        [(0, 0), (60, 0), (50, 30), (10, 30)], close=True
    )
    bulgeli = msp.add_lwpolyline(
        [(100, 0, 0, 0, 0.5), (160, 0), (160, 30), (100, 30)], close=True
    )

    assert dikdortgen_kenar_olculeri(trapez) is None
    assert dikdortgen_kenar_olculeri(bulgeli) is None


