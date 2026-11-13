import sys
import argparse
from pathlib import Path

from pafta.kat import KatPaftasi
from pafta.rapor import AnalizRaporu


def temizle(
    giris: str = "bozuk_kat.dxf",
    cikis: str = "temiz_kat.dxf",
    json_cikti: bool = False,
    katman_secimleri: dict | None = None,
    birim: str | None = None,
) -> AnalizRaporu:
    """
    DXF dosyasındaki kolon ve kiriş katmanlarını inceler, açık kolonları kapatır,
    çakışık elemanları birim duyarlı yöntemle ayıklar, kiriş eksenlerini türetir
    ve güvenli biçimde kaydeder.
    """
    pafta = KatPaftasi(giris, secimler=katman_secimleri, birim_zorla=birim)
    rapor = pafta.temizle(cikis)

    if json_cikti:
        print(rapor.to_json())
    else:
        # Birim uyarısı varsa yazdır
        for b in rapor.bulgular:
            if b.kod == "BIRIM_OLCEK_UYARISI":
                print(f"UYARI: {b.mesaj} Toleranslar cm varsayıyor, ortak.py'den ayarla.")

        print(rapor.konsol_raporu())

    return rapor


def main():
    parser = argparse.ArgumentParser(description="Structural CAD Analyzer - DXF Temizleme ve Eksen Çıkarma")
    parser.add_argument("giris", nargs="?", default="bozuk_kat.dxf", help="Giriş DXF dosyası")
    parser.add_argument("cikis", nargs="?", default="temiz_kat.dxf", help="Çıkış DXF dosyası")
    parser.add_argument("--json", action="store_true", help="Çıktıyı JSON formatında ver")
    parser.add_argument("--birim", choices=["mm", "cm", "m"], help="Çizim birimini zorla (mm, cm, m)")

    args = parser.parse_args()
    try:
        temizle(args.giris, args.cikis, json_cikti=args.json, birim=args.birim)
    except Exception as e:
        sys.exit(f"HATA: {e}")


if __name__ == "__main__":
    main()
