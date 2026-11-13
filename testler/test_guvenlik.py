import os
from pathlib import Path
import ezdxf

from temizle import temizle
from aks import aks_uret
from pafta.duzelt import guvenli_kaydet, ayni_dosya_mi, yedek_al


def test_ayni_dosyaya_yazarken_otomatik_yedek_olusturulur(tmp_path):
    dosya = tmp_path / "orijinal.dxf"
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    doc.saveas(dosya)

    # Giriş ve çıkış aynı dosya
    temizle(str(dosya), str(dosya))

    bak_dosyasi = tmp_path / "orijinal.dxf.bak"
    assert bak_dosyasi.exists(), ".bak yedek dosyası oluşturulmadı!"
    assert bak_dosyasi.stat().st_size > 0


def test_aks_ayni_dosyada_yedek_olusturur(tmp_path):
    dosya = tmp_path / "kat_aks.dxf"
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    doc.saveas(dosya)

    aks_uret(str(dosya), str(dosya))

    bak = tmp_path / "kat_aks.dxf.bak"
    assert bak.exists()


def test_metre_ciziminde_dilatasyon_derzli_ikiz_kolonlar_silinmez(tmp_path):
    """
    Metre çiziminde dilatasyon derzi (4 cm = 0.04 m aralık) olan iki kolon
    eski round(x, 1) mantığında siliniyordu. Yeni geometrik kontrolde ikisi de korunmalı.
    """
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 6  # metre
    doc.layers.add("KOLON")
    msp = doc.modelspace()

    # Kolon 1: x=10.00..10.30, y=5.00..5.60
    msp.add_lwpolyline(
        [(10.00, 5.0), (10.30, 5.0), (10.30, 5.6), (10.00, 5.6)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    # Kolon 2: x=10.04..10.34, y=5.00..5.60 (4 cm derz)
    msp.add_lwpolyline(
        [(10.04, 5.0), (10.34, 5.0), (10.34, 5.6), (10.04, 5.6)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )

    giris = tmp_path / "ikiz_kolon_m.dxf"
    cikis = tmp_path / "temiz_ikiz_m.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))

    sonuc_doc = ezdxf.readfile(cikis)
    kolonlar = list(sonuc_doc.modelspace().query('LWPOLYLINE[layer=="KOLON"]'))

    assert len(kolonlar) == 2, f"İkiz kolonlardan biri yanlışlıkla silindi! Kalan: {len(kolonlar)}"
    assert rapor.kolon_sayisi == 2
    assert rapor.cakisik_kolon_silinen == 0


def test_gercek_cakisik_kolon_silinir(tmp_path):
    """Birebir aynı koordinatlara sahip iki kolondan biri silinmelidir."""
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    msp = doc.modelspace()

    for _ in range(2):
        msp.add_lwpolyline(
            [(0, 0), (30, 0), (30, 60), (0, 60)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )

    giris = tmp_path / "cakisik.dxf"
    cikis = tmp_path / "temiz.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))
    sonuc = ezdxf.readfile(cikis)
    kolonlar = list(sonuc.modelspace().query('LWPOLYLINE[layer=="KOLON"]'))

    assert len(kolonlar) == 1
    assert rapor.cakisik_kolon_silinen == 1


def test_kullanici_elle_cizilmis_eksenleri_korunur(tmp_path):
    """Kullanıcının elle çizdiği KIRIS_EKSEN çizgileri tekrar çalıştırmalarda korunmalı."""
    doc = ezdxf.new()
    msp = doc.modelspace()
    for cx in (0, 400):
        msp.add_lwpolyline(
            [(cx - 15, -15), (cx + 15, -15), (cx + 15, 15), (cx - 15, 15)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    msp.add_line((0, -12.5), (400, -12.5), dxfattribs={"layer": "KIRIS"})
    msp.add_line((0, 12.5), (400, 12.5), dxfattribs={"layer": "KIRIS"})

    # Elle çizilen özel bir eksen
    elle = msp.add_line((800, 800), (900, 800), dxfattribs={"layer": "KIRIS_EKSEN"})
    elle_handle = elle.dxf.handle

    dosya = tmp_path / "koru.dxf"
    doc.saveas(dosya)

    # 3 kez ardışık temizle
    for _ in range(3):
        temizle(str(dosya), str(dosya))

    sonuc = ezdxf.readfile(dosya).modelspace()
    eksenler = list(sonuc.query('LINE[layer=="KIRIS_EKSEN"]'))
    handles = {e.dxf.handle for e in eksenler}

    assert elle_handle in handles, "Kullanıcının elle çizdiği eksen silindi!"
    assert len(eksenler) == 2  # 1 elle çizilen + 1 üretilen
