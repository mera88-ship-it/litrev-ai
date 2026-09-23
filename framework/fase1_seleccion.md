# Fase 1 — Recuperación y selección de literatura

Documento metodológico de la Fase 1. Cubre el flujo, la escala de prioridad híbrida y el
procedimiento de desempate por LLM. Los parámetros concretos viven en `config/*.yaml`.

## Objetivo de la fase

Pasar de un tema a un **corpus seleccionado, priorizado y descargado**, con un Excel entregable
para que el investigador decida la inclusión final. La fase termina produciendo
`data/candidatos/candidatos_aprobados.json`, contrato de entrada de la Fase 2.

## Flujo

| Paso | Script | Entrada | Salida |
|------|--------|---------|--------|
| 1 | `01_buscar.py` | `config/busqueda.yaml` | `candidatos_busqueda.json` |
| 2 | `02_clasificar_prioridad.py` | candidatos + `config/prioridad.yaml` | `candidatos_clasificados.json` + `revision_llm_pendiente.json` |
| 2b | **Claude Code** | dudosos + `config/proyecto.yaml` | actualiza `candidatos_clasificados.json` |
| 3 | `03_generar_excel.py` | clasificados | `base_candidatos.xlsx` |
| 3b | **Investigador** | Excel | columna "Decisión inclusión" |
| 4 | `04_descargar.py` | clasificados + `config/proyecto.yaml` | `data/pdfs/*.pdf` |
| 5 | `05_aprobar.py` | Excel + clasificados | `candidatos_aprobados.json` |

> La conversión a Markdown ya **no** pertenece a la Fase 1: es el primer paso del
> procesamiento (`fase2_procesamiento/01_convertir_markdown.py`). La Fase 1 termina cuando hay
> un corpus aprobado con sus PDFs descargados.

## Búsqueda (paso 1)

Multi-fuente (OpenAlex + Semantic Scholar), deduplicación por DOI o título, filtro por idioma y
año, enriquecimiento de acceso abierto con Unpaywall. Las queries y filtros se editan en
`config/busqueda.yaml`. Cada candidato conserva su procedencia (`fuente_api`, `query_origen`,
`relevance_score`) para trazabilidad.

## Escala de prioridad híbrida (pasos 2 y 2b)

La prioridad combina dos motores:

**Parte determinista (regex + reglas), en `02_clasificar_prioridad.py`:**
- Cada **vocabulario** de `config/prioridad.yaml` es un conjunto de regex; sobre
  "título. abstract" produce un flag booleano.
- Las **reglas** son un árbol de decisión ordenado; la primera cuya `condicion` (expresión
  booleana sobre los flags) es verdadera fija el nivel P0–P4 y la razón.
- Un **score** continuo (0–100) suma los pesos de los vocabularios activos; sirve para ordenar
  dentro de un nivel.

**Parte LLM (desempate), dentro de Claude Code:** los casos en zona gris se marcan
`confianza: dudosa` y se vuelcan a `revision_llm_pendiente.json`. Se marcan dudosos cuando:
- el score cae en la franja `[score_min, score_max]`,
- coinciden dos vocabularios en conflicto (p. ej. señal de exclusión y de inclusión a la vez),
- el título+abstract es demasiado corto para clasificar con confianza.

### Desempate por LLM (paso 2b) — procedimiento

Se ejecuta **dentro de Claude Code, sin llamar a la API de Anthropic** (regla del sistema).

1. Leer `data/candidatos/revision_llm_pendiente.json` (cada caso trae título, abstract,
   `prioridad_auto`, `razon_auto`, `score` y los `vocabularios_activos`).
2. Leer los criterios en lenguaje natural de `config/proyecto.yaml` (`criterios.inclusion`,
   `criterios.exclusion`) y las descripciones de niveles de `config/prioridad.yaml`.
3. Para cada caso, leer título+abstract y decidir el nivel correcto, prestando atención a lo
   que las regex no captan: **negaciones** ("no gender differences were found"), contexto,
   y si el enfoque clave es el **marco** o solo una **variable**.
4. Escribir en cada caso `prioridad_llm` y `razon_llm`, y reflejar el cambio en
   `candidatos_clasificados.json`: actualizar `prioridad`, poner `prioridad_fuente: "llm"` y
   conservar `prioridad_auto` para auditoría.
5. Procesar artículo por artículo; no inventar; si el abstract no alcanza para decidir, dejar
   el nivel automático y anotar la limitación en `razon_llm`.

El objetivo del desempate no es reclasificarlo todo, sino corregir donde la heurística falla.

## Excel y revisión humana (pasos 3 y 3b)

`03_generar_excel.py` genera `base_candidatos.xlsx` con tres hojas (Candidatos, Escala de
prioridad, Resumen), color por nivel y columnas para que el investigador escriba en
**"Decisión inclusión"** (`incluir` / `excluir`) y notas. Es el entregable de selección.

## Descarga y cierre (pasos 4 y 5)

- `04_descargar.py` baja los PDFs de los niveles indicados en `config/proyecto.yaml`
  (`descarga.prioridades_a_descargar`) por acceso abierto legal.
- `05_aprobar.py` lee las decisiones del Excel y construye `candidatos_aprobados.json`
  (solo incluidos). Ese JSON es el contrato que recoge la Fase 2; la conversión a Markdown
  es el primer paso de esa fase.

## Reglas de la fase

- **Validación humana para fuentes externas.** Artículos de fuentes no-API (búsqueda manual,
  referencias cruzadas) requieren aprobación explícita antes de entrar al pipeline.
- **No fabricar metadatos.** Los campos ausentes de las APIs se registran como `no_reportado`.
- **Trazabilidad.** Conservar procedencia y la prioridad automática aunque el LLM la corrija.
