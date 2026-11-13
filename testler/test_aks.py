import subprocess
import sys
from pathlib import Path

import ezdxf


KOK = Path(__file__).resolve().parent.parent


def test_aks_ayni_dosyada_tekrar_calistirilinca_mukerrer_uretmez(tmp_path):
    dosya = tmp_path / "kat.dxf"
    doc = ezdxf.new()
    msp = doc.modelspace()
    for x in (0, 500):
        for y in (0, 500):
            msp.add_lwpolyline(
                [(x, y), (x + 30, y), (x + 30, y + 30), (x, y + 30)],
                close=True,
                dxfattribs={"layer": "KOLON"},
            )
    elle_cizilen = msp.add_circle((200, 200), 10, dxfattribs={"layer": "AKS"})
    elle_handle = elle_cizilen.dxf.handle
    doc.saveas(dosya)

    komut = [sys.executable, str(KOK / "aks.py"), str(dosya), str(dosya)]
    subprocess.run(komut, check=True, capture_output=True, text=True)
    ilk_doc = ezdxf.readfile(dosya)
    ilk_msp = ilk_doc.modelspace()
    ilk_adet = len(ilk_msp.query('*[layer=="AKS"]'))
    ilk_isaretli = sum(e.has_xdata("PAFTA_ARACI") for e in ilk_msp)

    subprocess.run(komut, check=True, capture_output=True, text=True)
    ikinci_doc = ezdxf.readfile(dosya)
    ikinci_msp = ikinci_doc.modelspace()
    ikinci_adet = len(ikinci_msp.query('*[layer=="AKS"]'))
    ikinci_isaretli = sum(e.has_xdata("PAFTA_ARACI") for e in ikinci_msp)

    assert ikinci_adet == ilk_adet
    assert ilk_isaretli == ikinci_isaretli == 12
    assert elle_handle in {e.dxf.handle for e in ikinci_msp}
