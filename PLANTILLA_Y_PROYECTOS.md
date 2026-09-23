# Plantilla y proyectos — cómo trabajar sin contaminar la plantilla

Este repositorio (`litrev-ai`) es la **plantilla central**: la herramienta LITREV-AI.
Aquí solo se hacen **cambios técnicos** (código, framework, mejoras del método). Un tema concreto
de revisión **nunca** se define aquí.

Cada **revisión real** se ejecuta en una **copia aparte** —su propio repositorio en GitHub y su
propia carpeta en tu PC— para que sus archivos, su memoria y su corpus no ensucien la plantilla.

## Qué es de la plantilla y qué es de cada proyecto

| Permanente (vive en la plantilla) | Del tema (vive en cada proyecto) |
|-----------------------------------|----------------------------------|
| `litrev_core/`, `fase1_seleccion/`, `tools/`, `framework/` | `config/*.yaml` ya rellenados con el tema |
| Esta guía, `CLAUDE.md`, `README.md` | `proyecto/revision/` (memoria de esa revisión) |
| `proyecto/sistema/` (cómo se construye la herramienta) | `data/` (corpus: PDFs, Markdown, Excel…) — siempre fuera de git |

**Regla de oro: nada del tema vive en el código.** Por eso el código es *idéntico* en la plantilla
y en todos los proyectos; y por eso llevar un arreglo de un lado a otro es solo **copiar un
archivo**, sin conflictos.

## Crear un proyecto nuevo

Los proyectos viven en `…\Documents\proyectos-revision-literatura\` (carpeta separada de otros
tipos de trabajo, cada proyecto en su subcarpeta). `gh` (GitHub CLI) ya está instalado y
autenticado en este equipo.

**Forma rápida (recomendada) — comando-ayuda:**

```
powershell -ExecutionPolicy Bypass -File tools\nuevo_proyecto.ps1 "teletrabajo"
```

Crea el repo privado `litrev-teletrabajo` desde la plantilla y lo clona en
`…\proyectos-revision-literatura\litrev-teletrabajo`. También puedes pedírselo a Claude:
**«iniciemos el proyecto teletrabajo»**.

Después: abre Claude Code **en esa carpeta** y corre la **Fase 0** (`framework/fase0_definicion.md`)
para definir tema, objetivos y criterios; de ahí se derivan `config/busqueda.yaml` y
`config/prioridad.yaml`. El corpus va en `data/` (ya gitignored); para tenerlo en Google Drive,
define `LITREV_DATA_DIR` apuntando a la carpeta de Drive.

**Forma manual (por la web), si algún día no usas el comando:**

1. En GitHub, la plantilla → **«Use this template»** → **«Create a new repository»**; nómbralo
   `litrev-<tema>`, **Privado**.
2. Clónalo dentro de `…\Documents\proyectos-revision-literatura\`.
3. Abre Claude Code ahí y corre la Fase 0.

## Llevar un arreglo técnico de vuelta a la plantilla

Si trabajando en un proyecto aparece un problema en el **código** (no en la configuración del tema):

1. Lo arreglamos y probamos en el proyecto.
2. Copiamos **solo el/los archivo(s) de código corregido(s)** (p. ej. de `litrev_core/` o
   `fase1_seleccion/`) a la carpeta de la plantilla.
3. En la plantilla: `commit` + `push` a `main`. El arreglo queda en el centro.
4. *(Opcional)* Copiamos ese mismo archivo a los otros proyectos activos que lo necesiten.

Es seguro porque esos archivos no contienen nada del tema: no hay conflictos posibles. En la
práctica, basta con que le digas a Claude **«lleva este arreglo a la plantilla»** y lo hace.

## Lo que NO debe pasar

- **No** definir un tema en la plantilla: su `config/proyecto.yaml` se queda en `[TEMA POR DEFINIR]`.
- **No** subir el corpus a git (ya lo impide `.gitignore`).
- **No** editar `litrev_core/` ni `framework/` dentro de un proyecto para cosas del tema:
  eso va en `config/` y en `proyecto/revision/`.

## Estado de la configuración en GitHub

Este repo **ya está marcado como plantilla** (`isTemplate: true`) y es **privado**, por lo que el
botón «Use this template» está disponible. Para dejarlo igual en otro equipo: instala `gh`, haz
`gh auth login` una vez y, si hiciera falta, `gh repo edit <owner>/litrev-ai --template`.
