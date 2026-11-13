import ezdxf
from temizle import temizle
from aks import aks_uret


def test_milimetre_ciziminde_kiris_ciftleme_ve_eksen_uretimi(tmp_path):
    """
    Milimetre çiziminde (kolonlar 300x600, kiriş 250 genişliğinde, 5000 açıklık)
    kirişler doğru tespit edilmeli ve eksenleri üretilmelidir (eski kodda 0 çıkıyordu).
    """
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4  # mm
    msp = doc.modelspace()

    # 2 kolon (300 x 600 mm)
    for cx in (0, 5000):
        msp.add_lwpolyline(
            [(cx - 150, -300), (cx + 150, -300), (cx + 150, 300), (cx - 150, 300)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )

    # 1 kiriş (250 mm genişliğinde çift kenar çizgisi)
    msp.add_line((0, -125), (5000, -125), dxfattribs={"layer": "KIRIS"})
    msp.add_line((0, 125), (5000, 125), dxfattribs={"layer": "KIRIS"})

    giris = tmp_path / "mm_plan.dxf"
    cikis = tmp_path / "mm_temiz.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))

    assert rapor.birim == "mm"
    assert rapor.kolon_sayisi == 2
    assert rapor.cift_cizgi_eksen_sayisi == 1, "mm çiziminde kiriş çifti tespit edilemedi!"

    sonuc = ezdxf.readfile(cikis)
    eksenler = list(sonuc.modelspace().query('LINE[layer=="KIRIS_EKSEN"]'))
    assert len(eksenler) == 1
    # Eksen ortada y=0 olmalı
    assert abs(eksenler[0].dxf.start.y) < 1e-3
    assert abs(eksenler[0].dxf.end.y) < 1e-3


def test_metre_ciziminde_aks_uretimi(tmp_path):
    """
    Metre çiziminde (kolonlar 0.3x0.6 m, aks mesafesi 4.0 m ve 5.0 m)
    aks çizgileri ve balonları metre ölçeğinde doğru oluşturulmalıdır.
    """
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 6  # m
    msp = doc.modelspace()

    xs = [0.0, 4.0, 9.0]
    ys = [0.0, 5.0]

    for x in xs:
        for y in ys:
            msp.add_lwpolyline(
                [(x - 0.15, y - 0.3), (x + 0.15, y - 0.3), (x + 0.15, y + 0.3), (x - 0.15, y + 0.3)],
                close=True,
                dxfattribs={"layer": "KOLON"},
            )

    giris = tmp_path / "m_plan.dxf"
    cikis = tmp_path / "m_aks.dxf"
    doc.saveas(giris)

    rapor = aks_uret(str(giris), str(cikis))

    assert rapor.birim == "m"
    assert rapor.dusey_aks_sayisi == 3
    assert rapor.yatay_aks_sayisi == 2
    assert rapor.aciklik_x == [4.0, 5.0]
    assert rapor.aciklik_y == [5.0]


def test_farkli_katman_adlari_otomatik_taninir(tmp_path):
    """COLUMN ve BEAM katman adlarına sahip çizim otomatik tanınmalıdır."""
    doc = ezdxf.new()
    doc.layers.add("COLUMN")
    doc.layers.add("BEAM")
    msp = doc.modelspace()

    for cx in (0, 400):
        msp.add_lwpolyline(
            [(cx - 15, -15), (cx + 15, -15), (cx + 15, 15), (cx - 15, 15)],
            close=True,
            dxfattribs={"layer": "COLUMN"},
        )
    msp.add_line((0, -10), (400, -10), dxfattribs={"layer": "BEAM"})
    msp.add_line((0, 10), (400, 10), dxfattribs={"layer": "BEAM"})

    giris = tmp_path / "eng_plan.dxf"
    cikis = tmp_path / "eng_temiz.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))

    assert "COLUMN" in rapor.katmanlar.get("KOLON", [])
    assert "BEAM" in rapor.katmanlar.get("KIRIS", [])
    assert rapor.kolon_sayisi == 2
    assert rapor.cift_cizgi_eksen_sayisi == 1
