"""
Fase 1 · Paso 1 — Búsqueda de candidatos en APIs académicas.

Lee las queries y filtros de config/busqueda.yaml (NO hardcodeadas),
consulta OpenAlex y Semantic Scholar, deduplica, filtra por idioma/año,
enriquece con Unpaywall y guarda el corpus bruto de candidatos.

Uso:  python fase1_seleccion/01_buscar.py
Salida: data/candidatos/candidatos_busqueda.json
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litrev_core import apis, config
from litrev_core.estado import registrar_paso
from litrev_core.io import generar_id, guardar_json
from litrev_core.log import banner, get_logger

log = get_logger()


def deduplicar(articulos):
    log.info("\n=== Deduplicación ===")
    vistos, unicos = set(), []
    for art in articulos:
        clave = art.get("doi") or (art.get("titulo", "") or "").lower().strip()
        if clave and clave in vistos:
            continue
        if clave:
            vistos.add(clave)
        unicos.append(art)
    log.info(f"  {len(articulos)} brutos → {len(unicos)} únicos "
             f"({len(articulos) - len(unicos)} duplicados)")
    return unicos


def filtrar(articulos, filtros):
    log.info("\n=== Filtrado básico ===")
    idiomas = filtros.get("idiomas")
    anio_min = filtros.get("anio_minimo")
    salida = []
    for art in articulos:
        if idiomas and art.get("idioma") and art["idioma"] not in idiomas:
            continue
        if anio_min and art.get("anio") and art["anio"] < anio_min:
            continue
        salida.append(art)
    log.info(f"  {len(articulos)} → {len(salida)} tras filtro")
    return salida


def main():
    banner(log, "LITREV-AI · Fase 1 · Búsqueda de candidatos")

    faltan = config.configuracion_incompleta(["proyecto", "busqueda"])
    if faltan:
        log.info("\n⚠ El proyecto no está listo para buscar. Completa la Fase 0 (definición):")
        for p in faltan:
            log.info(f"  - {p}")
        log.info("  Ver framework/fase0_definicion.md.")
        sys.exit(1)

    cfg = config.cfg_busqueda()
    cred = config.credenciales()
    paths = config.get_paths()
    paths.crear()

    filtros = cfg.get("filtros", {}) or {}
    oa_cfg = cfg.get("openalex", {}) or {}
    ss_cfg = cfg.get("semantic_scholar", {}) or {}

    oa = apis.buscar_openalex(
        oa_cfg.get("queries", []), oa_cfg.get("max_por_query", 100),
        filtros, cred["openalex_email"], cred["openalex_api_key"], log)
    ss = apis.buscar_semantic_scholar(
        ss_cfg.get("queries", []), ss_cfg.get("max_por_query", 100),
        filtros.get("anio_minimo"), cred["semantic_scholar_api_key"], log)

    todos = oa + ss
    log.info(f"\nTotal bruto: {len(todos)}")
    todos = deduplicar(todos)
    todos = filtrar(todos, filtros)

    if (cfg.get("unpaywall", {}) or {}).get("habilitado", True):
        apis.enriquecer_con_unpaywall(todos, cred["unpaywall_email"], log)

    for i, art in enumerate(todos, 1):
        art["id_candidato"] = generar_id(i, art)

    guardar_json(paths.candidatos_busqueda, todos, backup=True)

    con_pdf = sum(1 for a in todos if a.get("pdf_url"))
    log.info("\n" + "=" * 64)
    log.info(f"Candidatos guardados: {len(todos)}  (con PDF: {con_pdf} | sin PDF: {len(todos) - con_pdf})")
    log.info(f"Archivo: {paths.candidatos_busqueda}")
    log.info("=" * 64)

    registrar_paso(paths.estado_json, "fase1", "buscar",
                   {"candidatos": len(todos), "con_pdf": con_pdf})


if __name__ == "__main__":
    main()
