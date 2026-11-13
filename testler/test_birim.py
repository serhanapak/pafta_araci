import ezdxf
from pafta.birim import birim_tahmin, Ayar

def kat(olcek=1, baslik=5, n=10):
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = baslik
    msp = doc.modelspace()

    for i in range(n):
        x = i * 400 * olcek
        w, h = 30 * olcek, 60 * olcek
        msp.add_lwpolyline(
            [(x, 0), (x+w, 0), (x+w, h), (x, h)],
            close=True
        )
    return doc


def test_santimetre():
    r = birim_tahmin(kat())
    assert r.birim == "cm"
    assert len(r.bulgular) == 0


def test_metre():
    r = birim_tahmin(kat(0.01, 6))
    assert r.birim == "m"


def test_milimetre():
    r = birim_tahmin(kat(10, 4))
    assert r.birim == "mm"


def test_geometri_yoksa_bilinen_dxf_baslik_birimi_kullanilir():
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4

    r = birim_tahmin(doc)

    assert r.birim == "mm"
    assert r.baslik == "mm"
    assert any(b.kod == "BIRIM_AZ_VERI" for b in r.bulgular)


def test_baslik_geometri_celiskisi():
    r = birim_tahmin(kat(1, 6))
    assert r.birim == "cm"
    assert r.bulgular[0].kod == "BIRIM_BASLIK_UYUSMUYOR"


def test_birim_ayarlari():
    assert Ayar.olustur("cm").tol_uc == 1
    assert Ayar.olustur("mm").tol_uc == 10
