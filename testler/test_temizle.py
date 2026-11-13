import ezdxf


def test_uzak_uclu_acik_kolon_otomatik_kapatilmaz(tmp_path, calistir):
    doc = ezdxf.new()
    doc.layers.add("KOLON")

    doc.modelspace().add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=False,
        dxfattribs={"layer": "KOLON"},
    )

    giris = tmp_path / "acik_kolon.dxf"
    cikis = tmp_path / "sonuc.dxf"
    doc.saveas(giris)

    calistir("temizle.py", tmp_path, giris.name, cikis.name)

    sonuc = ezdxf.readfile(cikis)
    kolonlar = list(sonuc.modelspace().query("LWPOLYLINE"))

    assert len(kolonlar) == 1
    assert kolonlar[0].closed is False


def test_yakin_uclu_acik_kolon_kapatilir(tmp_path, calistir):
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60), (0.2, 0)],
        close=False,
        dxfattribs={"layer": "KOLON"},
    )
    giris = tmp_path / "yakin_acik_kolon.dxf"
    cikis = tmp_path / "sonuc.dxf"
    doc.saveas(giris)

    calistir("temizle.py", tmp_path, giris.name, cikis.name)

    sonuc = ezdxf.readfile(cikis)
    kolonlar = list(sonuc.modelspace().query("LWPOLYLINE"))
    assert len(kolonlar) == 1
    assert kolonlar[0].closed is True
    assert len(list(kolonlar[0].get_points())) == 4


def test_ayni_dosyada_tekrar_calistirma_eksenleri_cogaltmaz_ve_elle_cizileni_korur(
    tmp_path, calistir
):
    doc = ezdxf.new()
    msp = doc.modelspace()
    for cx in (0, 500):
        msp.add_lwpolyline(
            [(cx - 15, -15), (cx + 15, -15), (cx + 15, 15), (cx - 15, 15)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    msp.add_line((0, -15), (500, -15), dxfattribs={"layer": "KIRIS"})
    msp.add_line((0, 15), (500, 15), dxfattribs={"layer": "KIRIS"})
    manual = msp.add_line((1000, 1000), (1200, 1000), dxfattribs={"layer": "KIRIS_EKSEN"})
    manual_handle = manual.dxf.handle
    dosya = tmp_path / "tekrar.dxf"
    doc.saveas(dosya)

    calistir("temizle.py", tmp_path, dosya.name, dosya.name)
    ilk = ezdxf.readfile(dosya).modelspace()
    ilk_eksenler = list(ilk.query('LINE[layer=="KIRIS_EKSEN"]'))
    ilk_isaretli = [e for e in ilk_eksenler if e.has_xdata("PAFTA_ARACI")]

    calistir("temizle.py", tmp_path, dosya.name, dosya.name)
    ikinci = ezdxf.readfile(dosya).modelspace()
    ikinci_eksenler = list(ikinci.query('LINE[layer=="KIRIS_EKSEN"]'))
    ikinci_isaretli = [e for e in ikinci_eksenler if e.has_xdata("PAFTA_ARACI")]

    assert len(ilk_eksenler) == len(ikinci_eksenler) == 2
    assert len(ilk_isaretli) == len(ikinci_isaretli) == 1
    assert manual_handle in {e.dxf.handle for e in ikinci_eksenler}
