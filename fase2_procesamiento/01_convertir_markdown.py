"""
Fase 2 · Paso 1 — Conversión a formato trabajable (Markdown).

Primer momento del PROCESAMIENTO de la literatura: convertir los PDFs de
los candidatos aprobados a un formato sobre el que se pueda trabajar de
forma óptima. Hoy se usa Markdown (pymupdf4llm); el formato es revisable
en el futuro sin tocar el resto del pipeline.

Entrada: data/candidatos/candidatos_aprobados.json (contrato de la Fase 1)
Salida:  data/markdown/*.md

Uso:  python fase2_procesamiento/01_convertir_markdown.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from litrev_core import config
from litrev_core.estado import registrar_paso
from litrev_core.io import cargar_json
from litrev_core.log import banner, get_logger

log = get_logger()


def convertir(pdf_path, md_path):
    try:
        import pymupdf4llm
    except ImportError:
        log.info("    pymupdf4llm no instalado (pip install pymupdf4llm).")
        return False, 0
    try:
        texto = pymupdf4llm.to_markdown(str(pdf_path))
    except Exception as e:  # noqa: BLE001 — conversor de terceros; registrar y seguir
        log.info(f"    error de conversión: {e}")
        return False, 0
    vacio = not texto or len(texto.strip()) < 20
    if vacio:
        log.info("    aviso: Markdown casi vacío (probable PDF escaneado sin OCR).")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(texto or "")
    log.info(f"    convertido: {len(texto or '')} caracteres")
    return True, len(texto or "")


def main():
    banner(log, "LITREV-AI · Fase 2 · Conversión a Markdown")

    paths = config.get_paths()
    if not paths.candidatos_aprobados.exists():
        log.info(f"No encontrado: {paths.candidatos_aprobados}")
        log.info("Ejecutar primero la Fase 1 (hasta 05_aprobar.py).")
        sys.exit(1)

    aprobados = cargar_json(paths.candidatos_aprobados)
    paths.markdown_dir.mkdir(parents=True, exist_ok=True)
    log.info(f"Aprobados: {len(aprobados)}")

    convertidos = ya = sin_pdf = vacios = 0
    for art in aprobados:
        aid = art.get("id_candidato", "")
        pdf_path = paths.pdf_dir / f"{aid}.pdf"
        md_path = paths.markdown_dir / f"{aid}.md"
        if not pdf_path.exists():
            sin_pdf += 1
            continue
        if md_path.exists():
            ya += 1
            continue
        log.info(f"\n[{art.get('prioridad', '')}] {aid}")
        ok, n = convertir(pdf_path, md_path)
        if ok:
            convertidos += 1
            if n < 20:
                vacios += 1

    log.info("\n" + "=" * 64)
    log.info(f"Convertidos: {convertidos} | ya existían: {ya} | sin PDF: {sin_pdf} | casi vacíos: {vacios}")
    log.info("=" * 64)
    if vacios:
        log.info("Revisar los casi vacíos: PDF escaneado → requiere OCR antes de extraer.")

    registrar_paso(paths.estado_json, "fase2", "convertir_markdown",
                   {"convertidos": convertidos, "sin_pdf": sin_pdf, "casi_vacios": vacios})


if __name__ == "__main__":
    main()
