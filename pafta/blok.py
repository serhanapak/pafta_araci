from dataclasses import dataclass, field
from collections import Counter

from pafta.hata import Bulgu


@dataclass
class BlokSonuc:
    adet: int = 0
    isimler: dict = field(default_factory=dict)
    bulgular: list = field(default_factory=list)


def blok_tani(doc):
    sonuc = BlokSonuc()
    msp = doc.modelspace()

    bloklar = list(msp.query("INSERT"))
    sonuc.adet = len(bloklar)

    sayac = Counter()

    for ins in bloklar:
        ad = ins.dxf.name
        sayac[ad] += 1

        handle = ins.dxf.handle

        x = ins.dxf.xscale
        y = ins.dxf.yscale
        z = ins.dxf.zscale

        donus = ins.dxf.rotation

        if x == 0 or y == 0 or z == 0:
            sonuc.bulgular.append(
                Bulgu(
                    "BLOK_SIFIR_OLCEK",
                    "HATA",
                    f"{ad} bloğunda sıfır ölçek bulundu.",
                    handle=handle
                )
            )

        if x < 0 or y < 0 or z < 0:
            sonuc.bulgular.append(
                Bulgu(
                    "BLOK_NEGATIF_OLCEK",
                    "UYARI",
                    f"{ad} bloğunda negatif ölçek bulundu.",
                    handle=handle
                )
            )

        if not (0 <= donus < 360):
            sonuc.bulgular.append(
                Bulgu(
                    "BLOK_DONUS_ACISI",
                    "UYARI",
                    f"{ad} bloğunun dönüş açısı alışılmadık: {donus}",
                    handle=handle
                )
            )

    sonuc.isimler = dict(sayac)

    return sonuc
