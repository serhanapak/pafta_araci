from ezdxf.enums import TextEntityAlignment

from pafta.birim import CARPAN
from pafta.hata import Bulgu
from pafta.isaret import appid_tanimla, isaretle, uretilenleri_temizle, ISARET_HATA

HATA_KATMAN = "PAFTA_HATA"


def tbdy_on_kontrol(kolon_sonuc, ayar) -> list[Bulgu]:
    bulgular: list[Bulgu] = []

    for kb in kolon_sonuc.kolonlar:
        if kb.kisa_kenar <= 0:
            continue
        if kb.tur == "POLYLINE" and kb.kisa_kenar < ayar.kolon_min_dikdortgen - 1e-6:
            bulgular.append(
                Bulgu(
                    "KOLON_MIN_KESIT",
                    "UYARI",
                    f"Dikdörtgen kolon kısa kenarı ({kb.kisa_kenar:.1f} {ayar.birim}) minimum {ayar.kolon_min_dikdortgen:.1f} {ayar.birim} sınırının altında",
                    konum=(float(kb.merkez[0]), float(kb.merkez[1])),
                    handle=kb.handle,
                )
            )
        elif kb.tur == "CIRCLE" and kb.kisa_kenar < ayar.kolon_min_dairesel - 1e-6:
            bulgular.append(
                Bulgu(
                    "KOLON_MIN_KESIT",
                    "UYARI",
                    f"Dairesel kolon çapı ({kb.kisa_kenar:.1f} {ayar.birim}) minimum {ayar.kolon_min_dairesel:.1f} {ayar.birim} sınırının altında",
                    konum=(float(kb.merkez[0]), float(kb.merkez[1])),
                    handle=kb.handle,
                )
            )

    return bulgular


def hatalari_ciz(doc, msp, bulgular: list[Bulgu], ayar) -> int:
    uretilenleri_temizle(msp, etiket=ISARET_HATA)
    appid_tanimla(doc)

    hedefler = [
        b for b in bulgular
        if b.siddet in ("HATA", "UYARI") and b.konum is not None
    ]
    if not hedefler:
        return 0

    if HATA_KATMAN not in doc.layers:
        doc.layers.add(HATA_KATMAN, color=1)

    c = CARPAN[ayar.birim]
    yaricap = 25.0 * c
    yazi_h = 10.0 * c
    gorulen = set()
    cizilen = 0

    for b in hedefler:
        x, y = float(b.konum[0]), float(b.konum[1])
        anahtar = (b.kod, round(x, 2), round(y, 2))
        if anahtar in gorulen:
            continue
        gorulen.add(anahtar)

        renk = 1 if b.siddet == "HATA" else 2
        daire = msp.add_circle((x, y), yaricap, dxfattribs={"layer": HATA_KATMAN, "color": renk})
        etiket = msp.add_text(b.kod, height=yazi_h, dxfattribs={"layer": HATA_KATMAN, "color": renk})
        etiket.set_placement((x, y + yaricap * 1.2), align=TextEntityAlignment.BOTTOM_CENTER)

        isaretle(daire, ISARET_HATA)
        isaretle(etiket, ISARET_HATA)
        cizilen += 1

    return cizilen
