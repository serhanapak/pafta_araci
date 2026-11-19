from collections import Counter
from dataclasses import dataclass, field
from enum import Enum


class Kategori(str, Enum):
    ISLEMSEL = "İŞLEMSEL"
    GEOMETRIK = "GEOMETRİK"
    YONETMELIK = "YÖNETMELİK"
    YAPILANDIRMA = "YAPILANDIRMA"
    BELIRSIZ = "BELİRSİZ"


SIDDET = ("BILGI", "UYARI", "HATA")
# Yeni isim, eski SIDDET sabitinin alias'ıdır.
SIDDETLER = SIDDET


class HataKodu:
    DOSYA_OKUNDU = ("DOSYA_OKUNDU", Kategori.ISLEMSEL, "Dosya başarıyla okundu ve ayrıştırıldı.")
    DWG_DONUSTURULDU = (
        "DWG_DONUSTURULDU", Kategori.ISLEMSEL,
        "DWG dosyası LibreDWG köprüsü ile DXF formatına dönüştürüldü.",
    )
    DOSYA_BASARISIZ = ("DOSYA_BASARISIZ", Kategori.ISLEMSEL, "Dosya işlenirken kritik hata oluştu.")
    KIRIS_CAKISIK_SILINEN = (
        "KIRIS_CAKISIK_SILINEN", Kategori.GEOMETRIK,
        "Mükerrer/silinen çizgi geometrik çakışması tespit edildi.",
    )
    KIRIS_CAKISIK_GERCEK = (
        "KIRIS_CAKISIK_GERCEK", Kategori.GEOMETRIK,
        "Gerçek geometrik çakışma tespit edildi.",
    )
    MUKERRER_BULGU = (
        "MUKERRER_BULGU", Kategori.GEOMETRIK,
        "Aynı konumda mükerrer bulgu raporlandı.",
    )
    TBDY_UYUMSUZ_KATMAN = (
        "TBDY_UYUMSUZ_KATMAN", Kategori.BELIRSIZ,
        "TBDY 2018 standartlarına uymayan katman veya eleman.",
    )
    KOLON_KESIT_OLCUSU_DOGRULANAMADI = (
        "KOLON_KESIT_OLCUSU_DOGRULANAMADI", Kategori.BELIRSIZ,
        "Kolon ölçüsü güvenilir biçimde doğrulanamadı; minimum kesit kontrolü yapılamadı.",
    )


def _json_deger(deger, gorulen=None):
    """NumPy scalar/array, enum ve nested rapor değerlerini JSON uyumlu yapar."""
    if isinstance(deger, Enum):
        return deger.value
    if deger is None or isinstance(deger, (str, int, float, bool)):
        return deger
    if hasattr(deger, "item"):
        try:
            return _json_deger(deger.item(), gorulen)
        except (ValueError, TypeError):
            pass
    if hasattr(deger, "tolist"):
        try:
            return _json_deger(deger.tolist(), gorulen)
        except (ValueError, TypeError):
            pass
    if hasattr(deger, "to_dict"):
        return _json_deger(deger.to_dict(), gorulen)

    if gorulen is None:
        gorulen = set()
    kimlik = id(deger)
    if kimlik in gorulen:
        return "<döngüsel başvuru>"

    if isinstance(deger, dict):
        gorulen.add(kimlik)
        sonuc = {str(k): _json_deger(v, gorulen) for k, v in deger.items()}
        gorulen.remove(kimlik)
        return sonuc
    if isinstance(deger, (list, tuple, set)):
        gorulen.add(kimlik)
        sonuc = [_json_deger(v, gorulen) for v in deger]
        gorulen.remove(kimlik)
        return sonuc
    if hasattr(deger, "__dict__"):
        gorulen.add(kimlik)
        sonuc = {k: _json_deger(v, gorulen) for k, v in vars(deger).items()}
        gorulen.remove(kimlik)
        return sonuc
    return str(deger)


_ISLEMSEL_KODLAR = {
    "BIRIM_AZ_VERI",
    "BIRIM_BELIRSIZ",
    "BIRIM_BASLIK_UYUSMUYOR",
    "BIRIM_OLCEK_UYARISI",
    "KATMAN_BELIRSIZ",
    "KATMAN_TANIMSIZ",
    "KOLON_BULUNAMADI",
    "AKS_KOLON_YOK",
}

_YAPILANDIRMA_KODLAR = {
    # Katman tanıma gereksinimleri yapılandırmada eşleştirilmedi.
    *(f"{ad}_KATMANI_BULUNAMADI" for ad in ("KOLON", "KIRIS", "AKS", "PERDE")),
}

_GEOMETRIK_KODLAR = {
    "KOLON_GECERSIZ",
    "KOLON_ACIK_KAPATILDI",
    "KOLON_ACIK_KAPATILAMADI",
    "KOLON_CAKISIK",
    "BLOK_SIFIR_OLCEK",
    "BLOK_NEGATIF_OLCEK",
    "BLOK_DONUS_ACISI",
    "BLOK_CAKISIK",
    "KIRIS_UC_YAKALANDI",
    "KIRIS_SIFIR_BOY",
    "KIRIS_CAKISIK",
    "KIRIS_EGIK",
    "KIRIS_KOLON_DISI_UC",
    "AKS_BOS_KESISIM",
    "PERDE_KALINLIK_YETERSIZ",
    "PERDE_ORAN_YETERSIZ",
}


def _kod_kategorisi(kod):
    for deger in vars(HataKodu).values():
        if isinstance(deger, tuple) and len(deger) >= 2 and deger[0] == kod:
            return deger[1]
    if kod in _ISLEMSEL_KODLAR:
        return Kategori.ISLEMSEL
    if kod in _YAPILANDIRMA_KODLAR:
        return Kategori.YAPILANDIRMA
    if kod in _GEOMETRIK_KODLAR:
        return Kategori.GEOMETRIK
    # Eşik kontrolü mevcut; ancak model kolonların TBDY'deki süneklik
    # sınıfı ve bu kontrolün uygulanabilirliğini belirlemiyor.
    if kod == "KOLON_MIN_KESIT":
        return Kategori.BELIRSIZ
    return Kategori.BELIRSIZ


@dataclass
class Bulgu:
    # İlk altı alanın sırası eski positional API ile aynıdır.
    kod: str
    siddet: str = "UYARI"
    mesaj: str | None = None
    konum: tuple | None = None
    handle: str | None = None
    kat: str | None = None
    kategori: Kategori | str | None = None
    detay: dict = field(default_factory=dict)

    def __setattr__(self, ad, deger):
        if ad == "siddet" and deger not in SIDDET:
            raise ValueError(f"Geçersiz şiddet: {deger}")
        super().__setattr__(ad, deger)

    def __post_init__(self):
        kod_bilgisi = self.kod if isinstance(self.kod, tuple) else None
        self.kod = kod_bilgisi[0] if kod_bilgisi else str(self.kod)
        if self.mesaj is None:
            self.mesaj = kod_bilgisi[2] if kod_bilgisi and len(kod_bilgisi) > 2 else self.kod
        if self.kategori is None:
            self.kategori = kod_bilgisi[1] if kod_bilgisi and len(kod_bilgisi) > 1 else _kod_kategorisi(self.kod)
        if self.detay is None:
            self.detay = {}

    def to_dict(self):
        kategori = self.kategori.value if isinstance(self.kategori, Kategori) else self.kategori
        return {
            "kod": self.kod,
            "siddet": self.siddet,
            "mesaj": self.mesaj,
            "konum": _json_deger(self.konum),
            "handle": self.handle,
            "kat": self.kat,
            "kategori": kategori,
            "detay": _json_deger(self.detay),
        }


def ozet(bulgular):
    sayac = Counter(b.siddet for b in bulgular)
    return {s: sayac.get(s, 0) for s in SIDDET}


def kategori_ozeti(bulgular):
    sayac = Counter(
        b.kategori.value if isinstance(b.kategori, Kategori) else b.kategori
        for b in bulgular
    )
    sonuc = {kategori.value: sayac.pop(kategori.value, 0) for kategori in Kategori}
    sonuc.update(sayac)
    return sonuc
