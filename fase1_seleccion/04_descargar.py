"""
Fase 1 · Paso 4 — Descarga de PDFs (cascada multi-fuente).

Recupera los PDFs de los candidatos cuyos niveles de prioridad estén en
config/proyecto.yaml (descarga.prioridades_a_descargar), probando una
cadena de fuentes de acceso abierto legal. Descarga en paralelo, valida
que sea un PDF real y lleva un libro de descargas para reanudar.

Uso:
  python fase1_seleccion/04_descargar.py          # según prioridades de config
  python fase1_seleccion/04_descargar.py --all     # todos los candidatos
Salidas:
  data/pdfs/*.pdf
  data/candidatos/descargas.json   (libro de descargas; permite reanudar)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litrev_core import config
from litrev_core.descarga import Contexto, descargar_corpus
from litrev_core.estado import registrar_paso
from litrev_core.io import cargar_json
from litrev_core.log import banner, get_logger

log = get_logger()


def main():
    banner(log, "LITREV-AI · Fase 1 · Descarga de PDFs (cascada)")
    modo_all = "--all" in sys.argv[1:]

    paths = config.get_paths()
    fuente = paths.candidatos_clasificados if paths.candidatos_clasificados.exists() \
        else paths.candidatos_busqueda
    if not fuente.exists():
        log.info("No hay candidatos. Ejecutar 01_buscar.py (y 02_clasificar_prioridad.py).")
        sys.exit(1)

    articulos = cargar_json(fuente)
    cred = config.credenciales()
    desc_cfg = config.cfg_proyecto().get("descarga", {}) or {}
    prioridades = desc_cfg.get("prioridades_a_descargar", ["P0", "P1", "P2"])
    min_kb = desc_cfg.get("tamano_minimo_kb", 10)
    workers = desc_cfg.get("workers", 4)

    objetivos = [a for a in articulos
                 if modo_all or not a.get("prioridad") or a["prioridad"] in prioridades]
    log.info(f"Candidatos objetivo: {len(objetivos)} / {len(articulos)}")

    ctx = Contexto(cred=cred, cfg_descarga=desc_cfg, logger=log)
    resumen = descargar_corpus(objetivos, ctx, paths, min_kb, workers=workers)

    log.info("\n" + "=" * 64)
    log.info(f"Recuperados: {resumen.get('ok', 0)}  |  sin encontrar: {resumen.get('no_encontrado', 0)}")
    if resumen.get("por_fuente"):
        detalle = ", ".join(f"{k}: {v}" for k, v in resumen["por_fuente"].items())
        log.info(f"Por fuente: {detalle}")
    log.info("=" * 64)

    registrar_paso(paths.estado_json, "fase1", "descargar", resumen)


if __name__ == "__main__":
    main()
