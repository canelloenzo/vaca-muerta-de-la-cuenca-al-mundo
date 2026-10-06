"""El HTML abre sin errores de consola en un navegador headless (Chromium), en escritorio y en celular."""
import sys

import pytest

import helpers as H

pytest.importorskip("playwright")
sys.path.insert(0, str(H.REPO / "scripts"))
from verificar_html_headless import verificar  # noqa: E402


@pytest.mark.parametrize("ancho", [1280, 390])
def test_html_sin_errores_de_consola(ancho):
    errores, _, s = verificar(None, ancho)
    assert not errores, errores
    assert s["charts"] == 5 and s["yac"] == 10 and s["marcadores"] == 0
    assert s["scrollW"] <= s["innerW"] + 1, "scroll horizontal"
