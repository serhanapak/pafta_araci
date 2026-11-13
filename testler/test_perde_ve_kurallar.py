import ezdxf
from pafta.kat import KatPaftasi


def test_perde_oran_ve_kalinlik_kontrolu(tmp_path):
    doc = ezdxf.new("AC1015")
    doc.layers.add("KOLON")
    doc.layers.add("PERDE")
    msp = doc.modelspace()

    msp.add_lwpolyline([(0, 0), (30, 0), (30, 50), (0, 50)], close=True, dxfattribs={"layer": "KOLON"})
    msp.add_lwpolyline([(600, 0), (630, 0), (630, 50), (600, 50)], close=True, dxfattribs={"layer": "KOLON"})

    # Geçerli perde (30x210 cm), oran yetersiz (30x120 cm), kalınlık yetersiz (20x180 cm)
    msp.add_lwpolyline([(100, 0), (310, 0), (310, 30), (100, 30)], close=True, dxfattribs={"layer": "PERDE"})
    msp.add_lwpolyline([(100, 200), (220, 200), (220, 230), (100, 230)], close=True, dxfattribs={"layer": "PERDE"})
    msp.add_lwpolyline([(100, 400), (280, 400), (280, 420), (100, 420)], close=True, dxfattribs={"layer": "PERDE"})

    giris = tmp_path / "perdeli.dxf"
    cikis = tmp_path / "perdeli_cikis.dxf"
    doc.saveas(giris)

    kp = KatPaftasi(giris)
    rapor = kp.temizle(cikis)

    kodlar = [b.kod for b in rapor.bulgular]
    assert rapor.perde_sayisi == 3
    assert rapor.perde_eksen_sayisi == 3
    assert "PERDE_ORAN_YETERSIZ" in kodlar
    assert "PERDE_KALINLIK_YETERSIZ" in kodlar


def test_min_kolon_kesiti_ve_pafta_hata_katmani(tmp_path):
    doc = ezdxf.new("AC1015")
    doc.layers.add("KOLON")
    msp = doc.modelspace()

    msp.add_lwpolyline([(0, 0), (25, 0), (25, 50), (0, 50)], close=True, dxfattribs={"layer": "KOLON"})
    msp.add_circle((400, 0), radius=15, dxfattribs={"layer": "KOLON"})

    giris = tmp_path / "kucuk_kolon.dxf"
    cikis = tmp_path / "kucuk_kolon_cikis.dxf"
    doc.saveas(giris)

    kp = KatPaftasi(giris)
    rapor = kp.temizle(cikis, gorsel_hata=True)
    adet = kp.hatalari_isaretle(cikis)

    assert len([b for b in rapor.bulgular if b.kod == "KOLON_MIN_KESIT"]) == 2
    assert adet == 2

    sonuc_doc = ezdxf.readfile(cikis)
    hata_daireleri = [e for e in sonuc_doc.modelspace().query("CIRCLE") if e.dxf.layer == "PAFTA_HATA"]
    assert len(hata_daireleri) == 2
