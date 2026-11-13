APPID_VARSAYILAN = "PAFTA_ARACI"
ISARET_AKS = "URETILEN_AKS_V1"
ISARET_KIRIS_EKSEN = "URETILEN_KIRIS_EKSEN_V1"


def appid_tanimla(doc, appid=APPID_VARSAYILAN):
    """DXF belgesine APPID kaydı ekler (eğer yoksa)."""
    if appid not in doc.appids:
        doc.appids.new(appid)


def isaretle(entity, etiket, appid=APPID_VARSAYILAN):
    """Bir DXF nesnesine XDATA etiketi ekler."""
    entity.set_xdata(appid, [(1000, etiket)])
    return entity


def isaretli_mi(entity, etiket=None, appid=APPID_VARSAYILAN):
    """
    Bir nesnenin belirtilen XDATA etiketine sahip olup olmadığını kontrol eder.
    etiket None ise yalnızca appid varlığına bakar.
    """
    if not entity.has_xdata(appid):
        return False
    if etiket is None:
        return True
    try:
        return any(
            tag.code == 1000 and tag.value == etiket
            for tag in entity.get_xdata(appid)
        )
    except Exception:
        return False


def uretilenleri_temizle(msp, etiket=None, appid=APPID_VARSAYILAN):
    """
    Yalnızca belirtilen XDATA etiketine sahip nesneleri model alanından siler.
    Kullanıcının elle çizdiği nesnelere asla dokunmaz.
    Silinen nesne adedini döndürür.
    """
    silinen = 0
    for entity in list(msp):
        if isaretli_mi(entity, etiket=etiket, appid=appid):
            msp.delete_entity(entity)
            silinen += 1
    return silinen
