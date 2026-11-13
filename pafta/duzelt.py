import os
import shutil
import tempfile
from pathlib import Path


def ayni_dosya_mi(yol1, yol2):
    """İki dosya yolunun aynı fiziksel dosyaya işaret edip etmediğini kontrol eder."""
    if not yol1 or not yol2:
        return False
    p1 = Path(yol1).resolve()
    p2 = Path(yol2).resolve()
    return p1 == p2


def yedek_al(dosya_yolu):
    """Dosyanın .bak uzantılı güvenli bir kopyasını oluşturur."""
    kaynak = Path(dosya_yolu)
    if not kaynak.exists() or not kaynak.is_file():
        return None
    hedef = kaynak.with_suffix(kaynak.suffix + ".bak")
    shutil.copy2(kaynak, hedef)
    return hedef


def guvenli_kaydet(doc, cikis_yolu, giris_yolu=None, yedekle=True):
    """
    DXF belgesini önce geçici bir dosyaya kaydeder, doğrular ve atomik olarak
    hedef yola taşır. Eğer giriş ve çıkış aynı dosyaysa otomatik .bak yedeği alır.
    """
    cikis = Path(cikis_yolu).resolve()
    giris = Path(giris_yolu).resolve() if giris_yolu else None

    # Hedef dizini garantiye al
    cikis.parent.mkdir(parents=True, exist_ok=True)

    # Aynı dosya üzerine yazılıyorsa yedek oluştur
    if yedekle and giris and (ayni_dosya_mi(giris, cikis) or (cikis.exists() and giris == cikis)):
        yedek_al(cikis)
    elif yedekle and cikis.exists() and (giris is None or ayni_dosya_mi(giris, cikis)):
        yedek_al(cikis)

    # Geçici dosyaya atomik kayıt
    fd, temp_path = tempfile.mkstemp(
        dir=str(cikis.parent),
        prefix=".tmp_pafta_",
        suffix=".dxf",
    )
    os.close(fd)

    try:
        if getattr(doc, "dxfversion", "AC1015") < "AC1015":
            doc.dxfversion = "AC1015"
        doc.saveas(temp_path)

        # Doğrulama: dosya yazıldı mı ve boş değil mi?
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise IOError(f"Geçici dosya oluşturulamadı veya boş: {temp_path}")

        # Atomik yer değiştirme (POSIX ve modern Windows'ta atomiktir)
        os.replace(temp_path, str(cikis))
    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise

    return cikis
