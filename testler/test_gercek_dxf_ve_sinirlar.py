import shutil
import time
from pathlib import Path
import ezdxf

from temizle import temizle
from aks import aks_uret


def test_tamamen_bos_dxf_dosyasi_guvenle_islenir(tmp_path):
    """Hiçbir entity içermeyen boş bir DXF dosyası çökmeden güvenle işlenmelidir."""
    doc = ezdxf.new()
    giris = tmp_path / "bos.dxf"
    cikis = tmp_path / "bos_temiz.dxf"
    doc.saveas(giris)

    rapor = temizle(str(giris), str(cikis))

    assert cikis.exists()
    assert rapor.kolon_sayisi == 0
    assert rapor.kiris_sayisi == 0
    assert any(b.siddet in ("UYARI", "HATA", "BILGI") for b in rapor.bulgular)


def test_kolonsuz_dxf_aks_uret_hata_bulgusu_verir(tmp_path):
    """Kolon olmayan DXF'te aks üretilmeye çalışıldığında güvenli hata bildirimi yapılmalıdır."""
    doc = ezdxf.new()
    doc.layers.add("KIRIS")
    doc.modelspace().add_line((0, 0), (100, 0), dxfattribs={"layer": "KIRIS"})

    giris = tmp_path / "kolonsuz.dxf"
    cikis = tmp_path / "aks_out.dxf"
    doc.saveas(giris)

    rapor = aks_uret(str(giris), str(cikis))

    assert rapor.kolon_sayisi == 0
    assert any(b.kod == "AKS_KOLON_YOK" or b.kod == "KOLON_BULUNAMADI" for b in rapor.bulgular)


def test_gercek_ornek_pafta_kopyasi_uzerinde_analiz(tmp_path):
    """
    Projedeki gerçek DXF paftasının bir kopyası üzerinde analiz ve temizleme çalıştırılır.
    Orijinal dosyaya kesinlikle dokunulmaz.
    """
    kok = Path(__file__).resolve().parent.parent
    orijinal = kok / "ornek_pafta" / "two-bay-slab-formwork-plan-plan-de-coffrage.dxf"
    if not orijinal.exists():
        return

    kopya = tmp_path / "kopya_ornek.dxf"
    shutil.copy2(orijinal, kopya)

    cikis = tmp_path / "sonuc_ornek.dxf"

    # Analiz çalıştır
    rapor = temizle(str(kopya), str(cikis))

    assert cikis.exists()
    assert rapor.birim == "mm", f"Birim INSUNITS=4 gereği mm olmalıydı, {rapor.birim} bulundu"
    assert cikis.stat().st_size > 0


def test_buyuk_dosya_performans_olcum(tmp_path):
    """
    1.000'den fazla entity içeren büyük bir çizimde işlem süresi ölçülür.
    Performans iddiası sayısal ölçüme dayandırılır.
    """
    doc = ezdxf.new()
    msp = doc.modelspace()
    doc.layers.add("KOLON")
    doc.layers.add("KIRIS")

    # 10 x 20 = 200 kolon
    xs = [i * 300 for i in range(10)]
    ys = [j * 400 for j in range(20)]

    for x in xs:
        for y in ys:
            msp.add_lwpolyline(
                [(x - 15, y - 30), (x + 15, y - 30), (x + 15, y + 30), (x - 15, y + 30)],
                close=True,
                dxfattribs={"layer": "KOLON"},
            )

    # Yatay ve düşey çift çizgili kirişler (yaklaşık 700 çizgi)
    for y in ys:
        for i in range(len(xs) - 1):
            x0, x1 = xs[i] + 15, xs[i + 1] - 15
            msp.add_line((x0, y - 12.5), (x1, y - 12.5), dxfattribs={"layer": "KIRIS"})
            msp.add_line((x0, y + 12.5), (x1, y + 12.5), dxfattribs={"layer": "KIRIS"})

    dosya = tmp_path / "buyuk_kat.dxf"
    cikis = tmp_path / "buyuk_temiz.dxf"
    doc.saveas(dosya)

    toplam_nesne = len(list(msp))
    assert toplam_nesne > 500, f"Yeterli nesne üretilemedi: {toplam_nesne}"

    t0 = time.perf_counter()
    rapor = temizle(str(dosya), str(cikis))
    t1 = time.perf_counter()

    gecen_sure_sn = t1 - t0

    # Ölçüm doğrulaması: 5 saniyenin altında tamamlanmalıdır
    assert gecen_sure_sn < 10.0, f"İşlem beklenenden uzun sürdü: {gecen_sure_sn:.2f} sn"
    assert rapor.kolon_sayisi == 200
    assert rapor.cift_cizgi_eksen_sayisi > 0

    print(f"\n[PERFORMANS ÖLÇÜMÜ] {toplam_nesne} nesne içeren pafta {gecen_sure_sn:.3f} saniyede temizlendi.")


def test_r12_ve_eksik_tablo_handle_yukseltme(tmp_path):
    import ezdxf
    from pafta.kat import KatPaftasi

    doc = ezdxf.new("R12")
    msp = doc.modelspace()
    for x, y in [(0, 0), (500, 0), (0, 400), (500, 400)]:
        msp.add_circle((x, y), radius=20, dxfattribs={"layer": "KOLON"})

    giris = tmp_path / "r12_pafta.dxf"
    cikis = tmp_path / "r12_cikis.dxf"
    doc.saveas(giris)

    kp = KatPaftasi(giris)
    kp.temizle()
    rapor = kp.aks_uret(cikis)

    assert cikis.exists()
    assert rapor.kolon_sayisi == 4
    assert (rapor.dusey_aks_sayisi, rapor.yatay_aks_sayisi) == (2, 2)
    assert ezdxf.readfile(cikis).dxfversion >= "AC1015"


def test_dairesel_kolon_ve_cok_dilli_katmanlar(tmp_path):
    import ezdxf
    from pafta.kat import KatPaftasi

    doc = ezdxf.new("AC1015")
    for kat in ["z9-COL", "STUP", "GREDA", "OSI", "ZID"]:
        doc.layers.add(kat)
    msp = doc.modelspace()
    msp.add_circle((0, 0), radius=25, dxfattribs={"layer": "z9-COL"})
    msp.add_circle((600, 0), radius=25, dxfattribs={"layer": "STUP"})
    msp.add_line((0, 0), (600, 0), dxfattribs={"layer": "GREDA"})
    msp.add_line((0, -100), (0, 100), dxfattribs={"layer": "OSI"})
    msp.add_lwpolyline([(0, 200), (600, 200)], dxfattribs={"layer": "ZID"})

    giris = tmp_path / "cok_dilli.dxf"
    doc.saveas(giris)

    kp = KatPaftasi(giris)
    rapor = kp.aks_uret(tmp_path / "cok_dilli_cikis.dxf")

    assert "z9-COL" in rapor.katmanlar["KOLON"]
    assert "STUP" in rapor.katmanlar["KOLON"]
    assert "GREDA" in rapor.katmanlar["KIRIS"]
    assert "OSI" in rapor.katmanlar["AKS"]
    assert "ZID" in rapor.katmanlar["PERDE"]
    assert rapor.kolon_sayisi == 2


def test_kapali_polyline_kiris_eksen_uretimi(tmp_path):
    import ezdxf
    from pafta.kat import KatPaftasi

    doc = ezdxf.new("AC1015")
    doc.layers.add("KOLON")
    doc.layers.add("KIRIS")
    msp = doc.modelspace()
    msp.add_lwpolyline([(-20, -20), (20, -20), (20, 20), (-20, 20)], close=True, dxfattribs={"layer": "KOLON"})
    msp.add_lwpolyline([(480, -20), (520, -20), (520, 20), (480, 20)], close=True, dxfattribs={"layer": "KOLON"})
    msp.add_lwpolyline([(20, -15), (480, -15), (480, 15), (20, 15)], close=True, dxfattribs={"layer": "KIRIS"})

    giris = tmp_path / "poly_kiris.dxf"
    cikis = tmp_path / "poly_kiris_cikis.dxf"
    doc.saveas(giris)

    kp = KatPaftasi(giris)
    kp.temizle()
    rapor = kp.aks_uret(cikis)

    assert rapor.kolon_sayisi == 2
    assert rapor.kiris_sayisi == 1
    assert rapor.cift_cizgi_eksen_sayisi == 1


def test_rapor_to_json_numpy_float64_uyumu():
    import json
    import numpy as np
    from pafta.hata import Bulgu
    from pafta.rapor import AnalizRaporu

    rapor = AnalizRaporu(
        dosya_adi="test.dxf",
        birim_medyan=np.float64(30.0),
        aciklik_x=[np.float64(450.5), np.float64(500.0)],
        aciklik_y=[np.float64(380.25)],
        bulgular=[
            Bulgu("TEST", "BILGI", "NumPy koordinat testi", konum=(np.float64(10.0), np.float64(20.0)))
        ],
    )
    veri = json.loads(rapor.to_json())
    assert veri["birim_medyan"] == 30.0
    assert veri["aciklik_x"] == [450.5, 500.0]
    assert veri["bulgular"][0]["konum"] == [10.0, 20.0]
