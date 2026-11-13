import math
import statistics
from dataclasses import dataclass
from pafta.hata import Bulgu

CM_KARSILIGI = {"mm": 0.1, "cm": 1.0, "m": 100.0}
CARPAN = {"mm": 10.0, "cm": 1.0, "m": 0.01}
BASLIK = {4: "mm", 5: "cm", 6: "m"}

KISA_KENAR_CM = (15.0, 120.0)
MIN_ORNEK = 5


@dataclass
class BirimSonuc:
    birim: str | None
    baslik: str | None
    medyan: float | None
    adet: int
    bulgular: list


@dataclass(frozen=True)
class Ayar:
    birim: str
    tol_uc: float
    tol_aks: float
    kiris_en_min: float
    kiris_en_max: float
    yuz_max: float
    tol_eksen: float
    kolon_min_dikdortgen: float = 30.0
    kolon_min_dairesel: float = 35.0
    perde_min_kalinlik: float = 25.0
    perde_min_oran: float = 6.0

    @staticmethod
    def olustur(birim):
        if birim not in CARPAN:
            raise ValueError(f"Birim belirsiz: {birim}")
        c = CARPAN[birim]
        return Ayar(
            birim, 1*c, 5*c, 10*c, 80*c, 60*c, 10*c,
            30.0*c, 35.0*c, 25.0*c, 6.0
        )


def kisa_kenarlar(msp, katmanlar=None):
    kat = {k.upper() for k in katmanlar} if katmanlar else None
    sonuc = []

    for e in msp.query("LWPOLYLINE"):
        pts = [(p[0], p[1]) for p in e.get_points("xy")]
        if len(pts) < 3:
            continue
        if kat is not None and e.dxf.layer.upper() not in kat:
            continue

        # Kapalı polyline veya uçları birbirine çok yakın (kapanabilir) kolon adayı
        if not e.closed:
            d_uc = math.dist(pts[0], pts[-1])
            # Uçları açık ama çizgiye göre çok yakınsa kolon kabul et
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            kisa = min(max(xs)-min(xs), max(ys)-min(ys))
            if kisa == 0 or d_uc > kisa * 0.2:
                continue
        else:
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            kisa = min(max(xs)-min(xs), max(ys)-min(ys))

        if kisa > 0:
            sonuc.append(kisa)

    return sonuc


def birim_tahmin(doc, katmanlar=None):
    baslik = BASLIK.get(doc.header.get("$INSUNITS", 0))
    kisa = kisa_kenarlar(doc.modelspace(), katmanlar)
    bulgular = []

    if not kisa:
        if baslik:
            bulgular.append(Bulgu(
                "BIRIM_AZ_VERI", "UYARI",
                f"Geometri ornegi yok; DXF baslik birimi ({baslik}) kullanildi"
            ))
            return BirimSonuc(baslik, baslik, None, 0, bulgular)

        bulgular.append(Bulgu(
            "BIRIM_BELIRSIZ", "HATA",
            "Kapali polyline yok; birim anlasilamadi"
        ))
        return BirimSonuc(None, baslik, None, 0, bulgular)

    med = statistics.median(kisa)
    uygun = [
        b for b, k in CM_KARSILIGI.items()
        if KISA_KENAR_CM[0] <= med*k <= KISA_KENAR_CM[1]
    ]

    if len(uygun) != 1:
        bulgular.append(Bulgu(
            "BIRIM_BELIRSIZ", "HATA",
            f"Kisa kenar medyani {med:.2f}; birim belirlenemedi"
        ))
        return BirimSonuc(None, baslik, med, len(kisa), bulgular)

    birim = uygun[0]

    if baslik and baslik != birim:
        bulgular.append(Bulgu(
            "BIRIM_BASLIK_UYUSMUYOR", "UYARI",
            f"Baslik {baslik}, geometri {birim}; geometri esas alindi"
        ))

    if len(kisa) < MIN_ORNEK:
        bulgular.append(Bulgu(
            "BIRIM_AZ_VERI", "UYARI",
            f"Yalnizca {len(kisa)} ornekle tahmin edildi"
        ))

    return BirimSonuc(birim, baslik, med, len(kisa), bulgular)
