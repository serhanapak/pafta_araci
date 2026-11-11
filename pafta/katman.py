from dataclasses import dataclass, field
import unicodedata

from pafta.hata import Bulgu


KATEGORILER = ("KOLON", "KIRIS", "AKS", "PERDE")

ESLESMELER = {
    "KOLON": ("KOLON", "SUTUN", "COLUMN", "COLUMNS"),
    "KIRIS": ("KIRIS", "BEAM", "BEAMS", "KIRISLER"),
    "AKS": ("AKS", "AXIS", "GRID", "GRIDS"),
    "PERDE": ("PERDE", "SHEARWALL", "SHEAR_WALL", "WALL"),
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
    return sorted(layer.dxf.name for layer in doc.layers)


def _siniflandir(ad):
    temiz = normalize(ad)

    # Katman adını ayraçlara göre böl.
    parcalar = temiz.replace("-", "_").replace(" ", "_").split("_")

    bulunan = []

    for kategori, anahtarlar in ESLESMELER.items():
        for anahtar in anahtarlar:
            anahtar = normalize(anahtar)

            if any(p == anahtar or p.startswith(anahtar)
                   for p in parcalar):
                bulunan.append(kategori)
                break

    return bulunan


def katman_tani(doc, secimler=None):
    """
    secimler örneği:
    {"KOLON": ["S-01"], "KIRIS": ["B-01"]}

    Kullanıcı seçimi otomatik tahminden önceliklidir.
    """
    mevcut = katmanlari_listele(doc)
    secimler = secimler or {}

    sonuc = KatmanSonuc(
        katmanlar={k: [] for k in KATEGORILER}
    )

    # Kullanıcı seçimlerini doğrula.
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

    # Otomatik tanıma ve kullanıcı seçimini birleştir.
    for ad in mevcut:
        if ad in secilmis:
            kategoriler = secilmis[ad]
        else:
            kategoriler = _siniflandir(ad)

        if len(kategoriler) == 1:
            sonuc.katmanlar[kategoriler[0]].append(ad)

        elif len(kategoriler) > 1:
            sonuc.bulgular.append(
                Bulgu(
                    "KATMAN_BELIRSIZ",
                    "UYARI",
                    f"{ad} birden fazla kategoriyle eşleşiyor: "
                    f"{', '.join(kategoriler)}"
                )
            )
            sonuc.tanimsiz.append(ad)

        else:
            sonuc.tanimsiz.append(ad)

    if sonuc.tanimsiz:
        sonuc.bulgular.append(
            Bulgu(
                "KATMAN_TANIMSIZ",
                "BILGI",
                f"{len(sonuc.tanimsiz)} katman otomatik tanınamadı."
            )
        )

    for kategori in KATEGORILER:
        if not sonuc.katmanlar[kategori]:
            sonuc.bulgular.append(
                Bulgu(
                    f"{kategori}_KATMANI_BULUNAMADI",
                    "UYARI",
                    f"{kategori} kategorisinde tanınan katman yok."
                )
            )

    return sonuc
