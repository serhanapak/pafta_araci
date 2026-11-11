import subprocess
import sys
import math
import ezdxf
from ortak import katmandakiler, kose_listesi, merkez, KOLON_KATMAN, KIRIS_KATMAN, AKS_KATMAN

for dosya in ["uret_kat.py", "boz.py", "temizle.py", "aks.py"]:
    r = subprocess.run([sys.executable, dosya], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{dosya} hata verdi:\n{r.stderr}")
        sys.exit(1)

hata = 0


def kontrol(ad, bulunan, beklenen):
    global hata
    ok = bulunan == beklenen
    if not ok:
        hata += 1
    print(f"{'OK  ' if ok else 'HATA'} {ad}: {bulunan} (beklenen {beklenen})")


# bozuk dosya
b = ezdxf.readfile("bozuk_kat.dxf").modelspace()
kontrol("bozuk, açık kolon", sum(1 for p in katmandakiler(b, "LWPOLYLINE", KOLON_KATMAN) if not p.closed), 2)
kontrol("bozuk, kiriş (3 çakışık dahil)", len(katmandakiler(b, "LINE", KIRIS_KATMAN)), 41)

# temiz dosya
t = ezdxf.readfile("temiz_kat.dxf").modelspace()
kolonlar = katmandakiler(t, "LWPOLYLINE", KOLON_KATMAN)
kirisler = katmandakiler(t, "LINE", KIRIS_KATMAN)
merk = [merkez(kose_listesi(p)) for p in kolonlar]
kontrol("temiz, kolon", len(kolonlar), 24)
kontrol("temiz, açık kolon", sum(1 for p in kolonlar if not p.closed), 0)
kontrol("temiz, kiriş", len(kirisler), 38)

disarda = 0
anahtarlar = set()
for l in kirisler:
    s = (l.dxf.start.x, l.dxf.start.y)
    e = (l.dxf.end.x, l.dxf.end.y)
    for p in (s, e):
        if min(math.dist(c, p) for c in merk) > 1e-6:
            disarda += 1
    anahtarlar.add(frozenset([(round(s[0], 1), round(s[1], 1)), (round(e[0], 1), round(e[1], 1))]))
kontrol("temiz, kolon merkezine oturmayan kiriş ucu", disarda, 0)
kontrol("temiz, çakışık kiriş", len(kirisler) - len(anahtarlar), 0)

# aks dosyası
a = ezdxf.readfile("aks_kat.dxf").modelspace()
kontrol("aks çizgisi", len(katmandakiler(a, "LINE", [AKS_KATMAN])), 10)
kontrol("aks balonu", len(katmandakiler(a, "CIRCLE", [AKS_KATMAN])), 10)
kontrol("aks yazısı", len(katmandakiler(a, "TEXT", [AKS_KATMAN])), 10)
kontrol("aks dosyasında kolon", len(katmandakiler(a, "LWPOLYLINE", KOLON_KATMAN)), 24)
kontrol("aks dosyasında kiriş", len(katmandakiler(a, "LINE", KIRIS_KATMAN)), 38)

print("TÜM TESTLER GEÇTİ" if hata == 0 else f"{hata} TEST BAŞARISIZ")
sys.exit(1 if hata else 0)
