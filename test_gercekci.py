import math
import re
import subprocess
import sys
import ezdxf
from ortak import katmandakiler, kolon_merkezleri, EKSEN_KATMAN


def calistir(*arg):
    r = subprocess.run([sys.executable, *arg], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"{' '.join(arg)} hata verdi:\n{r.stderr}")
        sys.exit(1)
    return r.stdout


calistir("uret_gercekci.py")
cikti_t = calistir("temizle.py", "gercekci_kat.dxf", "gercekci_temiz.dxf")
cikti_a = calistir("aks.py", "gercekci_temiz.dxf", "gercekci_aks.dxf")

hata = 0


def kontrol(ad, bulunan, beklenen):
    global hata
    ok = bulunan == beklenen
    if not ok:
        hata += 1
    print(f"{'OK  ' if ok else 'HATA'} {ad}: {bulunan} (beklenen {beklenen})")


kolon = int(re.search(r"KOLON\s*:\s*(\d+) adet", cikti_t).group(1))
kiris = int(re.search(r"KİRİŞ\s*:\s*(\d+) adet", cikti_t).group(1))
dusey, yatay = map(int, re.search(r"(\d+) düşey.*?(\d+) yatay", cikti_a).groups())
bos = int(re.search(r"boş kesişim:\s*(\d+)", cikti_a).group(1))

kontrol("kolon adedi (22 poligon + 2 blok)", kolon, 24)
kontrol("kiriş adedi (76 çizgi = 38 kiriş)", kiris, 38)
kontrol("düşey aks", dusey, 6)
kontrol("yatay aks", yatay, 4)
kontrol("boş aks kesişimi", bos, 0)

# çıktı dosyasını doğrudan oku
d = ezdxf.readfile("gercekci_temiz.dxf")
m = d.modelspace()
merk = kolon_merkezleri(d, m)
eks = katmandakiler(m, "LINE", [EKSEN_KATMAN])
kontrol("kolon merkezi (poligon + blok)", len(merk), 24)
kontrol("kiriş ekseni (KIRIS_EKSEN)", len(eks), 38)
disarda = 0
for l in eks:
    for p in ((l.dxf.start.x, l.dxf.start.y), (l.dxf.end.x, l.dxf.end.y)):
        if min(math.dist(c, p) for c in merk) > 1e-6:
            disarda += 1
kontrol("kolon merkezine oturmayan eksen ucu", disarda, 0)

print("TÜM TESTLER GEÇTİ" if hata == 0 else f"{hata} TEST BAŞARISIZ")
sys.exit(1 if hata else 0)
