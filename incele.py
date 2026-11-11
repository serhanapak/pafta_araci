import sys
from collections import Counter
import ezdxf
from ezdxf import bbox

if len(sys.argv) < 2:
    sys.exit("kullanım: python3 incele.py dosya.dxf")

dosya = sys.argv[1]
doc = ezdxf.readfile(dosya)
msp = doc.modelspace()

birimler = {0: "belirsiz", 1: "inç", 2: "feet", 4: "mm", 5: "cm", 6: "m"}
birim = doc.header.get("$INSUNITS", 0)
print(f"dosya  : {dosya}")
print(f"sürüm  : {doc.dxfversion}")
print(f"birim  : {birimler.get(birim, birim)} (INSUNITS={birim})")

kutu = bbox.extents(msp)
if kutu.has_data:
    print(f"sınır  : {kutu.size.x:.0f} x {kutu.size.y:.0f} (çizim birimi)")

tur = Counter((e.dxf.layer, e.dxftype()) for e in msp)
print("\nkatman / tür / adet")
for (kat, t), n in sorted(tur.items()):
    print(f"  {kat:<22}{t:<12}{n}")

pl = Counter()
for e in msp.query("LWPOLYLINE"):
    pl[(e.dxf.layer, "kapalı" if e.closed else "açık", len(e))] += 1
if pl:
    print("\npolyline: katman / durum / köşe sayısı / adet")
    for (kat, d, k), n in sorted(pl.items()):
        print(f"  {kat:<22}{d:<8}{k:<4}{n}")

ins = Counter((e.dxf.layer, e.dxf.name) for e in msp.query("INSERT"))
if ins:
    print("\nblok: katman / ad / adet / taban noktası")
    for (kat, ad), n in sorted(ins.items()):
        try:
            tn = doc.blocks.get(ad).block.dxf.base_point
            tp = f"({tn.x:.1f}, {tn.y:.1f})"
        except Exception:
            tp = "okunamadı"
        print(f"  {kat:<22}{ad:<14}{n:<5}{tp}")
