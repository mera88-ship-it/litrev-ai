# LITREV-AI — Instrucciones para Claude Code

## Qué es este proyecto

Plantilla reutilizable del sistema **LITREV-AI** para revisión de literatura científica.
El trabajo arranca con una **Fase 0 de definición** y luego **tres fases encadenadas** por un
contrato de datos:

0. **Fase 0 — Definición de la revisión.** Diálogo guiado para fijar tema, objetivos/preguntas,
   objetivo de revisión y criterios de inclusión/exclusión, y derivar de ahí `config/*.yaml`.
   Ver `framework/fase0_definicion.md`.
1. **Fase 1 — Recuperación y selección.** Búsqueda en APIs → deduplicación → filtrado →
   clasificación de prioridad (regex + desempate por LLM) → Excel entregable → descarga de
   PDFs → conversión a Markdown. Termina cuando el investigador aprueba candidatos.
2. **Fase 2 — Procesamiento y auditoría.** Extracción P1–P5 → validación de schema →
   auditoría L1+L2 → verificación humana → DuckDB → estandarización. *(Se construye después.)*
3. **Fase 3 — Síntesis y reportes.** *(No construida aún.)*

Tema actual: **[TEMA POR DEFINIR]**.

## Principio de arquitectura: nada del tema vive en el código

- **El código (`litrev_core/`, `fase1_seleccion/`) y el framework (`framework/`) son
  permanentes.** No se editan para cambiar de tema.
- **Todo lo específico del proyecto vive en `config/*.yaml`.** Queries, criterios,
  vocabularios de prioridad, catálogos de estandarización, modelo LLM y umbrales.
  Cambiar de tema = editar `config/`, nunca los scripts.
- **El corpus vive en `data/` y está fuera de git** (`.gitignore`). Los PDFs, Markdown,
  JSON y Excel no se versionan. `data/` puede apuntar a Google Drive vía `LITREV_DATA_DIR`.
- **La plantilla y los proyectos van por separado.** Este repo es la plantilla central (solo
  cambios técnicos); cada revisión se ejecuta en una copia aparte (su propio repo/carpeta). El
  flujo y cómo llevar arreglos de vuelta a la plantilla están en `PLANTILLA_Y_PROYECTOS.md`.

## Al iniciar cada sesión

**Si es la primera sesión** (el tema aún dice `[TEMA POR DEFINIR]`):
→ Ejecutar la **Fase 0 — Definición de la revisión** (`framework/fase0_definicion.md`). Lo primero
es preguntar al investigador el tema y sus objetivos/preguntas; luego definir (o revisar) el
objetivo de revisión y los criterios; y de ahí derivar `config/proyecto.yaml`, `config/busqueda.yaml`
y `config/prioridad.yaml`. No buscar nada hasta completarla.

**En sesiones posteriores:**
1. Leer `framework/maestro_framework.md` (punto de entrada del sistema).
2. Leer el estado del ámbito activo, que el hook `SessionStart` ya cargó:
   `proyecto/sistema/estado_sistema.md` (construcción) o `proyecto/revision/estado_revision.md`
   (revisión de un tema).
3. Identificar la tarea pendiente y leer el documento de framework correspondiente.

## Reglas inquebrantables

- **NUNCA inventar datos.** Si un campo no se puede extraer, usar: `no_reportado`,
  `no_especificado`, `no_identificado`, `no_evaluado`, `no_aplica`. Un vacío honesto vale
  infinitamente más que un dato fabricado.
- **Todo dato es rastreable.** Cada campo extraído lleva bloque `_meta`: fuente, confianza,
  seccion_referencia, pasada_origen.
- **La IA no se audita sola.** Extracción y verificación son procesos separados.
- **APIs en `.env`, configuración en `config/`, jamás en código.** Las credenciales se cargan
  con `python-dotenv`. Las queries y criterios se leen de `config/*.yaml`.
- **Solo configuración confiable.** `config/prioridad.yaml` se evalúa con `eval` restringido
  (`litrev_core/prioridad.py`); usar únicamente archivos escritos por ti o por Claude, nunca
  reglas de fuentes no confiables.
- **Extracción interna (Fase 2).** Las pasadas P1–P5 y el desempate de prioridad por LLM se
  ejecutan dentro de Claude Code, NO mediante llamadas a la API de Anthropic.
- **Sin sub-agentes para extracción.** Las pasadas se ejecutan en el hilo principal. Los
  sub-agentes producen formatos inconsistentes.
- **Procesamiento artículo por artículo (Fase 2).** Completar P1→P5→Validación→Auditoría para
  CADA artículo antes de pasar al siguiente.
- **Nombres canónicos de campos.** Usar exclusivamente los definidos en
  `framework/estructura_json.md` (Fase 2). Sin aliases.
- **Registro por ámbito obligatorio.** La memoria está separada en dos ámbitos:
  `proyecto/sistema/` (construcción de la herramienta) y `proyecto/revision/` (ejecución de un
  tema). Cada sesión actualiza el estado y el registro del ámbito trabajado
  (`estado_sistema.md` + `registro_sistema.md`, o `estado_revision.md` + `registro_revision.md`) y,
  al cierre, crea `logs/sesion_NNN.md` en ese ámbito. El modelo, el ritual y los formatos están en
  `framework/memoria_proyecto.md`.
- **UTF-8 siempre.** Escribir directamente á, é, í, ó, ú, ñ, ü. Sin secuencias de escape Unicode.
- **Validación humana para fuentes externas.** Artículos de fuentes no-API requieren aprobación
  explícita del investigador antes de entrar al pipeline.

## La prioridad es híbrida (regex + LLM)

`fase1_seleccion/02_clasificar_prioridad.py` clasifica con las regex y pesos de
`config/prioridad.yaml` (rápido, determinista, reproducible) y marca como **dudosos** los
casos en la franja límite o con señales en conflicto. Esos dudosos se escriben en
`data/candidatos/revision_llm_pendiente.json`. Claude Code los **reclasifica leyendo
título+abstract** contra los criterios en lenguaje natural de `config/proyecto.yaml`, sin
llamar a la API de Anthropic. El detalle del handoff está en
`framework/fase1_seleccion.md`.

## Recuperación de PDFs: solo acceso abierto legal

La descarga usa únicamente fuentes de acceso abierto legal (OpenAlex, Unpaywall, Europe PMC,
PMC, arXiv, bioRxiv, DOAJ, Crossref, CORE). Lo que no esté en abierto se consigue por la
biblioteca de la institución del investigador.

## Memoria y registro de sesiones

El proyecto recuerda en dos ámbitos —`proyecto/sistema/` (construcción) y `proyecto/revision/`
(ejecución de un tema)— mediante capas (detalle y formatos en `framework/memoria_proyecto.md`):
`data/estado.json` (checkpoint automático de los scripts, solo ejecución), `estado_*.md` (progreso),
`registro_*.md` (decisiones D{n} e incidencias I{n}) y `logs/sesion_NNN.md` (bitácora, secuencial
por ámbito).

- **Apertura:** el hook `SessionStart` (`.claude/settings.json` → `tools/memoria_session_start.py`)
  detecta el ámbito activo (construcción si el tema sigue `[TEMA POR DEFINIR]`; revisión si ya hay
  tema) y me carga automáticamente su estado y su último log al iniciar. No hay que pedirlo.
- **Cierre (ritual que ejecuto al terminar el trabajo de la sesión o cuando lo pidas):** en la
  carpeta del ámbito trabajado, actualizar su estado, registrar decisiones/incidencias y crear
  `sesion_NNN.md` desde su `logs/_plantilla_sesion.md`. No se usa hook `Stop` (gastaría tokens por turno).

## Pipeline de la Fase 1

```
config/busqueda.yaml
  → 01_buscar.py            → data/candidatos/candidatos_busqueda.json
  → 02_clasificar_prioridad → data/candidatos/candidatos_clasificados.json
                              + revision_llm_pendiente.json (dudosos)
  → [Claude desempata dudosos dentro de Claude Code]
  → 03_generar_excel.py     → data/candidatos/base_candidatos.xlsx
  → [el investigador marca inclusión en el Excel]
  → 04_descargar.py         → data/pdfs/*.pdf   (acceso abierto)
  → 05_aprobar.py           → data/candidatos/candidatos_aprobados.json  (contrato → Fase 2)
```

La conversión a Markdown es el **primer paso de la Fase 2** (procesamiento), no de la
Fase 1: `fase2_procesamiento/01_convertir_markdown.py`.

## Convenciones

- **IDs:** `ART_NNN_Apellido_Año` (secuencial, ej. `ART_001_Garcia_2025`).
- **Idioma de campos:** español para nombres de campos y metadatos; contenido en idioma original.
- **Niveles de prioridad:** P0 (núcleo) … P4 (descartado), definidos en `config/prioridad.yaml`.

## Incidencias conocidas (Windows)

- El encoding cp1252 de la consola rompe la salida con acentos. La librería `litrev_core.log`
  llama `sys.stdout.reconfigure(encoding="utf-8")` automáticamente; todos los scripts la usan.
- **Python 3.14+:** no usar `re.sub()` con texto crudo de usuario como patrón (las comillas
  tipográficas Unicode causan `re.PatternError`). Usar `.replace()` para sustituciones literales.
- **Versión de Python:** probado en 3.14; en equipos nuevos se recomienda 3.12+ (amplio soporte
  de wheels). Mantener la misma versión en todos tus equipos para resultados reproducibles.

## Estado actual

Plantilla sin tema configurado. Fase 0 (definición) y Fase 1 construidas; Fase 2 y 3 pendientes
(la Fase 2 se construye en otro sistema). Ver `proyecto/sistema/estado_sistema.md`.
