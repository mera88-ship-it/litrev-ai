# LITREV-AI — Framework maestro

## Nombre del sistema: LITREV-AI · Versión: 3.0

Punto de entrada del sistema. Al inicio de cada sesión, leer este documento y el estado del
ámbito activo (`proyecto/sistema/estado_sistema.md` o `proyecto/revision/estado_revision.md`, lo
carga el hook `SessionStart`) para saber cómo operar y dónde quedó el trabajo.

Este documento no contiene instrucciones de extracción: las referencia. Cada documento
operativo es autocontenido.

---

## Qué es LITREV-AI

Sistema para procesar conocimiento científico de forma confiable, eliminando el "slop" que
producen los modelos de lenguaje al extraer datos sin estructura, verificación ni trazabilidad.
Ataca el problema en tres niveles: **anti-alucinación** (si no está en el texto, no se inventa),
**trazabilidad** (cada dato rastreable a su fuente) y **auditoría mixta IA + humana** (el
sistema no se fía de sí mismo).

## Las fases (0 → 3)

```
FASE 0 — Definición de la revisión       [construida]
  tema → objetivos/preguntas → objetivo de revisión + criterios → config/*.yaml
FASE 1 — Recuperación y selección        [construida]
  config → buscar → clasificar prioridad → (desempate LLM) → Excel
         → (revisión humana) → descargar → aprobar
         → candidatos_aprobados.json  ── contrato ──▶
FASE 2 — Procesamiento y auditoría        [conversión construida; resto pendiente]
  conversión a Markdown → P1–P5 → validación de schema → auditoría L1+L2
         → verificación humana → DuckDB → estandarización
FASE 3 — Síntesis y reportes              [pendiente]
  workbenches → síntesis → manuscrito
```

## Principios fundacionales

1. **Nunca inventar datos.** Ausencia → `no_reportado`, `no_especificado`, `no_identificado`,
   `no_evaluado`, `no_aplica`. Un vacío honesto vale más que un dato fabricado.
2. **Todo dato es rastreable.** Cada campo extraído lleva `_meta` (fuente, confianza, sección,
   pasada de origen).
3. **La IA no se audita sola.** Extracción y verificación son procesos separados.
4. **Cada campo es autocontenido.** Sin abreviaturas ni referencias sin expandir.
5. **La compresión es el enemigo.** Fidelidad sobre brevedad; los datos cuantitativos se copian
   exactos.
6. **La ausencia es dato.** Los patrones de ausencia son analíticamente relevantes.
7. **El código es permanente; el tema vive en `config/`.** Cambiar de tema no toca el código.
8. **El corpus vive fuera de git.** `data/` está en `.gitignore`.

---

## Estructura de archivos

```
framework/         Permanente. Instrucciones del método.
  maestro_framework.md   ← ESTE ARCHIVO
  fase0_definicion.md    ← Definición de la revisión (tema, objetivos, criterios) → config
  fase1_seleccion.md     ← Metodología de selección + escala de prioridad + desempate LLM
  memoria_proyecto.md    ← Modelo de memoria, ritual de sesión y formatos de registro
  (pasada_*.md, protocolo_auditoria.md, estructura_json.md, schema_validacion.md → Fase 2)
config/            ÚNICO lugar a editar por proyecto (proyecto/busqueda/prioridad .yaml).
litrev_core/       Librería común (no se edita para cambiar de tema).
fase1_seleccion/   Scripts 01–05 de la Fase 1.
proyecto/          Memoria por ámbito: sistema/ (construcción) y revision/ (ejecución del tema).
data/              Corpus (gitignored).
```

---

## Fase 0 — Definir la revisión (primera vez)

Si `config/proyecto.yaml` aún tiene `[TEMA POR DEFINIR]`, el proyecto no está definido.
**Antes de cualquier búsqueda, ejecutar la Fase 0** (protocolo completo en
`framework/fase0_definicion.md`). En síntesis:

1. **Definición metodológica:** preguntar tema, objetivos/preguntas de investigación y tipo de
   revisión; definir el objetivo de revisión y los criterios de inclusión/exclusión (generándolos
   de forma adaptativa si el investigador no los tiene, o revisándolos si ya los trae).
2. **Traducción operativa:** derivar con el investigador `config/busqueda.yaml` (queries + filtros)
   y `config/prioridad.yaml` (vocabularios, pesos, reglas y niveles P0–P4), anclados a los criterios.
3. Registrar la definición como decisión en `proyecto/revision/registro_revision.md`.

Los pasos 1 y 2 de la Fase 1 **se niegan a correr** mientras la configuración tenga marcadores de
plantilla (guarda `litrev_core.config.revisar_configuracion`). **No buscar ni procesar nada hasta
que la Fase 0 esté completa.**

---

## Árbol de decisión por tarea

- **Iniciar sesión:** leer este archivo + el estado del ámbito activo
  (`proyecto/sistema/estado_sistema.md` o `proyecto/revision/estado_revision.md`).
- **Definir la revisión (tema sin definir):** seguir `framework/fase0_definicion.md`.
- **Ejecutar la Fase 1:** seguir `framework/fase1_seleccion.md` y los scripts `fase1_seleccion/01–05`.
- **Desempatar dudosos de prioridad:** ver `framework/fase1_seleccion.md` → "Desempate por LLM".
- **Procesar/auditar artículos (Fase 2):** pendiente de construir.
- **Cerrar sesión:** seguir el ritual de cierre de `framework/memoria_proyecto.md` (actualizar el
  estado del ámbito trabajado, registrar decisiones/incidencias, crear `logs/sesion_NNN.md` en ese ámbito).

---

## Marcas de prioridad

- **CRÍTICO — Codificación:** UTF-8 siempre; escribir á, é, í, ó, ú, ñ, ü directamente.
- **CRÍTICO — Continuidad:** leer el estado del ámbito activo al inicio, actualizarlo al cierre.
- **CRÍTICO — No editar `framework/` ni `litrev_core/` durante la operación normal.** Los
  ajustes son deliberados y se registran en `registro_sistema.md` (construcción).
- **CRÍTICO — Extracción y desempate dentro de Claude Code**, nunca por API de Anthropic, y
  sin sub-agentes.
