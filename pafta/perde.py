import math
from dataclasses import dataclass, field

from pafta.hata import Bulgu
from pafta.isaret import appid_tanimla, isaretle, uretilenleri_temizle, ISARET_PERDE_EKSEN
from ortak import katmandakiler, kose_listesi, merkez

PERDE_EKSEN_KATMAN = "PERDE_EKSEN"


@dataclass
class PerdeBilgi:
    merkez: tuple[float, float]
    uzunluk: float
    kalinlik: float
    oran: float
    eksen: tuple[tuple[float, float], tuple[float, float]]
    tur: str = "POLYLINE"
    handle: str = ""
    katman: str = ""


@dataclass
class PerdeAnalizSonucu:
    perdeler: list[PerdeBilgi] = field(default_factory=list)
    eksenler: list[tuple[tuple[float, float], tuple[float, float]]] = field(default_factory=list)
    bulgular: list[Bulgu] = field(default_factory=list)


def perdeleri_isle(doc, msp, katmanlar, ayar, duzelt=True) -> PerdeAnalizSonucu:
    sonuc = PerdeAnalizSonucu()
    if not katmanlar:
        return sonuc

    poly_eksenler: list[tuple[tuple[float, float], tuple[float, float]]] = []

    for pl in katmandakiler(msp, "LWPOLYLINE", katmanlar):
        handle = pl.dxf.handle if hasattr(pl.dxf, "handle") else ""
        pts = kose_listesi(pl)
        if len(pts) < 3:
            continue

        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        w, h = max_x - min_x, max_y - min_y
        if w <= 0 or h <= 0:
            continue

        lw = float(max(w, h))
        bw = float(min(w, h))
        oran = lw / bw
        m = merkez(pts)

        if w >= h:
            ym = (min_y + max_y) / 2.0
            eksen = ((float(min_x), float(ym)), (float(max_x), float(ym)))
        else:
            xm = (min_x + max_x) / 2.0
            eksen = ((float(xm), float(min_y)), (float(xm), float(max_y)))

        pb = PerdeBilgi(
            merkez=(float(m[0]), float(m[1])),
            uzunluk=lw,
            kalinlik=bw,
            oran=oran,
            eksen=eksen,
            tur="POLYLINE",
            handle=handle,
            katman=pl.dxf.layer,
        )
        sonuc.perdeler.append(pb)
        sonuc.eksenler.append(eksen)
        poly_eksenler.append(eksen)

        if bw < ayar.perde_min_kalinlik - 1e-6:
            sonuc.bulgular.append(
                Bulgu(
                    "PERDE_KALINLIK_YETERSIZ",
                    "UYARI",
                    f"Perde kalınlığı ({bw:.1f} {ayar.birim}) minimum {ayar.perde_min_kalinlik:.1f} {ayar.birim} sınırının altında",
                    konum=pb.merkez,
                    handle=handle,
                )
            )

        if oran < ayar.perde_min_oran - 1e-6:
            sonuc.bulgular.append(
                Bulgu(
                    "PERDE_ORAN_YETERSIZ",
                    "UYARI",
                    f"Perde en/boy oranı (lw/bw={oran:.2f} < {ayar.perde_min_oran:.1f}) sınırının altında; kolon olarak modellenmeli",
                    konum=pb.merkez,
                    handle=handle,
                )
            )

    for l in katmandakiler(msp, "LINE", katmanlar):
        handle = l.dxf.handle if hasattr(l.dxf, "handle") else ""
        p = (float(l.dxf.start.x), float(l.dxf.start.y))
        q = (float(l.dxf.end.x), float(l.dxf.end.y))
        uzunluk = math.dist(p, q)
        if uzunluk <= ayar.tol_uc:
            continue
        m = ((p[0] + q[0]) / 2.0, (p[1] + q[1]) / 2.0)
        pb = PerdeBilgi(
            merkez=m,
            uzunluk=float(uzunluk),
            kalinlik=0.0,
            oran=0.0,
            eksen=(p, q),
            tur="LINE",
            handle=handle,
            katman=l.dxf.layer,
        )
        sonuc.perdeler.append(pb)
        sonuc.eksenler.append((p, q))

    if duzelt and poly_eksenler:
        uretilenleri_temizle(msp, etiket=ISARET_PERDE_EKSEN)
        appid_tanimla(doc)
        if PERDE_EKSEN_KATMAN not in doc.layers:
            doc.layers.add(PERDE_EKSEN_KATMAN, color=4)
        for p, q in poly_eksenler:
            line = msp.add_line(p, q, dxfattribs={"layer": PERDE_EKSEN_KATMAN})
            isaretle(line, ISARET_PERDE_EKSEN)

    return sonuc
