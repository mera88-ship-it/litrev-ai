# Fase 2 — Procesamiento y auditoría (pendiente de construir)

Toma `data/candidatos/candidatos_aprobados.json` + los Markdown de la Fase 1 y produce una
base de datos auditada.

Pipeline previsto (a portar y depurar desde el proyecto maduro):

```
01_convertir_markdown.py  (CONSTRUIDO) — PDF → Markdown (pymupdf4llm)
  → P1–P5 (extracción interna en Claude Code, artículo por artículo)
  → validación de schema (Pydantic contra JSON Schema congelado)
  → auditoría L1 (determinista) + L2 (semántica)
  → verificación humana (interfaz de dos columnas)
  → migración a DuckDB
  → estandarización dirigida por config
```

La conversión a Markdown abre la Fase 2: es el primer momento del procesamiento (pasar la
literatura a un formato trabajable). El formato (Markdown u otro) es revisable más adelante.

Documentos de framework a crear aquí: `pasada_1..5`, `protocolo_auditoria`,
`estructura_json`, `schema_validacion`. Correcciones clave previstas: schema único congelado
desde el inicio, validación de extensión coherente (150/250 según enfoque en un solo lugar),
transacciones en DuckDB, sin esquemas JSON divergentes.
