"""
Fase 1 · Paso 2 — Clasificación de prioridad (parte regex del híbrido).

Aplica las reglas de config/prioridad.yaml a cada candidato y asigna un
nivel (P0–P4), una razón, un score continuo (0–100) y una confianza.
Los casos en zona gris (franja de score, señales en conflicto, sin texto)
se marcan como DUDOSOS y se vuelcan a un archivo aparte para que Claude
los desempate leyendo título+abstract (parte LLM del híbrido).

Uso:  python fase1_seleccion/02_clasificar_prioridad.py
Salidas:
  data/candidatos/candidatos_clasificados.json
  data/candidatos/revision_llm_pendiente.json   (solo los dudosos)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litrev_core import config
from litrev_core.estado import registrar_paso
from litrev_core.io import cargar_json, guardar_json
from litrev_core.log import banner, get_logger
from litrev_core.prioridad import build_motor

log = get_logger()


def main():
    banner(log, "LITREV-AI · Fase 1 · Clasificación de prioridad")

    paths = config.get_paths()
    if not paths.candidatos_busqueda.exists():
        log.info(f"No encontrado: {paths.candidatos_busqueda}")
        log.info("Ejecutar primero: python fase1_seleccion/01_buscar.py")
        sys.exit(1)

    faltan = config.configuracion_incompleta(["proyecto", "prioridad"])
    if faltan:
        log.info("\n⚠ La configuración de prioridad no está lista (se clasificaría todo igual).")
        log.info("  Completa la Fase 0 (framework/fase0_definicion.md):")
        for p in faltan:
            log.info(f"  - {p}")
        sys.exit(1)

    motor = build_motor()
    articulos = cargar_json(paths.candidatos_busqueda)

    distribucion = {nivel: 0 for nivel in motor.niveles}
    dudosos = []

    for art in articulos:
        r = motor.clasificar(art)
        art["prioridad"] = r.prioridad
        art["prioridad_auto"] = r.prioridad
        art["prioridad_razon"] = r.razon
        art["prioridad_score"] = r.score
        art["prioridad_confianza"] = r.confianza
        art["prioridad_fuente"] = "regex"
        distribucion[r.prioridad] = distribucion.get(r.prioridad, 0) + 1

        if r.confianza == "dudosa":
            dudosos.append({
                "id_candidato": art.get("id_candidato", ""),
                "titulo": art.get("titulo", ""),
                "abstract": art.get("abstract", ""),
                "prioridad_auto": r.prioridad,
                "razon_auto": r.razon,
                "score": r.score,
                "vocabularios_activos": [k for k, v in r.flags.items() if v],
                # Claude rellena estos tras leer título+abstract:
                "prioridad_llm": None,
                "razon_llm": None,
            })

    guardar_json(paths.candidatos_clasificados, articulos, backup=True)
    guardar_json(paths.revision_llm_pendiente, dudosos)

    total = len(articulos)
    log.info("\nDistribución de prioridad (preliminar, regex):")
    for nivel in motor.niveles:
        n = distribucion.get(nivel, 0)
        etiqueta = (motor.niveles[nivel] or {}).get("label", "")
        pct = (n / total * 100) if total else 0
        log.info(f"  {nivel} {etiqueta:<18} {n:>4}  ({pct:.1f}%)")
    log.info(f"  {'Total':<23} {total:>4}")
    log.info(f"\n  Dudosos para desempate por LLM: {len(dudosos)}")

    log.info("\n" + "=" * 64)
    log.info(f"Clasificados: {paths.candidatos_clasificados}")
    log.info(f"Dudosos:      {paths.revision_llm_pendiente}")
    log.info("=" * 64)
    if dudosos:
        log.info("\nSiguiente paso (dentro de Claude Code, sin API):")
        log.info("  Claude lee revision_llm_pendiente.json, reclasifica cada caso contra")
        log.info("  los criterios de config/proyecto.yaml y actualiza candidatos_clasificados.json.")
        log.info("  Ver framework/fase1_seleccion.md → 'Desempate por LLM'.")

    registrar_paso(paths.estado_json, "fase1", "clasificar",
                   {"total": total, "dudosos": len(dudosos), "distribucion": distribucion})


if __name__ == "__main__":
    main()
