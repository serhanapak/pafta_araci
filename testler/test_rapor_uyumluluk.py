import json

import numpy as np
import ezdxf

from pafta.hata import Bulgu, HataKodu, Kategori, SIDDET, SIDDETLER
from pafta.katman import katman_tani
from pafta.rapor import AnalizRaporu


ESKI_RAPOR_ALANLARI = {
    "dosya_adi", "cikis_dosyasi", "birim", "birim_baslik", "birim_medyan",
    "katmanlar", "kolon_sayisi", "poly_kolon_sayisi", "blok_kolon_sayisi",
    "kiris_sayisi", "cift_cizgi_eksen_sayisi", "tek_cizgi_sayisi",
    "perde_sayisi", "perde_eksen_sayisi", "dusey_aks_sayisi",
    "yatay_aks_sayisi", "aciklik_x", "aciklik_y", "bos_aks_kesisimi",
    "acik_kolon_kapatilan", "cakisik_kolon_silinen", "gecersiz_kolon_silinen",
    "cakisik_blok_sayisi", "sifir_olcek_blok_sayisi", "uc_yakalanan_kiris",
    "cakisik_kiris_silinen", "sifir_boy_kiris_silinen",
    "kolon_disi_uc_sayisi", "bulgular",
}


def test_siddet_eski_adi_ve_bulgu_ozeti_sozlesmesi():
    assert SIDDET == SIDDETLER == ("BILGI", "UYARI", "HATA")
    rapor = AnalizRaporu(bulgular=[
        Bulgu("A", "BILGI", "bilgi"),
        Bulgu("B", "UYARI", "uyarı"),
        Bulgu("C", "HATA", "hata"),
        Bulgu("D", "HATA", "hata 2"),
    ])

    assert rapor.bulgu_ozeti() == {"BILGI": 1, "UYARI": 1, "HATA": 2}
    assert rapor.to_dict()["bulgu_ozeti"] == rapor.bulgu_ozeti()


def test_rapor_json_eski_alanlari_ve_katman_dinamik_alanlarini_tasir():
    rapor = AnalizRaporu(dosya_adi="kat.dxf", birim="mm", bulgular=[])
    rapor.birim_baslik = "mm"
    rapor.poly_kolon_sayisi = 3
    rapor.perde_eksen_sayisi = 2
    rapor.bos_aks_kesisimi = [np.int64(1), np.int64(2)]
    rapor.kolon_disi_uc_sayisi = 4
    veri = json.loads(rapor.to_json())

    assert ESKI_RAPOR_ALANLARI <= veri.keys()
    assert veri["birim_baslik"] == "mm"
    assert veri["poly_kolon_sayisi"] == 3
    assert veri["perde_eksen_sayisi"] == 2
    assert veri["bos_aks_kesisimi"] == [1, 2]
    assert veri["kolon_disi_uc_sayisi"] == 4


def test_json_turkce_karakterleri_escape_etmeden_korur():
    rapor = AnalizRaporu(bulgular=[
        Bulgu("KOLON_KATMANI_BULUNAMADI", "UYARI", "Döşeme için katman eşlemesi yok.")
    ])

    json_metni = rapor.to_json()

    assert "Döşeme için katman eşlemesi yok." in json_metni
    assert Kategori.YAPILANDIRMA.value in json_metni
    assert "\\u00f6" not in json_metni


def test_bulgu_numpy_koordinatlari_ve_kategori_sayimlari_jsona_doner():
    bulgular = [
        Bulgu(HataKodu.DOSYA_OKUNDU, "BILGI", konum=(np.float64(0), np.float64(12.5))),
        Bulgu(HataKodu.TBDY_UYUMSUZ_KATMAN, "HATA", konum=(np.float64(1), np.float64(2))),
        Bulgu("KIRIS_CAKISIK", "UYARI"),
    ]
    rapor = AnalizRaporu(bulgular=bulgular)
    veri = json.loads(rapor.to_json())

    assert veri["bulgular"][0]["konum"] == [0.0, 12.5]
    assert veri["bulgular"][0]["kategori"] == Kategori.ISLEMSEL.value
    assert veri["bulgular"][1]["kategori"] == Kategori.BELIRSIZ.value
    assert veri["bulgular"][2]["kategori"] == Kategori.GEOMETRIK.value
    assert veri["kategori_ozeti"] == {
        Kategori.ISLEMSEL.value: 1,
        Kategori.GEOMETRIK.value: 1,
        Kategori.YONETMELIK.value: 0,
        Kategori.YAPILANDIRMA.value: 0,
        Kategori.BELIRSIZ.value: 1,
    }


def test_dort_katman_turu_bulunamadiginda_yapilandirma_siniflandirilir():
    doc = ezdxf.new()
    sonuc = katman_tani(doc)
    katman_bulunamadi = {
        b.kod: b for b in sonuc.bulgular if b.kod.endswith("_KATMANI_BULUNAMADI")
    }

    assert set(katman_bulunamadi) == {
        "KOLON_KATMANI_BULUNAMADI",
        "KIRIS_KATMANI_BULUNAMADI",
        "AKS_KATMANI_BULUNAMADI",
        "PERDE_KATMANI_BULUNAMADI",
    }
    assert all(b.kategori == Kategori.YAPILANDIRMA for b in katman_bulunamadi.values())


def test_katman_bulunamadi_kategorisi_json_ozetinde_sayilir():
    rapor = AnalizRaporu(bulgular=[
        Bulgu("KOLON_KATMANI_BULUNAMADI", "UYARI"),
        Bulgu("KIRIS_KATMANI_BULUNAMADI", "UYARI"),
        Bulgu("AKS_KATMANI_BULUNAMADI", "UYARI"),
        Bulgu("PERDE_KATMANI_BULUNAMADI", "UYARI"),
    ])

    assert json.loads(rapor.to_json())["kategori_ozeti"] == {
        Kategori.ISLEMSEL.value: 0,
        Kategori.GEOMETRIK.value: 0,
        Kategori.YONETMELIK.value: 0,
        Kategori.YAPILANDIRMA.value: 4,
        Kategori.BELIRSIZ.value: 0,
    }


def test_mevcut_kategori_eslemeleri_ve_belirsiz_varsayilan_korunur():
    assert Bulgu("DOSYA_OKUNDU", "BILGI").kategori == Kategori.ISLEMSEL
    assert Bulgu("KIRIS_CAKISIK", "UYARI").kategori == Kategori.GEOMETRIK
    assert Bulgu("TBDY_UYUMSUZ_KATMAN", "HATA").kategori == Kategori.BELIRSIZ
    assert Bulgu("YENI_BILINMEYEN_KOD", "UYARI").kategori == Kategori.BELIRSIZ


def test_tbd_yonetmelik_kodu_uygulanmis_ihlalmis_gibi_sunulmaz():
    bulgu = Bulgu(HataKodu.TBDY_UYUMSUZ_KATMAN, "UYARI")

    assert bulgu.kod == "TBDY_UYUMSUZ_KATMAN"
    assert bulgu.kategori == Kategori.BELIRSIZ


def test_kolon_min_kesit_kapsam_bilgisi_yokken_belirsiz_siniflanir():
    # TBDY 2018 7.3.1.1 minimum ölçüleri yüksek süneklik düzeyi kolonlar içindir;
    # motor modelinde kolonun süneklik sınıfı olmadığı için uygunluk iddiası kurulamaz.
    assert Bulgu("KOLON_MIN_KESIT", "UYARI").kategori == Kategori.BELIRSIZ


def test_acik_kategori_kod_cikarimindan_onceliklidir():
    bulgu = Bulgu(
        "KOLON_KATMANI_BULUNAMADI", "UYARI", "özel sınıf",
        kategori=Kategori.YONETMELIK,
    )

    assert bulgu.kategori == Kategori.YONETMELIK


def test_bilinmeyen_kod_acik_belirsiz_kategorisinde_kalir():
    bulgu = Bulgu("YENI_KOD_TANIMSIZ", "UYARI", "kayıtlı değil")

    assert bulgu.kategori == Kategori.BELIRSIZ


def test_bulgu_siddeti_gecerli_degerlere_sonradan_degistirilebilir():
    bulgu = Bulgu("TEST", "BILGI", "mesaj")

    bulgu.siddet = "HATA"

    assert bulgu.siddet == "HATA"


def test_bulgu_siddeti_gecersiz_degere_sonradan_degistirilemez():
    bulgu = Bulgu("TEST", "UYARI", "mesaj")

    import pytest

    with pytest.raises(ValueError, match="Geçersiz şiddet"):
        bulgu.siddet = "KRITIK"

    assert bulgu.siddet == "UYARI"


def test_bulgu_eski_konumsal_parametre_sirasi_korunur():
    bulgu = Bulgu("TEST", "HATA", "mesaj", (1, 2), "AB12", "KOLON")

    assert (bulgu.kod, bulgu.siddet, bulgu.mesaj, bulgu.konum, bulgu.handle, bulgu.kat) == (
        "TEST", "HATA", "mesaj", (1, 2), "AB12", "KOLON",
    )
