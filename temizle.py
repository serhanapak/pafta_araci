import sys
import math
import statistics
import ezdxf
from ortak import (katmandakiler, kose_listesi, merkez, blok_merkezleri, kiris_ciftle,
                   eksen_uzat, TOL_UC, KOLON_KATMAN, KIRIS_KATMAN, EKSEN_KATMAN,
                   KIRIS_EN_MIN, KIRIS_EN_MAX, YUZ_MAX, TOL_EKSEN)

giris = sys.argv[1] if len(sys.argv) > 1 else "bozuk_kat.dxf"
cikis = sys.argv[2] if len(sys.argv) > 2 else "temiz_kat.dxf"

doc = ezdxf.readfile(giris)
msp = doc.modelspace()

# kolon / perde: polyline
merkezler = []
gorulen = set()
acik = cakisik_kolon = gecersiz = 0
kisa_kenar = []

for pl in katmandakiler(msp, "LWPOLYLINE", KOLON_KATMAN):
    pts = kose_listesi(pl)
    if len(pts) < 3:
        msp.delete_entity(pl)
        gecersiz += 1
        continue
    if not pl.closed:
        if math.dist(pts[0], pts[-1]) <= TOL_UC:
            if len(pts) > 3:
                pts = pts[:-1]
                pl.set_points(pts, format="xy")
            pl.closed = True
            acik += 1
    anahtar = frozenset((round(x, 1), round(y, 1)) for x, y in pts)
    if anahtar in gorulen:
        msp.delete_entity(pl)
        cakisik_kolon += 1
        continue
    gorulen.add(anahtar)
    merkezler.append(merkez(pts))
    px = [p[0] for p in pts]
    py = [p[1] for p in pts]
    kisa_kenar.append(min(max(px) - min(px), max(py) - min(py)))

poly_adet = len(merkezler)

# kolon: blok (INSERT)
gorulen_blok = set()
blok_adet = cakisik_blok = 0
for ins in katmandakiler(msp, "INSERT", KOLON_KATMAN):
    for m in blok_merkezleri(doc, ins):
        anahtar = (round(m[0], 1), round(m[1], 1))
        if anahtar in gorulen_blok:
            cakisik_blok += 1
            continue
        gorulen_blok.add(anahtar)
        merkezler.append(m)
        blok_adet += 1


def yakala(p):
    if not merkezler:
        return p
    m = min(merkezler, key=lambda c: math.dist(c, p))
    return m if math.dist(m, p) <= TOL_UC else p


# kiriş çizgileri
gorulen_k = set()
yakalanan = cakisik_kiris = sifir_boy = 0
cizgiler = []

for l in katmandakiler(msp, "LINE", KIRIS_KATMAN):
    s0 = (l.dxf.start.x, l.dxf.start.y)
    e0 = (l.dxf.end.x, l.dxf.end.y)
    s, e = yakala(s0), yakala(e0)
    if math.dist(s, s0) > 1e-6 or math.dist(e, e0) > 1e-6:
        yakalanan += 1
    if math.dist(s, e) <= TOL_UC:
        msp.delete_entity(l)
        sifir_boy += 1
        continue
    anahtar = frozenset([(round(s[0], 1), round(s[1], 1)),
                         (round(e[0], 1), round(e[1], 1))])
    if anahtar in gorulen_k:
        msp.delete_entity(l)
        cakisik_kiris += 1
        continue
    gorulen_k.add(anahtar)
    l.dxf.start = (s[0], s[1], 0)
    l.dxf.end = (e[0], e[1], 0)
    cizgiler.append((s, e))

# çift kenar çizgisinden eksen, eşleşmeyenler tek çizgi kiriş
eksenler, eslesen = kiris_ciftle(cizgiler, KIRIS_EN_MIN, KIRIS_EN_MAX)
if EKSEN_KATMAN not in doc.layers:
    doc.layers.add(EKSEN_KATMAN, color=2)

nihai = []
for p, q in eksenler:
    p, q = eksen_uzat(p, q, merkezler, YUZ_MAX, TOL_EKSEN)
    msp.add_line(p, q, dxfattribs={"layer": EKSEN_KATMAN})
    nihai.append((p, q))
tek = [c for i, c in enumerate(cizgiler) if i not in eslesen]
nihai += tek

kolon_disi = 0
for p, q in nihai:
    for n in (p, q):
        if merkezler and min(math.dist(c, n) for c in merkezler) > 1e-6:
            kolon_disi += 1

doc.saveas(cikis)

if kisa_kenar:
    med = statistics.median(kisa_kenar)
    if med < 5 or med > 150:
        print(f"UYARI: kolon kısa kenar medyanı {med:.1f}, çizim cm değil (m/mm) olabilir. "
              f"Toleranslar cm varsayıyor, ortak.py'den ayarla.")

print(f"giriş : {giris}")
print(f"KOLON : {len(merkezler)} adet ({poly_adet} polyline + {blok_adet} blok) | açık->kapalı {acik} | "
      f"çakışık silinen {cakisik_kolon} | geçersiz silinen {gecersiz} | çakışık blok (silinmedi) {cakisik_blok}")
print(f"KİRİŞ : {len(nihai)} adet | çift çizgiden eksen {len(eksenler)} | tek çizgi {len(tek)} | "
      f"uç yakalanan {yakalanan} | çakışık silinen {cakisik_kiris} | sıfır boy silinen {sifir_boy} | "
      f"kolon dışı uç {kolon_disi}")
print(f"çıkış : {cikis}")
