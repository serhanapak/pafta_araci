# pafta_araci (Structural CAD Analyzer)

Yapısal DXF kat planlarını analiz eden, çizim hatalarını temizleyen, kiriş merkez eksenlerini çıkaran ve kolon yerleşimine göre otomatik aks ızgarası üreten açık kaynak Python aracı.

## Özellikler

- **Otomatik Birim ve Sürüm Kurtarma:** `$INSUNITS` ve kolon kesit boyutlarından çizim birimini (`mm`, `cm`, `m`) algılar; DXF R12 (`AC1009`) veya tablo handle'ı eksik dosyaları otomatik olarak `AC1015` sürümüne yükseltir.
- **Çok Dilli Katman Tanıma:** Türkçe, İngilizce, Hırvatça ve Fransızca standart katman adlarını (`KOLON`, `COLUMN`, `z9-COL`, `STUP`, `KIRIS`, `BEAM`, `GREDA`, `AKS`, `GRID`, `OSI`, `PERDE`, `WALL`, `ZID`) otomatik eşleştirir.
- **Geometrik Temizlik ve Eksen Çıkarma:** Açık poligon kolonları kapatır, mükerrer kolon/kirişleri eler, `CIRCLE` ve `INSERT` blok kolonlarını işler; paralel çift kiriş çizgilerinden ve kapalı `LWPOLYLINE` kesitlerden kiriş merkez ekseni üretir.
- **Otomatik Aks Üretimi:** Kolon ağırlık merkezlerini gruplayarak düşey (`1, 2, 3...`) ve yatay (`A, B, C...`) aks çizgileri ile aks balonlarını oluşturur; kolonsuz aks kesişimlerini ve mesnetsiz kiriş uçlarını raporlar.

## Kurulum

```bash
pip install -e ".[dev]"
pafta-temizle giris_pafta.dxf temiz_pafta.dxf
pafta-aks temiz_pafta.dxf aks_pafta.dxf --json
pytest
