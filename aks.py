import sys
import argparse
from pathlib import Path

from pafta.kat import KatPaftasi
from pafta.rapor import AnalizRaporu
from ortak import harf


def aks_uret(
    giris: str = "temiz_kat.dxf",
    cikis: str = "aks_kat.dxf",
    json_cikti: bool = False,
    katman_secimleri: dict | None = None,
    birim: str | None = None,
) -> AnalizRaporu:
    """
    DXF dosyasındaki kolon merkezlerinden düşey ve yatay aks çizgileri,
    balonları ve aks yazılarını türetir.
    """
    pafta = KatPaftasi(giris, secimler=katman_secimleri, birim_zorla=birim)
    rapor = pafta.aks_uret(cikis)

    if json_cikti:
        print(rapor.to_json())
    else:
        bos = rapor.bos_aks_kesisimi
        dx = rapor.dusey_aks_sayisi
        dy = rapor.yatay_aks_sayisi

        from ortak import grupla, kolon_merkezleri
        merkezler = kolon_merkezleri(pafta.doc, pafta.msp, pafta.kolon_katmanlari)
        xs_c = grupla([m[0] for m in merkezler], pafta.ayar.tol_aks)
        ys_c = grupla([m[1] for m in merkezler], pafta.ayar.tol_aks)

        print(f"aks      : {dx} düşey (1-{dx}) x {dy} yatay (A-{harf(dy - 1) if dy > 0 else 'A'})")
        print("açıklık X:", [round(xs_c[i + 1] - xs_c[i], 1) for i in range(len(xs_c) - 1)])
        print("açıklık Y:", [round(ys_c[i + 1] - ys_c[i], 1) for i in range(len(ys_c) - 1)])
        print(f"boş kesişim: {bos}")
        print(f"çıkış    : {cikis}")

    return rapor


def main():
    parser = argparse.ArgumentParser(description="Structural CAD Analyzer - DXF Aks Üretimi")
    parser.add_argument("giris", nargs="?", default="temiz_kat.dxf", help="Giriş DXF dosyası")
    parser.add_argument("cikis", nargs="?", default="aks_kat.dxf", help="Çıkış DXF dosyası")
    parser.add_argument("--json", action="store_true", help="Çıktıyı JSON formatında ver")
    parser.add_argument("--birim", choices=["mm", "cm", "m"], help="Çizim birimini zorla (mm, cm, m)")

    args = parser.parse_args()
    rapor = aks_uret(args.giris, args.cikis, json_cikti=args.json, birim=args.birim)
    if rapor.kolon_sayisi == 0:
        sys.exit("kolon bulunamadı, KOLON_KATMAN ayarını kontrol et")


if __name__ == "__main__":
    main()
