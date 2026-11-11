import math
import ezdxf

xs = [0, 400, 850, 1250, 1750, 2200]
ys = [0, 450, 900, 1300]
B, H = 30, 60       # kolon kesiti (cm)
KB = 25             # kiriş genişliği (cm)

doc = ezdxf.new("R2018")
for ad, renk in (("KOLON", 1), ("KIRIS", 5)):
    doc.layers.add(ad, color=renk)
msp = doc.modelspace()

blk = doc.blocks.new("K3060")
blk.add_lwpolyline([(-B / 2, -H / 2), (B / 2, -H / 2), (B / 2, H / 2), (-B / 2, H / 2)], close=True)

acili = {(xs[1], ys[1]): 30, (xs[4], ys[2]): -20}   # derece
blok = {(xs[0], ys[3]), (xs[5], ys[0])}


def dikdortgen(cx, cy, aci):
    t = math.radians(aci)
    c, s = math.cos(t), math.sin(t)
    kose = ((-B / 2, -H / 2), (B / 2, -H / 2), (B / 2, H / 2), (-B / 2, H / 2))
    return [(cx + x * c - y * s, cy + x * s + y * c) for x, y in kose]


for x in xs:
    for y in ys:
        if (x, y) in blok:
            msp.add_blockref("K3060", (x, y), dxfattribs={"layer": "KOLON"})
        else:
            msp.add_lwpolyline(dikdortgen(x, y, acili.get((x, y), 0)), close=True,
                               dxfattribs={"layer": "KOLON"})

# kiriş: iki kenar çizgisi, kolon yüzünden kolon yüzüne
oz = {"layer": "KIRIS"}
for y in ys:
    for i in range(len(xs) - 1):
        x0, x1 = xs[i] + B / 2, xs[i + 1] - B / 2
        for d in (-KB / 2, KB / 2):
            msp.add_line((x0, y + d), (x1, y + d), dxfattribs=oz)
for x in xs:
    for j in range(len(ys) - 1):
        y0, y1 = ys[j] + H / 2, ys[j + 1] - H / 2
        for d in (-KB / 2, KB / 2):
            msp.add_line((x + d, y0), (x + d, y1), dxfattribs=oz)

doc.saveas("gercekci_kat.dxf")
print("gercekci_kat.dxf: 24 kolon (2 dönük, 2 blok), 38 kiriş (76 çizgi)")
