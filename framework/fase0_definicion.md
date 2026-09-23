# Fase 0 — Definición de la revisión

Documento metodológico de la **Fase 0**, anterior a toda búsqueda. Convierte una idea de
investigación en una **definición de revisión accionable** (objetivo, preguntas, criterios) y la
**traduce a la configuración operativa** (`config/*.yaml`) que consume la Fase 1.

> **Regla del sistema:** todo el razonamiento de la Fase 0 ocurre **dentro de Claude Code**, sin
> llamar a la API de Anthropic. La Fase 0 la conduce Claude en diálogo con el investigador; no es
> un script. Produce artefactos concretos (los YAML + narrativa) para ser reproducible.

## Cuándo se ejecuta

Al abrir un proyecto cuyo `config/proyecto.yaml` aún dice `[TEMA POR DEFINIR]`. Es lo **primero**
que hace el sistema: antes de buscar, clasificar o descargar nada. Los pasos 1 y 2 de la Fase 1
**se niegan a correr** mientras la configuración tenga marcadores de plantilla
(guarda `litrev_core.config.revisar_configuracion`).

## Objetivo de la fase

Pasar de *"quiero revisar X"* a un proyecto **definido y configurado**: con objetivo de revisión,
preguntas, criterios de inclusión/exclusión, queries de búsqueda y escala de prioridad P0–P4,
todo coherente entre sí y aprobado por el investigador.

---

## Etapa A — Definición metodológica (conversación dirigida)

Claude conduce esta conversación, una pregunta clara a la vez, sin abrumar.

### A1. Tema de investigación
Preguntar el **tema** en lenguaje libre. Reformularlo en 1–2 frases y confirmarlo.
Proponer un **nombre** de proyecto: `LITREV-AI — [Tema conciso]` (2–6 palabras, siglas expandidas).

### A2. Objetivos / preguntas de investigación y tipo de revisión
- Preguntar los **objetivos** y/o **preguntas de investigación** del estudio.
- Preguntar el **tipo de revisión** buscado, porque define el rigor y la forma de los criterios:
  - **scoping** (mapeo de alcance), **sistemática**, **narrativa**, **rápida**.
  - Si el investigador no sabe, Claude recomienda uno según el tema y lo explica en términos llanos.

### A3. ¿Ya tiene objetivo de revisión y criterios?
Preguntar explícitamente si el investigador **ya tiene** un **objetivo de revisión** (distinto de
los objetivos del estudio) y **criterios de inclusión/exclusión**.

- **Si NO los tiene → generación adaptativa.**
  1. Claude **detecta el marco más pertinente** según tema y tipo de revisión:
     - Población–Concepto–Contexto (PCC) para *scoping*,
     - PICO (Población–Intervención–Comparación–Resultado) para preguntas clínicas/sistemáticas,
     - SPIDER para preguntas cualitativas/mixtas,
     - o un marco por **pertinencia** en lenguaje natural si ninguno encaja.
     Claude **nombra y justifica** el marco elegido en términos accesibles.
  2. Propone un **objetivo de revisión** y un set de **criterios de inclusión/exclusión**
     derivados del marco y del tema.
  3. Pregunta al investigador los **criterios clave a ajustar**, como mínimo:
     idioma(s), rango de años, tipos de estudio/publicación, población/contexto,
     y **exclusiones duras** (lo que definitivamente queda fuera).

- **Si SÍ los tiene → revisar y sugerir mejoras.**
  1. Claude los toma como base, sin reescribir el fondo.
  2. **Señala** vacíos, ambigüedades, solapamientos entre inclusión y exclusión, y criterios no
     verificables desde título+abstract.
  3. Propone ajustes concretos; **el investigador decide** qué aceptar.

### A4. Congelar la definición
Confirmar con el investigador y **escribir** la definición en:
- `config/proyecto.yaml` → `proyecto.nombre`, `tema.general`, `tema.objetivos`,
  `tema.preguntas_investigacion`, bloque `revision:` (`objetivo`, `tipo`, `marco`,
  `estado_criterios`), `criterios.inclusion`, `criterios.exclusion`, alcances.
- `proyecto/revision/config_proyecto.md` → narrativa: por qué este recorte, supuestos, marco elegido y
  notas de fuentes. La fuente de verdad de los **parámetros** es el YAML; este `.md` guarda el *porqué*.

`estado_criterios` toma uno de: `provistos_por_usuario`, `generados`, `revisados`.

---

## Etapa B — Traducción operativa (Claude deriva, el investigador ajusta)

A partir de la definición congelada, Claude deriva la configuración que ejecuta la Fase 1.

### B1. Queries de búsqueda → `config/busqueda.yaml`
- Derivar varias **queries** para OpenAlex y Semantic Scholar a partir del objetivo de revisión y
  los criterios (combinaciones de términos clave, sinónimos, español/inglés según alcance).
- Fijar **filtros**: `anio_minimo`, `idiomas`, `tipos_openalex`, según los criterios.
- Mostrar las queries al investigador para ajustar antes de correr.

### B2. Escala de prioridad → `config/prioridad.yaml`
- Derivar **vocabularios** (regex), **pesos**, **reglas** (árbol P0–P4) y **niveles con colores**,
  **anclados a los criterios de inclusión/exclusión**. El núcleo (P0) refleja lo más pertinente;
  P4 refleja las exclusiones duras.
- Usar los comentarios de `config/prioridad.yaml` como modelo de forma (no de contenido).
- Definir la `franja_dudosa` (rango de score y conflictos) para el desempate por LLM de la Fase 1.
- Mostrar la escala al investigador para ajustar ("las reglas y colores del nuevo tema").

> **Seguridad:** las `condicion` de las reglas se evalúan con `eval` restringido. Usar
> **únicamente** `prioridad.yaml` escrito por ti o por Claude; no cargar reglas de fuentes no
> confiables. (Ver `litrev_core/prioridad.py`.)

### B3. Validación de completitud (habilita la corrida)
Ejecutar la guarda `litrev_core.config.revisar_configuracion()` y confirmar que **no quedan
marcadores de plantilla** en proyecto/busqueda/prioridad. Mientras queden, la Fase 1 no corre.

---

## Handoff a la Fase 1

Con la configuración validada: **"ahora sí empieza el proceso"** →
`python fase1_seleccion/01_buscar.py` y el resto del flujo de `framework/fase1_seleccion.md`.

## Artefactos que produce la Fase 0

| Artefacto | Contenido |
|-----------|-----------|
| `config/proyecto.yaml` | tema, objetivos, preguntas, bloque `revision:`, criterios, alcances |
| `config/busqueda.yaml` | queries OpenAlex/Semantic Scholar + filtros |
| `config/prioridad.yaml` | vocabularios, pesos, reglas, niveles P0–P4, franja dudosa |
| `proyecto/revision/config_proyecto.md` | narrativa del recorte, supuestos y marco elegido |
| `proyecto/revision/registro_revision.md` | la definición registrada como decisión (D{n}) |

## Reglas de la fase

- **No buscar ni procesar nada** hasta que la definición esté congelada y la configuración validada.
- **No inventar el alcance por el investigador.** Claude propone; el investigador decide y ajusta.
- **Criterios verificables.** Preferir criterios que puedan evaluarse desde título+abstract, porque
  así los aplica la clasificación de prioridad de la Fase 1.
- **Trazabilidad.** Registrar la definición como decisión en `registro_revision.md`, incluyendo
  el marco elegido y el `estado_criterios` (provistos / generados / revisados).
