import ezdxf

from pafta.katman import katmanlari_listele, katman_tani


doc = ezdxf.new()

adlar = [
    "KOLON",
    "SUTUNLAR",
    "COLUMN",
    "KIRIS",
    "BEAM",
    "AKS",
    "GRID",
    "PERDE",
    "SHEAR_WALL",
    "ANTET",
    "TARAMA",
]

for ad in adlar:
    doc.layers.add(ad)

liste = katmanlari_listele(doc)
assert "KOLON" in liste
assert "ANTET" in liste

r = katman_tani(doc)

assert "KOLON" in r.katmanlar["KOLON"]
assert "SUTUNLAR" in r.katmanlar["KOLON"]
assert "COLUMN" in r.katmanlar["KOLON"]

assert "KIRIS" in r.katmanlar["KIRIS"]
assert "BEAM" in r.katmanlar["KIRIS"]

assert "AKS" in r.katmanlar["AKS"]
assert "GRID" in r.katmanlar["AKS"]

assert "PERDE" in r.katmanlar["PERDE"]
assert "SHEAR_WALL" in r.katmanlar["PERDE"]

assert "ANTET" in r.tanimsiz
assert "TARAMA" in r.tanimsiz

# Kullanıcı seçimi otomatik sınıflandırmayı geçersiz kılar.
r = katman_tani(doc, {"KOLON": ["ANTET"]})
assert "ANTET" in r.katmanlar["KOLON"]

# Olmayan katman seçilemez.
try:
    katman_tani(doc, {"KOLON": ["OLMAYAN"]})
    raise AssertionError("Olmayan katman kabul edildi")
except ValueError:
    pass

print("KATMAN MODULU: BUTUN TESTLER GECTI")
