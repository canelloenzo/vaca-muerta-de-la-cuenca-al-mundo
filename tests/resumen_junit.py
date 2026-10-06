"""Convierte la salida junit de pytest en un resumen Markdown sin rutas locales ni mensajes de error.

Uso:  python -m pytest -q --junitxml=tests/baseline/ultima.xml
      python tests/resumen_junit.py tests/baseline/ultima.xml tests/baseline/linea_base.md "Título"
"""
import datetime
import platform
import subprocess
import sys
import xml.etree.ElementTree as ET


def main(xml_path, out_path, titulo):
    root = ET.parse(xml_path).getroot()
    casos = []
    for tc in root.iter("testcase"):
        estado = "FAIL" if tc.find("failure") is not None or tc.find("error") is not None else (
            "SKIP" if tc.find("skipped") is not None else "PASS")
        casos.append((tc.get("classname").split(".")[-1], tc.get("name"), estado))
    try:
        commit = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        commit = "(sin git)"
    n = {e: sum(1 for c in casos if c[2] == e) for e in ("PASS", "FAIL", "SKIP")}
    objetivo = [c for c in casos if c[0] == "test_07_estado_objetivo" or "objetivo" in c[1]]
    lineas = [f"# {titulo}", "",
              f"- Fecha: {datetime.date.today().isoformat()} · commit base de la corrida: `{commit}` · "
              f"Python {platform.python_version()}",
              f"- Pruebas: {len(casos)} → PASS {n['PASS']} · FAIL {n['FAIL']} · SKIP {n['SKIP']}",
              f"- De las FAIL, pruebas de estado objetivo (esperadas en rojo antes de corregir): "
              f"{sum(1 for c in casos if c[2] == 'FAIL' and (c[0] == 'test_07_estado_objetivo' or 'ducto_logico' in c[1]))}",
              "", "| módulo | prueba | estado |", "|---|---|---|"]
    lineas += [f"| {m} | {t} | {e} |" for m, t, e in casos]
    open(out_path, "w", encoding="utf-8").write("\n".join(lineas) + "\n")
    print(f"{out_path}: PASS {n['PASS']} FAIL {n['FAIL']} SKIP {n['SKIP']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "Resumen de pruebas")
