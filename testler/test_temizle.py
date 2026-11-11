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
