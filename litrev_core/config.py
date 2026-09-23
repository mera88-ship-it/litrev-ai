"""
litrev_core.config — Carga de configuración y rutas.

Fuente única de verdad para:
  - dónde están las cosas (rutas del repo y del corpus),
  - las credenciales (.env),
  - la configuración del proyecto (config/*.yaml).

El corpus vive en data/ por defecto, pero puede reubicarse con la
variable de entorno LITREV_DATA_DIR (p. ej. una carpeta de Google Drive).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import load_dotenv

# Raíz del repositorio = carpeta que contiene litrev_core/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Paths:
    """Todas las rutas del proyecto, derivadas de la raíz y del corpus."""
    project_root: Path
    data_dir: Path
    candidatos_dir: Path
    pdf_dir: Path
    markdown_dir: Path
    json_parciales_dir: Path
    json_finales_dir: Path
    logs_dir: Path

    # Archivos canónicos del flujo (contratos entre pasos/fases)
    @property
    def candidatos_busqueda(self) -> Path:
        return self.candidatos_dir / "candidatos_busqueda.json"

    @property
    def candidatos_clasificados(self) -> Path:
        return self.candidatos_dir / "candidatos_clasificados.json"

    @property
    def revision_llm_pendiente(self) -> Path:
        return self.candidatos_dir / "revision_llm_pendiente.json"

    @property
    def base_candidatos_xlsx(self) -> Path:
        return self.candidatos_dir / "base_candidatos.xlsx"

    @property
    def candidatos_aprobados(self) -> Path:
        return self.candidatos_dir / "candidatos_aprobados.json"

    @property
    def estado_json(self) -> Path:
        return self.data_dir / "estado.json"

    def crear(self) -> None:
        """Crea las carpetas de datos si no existen."""
        for d in (self.candidatos_dir, self.pdf_dir, self.markdown_dir,
                  self.json_parciales_dir, self.json_finales_dir, self.logs_dir):
            d.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_paths() -> Paths:
    data_env = os.getenv("LITREV_DATA_DIR", "").strip()
    data_dir = Path(data_env) if data_env else (PROJECT_ROOT / "data")
    return Paths(
        project_root=PROJECT_ROOT,
        data_dir=data_dir,
        candidatos_dir=data_dir / "candidatos",
        pdf_dir=data_dir / "pdfs",
        markdown_dir=data_dir / "markdown",
        json_parciales_dir=data_dir / "json_parciales",
        json_finales_dir=data_dir / "json_finales",
        logs_dir=PROJECT_ROOT / "proyecto" / "revision" / "logs",
    )


# ── Credenciales (desde .env) ────────────────────────────────────
def credenciales() -> dict:
    return {
        "openalex_email": os.getenv("OPENALEX_EMAIL", ""),
        "openalex_api_key": os.getenv("OPENALEX_API_KEY", ""),
        "semantic_scholar_api_key": os.getenv("SEMANTIC_SCHOLAR_API_KEY", ""),
        "unpaywall_email": os.getenv("UNPAYWALL_EMAIL", ""),
        "core_api_key": os.getenv("CORE_API_KEY", ""),
    }


# ── Configuración del proyecto (config/*.yaml) ───────────────────
def _load_yaml(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró {path.name} en {path.parent}. "
            f"Copiar/editar la configuración antes de ejecutar."
        )
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data or {}


@lru_cache(maxsize=1)
def cfg_proyecto() -> dict:
    return _load_yaml(CONFIG_DIR / "proyecto.yaml")


@lru_cache(maxsize=1)
def cfg_busqueda() -> dict:
    return _load_yaml(CONFIG_DIR / "busqueda.yaml")


@lru_cache(maxsize=1)
def cfg_prioridad() -> dict:
    return _load_yaml(CONFIG_DIR / "prioridad.yaml")


def tema_sin_definir() -> bool:
    """True si el proyecto aún no se ha configurado (Fase 0 pendiente)."""
    nombre = (cfg_proyecto().get("proyecto", {}) or {}).get("nombre", "")
    return "TEMA POR DEFINIR" in nombre


def _es_marcador(valor) -> bool:
    """True si el valor sigue siendo un marcador de plantilla del tipo «[...]».

    Convención del repo: los huecos por completar van entre corchetes. Una query
    o regex reales no quedan envueltas por completo en corchetes (una clase de
    caracteres como «[A-Z]+» termina en «+», no en «]»).
    """
    s = str(valor or "").strip()
    return s.startswith("[") and s.endswith("]")


def revisar_configuracion() -> dict:
    """Diagnóstico de configuración por área (lista vacía = esa área lista).

    Detecta lo que haría correr mal el pipeline: tema sin definir, queries de
    plantilla y vocabularios de prioridad de plantilla. Fuente única de la
    pregunta «¿está listo para correr?»: la usan los scripts 01/02 y la Fase 0.
    """
    problemas = {"proyecto": [], "busqueda": [], "prioridad": []}

    if tema_sin_definir():
        problemas["proyecto"].append(
            "config/proyecto.yaml: el proyecto sigue como «[TEMA POR DEFINIR]». "
            "Ejecuta la Fase 0 (framework/fase0_definicion.md).")

    bs = cfg_busqueda()
    queries = []
    for fuente in ("openalex", "semantic_scholar"):
        queries += (bs.get(fuente, {}) or {}).get("queries", []) or []
    if not queries or any(_es_marcador(q) for q in queries):
        problemas["busqueda"].append(
            "config/busqueda.yaml: faltan queries reales (siguen los marcadores «[query ...]»).")

    pr = cfg_prioridad()
    patrones = []
    for pats in (pr.get("vocabularios", {}) or {}).values():
        patrones += [pats] if isinstance(pats, str) else (pats or [])
    if not patrones or any(_es_marcador(p) for p in patrones):
        problemas["prioridad"].append(
            "config/prioridad.yaml: faltan vocabularios reales (siguen los marcadores «[...]»). "
            "Sin esto, el paso 2 clasificaría todo en un mismo nivel.")

    return problemas


def configuracion_incompleta(areas) -> list:
    """Mensajes de las áreas indicadas que aún no están listas (vacío = todo OK)."""
    prob = revisar_configuracion()
    faltan = []
    for a in areas:
        faltan += prob.get(a, [])
    return faltan
