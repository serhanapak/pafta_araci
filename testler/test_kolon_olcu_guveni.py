import json
import math

import ezdxf
import pytest

from pafta.birim import Ayar, birim_tahmin
from pafta.hata import Kategori
from pafta.kat import KatPaftasi
from pafta.kolon import (
    KolonBilgi,
    KolonOlcuDurumu,
    kolonlari_isle,
)
from pafta.kural import tbdy_on_kontrol
from pafta.rapor import AnalizRaporu


def _dikdortgen(n, boy, aci=0.0, merkez=(0.0, 0.0)):
    t = math.radians(aci)
    c, s = math.cos(t), math.sin(t)
    cx, cy = merkez
    return [
        (cx + x * c - y * s, cy + x * s + y * c)
        for x, y in ((-n / 2, -boy / 2), (n / 2, -boy / 2),
                     (n / 2, boy / 2), (-n / 2, boy / 2))
    ]


def _analiz(entities, *, duzelt=False):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for add_entity in entities:
        add_entity(msp)
    result = kolonlari_isle(
        doc, msp, ["KOLON"], Ayar.olustur("cm"), duzelt=duzelt
    )
    return doc, result


def _polyline(points, *, closed=True, bulge=False):
    def add(msp):
        if bulge:
            msp.add_lwpolyline(
                [(x, y, 0, 0, 0.5 if i == 0 else 0) for i, (x, y) in enumerate(points)],
                close=closed,
                dxfattribs={"layer": "KOLON"},
            )
        else:
            msp.add_lwpolyline(
                points, close=closed, dxfattribs={"layer": "KOLON"}
            )
    return add


def _kontrol(result):
    return tbdy_on_kontrol(result, Ayar.olustur("cm"))


@pytest.mark.parametrize("angle", (0, 15, 30, 45, 60, 90))
def test_dondurulmus_dogrulanmis_dikdortgen_minimum_kesitte_kesin_olculur(angle):
    _, result = _analiz([_polyline(_dikdortgen(30, 60, angle))])

    kolon = result.kolonlar[0]
    assert kolon.olcu_durumu is KolonOlcuDurumu.KESIN
    assert (kolon.kisa_kenar, kolon.uzun_kenar) == pytest.approx((30, 60))
    assert not [b for b in _kontrol(result) if b.kod == "KOLON_MIN_KESIT"]


def test_dogrulanmis_kucuk_dikdortgen_kesin_minimum_kesit_bulgusu_uretir():
    _, result = _analiz([_polyline(_dikdortgen(25, 50))])

    assert result.kolonlar[0].olcu_durumu is KolonOlcuDurumu.KESIN
    assert [b.kod for b in _kontrol(result)] == ["KOLON_MIN_KESIT"]


def test_daire_capinin_kesin_olcumu_korunur():
    def add(msp):
        msp.add_circle((0, 0), 15, dxfattribs={"layer": "KOLON"})

    _, result = _analiz([add])
    kolon = result.kolonlar[0]

    assert kolon.olcu_durumu is KolonOlcuDurumu.KESIN
    assert kolon.kisa_kenar == kolon.uzun_kenar == 30
    assert [b.kod for b in _kontrol(result)] == ["KOLON_MIN_KESIT"]


@pytest.mark.parametrize(
    "points,bulge",
    [
        ([(0, 0), (25, 0), (20, 50), (5, 50)], False),  # trapez
        ([(0, 0), (25, 0), (22, 50), (4, 40)], False),  # düzensiz dörtgen
        ([(0, 0), (25, 0), (25, 50), (0, 50)], True),   # yay segmenti
    ],
    ids=("trapez", "duzensiz-dortgen", "bulge"),
)
def test_dogrulanamayan_kapali_polyline_kesin_ihlal_uretmez(points, bulge):
    _, result = _analiz([_polyline(points, bulge=bulge)])

    assert len(result.kolonlar) == 1
    assert result.kolonlar[0].olcu_durumu is KolonOlcuDurumu.YAKLASIK
    assert result.kolonlar[0].kisa_kenar > 0  # Eski tüketiciler için korunur.
    findings = _kontrol(result)
    assert "KOLON_MIN_KESIT" not in [b.kod for b in findings]
    assert [b.kod for b in findings] == ["KOLON_KESIT_OLCUSU_DOGRULANAMADI"]
    assert findings[0].detay["olcu_durumu"] == "YAKLASIK"


def test_yakindan_acik_polyline_duzeltmesiz_ve_duzeltmeli_yaklasik_kalir():
    points = [(0, 0), (25, 0), (25, 50), (0, 50), (0.2, 0)]
    _, unchanged = _analiz([_polyline(points, closed=False)], duzelt=False)
    _, repaired = _analiz([_polyline(points, closed=False)], duzelt=True)

    assert unchanged.kolonlar[0].olcu_durumu is KolonOlcuDurumu.YAKLASIK
    assert [b.kod for b in _kontrol(unchanged)] == ["KOLON_KESIT_OLCUSU_DOGRULANAMADI"]
    assert repaired.kolonlar[0].olcu_durumu is KolonOlcuDurumu.YAKLASIK
    assert [b.kod for b in _kontrol(repaired)] == ["KOLON_KESIT_OLCUSU_DOGRULANAMADI"]


def test_uzak_uclu_acik_polyline_kolon_olmaz_ve_kesit_kontrolune_girmez():
    _, result = _analiz([
        _polyline([(0, 0), (25, 0), (25, 50), (0, 50)], closed=False)
    ])

    assert result.kolonlar == []
    assert [b.kod for b in result.bulgular] == ["KOLON_ACIK_KAPATILAMADI"]
    assert _kontrol(result) == []


def test_olcusu_cikarilamayan_insert_belirsiz_olarak_bildirilir():
    doc = ezdxf.new()
    block = doc.blocks.new("COLUMN_BLOCK")
    block.add_lwpolyline(_dikdortgen(25, 50), close=True)
    doc.modelspace().add_blockref("COLUMN_BLOCK", (100, 200), dxfattribs={"layer": "KOLON"})
    result = kolonlari_isle(
        doc, doc.modelspace(), ["KOLON"], Ayar.olustur("cm"), duzelt=False
    )

    assert len(result.kolonlar) == 1
    assert result.kolonlar[0].tur == "INSERT"
    assert result.kolonlar[0].olcu_durumu is KolonOlcuDurumu.BELIRSIZ
    findings = _kontrol(result)
    assert [b.kod for b in findings] == ["KOLON_KESIT_OLCUSU_DOGRULANAMADI"]
    assert findings[0].detay["olcu_durumu"] == "BELIRSIZ"


def test_eski_kolon_bilgi_konumsal_parametre_sirasi_ve_varsayilan_durumu_korunur():
    kolon = KolonBilgi(
        (10, 20), 1500, (0, 0, 30, 50), "POLYLINE",
        None, "AB", "KOLON", 4, 25, 50,
    )

    assert kolon.merkez == (10, 20)
    assert kolon.alan == 1500
    assert kolon.kutu == (0, 0, 30, 50)
    assert kolon.tur == "POLYLINE"
    assert kolon.entity is None
    assert kolon.handle == "AB"
    assert kolon.katman == "KOLON"
    assert kolon.kose_sayisi == 4
    assert kolon.kisa_kenar == 25
    assert kolon.uzun_kenar == 50
    assert kolon.olcu_durumu is KolonOlcuDurumu.BELIRSIZ


def test_birim_tahmini_dogrulanmis_donus_olcusunu_kullanir_belirsiz_geom_tahmin_edilmez():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 0
    msp = doc.modelspace()
    for index in range(5):
        msp.add_lwpolyline(
            _dikdortgen(140, 500, 45, (index * 1000, 0)),
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    sonuc = birim_tahmin(doc, ["KOLON"])
    assert sonuc.birim is None  # bbox kısa kenarıyla yanlışlıkla mm seçilmez.
    assert any(b.kod == "BIRIM_BELIRSIZ" for b in sonuc.bulgular)

    only_approx = ezdxf.new()
    only_approx.header["$INSUNITS"] = 6
    for index in range(5):
        only_approx.modelspace().add_lwpolyline(
            [(index * 100, 0), (index * 100 + 25, 0),
             (index * 100 + 20, 50), (index * 100 + 5, 50)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    sonuc_approx = birim_tahmin(only_approx, ["KOLON"])
    assert sonuc_approx.birim is None  # Başlık tek başına yetersiz geometriyi onaylamaz.
    assert "başlığında m birimi var" in sonuc_approx.bulgular[-1].mesaj
    assert sonuc_approx.medyan is None
    assert sonuc_approx.adet == 0


def test_yaklasik_kesit_bulgusu_rapor_jsonunda_turkce_ve_durumuyla_korunur():
    _, result = _analiz([
        _polyline([(0, 0), (25, 0), (20, 50), (5, 50)])
    ])
    report = AnalizRaporu(dosya_adi="ölçüm.dxf", bulgular=_kontrol(result))
    encoded = report.to_json()
    decoded = json.loads(encoded)

    assert "Kolon ölçüsü YAKLASIK" in encoded
    assert decoded["bulgular"][0]["kod"] == "KOLON_KESIT_OLCUSU_DOGRULANAMADI"
    assert decoded["bulgular"][0]["kategori"] == Kategori.BELIRSIZ.value
    assert decoded["bulgular"][0]["detay"]["olcu_durumu"] == "YAKLASIK"


def test_kat_raporu_yaklasik_bbox_degerini_olcek_medyanina_sokmaz(tmp_path):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 5
    doc.modelspace().add_lwpolyline(
        [(0, 0), (4, 0), (3, 50), (1, 50)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    source = tmp_path / "yaklasik_kolon.dxf"
    output = tmp_path / "yaklasik_kolon_cikti.dxf"
    doc.saveas(source)

    report = KatPaftasi(source, birim_zorla="cm").temizle(output)

    codes = [finding.kod for finding in report.bulgular]
    assert "KOLON_KESIT_OLCUSU_DOGRULANAMADI" in codes
    assert "BIRIM_OLCEK_UYARISI" not in codes
