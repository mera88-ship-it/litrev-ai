"""
litrev_core.log — Logging y encoding centralizados.

Resuelve la incidencia recurrente de Windows (consola cp1252 que rompe
los acentos) en un solo lugar, en vez de repetir
`sys.stdout.reconfigure(...)` en cada script.
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

_IO_LISTO = False


def setup_io() -> None:
    """Fuerza UTF-8 en stdout/stderr. Idempotente. Llamar al inicio de cada script."""
    global _IO_LISTO
    if _IO_LISTO:
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (ValueError, OSError):
                pass
    _IO_LISTO = True


def get_logger(nombre: str = "litrev") -> logging.Logger:
    """Logger con formato uniforme. Evita handlers duplicados."""
    setup_io()
    logger = logging.getLogger(nombre)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


def banner(logger: logging.Logger, titulo: str) -> None:
    """Encabezado visual uniforme para los scripts."""
    linea = "=" * 64
    logger.info(linea)
    logger.info(titulo)
    logger.info(linea)


def timestamp() -> str:
    """Marca temporal legible (hora local). Se evita en módulos puros; aquí es seguro."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def append_log_sesion(logs_dir: Path, texto: str) -> Path:
    """
    Añade una entrada con marca temporal al log de sesión del día.
    Devuelve la ruta del archivo. No reemplaza al log manual de cierre
    de sesión (proyecto/<ámbito>/logs/sesion_NNN.md); es un rastro automático.
    """
    logs_dir.mkdir(parents=True, exist_ok=True)
    archivo = logs_dir / f"auto_{datetime.now().strftime('%Y%m%d')}.md"
    with open(archivo, "a", encoding="utf-8") as f:
        f.write(f"\n- **{timestamp()}** — {texto}\n")
    return archivo
