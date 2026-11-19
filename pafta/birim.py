import math
import statistics
from dataclasses import dataclass
from pafta.hata import Bulgu
from pafta.geometri import dikdortgen_kenar_olculeri

CM_KARSILIGI = {"mm": 0.1, "cm": 1.0, "m": 100.0}
CARPAN = {"mm": 10.0, "cm": 1.0, "m": 0.01}
BASLIK = {4: "mm", 5: "cm", 6: "m"}

KISA_KENAR_CM = (15.0, 120.0)
MIN_ORNEK = 5


class BirimBelirsizHatasi(ValueError):
    """Çizim birimi belirlenemediği için ölçüye duyarlı analizi durdurur."""


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


def _dogrulanmis_kisa_kenarlar(msp, katmanlar=None):
    """Birim tahmini için yalnızca ölçüsü doğrudan doğrulanabilen kesitleri kullan."""
    kat = {k.upper() for k in katmanlar} if katmanlar else None
    sonuc = []
    dikdortgen_adedi = 0
    for e in msp.query("LWPOLYLINE"):
        if kat is not None and e.dxf.layer.upper() not in kat:
            continue
        olculer = dikdortgen_kenar_olculeri(e)
        if olculer is not None:
            sonuc.append(olculer[0])
            dikdortgen_adedi += 1
    for circle in msp.query("CIRCLE"):
        if kat is not None and circle.dxf.layer.upper() not in kat:
            continue
        radius = float(circle.dxf.radius)
        if math.isfinite(radius) and radius > 0:
            sonuc.append(2.0 * radius)
    return sonuc, dikdortgen_adedi


def _geometrik_aday(deger):
    uygun = [
        birim for birim, carpan in CM_KARSILIGI.items()
        if KISA_KENAR_CM[0] <= deger * carpan <= KISA_KENAR_CM[1]
    ]
    return uygun[0] if len(uygun) == 1 else None


def _belirsiz_sonuc(baslik, medyan, adet, bulgular, mesaj, kod="BIRIM_BELIRSIZ"):
    if baslik:
        mesaj = f"DXF başlığında {baslik} birimi var; {mesaj}"
    else:
        mesaj = f"DXF birim başlığı bilinmiyor; {mesaj}"
    mesaj += ". Güvenli analiz için kullanıcı birimi açıkça seçmeli."
    bulgular.append(Bulgu(kod, "HATA", mesaj))
    return BirimSonuc(None, baslik, medyan, adet, bulgular)


def birim_tahmin(doc, katmanlar=None):
    baslik = BASLIK.get(doc.header.get("$INSUNITS", 0))
    kisa, dikdortgen_adedi = _dogrulanmis_kisa_kenarlar(doc.modelspace(), katmanlar)
    bulgular = []

    if not kisa:
        return _belirsiz_sonuc(
            baslik, None, 0, bulgular,
            "doğrulanmış dikdörtgen veya daire çapı örneği yok",
        )

    med = statistics.median(kisa)
    if len(kisa) < MIN_ORNEK or dikdortgen_adedi == 0:
        return _belirsiz_sonuc(
            baslik, med, len(kisa), bulgular,
            f"Yalnızca {len(kisa)} geometrik örnek var (en az {MIN_ORNEK} ve bir doğrulanmış dikdörtgen gerekli)",
        )

    adaylar = [_geometrik_aday(deger) for deger in kisa]
    bulunanlar = {aday for aday in adaylar if aday is not None}
    if len(bulunanlar) > 1:
        return _belirsiz_sonuc(
            baslik, med, len(kisa), bulgular,
            "doğrulanmış geometrik ölçüler farklı birim aralıklarına düşüyor; otomatik seçim yapılmadı",
            kod="BIRIM_GEO_TUTARSIZ",
        )

    if not bulunanlar:
        return _belirsiz_sonuc(
            baslik, med, len(kisa), bulgular,
            f"doğrulanmış geometrik ölçüler güvenilir aralığa uymuyor (medyan {med:.2f})",
        )

    birim = next(iter(bulunanlar))
    if any(aday is None for aday in adaylar):
        return _belirsiz_sonuc(
            baslik, med, len(kisa), bulgular,
            "geometrik ölçüler tutarlı bir birim aralığını desteklemiyor; otomatik seçim yapılmadı",
            kod="BIRIM_GEO_TUTARSIZ",
        )

    if baslik and baslik != birim:
        return _belirsiz_sonuc(
            baslik, med, len(kisa), bulgular,
            f"yeterli geometri {birim} birimini destekliyor; başlıkla çelişki otomatik çözülemedi",
            kod="BIRIM_BASLIK_UYUSMUYOR",
        )

    return BirimSonuc(birim, baslik, med, len(kisa), bulgular)
