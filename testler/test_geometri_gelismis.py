import pytest
import ezdxf
from ortak import grupla, merkez, blok_merkezleri
from temizle import temizle


def test_sifir_olcekli_blok_hayalet_kolon_uretmez(tmp_path):
    """Bozuk DXF dosyalarından gelen sıfır ölçekli (group code 41=0) bloklar hayalet kolon üretmemeli."""
    dosya = tmp_path / "sifir_blok.dxf"
    doc = ezdxf.new()
    block = doc.blocks.new("K3060")
    block.add_lwpolyline([(-15, -30), (15, -30), (15, 30), (-15, 30)], close=True)
    doc.modelspace().add_blockref("K3060", (100, 200))
    doc.saveas(dosya)

    # DXF dosyasında group code 41'i 0.0 yap (bozuk CAD ihracını simüle et)
    metin = dosya.read_text(encoding="utf-8")
    metin = metin.replace("K3060\n", "K3060\n 41\n0.0\n")
    dosya.write_text(metin, encoding="utf-8")

    doc_bozuk = ezdxf.readfile(dosya)
    ins_zero = list(doc_bozuk.modelspace().query("INSERT"))[0]

    merkezler = blok_merkezleri(doc_bozuk, ins_zero)
    assert merkezler == [], f"Sıfır ölçekli blok hayalet kolon üretti: {merkezler}"


def test_grupla_zincirleme_yapmaz():
    """
    [100, 104, 108, 112, 116, 120] değerleri tol=5 ile gruplanınca,
    eski kodda tek bir grup [110.0] oluyordu (zincirleme hatası).
    Yeni referans tabanlı gruplamada 3 ayrı grup oluşmalıdır.
    """
    degerler = [100, 104, 108, 112, 116, 120]
    sonuc = grupla(degerler, tol=5.0)
    assert len(sonuc) == 3
    assert sonuc == [102.0, 110.0, 118.0]


def test_merkez_dogrusal_sifir_alanli_geometride_guvenli():
    """Alanı 0 olan dejenere doğrusal polylinelerde bounding box merkezi dönmelidir."""
    pts = [(0, 0), (1, 0), (20, 0)]
    m = merkez(pts)
    # Bounding box ortası (0+20)/2 = 10.0
    assert m == (10.0, 0.0)


def test_egik_kiris_cizgisi_bulgu_olarak_raporlanir(tmp_path):
    """45 derece eğik kiriş çizgisi sessizce göz ardı edilmemeli, 'KIRIS_EGIK' bulgusu üretmelidir."""
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.layers.add("KIRIS")
    msp = doc.modelspace()

    msp.add_lwpolyline([(0, 0), (30, 0), (30, 30), (0, 30)], close=True, dxfattribs={"layer": "KOLON"})
    msp.add_lwpolyline([(500, 500), (530, 500), (530, 530), (500, 530)], close=True, dxfattribs={"layer": "KOLON"})

    # 45 derece eğik kiriş çizgisi
    msp.add_line((15, 15), (515, 515), dxfattribs={"layer": "KIRIS"})

    giris = tmp_path / "egik_plan.dxf"
    cikis = tmp_path / "egik_temiz.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))

    egik_bulgulari = [b for b in rapor.bulgular if b.kod == "KIRIS_EGIK"]
    assert len(egik_bulgulari) >= 1, "Eğik kiriş için açıklayıcı bulgu üretilmedi!"
