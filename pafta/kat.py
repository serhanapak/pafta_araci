import statistics
from pathlib import Path
import ezdxf
from ezdxf.addons import Importer

from pafta.birim import birim_tahmin, Ayar
from pafta.katman import katman_tani
from pafta.blok import blok_tani
from pafta.kolon import kolonlari_isle
from pafta.kiris import kirisleri_isle
from pafta.aks import akslari_isle
from pafta.rapor import AnalizRaporu
from pafta.duzelt import guvenli_kaydet
from pafta.hata import Bulgu


class KatPaftasi:
    """
    Statik kat planı DXF çizimini temsil eden ve analiz, temizleme ve
    aks üretimini yöneten ana servis sınıfı.
    """

    def __init__(self, dosya_yolu: str | Path, secimler: dict | None = None, birim_zorla: str | None = None):
        self.dosya_yolu = Path(dosya_yolu)
        self.secimler = secimler or {}
        self.birim_zorla = birim_zorla
        self.son_rapor: AnalizRaporu | None = None

        ham_doc = ezdxf.readfile(str(self.dosya_yolu))
        if getattr(ham_doc, "dxfversion", "AC1015") < "AC1015" or not getattr(ham_doc.layers._head.dxf, "handle", None):
            yeni_doc = ezdxf.new("AC1015")
            yeni_doc.header["$INSUNITS"] = ham_doc.header.get("$INSUNITS", 0)
            importer = Importer(ham_doc, yeni_doc)
            importer.import_modelspace()
            importer.finalize()
            self.doc = yeni_doc
        else:
            self.doc = ham_doc
        self.msp = self.doc.modelspace()

        self.katman_sonucu = katman_tani(self.doc, self.secimler)
        self.kolon_katmanlari = self.katman_sonucu.katmanlar.get("KOLON", []) or ["KOLON"]
        self.kiris_katmanlari = self.katman_sonucu.katmanlar.get("KIRIS", []) or ["KIRIS"]
        self.aks_katmanlari = self.katman_sonucu.katmanlar.get("AKS", []) or ["AKS"]
        self.perde_katmanlari = self.katman_sonucu.katmanlar.get("PERDE", [])

        if self.birim_zorla:
            self.ayar = Ayar.olustur(self.birim_zorla)
            self.birim_sonucu = None
        else:
            self.birim_sonucu = birim_tahmin(self.doc, self.kolon_katmanlari)
            secilen_birim = self.birim_sonucu.birim or "cm"
            self.ayar = Ayar.olustur(secilen_birim)

    @property
    def rapor(self) -> AnalizRaporu | None:
        return self.son_rapor

    def temizle(self, cikis_yolu: str | Path | None = None) -> AnalizRaporu:
        cikis = Path(cikis_yolu) if cikis_yolu else self.dosya_yolu
        rapor = AnalizRaporu(
            dosya_adi=str(self.dosya_yolu),
            cikis_dosyasi=str(cikis),
            birim=self.ayar.birim,
            katmanlar=self.katman_sonucu.katmanlar,
        )

        rapor.bulgular.extend(self.katman_sonucu.bulgular)
        if self.birim_sonucu:
            rapor.birim_baslik = self.birim_sonucu.baslik
            rapor.birim_medyan = self.birim_sonucu.medyan
            rapor.bulgular.extend(self.birim_sonucu.bulgular)

        # Blok ölçek / dönüş açısı kontrolleri
        blok_sonuc = blok_tani(self.doc)
        for b in blok_sonuc.bulgular:
            if b.kod != "BLOK_SIFIR_OLCEK":
                rapor.bulgular.append(b)

        # 1. Kolonları işle
        kolon_sonuc = kolonlari_isle(
            self.doc, self.msp, self.kolon_katmanlari, self.ayar, duzelt=True
        )
        rapor.kolon_sayisi = len(kolon_sonuc.merkezler)
        rapor.poly_kolon_sayisi = sum(1 for k in kolon_sonuc.kolonlar if k.tur in ("POLYLINE", "CIRCLE"))
        rapor.blok_kolon_sayisi = sum(1 for k in kolon_sonuc.kolonlar if k.tur == "INSERT")
        rapor.acik_kolon_kapatilan = kolon_sonuc.acik_kapatilan
        rapor.cakisik_kolon_silinen = kolon_sonuc.cakisik_kolon_sayisi
        rapor.gecersiz_kolon_silinen = kolon_sonuc.gecersiz_sayisi
        rapor.cakisik_blok_sayisi = kolon_sonuc.cakisik_blok_sayisi
        rapor.sifir_olcek_blok_sayisi = kolon_sonuc.sifir_olcek_sayisi
        rapor.bulgular.extend(kolon_sonuc.bulgular)

        # 2. Kirişleri işle
        kiris_sonuc = kirisleri_isle(
            self.doc,
            self.msp,
            self.kiris_katmanlari,
            kolon_sonuc.merkezler,
            self.ayar,
            duzelt=True,
            eksen_uret=True,
            perde_katmanlari=self.perde_katmanlari,
        )
        rapor.kiris_sayisi = len(kiris_sonuc.nihai_kirisler)
        rapor.cift_cizgi_eksen_sayisi = len(kiris_sonuc.eksenler)
        rapor.tek_cizgi_sayisi = len(kiris_sonuc.tek_cizgiler)
        rapor.uc_yakalanan_kiris = kiris_sonuc.yakalanan_uc_sayisi
        rapor.cakisik_kiris_silinen = kiris_sonuc.cakisik_silinen_sayisi
        rapor.sifir_boy_kiris_silinen = kiris_sonuc.sifir_boy_silinen_sayisi
        rapor.kolon_disi_uc_sayisi = kiris_sonuc.kolon_disi_uc_sayisi
        rapor.bulgular.extend(kiris_sonuc.bulgular)

        # 3. Kısa kenar uyarısı
        if kolon_sonuc.kisa_kenarlar:
            med = statistics.median(kolon_sonuc.kisa_kenarlar)
            if self.ayar.birim == "cm" and (med < 5 or med > 150):
                rapor.bulgular.append(
                    Bulgu(
                        "BIRIM_OLCEK_UYARISI",
                        "UYARI",
                        f"Kolon kısa kenar medyanı {med:.1f}, çizim cm değil (m/mm) olabilir.",
                    )
                )

        guvenli_kaydet(self.doc, cikis, giris_yolu=self.dosya_yolu)
        self.son_rapor = rapor
        return rapor

    def aks_uret(self, cikis_yolu: str | Path | None = None) -> AnalizRaporu:
        cikis = Path(cikis_yolu) if cikis_yolu else self.dosya_yolu
        rapor = self.son_rapor or AnalizRaporu(
            dosya_adi=str(self.dosya_yolu),
            cikis_dosyasi=str(cikis),
            birim=self.ayar.birim,
            katmanlar=self.katman_sonucu.katmanlar,
        )
        rapor.cikis_dosyasi = str(cikis)

        kolon_sonuc = kolonlari_isle(
            self.doc, self.msp, self.kolon_katmanlari, self.ayar, duzelt=False
        )
        rapor.kolon_sayisi = len(kolon_sonuc.merkezler)

        if not kolon_sonuc.merkezler:
            rapor.bulgular.append(
                Bulgu("KOLON_BULUNAMADI", "HATA", "Aks üretimi için kolon bulunamadı")
            )
            self.son_rapor = rapor
            return rapor

        aks_sonuc = akslari_isle(
            self.doc,
            self.msp,
            kolon_sonuc.merkezler,
            self.ayar,
            duzelt=True,
            aks_katman=self.aks_katmanlari[0] if self.aks_katmanlari else "AKS",
        )
        rapor.dusey_aks_sayisi = aks_sonuc.dusey_aks_sayisi
        rapor.yatay_aks_sayisi = aks_sonuc.yatay_aks_sayisi
        rapor.aciklik_x = aks_sonuc.aciklik_x
        rapor.aciklik_y = aks_sonuc.aciklik_y
        rapor.bos_aks_kesisimi = aks_sonuc.bos_kesisim
        rapor.bulgular.extend(aks_sonuc.bulgular)

        guvenli_kaydet(self.doc, cikis, giris_yolu=self.dosya_yolu)
        self.son_rapor = rapor
        return rapor
