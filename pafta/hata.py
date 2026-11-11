from dataclasses import dataclass
from collections import Counter

SIDDET = ("BILGI", "UYARI", "HATA")


@dataclass
class Bulgu:
    kod: str
    siddet: str
    mesaj: str
    konum: tuple | None = None
    handle: str | None = None
    kat: str | None = None

    def __post_init__(self):
        if self.siddet not in SIDDET:
            raise ValueError(f"Gecersiz siddet: {self.siddet}")


def ozet(bulgular):
    sayac = Counter(b.siddet for b in bulgular)
    return {s: sayac.get(s, 0) for s in SIDDET}
