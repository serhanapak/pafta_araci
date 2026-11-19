import os
import shutil
import stat
import tempfile
from pathlib import Path

import ezdxf


def ayni_dosya_mi(yol1, yol2):
    """İki dosya yolunun aynı fiziksel dosyaya işaret edip etmediğini kontrol eder."""
    if not yol1 or not yol2:
        return False
    return Path(yol1).resolve() == Path(yol2).resolve()


def yedek_al(dosya_yolu):
    """
    Kaynak dosyanın üzerine yazmadan yedek oluşturur.
    Mevcut yedeklerin üzerine yazılmaz; gerektiğinde numara eklenir.
    """
    kaynak = Path(dosya_yolu)
    if not kaynak.exists() or not kaynak.is_file():
        return None

    temel = Path(str(kaynak) + ".bak")
    hedef = temel
    sira = 1

    while hedef.exists():
        hedef = Path(f"{temel}.{sira}")
        sira += 1

    fd = os.open(
        str(hedef),
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o600,
    )

    try:
        with os.fdopen(fd, "wb") as hedef_dosya:
            with kaynak.open("rb") as kaynak_dosya:
                shutil.copyfileobj(kaynak_dosya, hedef_dosya)

            hedef_dosya.flush()
            os.fsync(hedef_dosya.fileno())

        shutil.copystat(kaynak, hedef)

    except Exception:
        try:
            hedef.unlink(missing_ok=True)
        except OSError:
            pass
        raise

    return hedef


def guvenli_kaydet(doc, cikis_yolu, giris_yolu=None, yedekle=True):
    """
    DXF'yi geçici dosyaya kaydeder, yeniden açarak doğrular,
    gerekli durumda mevcut hedefi yedekler ve atomik olarak değiştirir.

    Yalnızca giriş ve çıkış aynı dosyaysa veya giriş belirtilmemişse
    mevcut hedef için otomatik yedek oluşturur.

    Var olan hedefin dosya izinlerini ve bellek içindeki DXF sürümünü korur.
    """
    cikis = Path(cikis_yolu).resolve()
    giris = Path(giris_yolu).resolve() if giris_yolu else None

    cikis.parent.mkdir(parents=True, exist_ok=True)

    mevcut_izinler = (
        stat.S_IMODE(cikis.stat().st_mode)
        if cikis.exists()
        else None
    )

    yedek_gerekli = (
        yedekle
        and cikis.exists()
        and (giris is None or ayni_dosya_mi(giris, cikis))
    )

    fd, temp_path = tempfile.mkstemp(
        dir=str(cikis.parent),
        prefix=".tmp_pafta_",
        suffix=".dxf",
    )
    os.close(fd)

    try:
        orijinal_surumu = getattr(doc, "dxfversion", None)

        try:
            if orijinal_surumu is not None and orijinal_surumu < "AC1015":
                doc.dxfversion = "AC1015"

            doc.saveas(temp_path)

        finally:
            # Kaydetme başarılı veya başarısız olsa da belge sürümünü geri yükle.
            if orijinal_surumu is not None:
                doc.dxfversion = orijinal_surumu

        if not os.path.isfile(temp_path) or os.path.getsize(temp_path) == 0:
            raise IOError("Geçici DXF dosyası oluşturulamadı veya boş.")

        # Dosyanın gerçekten DXF olarak açılabildiğini doğrula.
        dogrulanan_doc = ezdxf.readfile(temp_path)

        if dogrulanan_doc is None:
            raise IOError("Geçici DXF doğrulanamadı.")

        # Hedefi ancak yeni dosya doğrulandıktan sonra yedekle.
        if yedek_gerekli:
            yedek_al(cikis)

        # Var olan hedefin dosya izinlerini koru.
        if mevcut_izinler is not None:
            os.chmod(temp_path, mevcut_izinler)

        # Aynı dosya sistemindeki atomik değiştirme.
        os.replace(temp_path, cikis)

    except Exception:
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        raise

    return cikis
