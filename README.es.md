# LITREV-AI

Plantilla reutilizable para **revisión de literatura científica asistida por IA**, con un
pipeline anti-alucinación, trazable y auditable. Se clona por proyecto y solo se edita la
configuración para cambiar de tema.

## Arquitectura en una frase

> El **código** y el **framework** son permanentes y viven en git/GitHub. La **configuración**
> del tema vive en `config/`. El **corpus** (PDFs, datos) vive en `data/`, fuera de git.

**La plantilla y cada proyecto van por separado** (un repo/carpeta por revisión). Cómo crear un
proyecto desde esta plantilla y cómo llevar arreglos técnicos de vuelta a `main`:
ver [`PLANTILLA_Y_PROYECTOS.md`](PLANTILLA_Y_PROYECTOS.md).

```
litrev-ai/
├── framework/          Permanente. Instrucciones del método (.md): Fase 0, selección, P1–P5, auditoría.
├── config/             ÚNICO lugar a editar por proyecto.
│   ├── proyecto.yaml        tema, objetivos, alcance, modelo LLM, umbrales, descarga
│   ├── busqueda.yaml        queries OpenAlex/Semantic Scholar, filtros
│   ├── prioridad.yaml       vocabularios + pesos + reglas del árbol P0–P4
├── litrev_core/        Librería común: config, logging, APIs, IO, motor de prioridad, estado.
├── fase1_seleccion/    Recuperación y selección (01→05). Construida.
├── fase2_procesamiento/  Validación, auditoría, DuckDB. (Pendiente.)
├── fase3_sintesis/     Síntesis y reportes. (Pendiente.)
├── proyecto/           Memoria por ámbito: sistema/ (construcción) y revision/ (ejecución del tema).
└── data/               GITIGNORED. candidatos/, pdfs/, markdown/, json_*/, *.duckdb.
```

## Las fases

| Fase | Qué hace | Entrega | Estado |
|------|----------|---------|--------|
| **0. Definición de la revisión** | Diálogo guiado: tema, objetivos/preguntas, objetivo de revisión y criterios; deriva la configuración | `config/*.yaml` definidos | **Construida** |
| **1. Recuperación y selección** | Busca, deduplica, filtra, clasifica por prioridad, descarga y aprueba | Excel de candidatos con prioridades + PDFs aprobados | **Construida** |
| **2. Procesamiento y auditoría** | Conversión a Markdown, extracción P1–P5, validación de schema, auditoría L1+L2, DuckDB | Base de datos auditada | Conversión construida; resto pendiente |
| **3. Síntesis y reportes** | Workbenches analíticos, síntesis, manuscrito | Reportes | Pendiente |

Las fases se conectan por un **contrato de datos**: la Fase 1 entrega
`data/candidatos/candidatos_aprobados.json`, que la Fase 2 consume.

## Puesta en marcha

```bash
# 1. Clonar (idealmente FUERA de carpetas sincronizadas como Google Drive,
#    porque la sincronización puede corromper el .git)
git clone <url-del-repo> mi-revision && cd mi-revision

# 2. Entorno y dependencias (Python recomendado: 3.12+; probado en 3.14)
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Credenciales
#    Crear un archivo .env en la raíz del repositorio (está en .gitignore):
#      OPENALEX_EMAIL=tu@correo.com       recomendado (polite pool de OpenAlex)
#      UNPAYWALL_EMAIL=tu@correo.com      recomendado (sin él, se omite Unpaywall)
#      OPENALEX_API_KEY=                  opcional
#      SEMANTIC_SCHOLAR_API_KEY=          opcional (más límite de consultas)
#      CORE_API_KEY=                      opcional (clave gratuita en core.ac.uk/services/api)
#      LITREV_DATA_DIR=                   opcional (corpus fuera del repositorio)

# 4. Definir la revisión (Fase 0): Claude te guía para fijar tema, objetivos y criterios,
#    y derivar config/proyecto.yaml, busqueda.yaml y prioridad.yaml.
#    Ver framework/fase0_definicion.md.
```

## Flujo de la Fase 1

> Requiere haber completado la **Fase 0** (definición) — ver `framework/fase0_definicion.md`.
> Los pasos 01 y 02 se niegan a correr si la configuración sigue en plantilla.

```bash
python fase1_seleccion/01_buscar.py             # → candidatos_busqueda.json
python fase1_seleccion/02_clasificar_prioridad.py  # → candidatos_clasificados.json + dudosos
# (Claude reclasifica los dudosos dentro de Claude Code)
python fase1_seleccion/03_generar_excel.py      # → base_candidatos.xlsx
# (el investigador marca inclusión/exclusión en el Excel)
python fase1_seleccion/04_descargar.py          # → data/pdfs/
python fase1_seleccion/05_aprobar.py            # → candidatos_aprobados.json (contrato → Fase 2)
# La conversión a Markdown es el primer paso de la Fase 2:
# python fase2_procesamiento/01_convertir_markdown.py
```

## Sobre el almacenamiento (GitHub vs. local vs. Drive)

- **GitHub** guarda el código, el framework y la configuración: ligero, versionable, reutilizable.
- **El corpus NO va a GitHub.** Los PDFs pesan y los binarios rompen el repo. Viven en `data/`.
- Para respaldar el corpus en **Google Drive**, apuntar `LITREV_DATA_DIR` (en `.env`) a una
  carpeta de Drive. Así Drive sincroniza los datos sin tocar el `.git`.

## Principios

Anti-alucinación · trazabilidad por campo · auditoría mixta IA+humana · configuración separada
del código · corpus separado del repositorio. Detalle en `framework/maestro_framework.md`.

## Proyecto actual

**[TEMA POR DEFINIR]** — plantilla sin tema. Al iniciar, Claude ejecuta la Fase 0 para definirlo.

## Autoría y licencia

**Carlos David Ascencio Mera** diseñó el método, los criterios de revisión, las reglas de auditoría y
las decisiones registradas en `proyecto/sistema/registro_sistema.md`, y probó el pipeline en revisiones
reales. **Mnemiic**, su asistente de inteligencia artificial, escribió la mayor parte del código y la
documentación bajo esa dirección.

Licencia [Creative Commons Atribución-NoComercial 4.0 Internacional](LICENSE) (CC BY-NC 4.0).
