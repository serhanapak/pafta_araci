# pafta_araci

AutoCAD ve Sta4CAD öncesi/sonrası yapısal kat planı DXF dosyalarını temizleyen, kiriş ve perde merkez eksenlerini çıkaran, kolon yerleşimine göre aks ızgarası üreten Python aracı.

## Ne Yapar?

- Çizim birimini (`mm`, `cm`, `m`) `$INSUNITS` ve kolon kesit boyutlarından otomatik algılar; eski R12 (`AC1009`) veya eksik tablolu DXF dosyalarını `AC1015` sürümüne kurtarır.
- Farklı ofis standartlarındaki katman adlarını (`KOLON`, `COLUMN`, `z9-COL`, `STUP`, `KIRIS`, `BEAM`, `GREDA`, `PERDE`, `WALL`, `AKS`, `GRID` vb.) eşleştirir.
- Açık kalmış kolon poligonlarını kapatır, üst üste binmiş mükerrer çizgileri eler, `CIRCLE` ve `INSERT` blok kolonlarını okur.
- Paralel çift kiriş çizgilerinden ve kapalı poligon kesitlerden kiriş merkez ekseni (`KIRIS_EKSEN`), perde poligonlarından perde ekseni (`PERDE_EKSEN`) üretir.
- Kolon ağırlık merkezlerini gruplayarak düşey (`1, 2, 3...`) ve yatay (`A, B, C...`) aks çizgileri ile aks balonlarını oluşturur.
- Mesnetsiz kiriş uçlarını, kolonsuz aks kesişimlerini ve TBDY 2018 minimum kesit sınırlarının altında kalan elemanları raporlar; istenirse `PAFTA_HATA` katmanında işaretler.

## Kurulum

```bash
git clone [https://github.com/serhanapak/pafta_araci.git](https://github.com/serhanapak/pafta_araci.git)
cd pafta_araci
pip install -e ".[dev]"
```

## Kullanım

Komut satırından:

```bash
pafta-temizle ham_pafta.dxf temiz_pafta.dxf
pafta-aks temiz_pafta.dxf aksli_pafta.dxf
```

JSON çıktı almak veya birimi elle sabitlemek için:

```bash
pafta-aks temiz_pafta.dxf aksli_pafta.dxf --birim cm --json
```

Python içinden:

```python
from pafta.kat import KatPaftasi

pafta = KatPaftasi("kat_plani.dxf")
pafta.temizle("temiz.dxf", gorsel_hata=True)
rapor = pafta.aks_uret("aksli.dxf", gorsel_hata=True)

print(rapor.konsol_raporu())
```

## Test

```bash
pytest
```
