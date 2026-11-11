import subprocess
import sys

TESTLER = [
    ("eski: test_kat", ["test_kat.py"]),
    ("eski: test_gercekci", ["test_gercekci.py"]),
    ("hata", ["-m", "testler.test_hata"]),
    ("birim", ["-m", "testler.test_birim"]),
]

basarisiz = 0

for ad, arg in TESTLER:
    r = subprocess.run(
        [sys.executable, *arg],
        capture_output=True,
        text=True
    )
    ok = r.returncode == 0
    print(f"{'OK  ' if ok else 'HATA'} {ad}")

    if not ok:
        basarisiz += 1
        print(r.stdout[-1500:])
        print(r.stderr[-1500:])

print("HEPSİ GEÇTİ" if basarisiz == 0 else f"{basarisiz} MODÜL BAŞARISIZ")
sys.exit(1 if basarisiz else 0)
