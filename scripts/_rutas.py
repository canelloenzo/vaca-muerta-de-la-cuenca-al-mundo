"""Rutas del pipeline. Todos los scripts importan de acá.

Variables de entorno (opcionales):
  VM_DATA_ROOT  carpeta que contiene raw/ y clean/ (por defecto, la raíz del repositorio)
  VM_RAW_DIR    sobreescribe raw/   (solo lectura: ningún script escribe en raw/)
  VM_CLEAN_DIR  sobreescribe clean/ (se crea si no existe)
  VM_WEB_DIR    sobreescribe data/web/ (solo para pruebas de sensibilidad)
Las tablas resumen publicadas se escriben por defecto en data/web/ del repositorio.
"""
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = Path(os.environ.get("VM_DATA_ROOT") or REPO)
RAW = str(Path(os.environ.get("VM_RAW_DIR") or DATA_ROOT / "raw"))
CLEAN = str(Path(os.environ.get("VM_CLEAN_DIR") or DATA_ROOT / "clean"))
WEB = str(Path(os.environ.get("VM_WEB_DIR") or REPO / "data" / "web"))

os.makedirs(CLEAN, exist_ok=True)
os.makedirs(WEB, exist_ok=True)
