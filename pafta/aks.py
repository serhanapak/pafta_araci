from bisect import bisect_left
from dataclasses import dataclass, field
from ezdxf.enums import TextEntityAlignment

from pafta.hata import Bulgu
from pafta.isaret import appid_tanimla, isaretle, uretilenleri_temizle, ISARET_AKS
from ortak import (
    grupla,
    harf,
    AKS_KATMAN,
    BALON_YC,
    BALON_OFS,
    AKS_UZAMA,
    YAZI_H,
)


@dataclass
class AksAnalizSonucu:
    xs: list[float] = field(default_factory=list)
    ys: list[float] = field(default_factory=list)
    aciklik_x: list[float] = field(default_factory=list)
    aciklik_y: list[float] = field(default_factory=list)
    bos_kesisim: int = 0
    dusey_aks_sayisi: int = 0
    yatay_aks_sayisi: int = 0
    bulgular: list[Bulgu] = field(default_factory=list)


def _en_yakin_indis(sirali_dizi, val, tol):
    if not sirali_dizi:
        return None
    idx = bisect_left(sirali_dizi, val)
    adaylar = []
    if idx < len(sirali_dizi):
        adaylar.append(idx)
    if idx > 0:
        adaylar.append(idx - 1)
    en_iyi = None
    en_fark = tol
    for i in adaylar:
        fark = abs(sirali_dizi[i] - val)
        if fark <= en_fark:
            en_fark = fark
            en_iyi = i
    return en_iyi


def akslari_isle(
    doc,
    msp,
    merkezler,
    ayar,
    duzelt=True,
    aks_katman=AKS_KATMAN,
) -> AksAnalizSonucu:
    sonuc = AksAnalizSonucu()
    if not merkezler:
        sonuc.bulgular.append(
            Bulgu("AKS_KOLON_YOK", "HATA", "Aks üretimi için kolon merkezi bulunamadı")
        )
        return sonuc

    tol_aks = ayar.tol_aks
    carpan = ayar.tol_uc
    balon_yc = BALON_YC * carpan
    balon_ofs = BALON_OFS * carpan
    aks_uzama = AKS_UZAMA * carpan
    yazi_h = YAZI_H * carpan

    if duzelt:
        uretilenleri_temizle(msp, etiket=ISARET_AKS)
        appid_tanimla(doc)

    xs = [float(v) for v in grupla([m[0] for m in merkezler], tol_aks)]
    ys = [float(v) for v in grupla([m[1] for m in merkezler], tol_aks)]

    sonuc.xs = xs
    sonuc.ys = ys
    sonuc.dusey_aks_sayisi = len(xs)
    sonuc.yatay_aks_sayisi = len(ys)
    sonuc.aciklik_x = [round(float(xs[i + 1] - xs[i]), 1) for i in range(len(xs) - 1)]
    sonuc.aciklik_y = [round(float(ys[i + 1] - ys[i]), 1) for i in range(len(ys) - 1)]

    if duzelt:
        if aks_katman not in doc.layers:
            doc.layers.add(aks_katman, color=3)
        oz = {"layer": aks_katman}

        for i, x in enumerate(xs):
            by = ys[0] - balon_ofs
            line = msp.add_line((x, by + balon_yc), (x, ys[-1] + aks_uzama), dxfattribs=oz)
            circle = msp.add_circle((x, by), balon_yc, dxfattribs=oz)
            text = msp.add_text(str(i + 1), height=yazi_h, dxfattribs=oz)
            text.set_placement((x, by), align=TextEntityAlignment.MIDDLE_CENTER)

            isaretle(line, ISARET_AKS)
            isaretle(circle, ISARET_AKS)
            isaretle(text, ISARET_AKS)

        for j, y in enumerate(ys):
            bx = xs[0] - balon_ofs
            line = msp.add_line((bx + balon_yc, y), (xs[-1] + aks_uzama, y), dxfattribs=oz)
            circle = msp.add_circle((bx, y), balon_yc, dxfattribs=oz)
            text = msp.add_text(harf(j), height=yazi_h, dxfattribs=oz)
            text.set_placement((bx, y), align=TextEntityAlignment.MIDDLE_CENTER)

            isaretle(line, ISARET_AKS)
            isaretle(circle, ISARET_AKS)
            isaretle(text, ISARET_AKS)

    # O(N log N): dolu aks kesişimlerini ikili aramayla bul
    dolu_kesisimler = set()
    for mx, my in merkezler:
        ix = _en_yakin_indis(xs, mx, tol_aks)
        if ix is not None:
            iy = _en_yakin_indis(ys, my, tol_aks)
            if iy is not None:
                dolu_kesisimler.add((ix, iy))

    bos = max(0, len(xs) * len(ys) - len(dolu_kesisimler))
    sonuc.bos_kesisim = bos

    if bos > 0:
        sonuc.bulgular.append(
            Bulgu(
                "AKS_BOS_KESISIM",
                "BILGI",
                f"{bos} adet kolonsuz aks kesişimi tespit edildi",
            )
        )

    return sonuc
