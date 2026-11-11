import subprocess
import sys

# kısayol: asıl komut python3 -m pytest -q; çıkış kodu aynen iletilir
if __name__ == "__main__":
    raise SystemExit(subprocess.call([sys.executable, "-m", "pytest", "-q", *sys.argv[1:]]))
