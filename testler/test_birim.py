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

# Santimetre
r = birim_tahmin(kat())
assert r.birim == "cm"
assert len(r.bulgular) == 0

# Metre
r = birim_tahmin(kat(0.01, 6))
assert r.birim == "m"

# Milimetre
r = birim_tahmin(kat(10, 4))
assert r.birim == "mm"

# Baslik ve geometri celiskisi
r = birim_tahmin(kat(1, 6))
assert r.birim == "cm"
assert r.bulgular[0].kod == "BIRIM_BASLIK_UYUSMUYOR"

# Birim ayarlari
assert Ayar.olustur("cm").tol_uc == 1
assert Ayar.olustur("mm").tol_uc == 10

print("BIRIM MODULU: BUTUN TESTLER GECTI")
