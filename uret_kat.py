import ezdxf

# Aks mesafeleri (cm)
xs = [0, 400, 850, 1250, 1750, 2200]   # 6 aks
ys = [0, 450, 900, 1300]               # 4 aks
KOLON_B, KOLON_H = 30, 60              # 30x60 kolon

doc = ezdxf.new("R2018")
doc.layers.add("KOLON", color=1)
doc.layers.add("KIRIS", color=5)
msp = doc.modelspace()

# Kolonlar: kapalı dikdörtgen polyline
for x in xs:
    for y in ys:
        a, b = KOLON_B / 2, KOLON_H / 2
        pts = [(x-a, y-b), (x+a, y-b), (x+a, y+b), (x-a, y+b)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "KOLON"})

# Kirişler: kolon merkezleri arası çizgi
for y in ys:
    for i in range(len(xs) - 1):
        msp.add_line((xs[i], y), (xs[i+1], y), dxfattribs={"layer": "KIRIS"})
for x in xs:
    for j in range(len(ys) - 1):
        msp.add_line((x, ys[j]), (x, ys[j+1]), dxfattribs={"layer": "KIRIS"})

doc.saveas("ornek_kat.dxf")

# Geri oku ve say
doc2 = ezdxf.readfile("ornek_kat.dxf")
m = doc2.modelspace()
kolon = len(m.query('LWPOLYLINE[layer=="KOLON"]'))
kiris = len(m.query('LINE[layer=="KIRIS"]'))
print("Kolon:", kolon, "(beklenen 24)")
print("Kiriş:", kiris, "(beklenen 38)")

