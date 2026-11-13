import math
from dataclasses import dataclass, field
from pafta.hata import Bulgu
from ortak import (
    katmandakiler,
    kose_listesi,
    merkez,
    blok_merkezleri,
)


@dataclass
class KolonBilgi:
    merkez: tuple[float, float]
    alan: float
    kutu: tuple[float, float, float, float]
    tur: str  # "POLYLINE", "CIRCLE" veya "INSERT"
    entity: object = None
    handle: str = ""
    katman: str = ""
    kose_sayisi: int = 0
    kisa_kenar: float = 0.0
    uzun_kenar: float = 0.0


@dataclass
class KolonAnalizSonucu:
    kolonlar: list[KolonBilgi] = field(default_factory=list)
    merkezler: list[tuple[float, float]] = field(default_factory=list)
    kisa_kenarlar: list[float] = field(default_factory=list)
    acik_kapatilan: int = 0
    cakisik_kolon_sayisi: int = 0
    gecersiz_sayisi: int = 0
    cakisik_blok_sayisi: int = 0
    sifir_olcek_sayisi: int = 0
    bulgular: list[Bulgu] = field(default_factory=list)


def poligon_alani(pts):
    n = len(pts)
    if n < 3:
        return 0.0
    a2 = 0.0
    for i in range(n):
        x0, y0 = pts[i]
        x1, y1 = pts[(i + 1) % n]
        a2 += x0 * y1 - x1 * y0
    return abs(a2) / 2.0


def kolon_cakisik_mi(k1: KolonBilgi, k2: KolonBilgi, tol_mesafe: float) -> bool:
    dist_m = math.dist(k1.merkez, k2.merkez)
    if dist_m > tol_mesafe:
        return False

    if k1.alan > 0 and k2.alan > 0:
        fark_alan = abs(k1.alan - k2.alan)
        maks_alan = max(k1.alan, k2.alan)
        if fark_alan / maks_alan > 0.05:
            return False

    w1, h1 = k1.kutu[2] - k1.kutu[0], k1.kutu[3] - k1.kutu[1]
    w2, h2 = k2.kutu[2] - k2.kutu[0], k2.kutu[3] - k2.kutu[1]
    if abs(w1 - w2) > tol_mesafe * 2 or abs(h1 - h2) > tol_mesafe * 2:
        return False

    return True


def _hucre_anahtari(pt, boyut):
    return (int(math.floor(pt[0] / boyut)), int(math.floor(pt[1] / boyut)))


def _komsular(izgara, pt, boyut):
    gx, gy = _hucre_anahtari(pt, boyut)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for item in izgara.get((gx + dx, gy + dy), ()):
                yield item


def kolonlari_isle(doc, msp, katmanlar, ayar, duzelt=True) -> KolonAnalizSonucu:
    sonuc = KolonAnalizSonucu()
    tol_uc = ayar.tol_uc
    tol_cakisma = tol_uc * 0.2
    hucre_boyutu = max(tol_cakisma * 2.0, 1e-3)

    poly_izgara: dict[tuple[int, int], list[KolonBilgi]] = {}

    # --- 1. LWPOLYLINE Kolonlar ---
    for pl in katmandakiler(msp, "LWPOLYLINE", katmanlar):
        handle = pl.dxf.handle if hasattr(pl.dxf, "handle") else ""
        pts = kose_listesi(pl)

        if len(pts) < 3:
            if duzelt:
                msp.delete_entity(pl)
            sonuc.gecersiz_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KOLON_GECERSIZ",
                    "UYARI",
                    f"3 köşeden az polyline elendi ({len(pts)} köşe)",
                    konum=pts[0] if pts else None,
                    handle=handle,
                )
            )
            continue

        if not pl.closed:
            d_uc = math.dist(pts[0], pts[-1])
            if d_uc <= tol_uc:
                if duzelt:
                    if len(pts) > 4:
                        pts = pts[:-1]
                        pl.set_points(pts, format="xy")
                    pl.closed = True
                sonuc.acik_kapatilan += 1
                sonuc.bulgular.append(
                    Bulgu(
                        "KOLON_ACIK_KAPATILDI",
                        "BILGI",
                        f"Uçları yakın ({d_uc:.2f} <= {tol_uc}) açık kolon polyline'ı kapatıldı",
                        konum=pts[0],
                        handle=handle,
                    )
                )
            else:
                sonuc.bulgular.append(
                    Bulgu(
                        "KOLON_ACIK_KAPATILAMADI",
                        "UYARI",
                        f"Uçları uzak ({d_uc:.2f} > {tol_uc}) açık kolon polyline'ı kapatılmadı",
                        konum=pts[0],
                        handle=handle,
                    )
                )

        px = [p[0] for p in pts]
        py = [p[1] for p in pts]
        min_x, max_x = min(px), max(px)
        min_y, max_y = min(py), max(py)
        w, h = max_x - min_x, max_y - min_y
        m = merkez(pts)
        alan = poligon_alani(pts)

        kb = KolonBilgi(
            merkez=m,
            alan=alan,
            kutu=(min_x, min_y, max_x, max_y),
            tur="POLYLINE",
            entity=pl,
            handle=handle,
            katman=pl.dxf.layer,
            kose_sayisi=len(pts),
            kisa_kenar=min(w, h),
            uzun_kenar=max(w, h),
        )

        if any(kolon_cakisik_mi(kb, mevcut, tol_cakisma) for mevcut in _komsular(poly_izgara, m, hucre_boyutu)):
            if duzelt:
                msp.delete_entity(pl)
            sonuc.cakisik_kolon_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KOLON_CAKISIK",
                    "BILGI",
                    "Çakışık kolon polyline'ı elendi",
                    konum=m,
                    handle=handle,
                )
            )
            continue

        poly_izgara.setdefault(_hucre_anahtari(m, hucre_boyutu), []).append(kb)
        sonuc.kolonlar.append(kb)
        sonuc.merkezler.append(m)
        sonuc.kisa_kenarlar.append(kb.kisa_kenar)

    # --- 2. CIRCLE (Dairesel) Kolonlar ---
    for c in katmandakiler(msp, "CIRCLE", katmanlar):
        handle = c.dxf.handle if hasattr(c.dxf, "handle") else ""
        r = float(c.dxf.radius)
        m = (float(c.dxf.center.x), float(c.dxf.center.y))
        if r <= 0:
            if duzelt:
                msp.delete_entity(c)
            sonuc.gecersiz_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KOLON_GECERSIZ",
                    "UYARI",
                    f"Sıfır/negatif yarıçaplı dairesel kolon elendi (r={r})",
                    konum=m,
                    handle=handle,
                )
            )
            continue

        cap = 2.0 * r
        kb = KolonBilgi(
            merkez=m,
            alan=math.pi * r * r,
            kutu=(m[0] - r, m[1] - r, m[0] + r, m[1] + r),
            tur="CIRCLE",
            entity=c,
            handle=handle,
            katman=c.dxf.layer,
            kisa_kenar=cap,
            uzun_kenar=cap,
        )

        if any(kolon_cakisik_mi(kb, mevcut, tol_cakisma) for mevcut in _komsular(poly_izgara, m, hucre_boyutu)):
            if duzelt:
                msp.delete_entity(c)
            sonuc.cakisik_kolon_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "KOLON_CAKISIK",
                    "BILGI",
                    "Çakışık dairesel kolon elendi",
                    konum=m,
                    handle=handle,
                )
            )
            continue

        poly_izgara.setdefault(_hucre_anahtari(m, hucre_boyutu), []).append(kb)
        sonuc.kolonlar.append(kb)
        sonuc.merkezler.append(m)
        sonuc.kisa_kenarlar.append(cap)

    # --- 3. INSERT (Blok) Kolonlar ---
    blok_izgara: dict[tuple[int, int], list[tuple[float, float]]] = {}

    for ins in katmandakiler(msp, "INSERT", katmanlar):
        handle = ins.dxf.handle if hasattr(ins.dxf, "handle") else ""
        ad = ins.dxf.name

        xs = ins.dxf.get("xscale", 1.0)
        ys = ins.dxf.get("yscale", 1.0)
        if abs(xs) < 1e-6 or abs(ys) < 1e-6:
            sonuc.sifir_olcek_sayisi += 1
            sonuc.bulgular.append(
                Bulgu(
                    "BLOK_SIFIR_OLCEK",
                    "HATA",
                    f"{ad} bloğunda sıfır ölçek bulundu, hayalet kolon oluşturulmadı",
                    handle=handle,
                )
            )
            continue

        for bm in blok_merkezleri(doc, ins):
            if any(math.dist(bm, mevcut_m) <= tol_cakisma for mevcut_m in _komsular(blok_izgara, bm, hucre_boyutu)):
                sonuc.cakisik_blok_sayisi += 1
                sonuc.bulgular.append(
                    Bulgu(
                        "BLOK_CAKISIK",
                        "BILGI",
                        f"{ad} bloğu çakışık konumda tespit edildi",
                        konum=bm,
                        handle=handle,
                    )
                )
                continue

            blok_izgara.setdefault(_hucre_anahtari(bm, hucre_boyutu), []).append(bm)
            kb = KolonBilgi(
                merkez=bm,
                alan=0.0,
                kutu=(bm[0], bm[1], bm[0], bm[1]),
                tur="INSERT",
                entity=ins,
                handle=handle,
                katman=ins.dxf.layer,
            )
            sonuc.kolonlar.append(kb)
            sonuc.merkezler.append(bm)

    return sonuc
