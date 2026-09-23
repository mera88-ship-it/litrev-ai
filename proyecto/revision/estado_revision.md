# Estado de la revisión

> Memoria de **EJECUCIÓN**: progreso y corpus de la revisión temática actual. Se actualiza al
> cierre de cada sesión de ejecución. El rastro automático legible por máquina está en
> `data/estado.json` (lo escriben los scripts). Cómo se construyó la herramienta está aparte, en
> `proyecto/sistema/estado_sistema.md`.

**Tema:** [TEMA POR DEFINIR]
**Última sesión de revisión:** (ninguna aún)
**Estado:** sin tema definido. Ejecutar la Fase 0 (`framework/fase0_definicion.md`) para empezar.

## Progreso de la Fase 1 — Recuperación y selección
| # | Paso | Script | Estado | Notas |
|---|------|--------|--------|-------|
| 1 | Búsqueda en APIs | `fase1_seleccion/01_buscar.py` | pendiente | |
| 2 | Clasificación de prioridad | `fase1_seleccion/02_clasificar_prioridad.py` | pendiente | |
| 2b | Desempate de dudosos (LLM) | Claude Code | pendiente | |
| 3 | Excel de candidatos | `fase1_seleccion/03_generar_excel.py` | pendiente | |
| 3b | Revisión humana (Excel) | investigador | pendiente | |
| 4 | Descarga de PDFs | `fase1_seleccion/04_descargar.py` | pendiente | |
| 5 | Aprobación (cierre) | `fase1_seleccion/05_aprobar.py` | pendiente | |

## Progreso de la Fase 2 — Procesamiento y auditoría
| # | Paso | Script | Estado | Notas |
|---|------|--------|--------|-------|
| 1 | Conversión a Markdown | `fase2_procesamiento/01_convertir_markdown.py` | pendiente | |
| 2+ | Extracción / validación / auditoría | (se construye en otro sistema) | pendiente | |

## Corpus
| Métrica | Valor |
|---------|-------|
| Candidatos brutos | 0 |
| Candidatos únicos | 0 |
| Clasificados | 0 |
| Dudosos (desempate LLM) | 0 |
| Aprobados | 0 |
| PDFs descargados | 0 |
| Markdown convertidos | 0 |

## Distribución de prioridad
| Nivel | N | % |
|-------|---|---|
| P0 | 0 | 0% |
| P1 | 0 | 0% |
| P2 | 0 | 0% |
| P3 | 0 | 0% |
| P4 | 0 | 0% |
