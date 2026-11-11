import ezdxf

doc = ezdxf.readfile("ornek_kat.dxf")
msp = doc.modelspace()
kolonlar = list(msp.query('LWPOLYLINE[layer=="KOLON"]'))
kirisler = list(msp.query('LINE[layer=="KIRIS"]'))

for pl in kolonlar[:2]:
    pl.closed = False

for l in kirisler[:3]:
    msp.add_line(l.dxf.start, l.dxf.end, dxfattribs={"layer": "KIRIS"})

for l in kirisler[3:7]:
    s = l.dxf.start
    l.dxf.start = (s.x + 0.4, s.y + 0.4, 0)

doc.saveas("bozuk_kat.dxf")
print("bozuk_kat.dxf hazir")
