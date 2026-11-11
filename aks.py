import sys
import ezdxf
from ezdxf.enums import TextEntityAlignment
from ortak import (kolon_merkezleri, grupla, harf, AKS_KATMAN, TOL_AKS,
                   BALON_YC, BALON_OFS, AKS_UZAMA, YAZI_H)

giris = sys.argv[1] if len(sys.argv) > 1 else "temiz_kat.dxf"
cikis = sys.argv[2] if len(sys.argv) > 2 else "aks_kat.dxf"

doc = ezdxf.readfile(giris)
msp = doc.modelspace()

merkezler = kolon_merkezleri(doc, msp)
if not merkezler:
    sys.exit("kolon bulunamadı, KOLON_KATMAN ayarını kontrol et")

xs = grupla([m[0] for m in merkezler], TOL_AKS)
ys = grupla([m[1] for m in merkezler], TOL_AKS)

if AKS_KATMAN not in doc.layers:
    doc.layers.add(AKS_KATMAN, color=3)
oz = {"layer": AKS_KATMAN}

# düşey akslar: 1, 2, 3...
for i, x in enumerate(xs):
    by = ys[0] - BALON_OFS
    msp.add_line((x, by + BALON_YC), (x, ys[-1] + AKS_UZAMA), dxfattribs=oz)
    msp.add_circle((x, by), BALON_YC, dxfattribs=oz)
    msp.add_text(str(i + 1), height=YAZI_H, dxfattribs=oz).set_placement(
        (x, by), align=TextEntityAlignment.MIDDLE_CENTER)

# yatay akslar: A, B, C...
for j, y in enumerate(ys):
    bx = xs[0] - BALON_OFS
    msp.add_line((bx + BALON_YC, y), (xs[-1] + AKS_UZAMA, y), dxfattribs=oz)
    msp.add_circle((bx, y), BALON_YC, dxfattribs=oz)
    msp.add_text(harf(j), height=YAZI_H, dxfattribs=oz).set_placement(
        (bx, y), align=TextEntityAlignment.MIDDLE_CENTER)

# kolonu olmayan aks kesişimi
bos = 0
for x in xs:
    for y in ys:
        if not any(abs(m[0] - x) <= TOL_AKS and abs(m[1] - y) <= TOL_AKS for m in merkezler):
            bos += 1

doc.saveas(cikis)

print(f"aks      : {len(xs)} düşey (1-{len(xs)}) x {len(ys)} yatay (A-{harf(len(ys) - 1)})")
print("açıklık X:", [round(xs[i + 1] - xs[i], 1) for i in range(len(xs) - 1)])
print("açıklık Y:", [round(ys[i + 1] - ys[i], 1) for i in range(len(ys) - 1)])
print(f"boş kesişim: {bos}")
print(f"çıkış    : {cikis}")
