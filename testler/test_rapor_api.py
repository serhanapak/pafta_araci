import json
import subprocess
import sys
from pathlib import Path
import ezdxf

from temizle import temizle
from aks import aks_uret
from pafta.rapor import AnalizRaporu


def test_temizle_ve_aks_uret_python_api_rapor_dondurur(tmp_path):
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.layers.add("KIRIS")
    msp = doc.modelspace()

    for cx in (0, 400):
        msp.add_lwpolyline(
            [(cx - 15, -15), (cx + 15, -15), (cx + 15, 15), (cx - 15, 15)],
            close=True,
            dxfattribs={"layer": "KOLON"},
        )
    msp.add_line((0, -12.5), (400, -12.5), dxfattribs={"layer": "KIRIS"})
    msp.add_line((0, 12.5), (400, 12.5), dxfattribs={"layer": "KIRIS"})

    giris = tmp_path / "plan.dxf"
    cikis_t = tmp_path / "temiz.dxf"
    cikis_a = tmp_path / "aks.dxf"
    doc.saveas(giris)

    # API çağrısı: temizle
    rapor_t = temizle(str(giris), str(cikis_t))
    assert isinstance(rapor_t, AnalizRaporu)
    assert rapor_t.kolon_sayisi == 2
    assert rapor_t.kiris_sayisi == 1

    # JSON dönüşümü doğrulaması
    json_metni = rapor_t.to_json()
    veri = json.loads(json_metni)
    assert veri["kolon_sayisi"] == 2
    assert veri["birim"] == "cm"
    assert "bulgu_ozeti" in veri

    # API çağrısı: aks_uret
    rapor_a = aks_uret(str(cikis_t), str(cikis_a))
    assert isinstance(rapor_a, AnalizRaporu)
    assert rapor_a.dusey_aks_sayisi == 2
    assert rapor_a.yatay_aks_sayisi == 1


def test_cli_json_argumani_gecerli_json_uretir(tmp_path):
    doc = ezdxf.new()
    doc.layers.add("KOLON")
    doc.modelspace().add_lwpolyline(
        [(0, 0), (30, 0), (30, 60), (0, 60)],
        close=True,
        dxfattribs={"layer": "KOLON"},
    )
    giris = tmp_path / "tek_kolon.dxf"
    cikis = tmp_path / "out.dxf"
    doc.saveas(giris)

    kok = Path(__file__).resolve().parent.parent
    r = subprocess.run(
        [sys.executable, str(kok / "temizle.py"), str(giris), str(cikis), "--json"],
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    veri = json.loads(r.stdout)
    assert veri["kolon_sayisi"] == 1
    assert "bulgular" in veri
