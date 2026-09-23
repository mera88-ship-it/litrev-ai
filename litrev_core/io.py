"""
litrev_core.io — Lectura/escritura de JSON segura y utilidades de IDs.

Escritura atómica (tmp + replace) para que una interrupción no deje un
JSON a medias, con respaldo opcional con marca temporal. Resuelve el
riesgo de "se sobrescribe candidatos_busqueda.json sin backup".
"""
from __future__ import annotations

import json
import os
import re
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any


def cargar_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_json(path: Path, data: Any, backup: bool = False) -> None:
    """
    Escribe JSON UTF-8 de forma atómica. Si backup=True y el archivo ya
    existe, conserva una copia con marca temporal antes de reemplazarlo.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if backup and path.exists():
        sello = datetime.now().strftime("%Y%m%d_%H%M%S")
        respaldo = path.with_suffix(f".{sello}.bak{path.suffix}")
        shutil.copy2(path, respaldo)

    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)  # atómico en el mismo sistema de archivos


def primer_apellido(autores: list[str]) -> str:
    if not autores:
        return "SinAutor"
    partes = (autores[0] or "").strip().split()
    return partes[-1] if partes else "SinAutor"


def generar_id(indice: int, articulo: dict) -> str:
    """
    ID canónico ART_NNN_Apellido_Año. El apellido se normaliza a ASCII a
    propósito (los nombres de archivo deben ser portables entre sistemas);
    el dato original con tildes se conserva intacto en los metadatos.
    """
    apellido = primer_apellido(articulo.get("autores", []))
    nfkd = unicodedata.normalize("NFKD", apellido)
    apellido = nfkd.encode("ascii", "ignore").decode("ascii")
    apellido = re.sub(r"[^a-zA-Z]", "", apellido) or "SinAutor"
    anio = articulo.get("anio") or "XXXX"
    return f"ART_{indice:03d}_{apellido}_{anio}"
