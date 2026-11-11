import math

# katman adları: Sta4CAD çıktısında farklıysa buradan değiştir
KOLON_KATMAN = ["KOLON"]
KIRIS_KATMAN = ["KIRIS"]
AKS_KATMAN = "AKS"
EKSEN_KATMAN = "KIRIS_EKSEN"

# tolerans ve ölçüler (çizim birimi cm varsayımı)
TOL_UC = 1.0          # kiriş ucu -> kolon merkezi yakalama mesafesi
TOL_AKS = 5.0         # bu farkın altındaki merkezler aynı aks sayılır
BALON_YC = 40         # aks balonu yarıçapı
BALON_OFS = 150       # balonun ilk akstan dışarı kaçıklığı
AKS_UZAMA = 100       # aks çizgisinin son elemandan taşması
YAZI_H = 30           # balon yazı yüksekliği
KIRIS_EN_MIN = 10.0   # kiriş kenar çizgileri arası alt sınır (kiriş genişliği)
KIRIS_EN_MAX = 80.0   # üst sınır
YUZ_MAX = 60.0        # eksen ucu -> kolon merkezi azami mesafe
TOL_EKSEN = 10.0      # kolon merkezinin kiriş ekseninden azami kaçıklığı


def katmandakiler(msp, tur, katmanlar):
    kat = {k.upper() for k in katmanlar}
    return [e for e in msp.query(tur) if e.dxf.layer.upper() in kat]


def kose_listesi(pl):
    return [(p[0], p[1]) for p in pl.get_points("xy")]


def merkez(pts):
    # alan ağırlık merkezi; köşe ortalaması L/T perdede ve ara noktalı kolonda şaşar
    n = len(pts)
    a2 = cx = cy = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        a2 += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a2) < 1e-9:
        return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n)
    return (cx / (3 * a2), cy / (3 * a2))


def blok_merkezleri(doc, ins):
    # INSERT içindeki kapalı polyline merkezleri: ölçek, dönüş, yerleşim noktası uygulanır
    blk = doc.blocks.get(ins.dxf.name)
    if blk is None:
        return []
    ix, iy = ins.dxf.insert.x, ins.dxf.insert.y
    t = math.radians(ins.dxf.get("rotation", 0))
    sx = ins.dxf.get("xscale", 1)
    sy = ins.dxf.get("yscale", 1)
    c, s = math.cos(t), math.sin(t)
    sonuc = []
    for e in blk:
        if e.dxftype() != "LWPOLYLINE":
            continue
        pts = kose_listesi(e)
        if len(pts) < 3:
            continue
        mx, my = merkez(pts)
        mx, my = mx * sx, my * sy
        sonuc.append((ix + mx * c - my * s, iy + mx * s + my * c))
    return sonuc


def kolon_merkezleri(doc, msp):
    m = []
    for pl in katmandakiler(msp, "LWPOLYLINE", KOLON_KATMAN):
        pts = kose_listesi(pl)
        if len(pts) >= 3:
            m.append(merkez(pts))
    for ins in katmandakiler(msp, "INSERT", KOLON_KATMAN):
        m += blok_merkezleri(doc, ins)
    return m


def grupla(degerler, tol):
    d = sorted(degerler)
    gruplar = [[d[0]]]
    for v in d[1:]:
        if v - gruplar[-1][-1] <= tol:
            gruplar[-1].append(v)
        else:
            gruplar.append([v])
    return [round(sum(g) / len(g), 1) for g in gruplar]


def harf(j):
    # 0->A, 25->Z, 26->AA
    s = ""
    j += 1
    while j:
        j, r = divmod(j - 1, 26)
        s = chr(65 + r) + s
    return s


def kiris_ciftle(cizgiler, en_min, en_max, tol=0.05):
    # yatay/düşey kenar çizgilerini çift olarak eşler, eksen çizgisi üretir
    # cizgiler: [(p, q), ...]  döner: (eksenler, eşleşen çizgi indisleri)
    eksenler = []
    kullanilan = set()
    for yatay in (True, False):
        liste = []
        for i, (p, q) in enumerate(cizgiler):
            if yatay and abs(p[1] - q[1]) < tol and abs(p[0] - q[0]) > tol:
                liste.append((i, p[1], min(p[0], q[0]), max(p[0], q[0])))
            elif not yatay and abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) > tol:
                liste.append((i, p[0], min(p[1], q[1]), max(p[1], q[1])))
        for a in liste:
            if a[0] in kullanilan:
                continue
            en_iyi = None
            for b in liste:
                if b[0] == a[0] or b[0] in kullanilan:
                    continue
                fark = abs(b[1] - a[1])
                if fark < en_min or fark > en_max:
                    continue
                bas = max(a[2], b[2])
                son = min(a[3], b[3])
                if son - bas < 0.8 * min(a[3] - a[2], b[3] - b[2]):
                    continue
                if en_iyi is None or fark < en_iyi[0]:
                    en_iyi = (fark, b, bas, son)
            if en_iyi is None:
                continue
            _, b, bas, son = en_iyi
            orta = (a[1] + b[1]) / 2
            kullanilan.update((a[0], b[0]))
            if yatay:
                eksenler.append(((bas, orta), (son, orta)))
            else:
                eksenler.append(((orta, bas), (orta, son)))
    return eksenler, kullanilan


def eksen_uzat(p, q, merkezler, yuz_max, tol_dik, tol_uc=TOL_UC):
    # eksen uçlarını, eksen üzerinde duran en yakın kolon merkezine uzatır
    yatay = abs(p[1] - q[1]) < 1e-6

    def uv(n):
        return (n[0], n[1]) if yatay else (n[1], n[0])

    (u0, v), (u1, _) = uv(p), uv(q)
    lo, hi = min(u0, u1), max(u0, u1)
    sol = sag = None
    for c in merkezler:
        cu, cv = uv(c)
        if abs(cv - v) > tol_dik:
            continue
        if lo - yuz_max <= cu <= lo + tol_uc and (sol is None or cu > sol):
            sol = cu
        if hi - tol_uc <= cu <= hi + yuz_max and (sag is None or cu < sag):
            sag = cu
    if sol is not None:
        lo = sol
    if sag is not None:
        hi = sag
    return ((lo, v), (hi, v)) if yatay else ((v, lo), (v, hi))
