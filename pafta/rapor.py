import json
from dataclasses import dataclass, field, asdict
from pafta.hata import Bulgu, ozet


@dataclass
class AnalizRaporu:
    dosya_adi: str = ""
    cikis_dosyasi: str = ""
    birim: str = "cm"
    birim_baslik: str | None = None
    birim_medyan: float | None = None
    katmanlar: dict = field(default_factory=dict)

    # Eleman sayıları
    kolon_sayisi: int = 0
    poly_kolon_sayisi: int = 0
    blok_kolon_sayisi: int = 0
    kiris_sayisi: int = 0
    cift_cizgi_eksen_sayisi: int = 0
    tek_cizgi_sayisi: int = 0

    # Aks bilgileri
    dusey_aks_sayisi: int = 0
    yatay_aks_sayisi: int = 0
    aciklik_x: list[float] = field(default_factory=list)
    aciklik_y: list[float] = field(default_factory=list)
    bos_aks_kesisimi: int = 0

    # Düzeltme ve temizleme istatistikleri
    acik_kolon_kapatilan: int = 0
    cakisik_kolon_silinen: int = 0
    gecersiz_kolon_silinen: int = 0
    cakisik_blok_sayisi: int = 0
    sifir_olcek_blok_sayisi: int = 0
    uc_yakalanan_kiris: int = 0
    cakisik_kiris_silinen: int = 0
    sifir_boy_kiris_silinen: int = 0
    kolon_disi_uc_sayisi: int = 0

    # Bulgular
    bulgular: list[Bulgu] = field(default_factory=list)

    def bulgu_ozeti(self) -> dict:
        return ozet(self.bulgular)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["bulgu_ozeti"] = self.bulgu_ozeti()
        return d

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=indent)

    def konsol_raporu(self) -> str:
        lines = [
            f"giriş : {self.dosya_adi}",
            f"KOLON : {self.kolon_sayisi} adet ({self.poly_kolon_sayisi} polyline + {self.blok_kolon_sayisi} blok) | "
            f"açık->kapalı {self.acik_kolon_kapatilan} | çakışık silinen {self.cakisik_kolon_silinen} | "
            f"geçersiz silinen {self.gecersiz_kolon_silinen} | çakışık blok (silinmedi) {self.cakisik_blok_sayisi}",
            f"KİRİŞ : {self.kiris_sayisi} adet | çift çizgiden eksen {self.cift_cizgi_eksen_sayisi} | "
            f"tek çizgi {self.tek_cizgi_sayisi} | uç yakalanan {self.uc_yakalanan_kiris} | "
            f"çakışık silinen {self.cakisik_kiris_silinen} | sıfır boy silinen {self.sifir_boy_kiris_silinen} | "
            f"kolon dışı uç {self.kolon_disi_uc_sayisi}",
            f"çıkış : {self.cikis_dosyasi}",
        ]
        return "\n".join(lines)
