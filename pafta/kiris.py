import math
from dataclasses import dataclass, field
from pafta.hata import Bulgu
from pafta.isaret import appid_tanimla, isaretle, uretilenleri_temizle, ISARET_KIRIS_EKSEN
from ortak import (
    katmandakiler,
    kose_listesi,
    kiris_ciftle,
    eksen_uzat,
    EKSEN_KATMAN,
)


@dataclass
class KirisAnalizSonucu:
    cizgiler: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    eksenler: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    tek_cizgiler: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    nihai_kirisler: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    eslesen_cizgi_sayisi: int = 0
    yakalanan_uc_sayisi: int = 0
    cakisik_silinen_sayisi: int = 0
    sifir_boy_silinen_sayisi: int = 0
    kolon_disi_uc_sayisi: int = 0
    egik_kiris_sayisi: int = 0
    bulgular: list[Bulgu] = field(default_factory=list)


def cizgi_acisi(p1, p2):
    dx = p2[0] - p1[0]
    dy = p2[1] - p1[1]
    return math.degrees(math.atan2(dy, dx)) % 180


def _hucre(pt, boyut):
    return (int(math.floor(pt[0] / boyut)), int(math.floor(pt[1] / boyut)))


def _izgara_kur(noktalar, boyut):
    izgara: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for pt in noktalar:
        izgara.setdefault(_hucre(pt, boyut), []).append(pt)
    return izgara


def _en_yakin_nokta(pt, izgara, boyut, max_mesafe):
    gx, gy = _hucre(pt, boyut)
    en_iyi = None
    en_d = max_mesafe
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for c in izgara.get((gx + dx, gy + dy), ()):
                d = math.dist(c, pt)
                if d <= en_d:
                    en_d = d
                    en_iyi = c
    return en_iyi


def _nokta_dogru_parcasi_mesafe(p, a, b):
    vx, vy = b[0] - a[0], b[1] - a[1]
    l2 = vx * vx + vy * vy
    if l2 == 0:
        return math.dist(p, a)
    t = max(0.0, min(1.0, ((p[0] - a[0]) * vx + (p[1] - a[1]) * vy) / l2))
    return math.dist(p, (a[0] + t * vx, a[1] + t * vy))


def _perde_segmentleri(msp, perde_katmanlari):
    if not perde_katmanlari:
        return []
    segler = []
    for pl in katmandakiler(msp, "LWPOLYLINE", perde_katmanlari):
        pts = kose_listesi(pl)
        n = len(pts)
        for i in range(n if pl.closed else n - 1):
            segler.append((pts[i], pts[(i + 1) % n]))
    for l in katmandakiler(msp, "LINE", perde_katmanlari):
        segler.append(((l.dxf.start.x, l.dxf.start.y), (l.dxf.end.x, l.dxf.end.y)))
    return segler


def kirisleri_isle(
    doc,
    msp,
    katmanlar,
    merkezler,
    ayar,
    duzelt=True,
    eksen_uret=True,
    perde_katmanlari=None,
) -> KirisAnalizSonucu:
    sonuc = KirisAnalizSonucu()
    tol_uc = ayar.tol_uc
    tol_cakisma = max(tol_uc * 0.1, 0.01)

    merkez_boyut = max(tol_uc, 1e-3)
    merkez_izgara = _izgara_kur(merkezler, merkez_boyut) if merkezler else {}

    def yakala(p):
        if not merkez_izgara:
            return p
        m = _en_yakin_nokta(p, merkez_izgara, merkez_boyut, tol_uc)
        return m if m is not None else p

    cizgi_boyut = max(tol_cakisma * 4.0, 1e-3)
    gorulen_izgara: dict[tuple[int, int], list[tuple[tuple[float, float], tuple[float, float]]]] = {}
    cizgiler = []

    for l in katmandakiler(msp, "LINE", katmanlar):
        handle = l.dxf.handle if hasattr(l.dxf, "handle") else ""
        s0 = (l.dxf.start.x, l.dxf.start.y)
        e0 = (l.dxf.end.x, l.dxf.end.y)

        s, e = yakala(s0), yakala(e0)
        s_yakalandi = math.dist(s, s0) > 1e-6
        e_yakalandi = math.dist(e, e0) > 1e-6

        if s_yakalandi or e_yakalandi:
            sonuc.yakalanan_uc_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KIRIS_UC_YAKALANDI",
                    "BILGI",
                    f"Kiriş ucu kolon merkezine yakalandı (s_fark={math.dist(s, s0):.2f}, e_fark={math.dist(e, e0):.2f})",
                    konum=s if s_yakalandi else e,
                    handle=handle,
                )
            )

        if math.dist(s, e) <= tol_uc:
            if duzelt:
                msp.delete_entity(l)
            sonuc.sifir_boy_silinen_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KIRIS_SIFIR_BOY",
                    "UYARI",
                    f"Sıfır boylu ({math.dist(s, e):.2f} <= {tol_uc}) kiriş çizgisi elendi",
                    konum=s,
                    handle=handle,
                )
            )
            continue

        orta = ((s[0] + e[0]) / 2.0, (s[1] + e[1]) / 2.0)
        gx, gy = _hucre(orta, cizgi_boyut)
        cakisik = False
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for ms, me in gorulen_izgara.get((gx + dx, gy + dy), ()):
                    d_duz = math.dist(s, ms) + math.dist(e, me)
                    d_ters = math.dist(s, me) + math.dist(e, ms)
                    if min(d_duz, d_ters) <= tol_cakisma * 2:
                        cakisik = True
                        break
                if cakisik:
                    break
            if cakisik:
                break

        if cakisik:
            if duzelt:
                msp.delete_entity(l)
            sonuc.cakisik_silinen_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KIRIS_CAKISIK",
                    "BILGI",
                    "Çakışık kiriş çizgisi elendi",
                    konum=s,
                    handle=handle,
                )
            )
            continue

        gorulen_izgara.setdefault((gx, gy), []).append((s, e))

        aci = cizgi_acisi(s, e)
        yatay_fark = min(abs(aci - 0), abs(aci - 180))
        dusey_fark = abs(aci - 90)
        if yatay_fark > 1.0 and dusey_fark > 1.0:
            sonuc.egik_kiris_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KIRIS_EGIK",
                    "BILGI",
                    f"Eğik / açılı kiriş çizgisi ({aci:.1f}°)",
                    konum=s,
                    handle=handle,
                )
            )

        if duzelt and (s_yakalandi or e_yakalandi):
            l.dxf.start = (s[0], s[1], 0)
            l.dxf.end = (e[0], e[1], 0)

        cizgiler.append((s, e))

    # --- Kapalı 4 Köşeli LWPOLYLINE Kirişler ---
    poly_eksenler = []
    for pl in katmandakiler(msp, "LWPOLYLINE", katmanlar):
        pts = kose_listesi(pl)
        if len(pts) == 5 and math.dist(pts[0], pts[-1]) <= 1e-6:
            pts = pts[:-1]
        if len(pts) != 4:
            continue
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        w, h = max(xs) - min(xs), max(ys) - min(ys)
        kisa, uzun = min(w, h), max(w, h)
        if ayar.kiris_en_min <= kisa <= ayar.kiris_en_max and uzun > kisa:
            if w >= h:
                ym = (min(ys) + max(ys)) / 2.0
                p, q = yakala((min(xs), ym)), yakala((max(xs), ym))
            else:
                xm = (min(xs) + max(xs)) / 2.0
                p, q = yakala((xm, min(ys))), yakala((xm, max(ys)))
            poly_eksenler.append((p, q))

    sonuc.cizgiler = cizgiler

    eksenler, eslesen = kiris_ciftle(cizgiler, ayar.kiris_en_min, ayar.kiris_en_max)
    tum_eksenler = eksenler + poly_eksenler
    sonuc.eslesen_cizgi_sayisi = len(eslesen)

    if duzelt:
        uretilenleri_temizle(msp, etiket=ISARET_KIRIS_EKSEN)
        appid_tanimla(doc)

    if EKSEN_KATMAN not in doc.layers:
        doc.layers.add(EKSEN_KATMAN, color=2)

    nihai = []
    for p, q in tum_eksenler:
        p, q = eksen_uzat(p, q, merkezler, ayar.yuz_max, ayar.tol_eksen, ayar.tol_uc)
        if eksen_uret and duzelt:
            line = msp.add_line(p, q, dxfattribs={"layer": EKSEN_KATMAN})
            isaretle(line, ISARET_KIRIS_EKSEN)
        nihai.append((p, q))

    sonuc.eksenler = nihai
    tek = [c for i, c in enumerate(cizgiler) if i not in eslesen]
    sonuc.tek_cizgiler = tek
    sonuc.nihai_kirisler = nihai + tek

    # Kolon / perde dışı uç kontrolü (O(1) uzamsal ızgara ile)
    perde_seg = _perde_segmentleri(msp, perde_katmanlari)
    kolon_disi = 0
    if merkez_izgara or perde_seg:
        for p, q in sonuc.nihai_kirisler:
            for n in (p, q):
                kolonda = bool(merkez_izgara) and _en_yakin_nokta(n, merkez_izgara, merkez_boyut, 1e-6) is not None
                perdede = any(_nokta_dogru_parcasi_mesafe(n, a, b) <= tol_uc for a, b in perde_seg)
                if not kolonda and not perdede:
                    kolon_disi += 1
    sonuc.kolon_disi_uc_sayisi = kolon_disi

    if kolon_disi > 0:
        sonuc.bulgular.append(
            Bulgu(
                "KIRIS_KOLON_DISI_UC",
                "BILGI",
                f"{kolon_disi} kiriş ucu kolon merkezine bağlanmadı",
            )
        )

    return sonuc
