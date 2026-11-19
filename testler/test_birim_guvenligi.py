import ezdxf
import pytest

from pafta.birim import Ayar, BirimBelirsizHatasi, birim_tahmin
from pafta.kat import KatPaftasi


def _dxf_dosyasi(path, *, header, rectangle=None):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = header
    if rectangle is not None:
        width, height = rectangle
        doc.modelspace().add_lwpolyline(
            [(0, 0), (width, 0), (width, height), (0, height)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    doc.saveas(path)
    return path


def _dikdortgenler(doc, boyutlar, katman="KOLON"):
    msp = doc.modelspace()
    for i, (width, height) in enumerate(boyutlar):
        x = i * max(width, 300) * 2
        msp.add_lwpolyline(
            [(x, 0), (x + width, 0), (x + width, height), (x, height)],
            close=True,
            dxfattribs={"layer": katman},
        )


@pytest.mark.parametrize(
    "unit,header,dimensions",
    [("mm", 4, (300, 600)), ("cm", 5, (30, 60)), ("m", 6, (0.3, 0.6))],
)
def test_bilinen_baslik_ve_guvenilir_geometri_birim_davranisini_korur(
    tmp_path, unit, header, dimensions
):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = header
    _dikdortgenler(doc, [dimensions] * 5)
    source = tmp_path / f"{unit}.dxf"
    doc.saveas(source)

    pafta = KatPaftasi(source)

    assert pafta.ayar.birim == unit
    assert birim_tahmin(pafta.doc, ["KOLON"]).birim == unit
    assert Ayar.olustur(unit).birim == unit


def test_geometri_bilinen_baslik_olmadan_birimi_tahmin_edebilir(tmp_path):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 0
    _dikdortgenler(doc, [(30, 60)] * 5)
    source = tmp_path / "geometri.dxf"
    doc.saveas(source)

    pafta = KatPaftasi(source)

    assert pafta.ayar.birim == "cm"
    assert pafta.birim_sonucu.birim == "cm"


def test_daireler_dikdortgen_ornekleriyle_birlikte_degerlendirilebilir():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 0
    _dikdortgenler(doc, [(30, 60)] * 4)
    for x in (5000,):
        doc.modelspace().add_circle((x, 0), 20, dxfattribs={"layer": "KOLON"})

    result = birim_tahmin(doc, ["KOLON"])

    assert result.birim == "cm"
    assert result.medyan == 30
    assert result.adet == 5


def test_daire_caplari_tek_basina_birim_belirleyemez():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 0
    for x in (0, 500, 1000, 1500, 2000):
        doc.modelspace().add_circle((x, 0), 20, dxfattribs={"layer": "KOLON"})

    result = birim_tahmin(doc, ["KOLON"])

    assert result.birim is None
    assert result.bulgular[-1].kod == "BIRIM_BELIRSIZ"


def test_geometrik_ornekler_farkli_birim_araliklarina_duserse_tahmin_durur():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 0
    _dikdortgenler(doc, [(30, 60)] * 3 + [(300, 600)] * 2)

    result = birim_tahmin(doc, ["KOLON"])

    assert result.birim is None
    assert any(b.kod == "BIRIM_GEO_TUTARSIZ" for b in result.bulgular)


def test_baslik_geometri_celiskisi_katpaftasi_analizini_durdurur(tmp_path):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 6
    _dikdortgenler(doc, [(30, 60)] * 5)
    source = tmp_path / "baslik_geometri_celiskisi.dxf"
    doc.saveas(source)

    with pytest.raises(BirimBelirsizHatasi):
        KatPaftasi(source)


def test_bilinen_baslik_ve_yetersiz_geometri_birlikte_analizi_durdurur(tmp_path):
    source = _dxf_dosyasi(
        tmp_path / "baslik_fallback.dxf", header=4, rectangle=(140, 500)
    )

    result = birim_tahmin(ezdxf.readfile(source), ["KOLON"])

    assert result.birim is None
    assert result.baslik == "mm"
    assert "başlığında mm birimi var" in result.bulgular[-1].mesaj
    assert "örnek var" in result.bulgular[-1].mesaj
    with pytest.raises(BirimBelirsizHatasi, match="başlığında mm birimi var"):
        KatPaftasi(source)


def test_bilinen_baslik_geometri_yokken_kullanilmaz(tmp_path):
    source = _dxf_dosyasi(tmp_path / "baslik.dxf", header=4)

    result = birim_tahmin(ezdxf.readfile(source), ["KOLON"])

    assert result.birim is None
    assert result.baslik == "mm"
    assert "başlığında mm birimi var" in result.bulgular[-1].mesaj
    with pytest.raises(BirimBelirsizHatasi):
        KatPaftasi(source)


def test_bilinen_baslik_tek_dikdortgenle_kullanilir_ve_uyari_verilir():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    _dikdortgenler(doc, [(30, 60)])

    result = birim_tahmin(doc, ["KOLON"])

    assert result.birim is None
    assert result.baslik == "mm"
    assert "Yalnızca 1 geometrik örnek var" in result.bulgular[-1].mesaj


def test_bilinmeyen_baslikta_yetersiz_dikdortgen_ornegi_analizi_durdurur(tmp_path):
    source = _dxf_dosyasi(tmp_path / "tek_ornek.dxf", header=0, rectangle=(30, 60))

    with pytest.raises(BirimBelirsizHatasi):
        KatPaftasi(source)


def test_yanlis_bilinen_baslik_ve_tek_dikdortgen_cikis_dosyasina_yazmaz(tmp_path):
    source = _dxf_dosyasi(
        tmp_path / "yanlis_baslik.dxf", header=6, rectangle=(30, 60)
    )
    output = tmp_path / "yanlis_baslik_cikti.dxf"

    with pytest.raises(BirimBelirsizHatasi, match="başlığında m birimi var"):
        KatPaftasi(source).temizle(output)

    assert not output.exists()


def test_bilinen_baslikla_daireler_tek_basina_yine_yetersizdir():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 5
    for x in range(5):
        doc.modelspace().add_circle((x * 100, 0), 20, dxfattribs={"layer": "KOLON"})

    result = birim_tahmin(doc, ["KOLON"])

    assert result.birim is None
    assert result.baslik == "cm"
    assert "başlığında cm birimi var" in result.bulgular[-1].mesaj


def test_birim_belirsizse_analiz_baslamadan_durur_ve_cikis_yazilmaz(tmp_path):
    source = _dxf_dosyasi(tmp_path / "belirsiz.dxf", header=0)
    doc = ezdxf.readfile(source)
    doc.modelspace().add_lwpolyline(
        [(0, 0), (25, 0), (20, 50), (5, 50)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    doc.saveas(source)
    output = tmp_path / "cikti.dxf"

    with pytest.raises(BirimBelirsizHatasi, match="birimi açıkça seçin"):
        KatPaftasi(source).temizle(output)

    assert not output.exists()


def test_belirsiz_birim_kullanici_tarafindan_zorlanabilir(tmp_path):
    source = _dxf_dosyasi(tmp_path / "zorla.dxf", header=0)
    output = tmp_path / "zorla_cikti.dxf"

    report = KatPaftasi(source, birim_zorla="cm").temizle(output)

    assert report.birim == "cm"
    assert output.exists()


def test_aks_cli_birim_belirsizligini_temiz_hata_olarak_gosterir(
    tmp_path, monkeypatch, capsys
):
    from aks import main

    source = _dxf_dosyasi(tmp_path / "aks_belirsiz.dxf", header=0)
    output = tmp_path / "aks_cikti.dxf"
    monkeypatch.setattr("sys.argv", ["aks.py", str(source), str(output)])

    with pytest.raises(SystemExit) as exc:
        main()

    assert exc.value.code.startswith("HATA: Çizim birimi güvenilir biçimde belirlenemedi")
    assert not output.exists()
    assert "--birim mm|cm|m" in capsys.readouterr().out + str(exc.value.code)


def test_aks_cli_acik_birim_secimiyle_devam_eder(tmp_path, monkeypatch):
    from aks import main

    source = _dxf_dosyasi(tmp_path / "aks_zorla.dxf", header=0)
    doc = ezdxf.readfile(source)
    _dikdortgenler(doc, [(30, 30)] * 4)
    doc.saveas(source)
    output = tmp_path / "aks_zorla_cikti.dxf"
    monkeypatch.setattr(
        "sys.argv", ["aks.py", str(source), str(output), "--birim", "cm"]
    )

    main()

    assert output.exists()


def test_temizle_cli_birim_belirsizliginde_cikis_kaydetmez(
    tmp_path, monkeypatch, capsys
):
    from temizle import main

    source = _dxf_dosyasi(tmp_path / "temizle_belirsiz.dxf", header=0)
    output = tmp_path / "temizle_cikti.dxf"
    monkeypatch.setattr("sys.argv", ["temizle.py", str(source), str(output)])

    with pytest.raises(SystemExit) as exc:
        main()

    assert str(exc.value.code).startswith("HATA: Çizim birimi güvenilir biçimde belirlenemedi")
    assert not output.exists()
    assert "--birim mm|cm|m" in str(exc.value.code)


def test_temizle_cli_acik_birim_secimiyle_devam_eder(tmp_path, monkeypatch):
    from temizle import main

    source = _dxf_dosyasi(tmp_path / "cli_zorla.dxf", header=0)
    output = tmp_path / "cli_zorla_cikti.dxf"
    monkeypatch.setattr(
        "sys.argv", ["temizle.py", str(source), str(output), "--birim", "cm"]
    )

    main()

    assert output.exists()
    assert ezdxf.readfile(output).header["$INSUNITS"] == 0
