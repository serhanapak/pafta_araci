from dataclasses import dataclass, field
import unicodedata

from pafta.hata import Bulgu
from pafta.isaret import (
    isaretli_mi,
    ISARET_AKS,
    ISARET_KIRIS_EKSEN,
    ISARET_PERDE_EKSEN,
    ISARET_HATA,
)


KATEGORILER = ("KOLON", "KIRIS", "AKS", "PERDE")

ESLESMELER = {
    "KOLON": ("KOLON", "SUTUN", "COLUMN", "COLUMNS", "STUP", "POTEAU"),
    "KIRIS": ("KIRIS", "BEAM", "BEAMS", "KIRISLER", "GREDA", "GREDE", "POUTRE"),
    "AKS": ("AKS", "AXIS", "GRID", "GRIDS", "AXE", "AXES"),
    "PERDE": ("PERDE", "SHEARWALL", "SHEAR_WALL", "WALL", "ZID", "VOILE"),
}

TAM_ESLESME = {
    "KOLON": ("COL", "COLS"),
    "AKS": ("OSI",),
}


@dataclass
class KatmanSonuc:
    katmanlar: dict = field(default_factory=dict)
    tanimsiz: list = field(default_factory=list)
    bulgular: list = field(default_factory=list)


def normalize(ad):
    ad = str(ad).upper().replace("İ", "I").replace("Ş", "S")
    ad = ad.replace("Ğ", "G").replace("Ü", "U")
    ad = ad.replace("Ö", "O").replace("Ç", "C")
    return unicodedata.normalize("NFKD", ad)


def katmanlari_listele(doc):
    katmanlar = {layer.dxf.name for layer in doc.layers}
    try:
        for e in doc.modelspace():
            if hasattr(e.dxf, "layer"):
                katmanlar.add(e.dxf.layer)
    except Exception:
        pass
    return sorted(katmanlar)


def _siniflandir(ad):
    temiz = normalize(ad)
    parcalar = temiz.replace("-", "_").replace(" ", "_").split("_")
    bulunan = []

    for kategori, anahtarlar in ESLESMELER.items():
        if kategori in ("KIRIS", "PERDE") and "EKSEN" in parcalar:
            continue

        tam_set = {normalize(t) for t in TAM_ESLESME.get(kategori, ())}
        if any(p in tam_set for p in parcalar):
            bulunan.append(kategori)
            continue

        for anahtar in anahtarlar:
            anahtar = normalize(anahtar)
            if any(p == anahtar or p.startswith(anahtar) for p in parcalar):
                bulunan.append(kategori)
                break

    return bulunan




PROGRAM_ETIKETLERI = (
    ISARET_AKS,
    ISARET_KIRIS_EKSEN,
    ISARET_PERDE_EKSEN,
    ISARET_HATA,
)


def _program_uretimi_katmanlari(doc):
    """
    Yalnızca bütün nesneleri program etiketi taşıyan katmanları döndürür.
    Model alanı, kağıt alanları ve bloklar kontrol edilir.
    Herhangi bir tarama hatasında hiçbir katman gizlenmez.
    """
    durumlar = {}

    try:
        koleksiyonlar = (doc.layouts, doc.blocks)

        for koleksiyon in koleksiyonlar:
            for layout in koleksiyon:
                for entity in layout:
                    if not hasattr(entity, "dxf"):
                        continue

                    katman = entity.dxf.layer
                    isaretli = any(
                        isaretli_mi(entity, etiket=etiket)
                        for etiket in PROGRAM_ETIKETLERI
                    )

                    durumlar.setdefault(katman, []).append(isaretli)

    except Exception:
        return set()

    return {
        katman
        for katman, durumlar_listesi in durumlar.items()
        if durumlar_listesi and all(durumlar_listesi)
    }


def katman_tani(doc, secimler=None):
    mevcut = katmanlari_listele(doc)
    program_katmanlari = _program_uretimi_katmanlari(doc)
    secimler = secimler or {}

    sonuc = KatmanSonuc(katmanlar={k: [] for k in KATEGORILER})
    secilmis = {}

    for kategori, adlar in secimler.items():
        kategori = kategori.upper()
        if kategori not in KATEGORILER:
            raise ValueError(f"Bilinmeyen kategori: {kategori}")
        if isinstance(adlar, str):
            adlar = [adlar]
        for ad in adlar:
            if ad not in mevcut:
                raise ValueError(f"DXF içinde katman bulunamadı: {ad}")
            secilmis.setdefault(ad, []).append(kategori)

    for ad in mevcut:
        kategoriler = secilmis[ad] if ad in secilmis else _siniflandir(ad)

        if len(kategoriler) == 1:
            sonuc.katmanlar[kategoriler[0]].append(ad)
        elif len(kategoriler) > 1:
            sonuc.bulgular.append(
                Bulgu(
                    "KATMAN_BELIRSIZ",
                    "UYARI",
                    f"{ad} birden fazla kategoriyle eşleşiyor: {', '.join(kategoriler)}",
                )
            )
            sonuc.tanimsiz.append(ad)
        else:
            if ad not in program_katmanlari:
                sonuc.tanimsiz.append(ad)

    if sonuc.tanimsiz:
        sonuc.bulgular.append(
            Bulgu(
                "KATMAN_TANIMSIZ",
                "BILGI",
                f"{len(sonuc.tanimsiz)} katman otomatik tanınamadı.",
            )
        )

    for kategori in KATEGORILER:
        if not sonuc.katmanlar[kategori]:
            sonuc.bulgular.append(
                Bulgu(
                    f"{kategori}_KATMANI_BULUNAMADI",
                    "UYARI",
                    f"{kategori} kategorisinde tanınan katman yok.",
                )
            )

    return sonuc
