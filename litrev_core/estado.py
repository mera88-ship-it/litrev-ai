"""
litrev_core.estado — Registro de progreso legible por máquina (estado.json).

Complementa a proyecto/revision/estado_revision.md (humano). Cada paso del pipeline
registra cuándo terminó y con qué conteos, para que los scripts puedan
verificar precondiciones y para tener un rastro automático del avance.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from litrev_core.io import cargar_json, guardar_json


def leer_estado(estado_path: Path) -> dict:
    if Path(estado_path).exists():
        try:
            return cargar_json(estado_path)
        except (ValueError, OSError):
            return {}
    return {}


def registrar_paso(estado_path: Path, fase: str, paso: str, datos: dict) -> None:
    """Anota la finalización de un paso con marca temporal y conteos."""
    estado = leer_estado(estado_path)
    estado.setdefault(fase, {})
    estado[fase][paso] = {
        "completado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **datos,
    }
    guardar_json(estado_path, estado)
