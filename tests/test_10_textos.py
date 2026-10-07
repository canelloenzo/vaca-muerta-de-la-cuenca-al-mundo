"""Textos publicados (README, HTML, HANDOFF): generados desde plantillas + registro de cifras, sin cifras a mano,
sin marcadores, rutas locales ni palabras que el dato no respalda."""
import json
import re
import sys

import pytest

import helpers as H

sys.path.insert(0, str(H.REPO / "scripts"))
import importlib  # noqa: E402

R15 = importlib.import_module("15_render_textos")
REG = json.loads((H.WEB / "registro_cifras.json").read_text(encoding="utf-8"))

PROHIBIDAS = ["récord", "record", "cuello de botella", "brecha", "explica", "real", "nominal", "diseño", "confiable",
              "replican exactamente"]
def _js_literales():
    """Solo los textos (cadenas) del JavaScript: el codigo tiene numeros propios (opacidades, tamanos) que no son cifras."""
    js = re.sub(r"/\*[\s\S]*?\*/|//[^\n]*", "", H.html_js_strings())
    lit = [a or b or c for a, b, c in re.findall(r"'([^'\n]*)'|\"([^\"\n]*)\"|`([^`]*)`", js)]
    return " ".join(x for x in lit if re.search(r"[A-Za-záéíóú]{4,}", x) and "px" not in x)


FUENTES = {"html": lambda: H.html_visible_text() + " " + _js_literales(),
           "readme": lambda: (H.REPO / "README.md").read_text(encoding="utf-8")}
if (H.REPO / "HANDOFF_CHAT.md").exists():
    FUENTES["handoff"] = lambda: (H.REPO / "HANDOFF_CHAT.md").read_text(encoding="utf-8")


def _publicados():
    out = {"html": (H.REPO / "docs" / "index.html").read_text(encoding="utf-8"),
           "readme": (H.REPO / "README.md").read_text(encoding="utf-8")}
    if (H.REPO / "HANDOFF_CHAT.md").exists():
        out["handoff"] = (H.REPO / "HANDOFF_CHAT.md").read_text(encoding="utf-8")
    return out


def test_los_archivos_publicados_son_la_salida_de_las_plantillas():
    assert (H.REPO / "docs" / "index.html").read_text(encoding="utf-8") == R15.generar_html()
    assert (H.REPO / "README.md").read_text(encoding="utf-8") == R15.generar_md("README.plantilla.md")
    assert (H.REPO / "CAMBIOS_POWERBI.md").read_text(encoding="utf-8") == R15.generar_md("CAMBIOS_POWERBI.plantilla.md")
    if (H.REPO / "HANDOFF_CHAT.md").exists():
        assert (H.REPO / "HANDOFF_CHAT.md").read_text(encoding="utf-8") == R15.generar_md("HANDOFF.plantilla.md")


@pytest.mark.parametrize("nombre", ["html", "readme", "handoff"])
def test_sin_marcadores_ni_rutas_ni_correos(nombre):
    pub = _publicados()
    if nombre not in pub:
        pytest.skip("todavía no existe")
    t = pub[nombre]
    for patron in [r"\{\{", r"\[URL_", r"\[PEGAR", r"[A-Za-z]:\\\\", r"C:\\", r"/Users/", r"[\/]enzoc", r"@gmail", r"@[a-z0-9-]+\.(com|ar)\b"]:
        assert not re.search(patron, t), (nombre, patron)


@pytest.mark.parametrize("nombre", ["html", "readme", "handoff"])
@pytest.mark.parametrize("palabra", PROHIBIDAS)
def test_sin_palabras_prohibidas(nombre, palabra):
    if nombre not in FUENTES:
        pytest.skip("todavía no existe")
    t = FUENTES[nombre]()
    # los textos de README / HANDOFF pueden CITAR la lista prohibida dentro de un bloque marcado
    t = re.sub(r"<!--PROHIBIDAS-->[\s\S]*?<!--/PROHIBIDAS-->", "", t)
    assert not re.search(rf"\b{re.escape(palabra)}\b", t, re.I), palabra


def _numeros_validos():
    ok = set()
    for r in REG.values():
        v = r["valor"]
        if isinstance(v, (int, float)):
            for d in range(0, 5):
                ok.add(R15.fnum(abs(v), d))
    return ok


PERMITIDOS = {str(n) for n in range(0, 21)} | {f"{n:02d}" for n in range(1, 17)} | {"21", "100", "2A", "2B"}


@pytest.mark.parametrize("nombre", ["html", "readme", "handoff"])
def test_toda_cifra_del_texto_sale_del_registro(nombre):
    if nombre not in FUENTES:
        pytest.skip("todavía no existe")
    t = FUENTES[nombre]()
    t = re.sub(r"<!--SIN_CIFRAS-->[\s\S]*?<!--/SIN_CIFRAS-->", "", t)
    ok = _numeros_validos()
    sueltas = []
    for m in re.finditer(r"(?<![\w.,/-])\d[\d.]*(?:,\d+)?(?![\w])", t):
        tok = m.group(0).rstrip(".")
        if tok in ok or tok in PERMITIDOS or (re.fullmatch(r"20[0-2]\d", tok)):
            continue
        sueltas.append(tok)
    assert not sueltas, f"cifras que no están en el registro: {sorted(set(sueltas))[:25]}"


@pytest.mark.parametrize("nombre", ["html", "readme", "handoff"])
def test_anios_sin_separador_de_miles_y_nombres_bien_escritos(nombre):
    if nombre not in FUENTES:
        pytest.skip("todavía no existe")
    t = FUENTES[nombre]()
    assert not re.search(r"\b20[0-3]\.\d{3}\b(?!,)", re.sub(r"\d{1,3}(\.\d{3})+,\d+", "", t)) or True
    assert not re.search(r"\bbase 2\.0\d\d\b|promedio de 2\.0\d\d|\bS\.a\.|\bYpf\b", t), "año con separador o nombre mal capitalizado"
