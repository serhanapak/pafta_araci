import math

KOLON_KATMAN = ["KOLON"]
KIRIS_KATMAN = ["KIRIS"]
AKS_KATMAN = "AKS"
EKSEN_KATMAN = "KIRIS_EKSEN"

TOL_UC = 1.0
TOL_AKS = 5.0
BALON_YC = 40
BALON_OFS = 150
AKS_UZAMA = 100
YAZI_H = 30
KIRIS_EN_MIN = 10.0
KIRIS_EN_MAX = 80.0
YUZ_MAX = 60.0
TOL_EKSEN = 10.0


def katmandakiler(msp, tur, katmanlar):
    kat = {k.upper() for k in katmanlar}
    return [e for e in msp.query(tur) if e.dxf.layer.upper() in kat]


def kose_listesi(pl):
    return [(p[0], p[1]) for p in pl.get_points("xy")]


def merkez(pts):
    n = len(pts)
    if n == 0:
        return (0.0, 0.0)
    a2 = cx = cy = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        c = x0 * y1 - x1 * y0
        a2 += c
        cx += (x0 + x1) * c
        cy += (y0 + y1) * c
    if abs(a2) < 1e-9:
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
    return (cx / (3 * a2), cy / (3 * a2))


def blok_merkezleri(doc, ins):
    blk = doc.blocks.get(ins.dxf.name)
    if blk is None:
        return []

    sx = ins.dxf.get("xscale", 1.0)
    sy = ins.dxf.get("yscale", 1.0)
    if abs(sx) < 1e-6 or abs(sy) < 1e-6:
        return []

    matrix = ins.matrix44()
    sonuc = []

    for e in blk:
        if e.dxftype() == "LWPOLYLINE":
            if not e.closed:
                continue
            pts = kose_listesi(e)
            if len(pts) < 3:
                continue
            mx, my = merkez(pts)
            nokta = matrix.transform((mx, my, 0))
            sonuc.append((nokta.x, nokta.y))
        elif e.dxftype() == "CIRCLE":
            if e.dxf.radius <= 0:
                continue
            nokta = matrix.transform((e.dxf.center.x, e.dxf.center.y, 0))
            sonuc.append((nokta.x, nokta.y))

    return sonuc


def kolon_merkezleri(doc, msp, katmanlar=None):
    if katmanlar is None:
        katmanlar = KOLON_KATMAN
    m = []
    for pl in katmandakiler(msp, "LWPOLYLINE", katmanlar):
        pts = kose_listesi(pl)
        if len(pts) >= 3:
            m.append(merkez(pts))
    for c in katmandakiler(msp, "CIRCLE", katmanlar):
        if c.dxf.radius > 0:
            m.append((c.dxf.center.x, c.dxf.center.y))
    for ins in katmandakiler(msp, "INSERT", katmanlar):
        m += blok_merkezleri(doc, ins)
    return m


def grupla(degerler, tol):
    if not degerler:
        return []
    d = sorted(float(v) for v in degerler)
    gruplar = [[d[0]]]
    for v in d[1:]:
        if v - gruplar[-1][0] <= tol:
            gruplar[-1].append(v)
        else:
            gruplar.append([v])
    return [round(float(sum(g) / len(g)), 1) for g in gruplar]


def harf(j):
    s = ""
    j += 1
    while j:
        j, r = divmod(j - 1, 26)
        s = chr(65 + r) + s
    return s


def kiris_ciftle(cizgiler, en_min, en_max, tol=0.05):
    # O(N log N): dik koordinata göre sıralı pencerede kenar çiftleme
    eksenler = []
    kullanilan = set()
    for yatay in (True, False):
        liste = []
        for i, (p, q) in enumerate(cizgiler):
            if yatay and abs(p[1] - q[1]) < tol and abs(p[0] - q[0]) > tol:
                liste.append((i, p[1], min(p[0], q[0]), max(p[0], q[0])))
            elif not yatay and abs(p[0] - q[0]) < tol and abs(p[1] - q[1]) > tol:
                liste.append((i, p[0], min(p[1], q[1]), max(p[1], q[1])))

        liste.sort(key=lambda item: item[1])
        n = len(liste)
        for idx_a in range(n):
            a = liste[idx_a]
            if a[0] in kullanilan:
                continue
            en_iyi = None
            for idx_b in range(idx_a + 1, n):
                b = liste[idx_b]
                fark = b[1] - a[1]
                if fark > en_max:
                    break
                if fark < en_min or b[0] in kullanilan:
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
