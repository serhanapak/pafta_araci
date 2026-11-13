import pytest
import ezdxf

from ortak import blok_merkezleri


def test_blok_merkezi_taban_noktasi_olcek_ve_donus():
    doc = ezdxf.new()

    block = doc.blocks.new(
        "B_TEST",
        base_point=(100, 50, 0)
    )

    block.add_lwpolyline(
        [(100, 50), (120, 50), (120, 70), (100, 70)],
        close=True,
        dxfattribs={"layer": "KOLON"}
    )

    ins = doc.modelspace().add_blockref(
        "B_TEST",
        (1000, 2000),
        dxfattribs={
            "xscale": 2,
            "yscale": 3,
            "rotation": 90
        }
    )

    mevcut = blok_merkezleri(doc, ins)[0]

    assert mevcut == pytest.approx((970, 2020))


def test_acik_polyline_blokta_kolon_merkezi_sayilmaz():
    doc = ezdxf.new()
    block = doc.blocks.new("B_ACIK")
    block.add_lwpolyline([(0, 0), (20, 0), (20, 20)])
    ins = doc.modelspace().add_blockref("B_ACIK", (0, 0))

    assert blok_merkezleri(doc, ins) == []
