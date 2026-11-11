import ezdxf

from pafta.blok import blok_tani


def test_normal_blok():
    doc = ezdxf.new()
    doc.blocks.new("K3060")
    doc.modelspace().add_blockref("K3060", (0, 0))

    sonuc = blok_tani(doc)

    assert sonuc.adet == 1
    assert sonuc.isimler == {"K3060": 1}
    assert sonuc.bulgular == []


def test_sifir_olcek(tmp_path):
    doc = ezdxf.new()
    doc.blocks.new("K3060")
    doc.modelspace().add_blockref("K3060", (0, 0))

    dosya = tmp_path / "sifir_olcek.dxf"
    doc.saveas(dosya)

    satirlar = dosya.read_text(encoding="utf-8").splitlines()

    bulundu = False

    for i in range(len(satirlar) - 1):
        if satirlar[i].strip() != "0":
            continue
        if satirlar[i + 1].strip() != "INSERT":
            continue

        son = len(satirlar)
        for j in range(i + 2, len(satirlar) - 1, 2):
            if satirlar[j].strip() == "0":
                son = j
                break

        kayit = satirlar[i:son]

        ad = None
        for j in range(0, len(kayit) - 1, 2):
            if kayit[j].strip() == "2":
                ad = kayit[j + 1].strip()
                break

        if ad != "K3060":
            continue

        for j in range(0, len(kayit) - 1, 2):
            if kayit[j].strip() == "41":
                kayit[j + 1] = "0"
                break
        else:
            kayit.extend(["41", "0"])

        satirlar[i:son] = kayit
        bulundu = True
        break

    assert bulundu, "K3060 INSERT kaydı DXF içerisinde bulunamadı."

    dosya.write_text("\n".join(satirlar) + "\n", encoding="utf-8")

    okunan = ezdxf.readfile(dosya)
    ins = list(okunan.modelspace().query("INSERT"))[0]

    assert ins.dxf.xscale == 0

    sonuc = blok_tani(okunan)

    assert any(
        b.kod == "BLOK_SIFIR_OLCEK"
        for b in sonuc.bulgular
    )


def test_negatif_olcek():
    doc = ezdxf.new()
    doc.blocks.new("K3060")
    doc.modelspace().add_blockref(
        "K3060", (0, 0),
        dxfattribs={"xscale": -1}
    )

    sonuc = blok_tani(doc)

    assert any(
        b.kod == "BLOK_NEGATIF_OLCEK"
        for b in sonuc.bulgular
    )


def test_donus_acisi():
    doc = ezdxf.new()
    doc.blocks.new("K3060")
    doc.modelspace().add_blockref(
        "K3060", (0, 0),
        dxfattribs={"rotation": 450}
    )

    sonuc = blok_tani(doc)

    assert any(
        b.kod == "BLOK_DONUS_ACISI"
        for b in sonuc.bulgular
    )


def test_gercekci_dxf():
    doc = ezdxf.readfile("gercekci_kat.dxf")

    sonuc = blok_tani(doc)

    assert sonuc.adet == 2
    assert sonuc.isimler == {"K3060": 2}
    assert sonuc.bulgular == []


if __name__ == "__main__":
    test_normal_blok()
    test_sifir_olcek()
    test_negatif_olcek()
    test_donus_acisi()
    test_gercekci_dxf()

    print("BLOK MODULU: BUTUN TESTLER GECTI")
