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
    temizle(str(dosya), str(dosya), birim="cm")

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

    aks_uret(str(dosya), str(dosya), birim="cm")

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

    rapor = temizle(str(giris), str(cikis), birim="m")

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

    rapor = temizle(str(giris), str(cikis), birim="cm")
    sonuc = ezdxf.readfile(cikis)
    kolonlar = list(sonuc.modelspace().query('LWPOLYLINE[layer=="KOLON"]'))

    assert len(kolonlar) == 1
    assert rapor.cakisik_kolon_silinen == 1


def test_kullanici_elle_cizilmis_eksenleri_korunur(tmp_path):
    """Kullanıcının elle çizdiği KIRIS_EKSEN çizgileri tekrar çalıştırmalarda korunmalı."""
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 5
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
        temizle(str(dosya), str(dosya), birim="cm")

    sonuc = ezdxf.readfile(dosya).modelspace()
    eksenler = list(sonuc.query('LINE[layer=="KIRIS_EKSEN"]'))
    handles = {e.dxf.handle for e in eksenler}

    assert elle_handle in handles, "Kullanıcının elle çizdiği eksen silindi!"
    assert len(eksenler) == 2  # 1 elle çizilen + 1 üretilen


def test_yedekler_onceki_yedeklerin_uzerine_yazilmaz(tmp_path):
    """Ardışık yedeklemelerde önceki yedeklerin içeriği korunmalıdır."""
    dosya = tmp_path / "proje.dxf"

    dosya.write_bytes(b"ilk surum")
    ilk = yedek_al(dosya)

    dosya.write_bytes(b"ikinci surum")
    ikinci = yedek_al(dosya)

    assert ilk is not None
    assert ikinci is not None
    assert ilk != ikinci
    assert ilk.read_bytes() == b"ilk surum"
    assert ikinci.read_bytes() == b"ikinci surum"


def test_gecersiz_gecici_dxf_orijinali_ve_yedegi_korur(tmp_path):
    """Geçici DXF açılamazsa hedef dosya değiştirilmemeli ve yedek alınmamalıdır."""

    hedef = tmp_path / "orijinal.dxf"
    orijinal_icerik = b"orijinal dosya icerigi"
    hedef.write_bytes(orijinal_icerik)

    class GecersizDoc:
        dxfversion = "AC1015"

        def saveas(self, yol):
            Path(yol).write_bytes(b"bu gecerli bir DXF degil")

    hata_alindi = False

    try:
        guvenli_kaydet(GecersizDoc(), hedef)
    except Exception:
        hata_alindi = True

    assert hata_alindi, "Geçersiz DXF kaydı hata üretmeliydi."
    assert hedef.read_bytes() == orijinal_icerik
    assert not Path(str(hedef) + ".bak").exists()


def test_guvenli_kaydet_mevcut_dosya_izinlerini_korur(tmp_path):
    """Üzerine yazılan DXF'nin dosya izinleri korunmalıdır."""
    import stat

    hedef = tmp_path / "izin_testi.dxf"
    ezdxf.new().saveas(hedef)

    hedef.chmod(0o640)

    guvenli_kaydet(ezdxf.new(), hedef)

    izinler = stat.S_IMODE(hedef.stat().st_mode)
    assert izinler == 0o640


def test_guvenli_kaydet_bellekteki_dxf_surumu_korur(tmp_path):
    """Kaydetme sırasında sürüm yükseltilse de bellek içindeki belge değişmemelidir."""
    hedef = tmp_path / "surum_testi.dxf"
    doc = ezdxf.new("R12")
    orijinal_surumu = doc.dxfversion

    guvenli_kaydet(doc, hedef, yedekle=False)

    assert doc.dxfversion == orijinal_surumu
    kaydedilen_doc = ezdxf.readfile(hedef)
    assert kaydedilen_doc.dxfversion == "AC1015"


def test_farkli_giris_ve_cikis_dosyalarinda_cikis_yedeklenmez(tmp_path):
    """Farklı bir çıkış dosyasının üzerine yazılırken otomatik yedek alınmamalıdır."""
    giris = tmp_path / "giris.dxf"
    cikis = tmp_path / "cikis.dxf"

    ezdxf.new().saveas(giris)
    ezdxf.new().saveas(cikis)

    doc = ezdxf.readfile(giris)
    guvenli_kaydet(doc, cikis, giris_yolu=giris)

    assert cikis.exists()
    assert not Path(str(cikis) + ".bak").exists()
    ezdxf.readfile(cikis)
