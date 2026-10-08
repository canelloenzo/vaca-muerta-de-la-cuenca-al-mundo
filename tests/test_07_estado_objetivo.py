"""Estado final deseado tras corregir los hallazgos F1-F19 (decisiones D1-D3).

Estas pruebas codifican lo que el proyecto DEBE cumplir cuando termine la corrección. En la línea de base
(antes de cambiar nada) se espera que fallen; cada fase las va poniendo en verde. Marcador: `objetivo`.
"""
import json
import re

import pandas as pd
import pytest

import helpers as H

pytestmark = pytest.mark.objetivo

README = lambda: (H.REPO / "README.md").read_text(encoding="utf-8")
DAX = lambda: (H.REPO / "powerbi" / "dax_measures.md").read_text(encoding="utf-8")
DICC = lambda: (H.REPO / "documentacion" / "diccionario_datos.md").read_text(encoding="utf-8")


def _hay(texto, patron):
    return re.search(patron, texto, re.I) is not None


# ---------------- Datos publicados (D1, D3) ----------------
def test_f1_serie_exportacion_cuenca_neuquina_existe():
    p = H.WEB / "exportacion_cuenca_neuquina_mensual.csv"
    assert p.exists(), "falta data/web/exportacion_cuenca_neuquina_mensual.csv"
    d = pd.read_csv(p)
    assert {"fecha", "exportacion_terminales_bbl_dia"} <= set(d.columns)


def test_f1_comparacion_cierra_en_dic_2025():
    p = H.WEB / "comparacion_produccion_exportacion.csv"
    assert p.exists(), "falta data/web/comparacion_produccion_exportacion.csv"
    d = pd.read_csv(p)
    assert d.fecha.max() == "2025-12-01"


def test_f1_indice_con_base_documentada_y_sensibilidad():
    k = H.web_json("kpis_resumen.json")
    assert k.get("indice_anio_base") == 2022
    assert set(k.get("indice_sensibilidad_bases", [])) == {2021, 2022, 2023}


def test_f6_tarjeta_produccion_jun_2026_rotulada():
    k = H.web_json("kpis_resumen.json")
    assert k["fecha_ultimo_mes_produccion"] == "2026-06-01"
    assert "no convencional" in k.get("produccion_alcance", "").lower()


def test_f7_serie_nacional_muestra_no_identificado():
    p = H.WEB / "exportacion_nacional_por_terminal_anual.csv"
    assert p.exists()
    d = pd.read_csv(p)
    assert "volumen_no_identificado_m3" in d.columns


def test_f8_concentracion_por_cargador_publicada():
    k = H.web_json("kpis_resumen.json")
    assert "concentracion_top3_cargadores_pct_2020_2025" in k
    assert "concentracion_top3_operadores_terminal_pct_2020_2025" in k


# ---------------- Ductos (D2, F2-F5) ----------------
def test_f2_no_se_publica_171_de_vmoc(DATA):
    assert "171" not in H.html_visible_text()
    assert not any("VMOC" in r["d"] for r in DATA.get("ductos_util", []))


def test_f4_html_no_dice_85_sin_capacidad():
    t = H.html_visible_text()
    assert not _hay(t, r"85 ductos sin dato de capacidad") and not _hay(t, r"los otros 85")


def test_f2_utilizacion_usa_solo_liquidos(clean_ok):
    c = H.clean("fact_capacidad_ductos.csv")
    assert {"volumen_liquidos", "volumen_segmento_mas_cargado", "capacidad_dudosa", "motivo_capacidad_dudosa"} <= set(c.columns)


def test_f3_exclusion_por_ducto_anio(clean_ok):
    c = H.clean("fact_capacidad_ductos.csv")
    assert "capacidad_dudosa" in c.columns
    # el ducto 329 (mezcla de gas) debe tener años válidos: ya no se excluye entero
    d329 = c[c.idducto == 329]
    assert len(d329) > 0 and (~d329.capacidad_dudosa.astype(bool)).any()


# ---------------- Textos (F7, F10, F11, limitaciones) ----------------
def test_html_tiene_seccion_limitaciones():
    assert _hay(H.html_visible_text(), r"\bLimitaciones\b")


def test_readme_tiene_limitaciones_y_cobertura_por_serie():
    t = README()
    assert _hay(t, r"##\s*Limitaciones") and _hay(t, r"cobertura")


def test_readme_explica_como_conseguir_raw_y_correr_pruebas():
    t = README()
    assert "VM_DATA_ROOT" in t and _hay(t, r"pytest")


def test_f7_html_rotula_volumen_sin_pais():
    assert _hay(H.html_visible_text() + H.html_js_strings(), r"no identificado|sin pa[ií]s")


@pytest.mark.parametrize("frase", ["explica buena parte", "capacidad real", "replican exactamente", "capacidad nominal",
                                   "por encima de su capacidad de diseño", "cuello de botella"])
def test_f10_sin_lenguaje_causal_sin_evidencia(frase):
    corpus = H.html_visible_text() + H.html_js_strings() + README()
    assert not _hay(corpus, re.escape(frase)), frase


def test_f17_no_dice_238_convencionales():
    for t in (README(), DICC(), (H.REPO / "documentacion" / "historico" / "RESUMEN_PROYECTO.md").read_text(encoding="utf-8")):
        assert not _hay(t, r"238\s+(pozos\s+)?convencionales")


# ---------------- Power BI / DAX (F12, F16) ----------------
def test_f12_dax_sin_allexcept_con_tabla():
    codigo = "\n".join(re.findall(r"```dax\n(.*?)```", DAX(), re.S))           # solo los bloques de código, no las notas
    assert "ALLEXCEPT(Fact_MovimientosExportacion, Dim_Pais)" not in codigo


def test_f12_dax_balance_corrige_el_signo():
    t = DAX()
    i = t.index("% Exportado sobre Produccion")
    assert "ABS(" in t[i:i + 900]


def test_f16_dax_no_cita_1660():
    assert "1.660%" not in DAX() and "1.761%" in DAX()


def test_f19_sin_cifras_de_vmos_sin_fuente():
    corpus = README() + DAX() + DICC()
    assert not _hay(corpus, r"180\.000-190\.000|550\.000-690\.000")
