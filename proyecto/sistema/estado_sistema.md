# Estado del sistema

> Memoria de **CONSTRUCCIÓN**: qué piezas de la herramienta LITREV-AI están construidas. No
> describe ninguna revisión temática (eso vive en `proyecto/revision/estado_revision.md`). Se
> actualiza al cerrar una sesión de construcción/configuración del sistema.

**Versión del framework:** 3.0
**Última sesión de construcción:** 003 (2026-06-25) — separación de la memoria en dos ámbitos (sistema/revision)

## Qué está construido
| Componente | Estado | Notas |
|------------|--------|-------|
| Fase 0 — Definición de la revisión | construida | `framework/fase0_definicion.md` (protocolo guiado) |
| Fase 1 — Recuperación y selección | construida | scripts `01–05`; **no probada en vivo** (ver I1) |
| Fase 2 — Procesamiento y auditoría | se construye en otro sistema | aquí solo `01_convertir_markdown.py` |
| Fase 3 — Síntesis y reportes | pendiente | |
| Librería `litrev_core` | construida | config, log, io, apis, prioridad, estado, descarga |
| Guarda de configuración | construida | `revisar_configuracion()` (D5) |
| Memoria sistema/revisión | construida | hook SessionStart con detección de ámbito; referencias y plantillas por ámbito completas (D7) |

## Pendientes de construcción / validación
- Validar la cascada de descarga contra red real (incidencia I1).
- Fase 2 y 3 las lleva otro sistema (fuera de este repo de construcción).

## Decisiones de construcción
Ver `proyecto/sistema/registro_sistema.md` (D0–D7) e incidencias (I1–I2).
