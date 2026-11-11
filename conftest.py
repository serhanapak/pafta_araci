import os
import subprocess
import sys
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parent


def _betik_calistir(betik, cwd, *arg):
    # kök dizindeki betiği verilen dizinde çalıştırır; DXF çıktıları cwd'ye yazılır
    r = subprocess.run(
        [sys.executable, str(KOK / betik), *arg],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert r.returncode == 0, f"{betik} hata verdi (çıkış kodu {r.returncode}):\n{r.stderr}"
    return r.stdout


@pytest.fixture(scope="session")
def calistir():
    return _betik_calistir
