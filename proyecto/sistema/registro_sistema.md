# Registro del sistema (construcción)

> Decisiones sobre cómo se **construye y afina la herramienta** LITREV-AI (formato D{n}) e
> incidencias técnicas (formato I{n}, al final). Las decisiones metodológicas de una revisión
> temática concreta van aparte, en `proyecto/revision/registro_revision.md`. Formatos y ritual en
> `framework/memoria_proyecto.md`. Se escribe por decisión, no por ejecución.

## Decisiones de arquitectura heredadas (D0)

Estas decisiones definen la plantilla v3.0 y se heredan en cada proyecto.

- **D0.1 — Código permanente, configuración por proyecto.** Todo lo específico del tema vive
  en `config/*.yaml`; los scripts y la librería nunca se editan para cambiar de tema.
  *Justificación:* en versiones previas las queries estaban hardcodeadas en el script,
  rompiendo la separación framework/proyecto.
- **D0.2 — Corpus fuera de git.** Los PDFs, Markdown, JSON y Excel viven en `data/`
  (gitignored). Git/GitHub solo versiona código, framework y configuración.
  *Justificación:* los binarios pesados inflan el repositorio; Google Drive sincronizando un
  `.git` lo corrompe.
- **D0.3 — Pipeline segmentado en tres fases con contrato de datos.** Fase 1 (selección) →
  `candidatos_aprobados.json` → Fase 2 (procesamiento) → Fase 3 (síntesis).
  *Justificación:* permite ejecutar y entregar la selección por separado del procesamiento.
- **D0.4 — Prioridad híbrida (regex + LLM).** Las reglas configurables hacen el grueso; los
  casos dudosos los desempata Claude leyendo el artículo. *Justificación:* reproducibilidad
  y bajo costo de las regex + comprensión de contexto del LLM donde hace falta.
- **D0.5 — Solo acceso abierto legal.** La descarga usa únicamente fuentes de acceso abierto.
  *Justificación:* reproducibilidad y cumplimiento legal en cualquier jurisdicción.
- **D0.6 — Una librería común (`litrev_core`).** Rutas, logging, encoding, APIs, IO y estado
  centralizados. *Justificación:* en el proyecto maduro previo, 47 scripts ad-hoc generaron
  tres esquemas JSON divergentes y deuda técnica.
- **D0.7 — Escritura atómica + respaldo.** Los JSON del flujo se escriben con tmp+replace y
  respaldo con marca temporal. *Justificación:* evitar pérdida por sobrescritura/interrupción.
- **D0.8 — Anti-alucinación y trazabilidad (Fase 2).** Nunca inventar datos; cada campo con
  `_meta`. La IA no se audita sola.

## Decisiones de este proyecto

### D1 — Conversión a Markdown movida a la Fase 2 (2026-06-25, sesión 001)
- **Tipo:** metodológica
- **Contexto:** la conversión a Markdown estaba al final de la Fase 1 (selección).
- **Alternativas:** dejarla en Fase 1 / moverla a Fase 2.
- **Decisión:** la conversión es el primer paso de la Fase 2 (procesamiento).
- **Justificación:** pasar la literatura a un formato trabajable es el inicio del
  procesamiento, no de la selección; la Fase 1 termina en un corpus aprobado con PDFs.
- **Consecuencias:** Fase 1 cierra en `05_aprobar.py`; nace `fase2_procesamiento/01_convertir_markdown.py`.

### D2 — Descarga en cascada multi-fuente (2026-06-25, sesión 001)
- **Tipo:** técnica
- **Contexto:** una sola fuente de descarga era lenta y frágil.
- **Alternativas:** optimizar una fuente / cascada de fuentes de acceso abierto.
- **Decisión:** cadena de fuentes de acceso abierto legal (Unpaywall, Europe PMC, PMC, arXiv,
  bioRxiv, DOAJ, Crossref, CORE), con concurrencia, libro de descargas (reanudación) y
  validación de PDF real.
- **Justificación:** la mayoría de PDFs se recuperan por vías abiertas rápidas. CORE opcional
  por key gratuita.
- **Consecuencias:** `litrev_core/descarga.py`; `04_descargar.py` reescrito; nuevo campo de
  config (`fuentes_orden`) y `CORE_API_KEY` en `.env`.

### D3 — Sistema de memoria con hook SessionStart, sin hook Stop (2026-06-25, sesión 001)
- **Tipo:** técnica/metodológica
- **Contexto:** se necesitaba memoria de avances/decisiones/incidencias con un "loop" automático.
- **Alternativas:** hook Stop bloqueante por turno / SessionStart + ritual / solo plantillas.
- **Decisión:** hook `SessionStart` que carga el estado al abrir + ritual de cierre documentado;
  sin hook `Stop`.
- **Justificación:** el `Stop` se dispara cada turno e inyecta tokens repetidamente; el
  `SessionStart` cuesta una vez por sesión y aporta el contexto necesario.
- **Consecuencias:** `framework/memoria_proyecto.md`, `tools/memoria_session_start.py`,
  `.claude/settings.json`, plantilla de sesión.

### D4 — Fase 0: Definición de la revisión (2026-06-25, sesión 002)
- **Tipo:** metodológica
- **Contexto:** el "Paso 0" solo decía "llenar los YAML"; faltaba una fase guiada que definiera
  la revisión (objetivo, preguntas, criterios) antes de configurar y correr.
- **Alternativas:** mantener un Paso 0 minimal / fase guiada por Claude / script con prompts.
- **Decisión:** nueva **Fase 0** guiada por Claude (dentro de Claude Code, sin API), en dos etapas:
  (A) definición metodológica — tema, objetivos/preguntas, tipo de revisión, objetivo de revisión
  y criterios, **generados de forma adaptativa** si el investigador no los tiene o **revisados y
  mejorados** si ya los trae; (B) traducción operativa — derivar queries y escala de prioridad.
  Documentada en `framework/fase0_definicion.md`.
- **Justificación:** alinear el arranque con la práctica de revisión (objetivo + criterios primero);
  generar criterios por pertinencia cuando faltan; conservar la regla de que el razonamiento del
  LLM ocurre dentro de Claude Code.
- **Consecuencias:** nuevo `framework/fase0_definicion.md`; nuevos campos en `proyecto.yaml`
  (`tema.preguntas_investigacion`, bloque `revision:`); actualización de maestro/CLAUDE/README.
  Decisiones confirmadas con el investigador: generación **adaptativa** del marco; criterios
  existentes se **revisan y mejoran**.

### D5 — Guarda de configuración completa (2026-06-25, sesión 002)
- **Tipo:** técnica
- **Contexto:** la auditoría detectó que con `prioridad.yaml` en plantilla, el paso 2 clasificaba
  **todo** como "P0 dudoso" sin avisar (fallo silencioso).
- **Alternativas:** confiar en el operador / validar en cada script por separado / validador central.
- **Decisión:** helper central `litrev_core.config.revisar_configuracion()` /
  `configuracion_incompleta()`; `01_buscar` y `02_clasificar` abortan con mensaje claro si quedan
  marcadores de plantilla, remitiendo a la Fase 0.
- **Justificación:** convierte un fallo silencioso en un error explícito; lógica única, sin duplicar.
- **Consecuencias:** cambios en `litrev_core/config.py`, `fase1_seleccion/01_buscar.py` y
  `02_clasificar_prioridad.py`.

### D6 — Pines de dependencias y versión de Python (2026-06-25, sesión 002)
- **Tipo:** técnica
- **Contexto:** `requirements.txt` fijaba versiones exactas que no coincidían con lo instalado
  (`requests==2.32.3` vs `2.33.1`); Python 3.14 en uso.
- **Alternativas:** fijar exactas / relajar a `>=` mínimos probados.
- **Decisión:** `requirements.txt` con `>=` (mínimos probados); documentar "probado en 3.14,
  recomendado 3.12+ en equipos nuevos".
- **Justificación:** instalación más robusta para un usuario en 1–2 equipos; elimina la
  inconsistencia de pines.
- **Consecuencias:** `requirements.txt` y notas en `CLAUDE.md` / `README.md`.

### D7 — Memoria separada en dos ámbitos: sistema/ y revision/ (2026-06-25, sesión 003)
- **Tipo:** técnica/metodológica
- **Contexto:** la memoria (estado, registro, logs) mezclaba en una sola carpeta `proyecto/` dos
  cosas distintas: cómo se construye la herramienta y cómo va una revisión de un tema concreto. Al
  reutilizar la plantilla para varios temas, ese cruce confunde el historial.
- **Alternativas:** una sola memoria con secciones / dos carpetas con detección automática de
  ámbito / un repositorio por tema.
- **Decisión:** dos ámbitos —`proyecto/sistema/` (construcción) y `proyecto/revision/` (ejecución
  de un tema)—, cada uno con su estado, registro y logs. El hook `SessionStart` detecta el ámbito
  leyendo `config/proyecto.yaml` (CONSTRUCCIÓN si sigue `[TEMA POR DEFINIR]`, REVISIÓN si ya hay
  tema) y carga la memoria correspondiente.
- **Justificación:** separa responsabilidades sin duplicar trabajo; la herramienta evoluciona en
  `sistema/` y cada tema deja su rastro en `revision/` sin contaminarse; la numeración de sesiones
  es independiente por ámbito.
- **Consecuencias:** archivos movidos conservando historial (estado_proyecto → revision/estado_revision;
  registro_metodologico → sistema/registro_sistema; config_proyecto y logs a su ámbito); nuevos
  estado_sistema y registro_revision y plantillas por ámbito; reescrito `framework/memoria_proyecto.md`
  y actualizadas todas las referencias en `CLAUDE.md`, framework/ (maestro, fase0), `README.md` y
  comentarios de código. Diseñada en la sesión 002 (otra cuenta) y completada en la 003 (referencias
  + corrección de `config.py`, ver I2).

## Incidencias técnicas

### I1 — Resolvers de descarga sin validar contra red (2026-06-25, sesión 001)
- **Síntoma:** los resolvers (Europe PMC, PMC, arXiv, bioRxiv, DOAJ, Crossref, CORE) se
  implementaron según la forma conocida de cada API, pero no se probaron con llamadas reales.
- **Causa:** entorno de construcción sin credenciales/red.
- **Resolución:** cada resolver es defensivo (cualquier excepción → None → siguiente fuente).
- **Estado:** pendiente de validación al correr la Fase 1 con un tema real.
- **Prevención:** verificar por fuente en la primera corrida.

### I2 — config.py recreaba la carpeta de logs vieja tras la mudanza (2026-06-25, sesión 003)
- **Síntoma:** `litrev_core/config.py` definía `logs_dir = proyecto/logs`, carpeta disuelta al
  separar la memoria en dos ámbitos; `Paths.crear()` la habría vuelto a crear al correr cualquier script.
- **Causa:** la ruta de logs quedó sin actualizar al mover la memoria.
- **Resolución:** `logs_dir` ahora apunta a `proyecto/revision/logs/` (los logs automáticos son de
  ejecución); `.gitignore` ajustado a `proyecto/*/logs/auto_*.md`.
- **Estado:** resuelta.
- **Prevención:** al mover carpetas, revisar las rutas en `litrev_core/config.py` (fuente única de
  rutas) y los comentarios que las citan.
