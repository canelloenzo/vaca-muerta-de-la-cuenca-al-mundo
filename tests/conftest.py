import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import helpers as H  # noqa: E402


def pytest_collection_modifyitems(config, items):
    for item in items:
        if "raw" in item.fixturenames or "vm" in item.fixturenames or "vm_raw_data" in item.fixturenames:
            item.add_marker(pytest.mark.slow)


@pytest.fixture(scope="session")
def raw():
    d = H.raw_dir()
    if not (d / H.RAW_NC).exists():
        pytest.skip(f"No se encontró raw/ en {d}. Ver README (sección Cómo correr las pruebas): VM_DATA_ROOT / VM_RAW_DIR.")
    return d


@pytest.fixture(scope="session")
def clean_ok():
    d = H.clean_dir()
    if not (d / "fact_produccion_pozo_mes_vaca_muerta.csv").exists():
        pytest.skip(f"No se encontró clean/ en {d}. Generarlo con scripts/01..08 o fijar VM_CLEAN_DIR.")
    return d


@pytest.fixture(scope="session")
def vm_raw_data(raw):
    return H.vm_raw()


@pytest.fixture(scope="session")
def vm(vm_raw_data):
    return H.vm_dedup(vm_raw_data)


@pytest.fixture(scope="session")
def export_raw(raw):
    return H.p21_export()


@pytest.fixture(scope="session")
def util(raw):
    return H.util_ducto_mes()


@pytest.fixture(scope="session")
def DATA():
    return H.html_data()
