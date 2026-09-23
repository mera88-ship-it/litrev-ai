# LITREV-AI

*[Versión en español](README.es.md)*

A reusable template for **AI-assisted scientific literature reviews**, built as an agent
harness: AI agents run the pipeline under explicit rules, shared project memory and human
review. The pipeline is designed against hallucination, and every step is traceable and
auditable. You clone it once per review and only edit the configuration to change the topic.

It was distilled from the pipeline used in a systematic review on AI-mediated cognitive
offloading and cognitive amplification in higher education.

## Architecture in one sentence

> The **code** and the **framework** are permanent and live in git. The topic
> **configuration** lives in `config/`. The **corpus** (PDFs, data) lives in `data/`, outside git.

**The template and each review are kept separate** (one repository or folder per review). How to
start a review from this template and how to bring technical fixes back to `main` is described in
[`PLANTILLA_Y_PROYECTOS.md`](PLANTILLA_Y_PROYECTOS.md) (Spanish).

```
litrev-ai/
├── framework/          Permanent. Method instructions (.md): Phase 0, selection, P1–P5, audit.
├── config/             The ONLY place to edit per review.
│   ├── proyecto.yaml        topic, objectives, scope, LLM model, thresholds, download
│   ├── busqueda.yaml        OpenAlex / Semantic Scholar queries, filters
│   └── prioridad.yaml       vocabularies + weights + P0–P4 decision-tree rules
├── litrev_core/        Shared library: config, logging, APIs, IO, priority engine, state.
├── fase1_seleccion/    Retrieval and selection (01→05). Built.
├── fase2_procesamiento/  Conversion, validation, audit, DuckDB. (Conversion built.)
├── fase3_sintesis/     Synthesis and reports. (Pending.)
├── proyecto/           Memory by scope: sistema/ (building the tool) and revision/ (running a topic).
└── data/               GITIGNORED. candidatos/, pdfs/, markdown/, json_*/, *.duckdb.
```

## Phases

| Phase | What it does | Output | Status |
|------|----------|---------|--------|
| **0. Review definition** | Guided dialogue: topic, objectives and questions, review aim and criteria; derives the configuration | `config/*.yaml` defined | **Built** |
| **1. Retrieval and selection** | Searches, deduplicates, filters, ranks by priority, downloads and approves | Candidate spreadsheet with priorities + approved PDFs | **Built** |
| **2. Processing and audit** | Markdown conversion, P1–P5 extraction, schema validation, L1+L2 audit, DuckDB | Audited database | Conversion built; the rest pending |
| **3. Synthesis and reports** | Analytical workbenches, synthesis, manuscript | Reports | Pending |

Phases connect through a **data contract**: Phase 1 delivers
`data/candidatos/candidatos_aprobados.json`, which Phase 2 consumes.

## Getting started

```bash
# 1. Clone (ideally OUTSIDE synced folders such as Google Drive,
#    because syncing can corrupt .git)
git clone https://github.com/mera88-ship-it/litrev-ai.git my-review && cd my-review

# 2. Environment and dependencies (Python 3.12+ recommended; tested on 3.14)
python -m venv .venv && .venv\Scripts\activate   # Windows
pip install -r requirements.txt

# 3. Credentials
#    Create a .env file in the repository root (it is gitignored):
#      OPENALEX_EMAIL=you@example.com     recommended (OpenAlex polite pool)
#      UNPAYWALL_EMAIL=you@example.com    recommended (without it, Unpaywall is skipped)
#      OPENALEX_API_KEY=                  optional
#      SEMANTIC_SCHOLAR_API_KEY=          optional (higher rate limit)
#      CORE_API_KEY=                      optional (free key at core.ac.uk/services/api)
#      LITREV_DATA_DIR=                   optional (corpus outside the repository)

# 4. Define the review (Phase 0): the agent guides you to set topic, objectives and criteria,
#    and derives config/proyecto.yaml, busqueda.yaml and prioridad.yaml.
#    See framework/fase0_definicion.md.
```

## Phase 1 workflow

> Requires **Phase 0** (definition) first; see `framework/fase0_definicion.md`.
> Steps 01 and 02 refuse to run while the configuration is still a template.

```bash
python fase1_seleccion/01_buscar.py                # → candidatos_busqueda.json
python fase1_seleccion/02_clasificar_prioridad.py  # → candidatos_clasificados.json + borderline cases
# (the agent re-classifies borderline cases inside Claude Code)
python fase1_seleccion/03_generar_excel.py         # → base_candidatos.xlsx
# (the researcher marks inclusion/exclusion in the spreadsheet)
python fase1_seleccion/04_descargar.py             # → data/pdfs/ (legal open access only)
python fase1_seleccion/05_aprobar.py               # → candidatos_aprobados.json (contract → Phase 2)
# Markdown conversion is the first step of Phase 2:
# python fase2_procesamiento/01_convertir_markdown.py
```

PDFs are retrieved only from legal open-access sources (OpenAlex, Unpaywall, Europe PMC, PMC,
arXiv, bioRxiv, DOAJ, Crossref, CORE). Anything not openly available is obtained through the
researcher's institutional library.

## Storage (GitHub vs. local vs. Drive)

- **GitHub** holds the code, the framework and the configuration: light, versioned, reusable.
- **The corpus does NOT go to GitHub.** PDFs are heavy and binaries bloat the repository. They live in `data/`.
- To back up the corpus on **Google Drive**, point `LITREV_DATA_DIR` (in `.env`) to a Drive
  folder. Drive then syncs the data without touching `.git`.

## Principles

No hallucination · field-level traceability · mixed AI and human audit · configuration separate
from code · corpus separate from the repository. Details in `framework/maestro_framework.md`.

## Language

The framework documents, configuration comments and agent instructions (`CLAUDE.md`) are in
Spanish, the working language of the reviews it was built for. Article content is kept in its
original language.

## Authorship and license

**Carlos David Ascencio Mera** designed the method, the review criteria, the audit rules and the
decisions recorded in `proyecto/sistema/registro_sistema.md`, and tested the pipeline on real
reviews. **Mnemiic**, his artificial intelligence assistant, wrote most of the code and the
documentation under that direction.

Licensed under [Creative Commons Attribution-NonCommercial 4.0 International](LICENSE)
(CC BY-NC 4.0). You may use and adapt it with attribution, for non-commercial purposes.
