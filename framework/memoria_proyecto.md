# Memoria del proyecto — modelo, ritual y formatos de registro

Cómo el proyecto recuerda lo que se hace, por qué se decide y qué se complica, a través de las
sesiones. Documento canónico de la memoria; `CLAUDE.md` resume el ritual y remite aquí.

## Dos ámbitos de memoria

La memoria está separada en dos ámbitos, porque **construir la herramienta** y **ejecutar una
revisión temática** son cosas distintas y no deben mezclarse:

| Ámbito | Carpeta | De qué trata |
|--------|---------|--------------|
| **SISTEMA** (construcción) | `proyecto/sistema/` | cómo se construye y afina LITREV-AI; permanece entre temas |
| **REVISIÓN** (ejecución) | `proyecto/revision/` | cómo va la revisión de un tema concreto (corpus, decisiones del tema) |

Al **abrir** sesión, el hook `SessionStart` (`tools/memoria_session_start.py`) **detecta el ámbito
activo**: si `config/proyecto.yaml` aún dice `[TEMA POR DEFINIR]` es CONSTRUCCIÓN; si ya hay un tema,
es REVISIÓN. Carga la memoria de ese ámbito. La escritura al **cerrar** la hago yo (ritual abajo),
en la carpeta del ámbito en que se trabajó.

## Capas de cada ámbito

| Capa | SISTEMA | REVISIÓN | Quién escribe |
|------|---------|----------|---------------|
| **Checkpoint (máquina)** | — | `data/estado.json` | scripts (`litrev_core.estado`) |
| **Progreso (humano)** | `sistema/estado_sistema.md` | `revision/estado_revision.md` | Claude al cerrar |
| **Decisiones** | `sistema/registro_sistema.md` | `revision/registro_revision.md` | Claude al decidir |
| **Bitácora** | `sistema/logs/sesion_NNN.md` | `revision/logs/sesion_NNN.md` | Claude al cerrar |

`data/estado.json` (checkpoint automático de los scripts) pertenece a la ejecución y vive en
`data/`, fuera de git. La numeración de sesiones es **secuencial dentro de cada ámbito**.

## Layout

```
proyecto/
  sistema/                 (construcción de la herramienta)
    estado_sistema.md      progreso de lo construido
    registro_sistema.md    decisiones D{n} de construcción + incidencias I{n}
    logs/                  sesion_NNN.md, _plantilla_sesion.md
  revision/                (ejecución de un tema)
    config_proyecto.md     narrativa del recorte del tema (el porqué)
    estado_revision.md     progreso de los pasos y tabla de corpus
    registro_revision.md   decisiones D{n} del tema (definición de Fase 0, ajustes)
    logs/                  sesion_NNN.md, _plantilla_sesion.md
```

## Ritual de sesión

### Apertura (automática + verificación)
1. El hook `SessionStart` ya cargó el estado y el último log del **ámbito activo**.
2. Confirmar la fase/paso pendiente antes de actuar. En REVISIÓN, si algo no cuadra con
   `data/estado.json`, resolver la discrepancia primero.

### Cierre (lo ejecuto cuando el trabajo de la sesión termina o el investigador lo pide)
Escribir en la carpeta del **ámbito en que se trabajó** (`sistema/` o `revision/`):
1. **Actualizar el estado** (`estado_sistema.md` o `estado_revision.md`).
2. **Registrar decisiones** nuevas (formato D{n}) en el registro del ámbito.
3. **Registrar incidencias** técnicas relevantes (formato I{n}).
4. **Crear `logs/sesion_NNN.md`** copiando `_plantilla_sesion.md` y llenándolo.
5. Dejar explícitos los **pendientes** para la próxima sesión.

> El cierre no se automatiza con un hook `Stop` porque ese hook se dispararía en cada turno y
> gastaría tokens innecesariamente. La garantía es este ritual + el recordatorio del `SessionStart`.

## Formatos de registro

### (a) Log de sesión
Usar la plantilla `_plantilla_sesion.md` del ámbito. Un archivo por sesión, secuencial por ámbito.

### (b) Decisión metodológica o técnica — registro del ámbito
```
### D{n} — {título corto} ({AAAA-MM-DD}, sesión {NNN})
- **Tipo:** metodológica | técnica
- **Contexto:** qué problema o disyuntiva la motivó.
- **Alternativas consideradas:** opciones evaluadas.
- **Decisión:** qué se eligió.
- **Justificación:** por qué, frente a las alternativas.
- **Consecuencias:** qué implica (incluye lo que se renuncia).
```

### (c) Incidencia técnica — registro del ámbito (sección Incidencias)
```
### I{n} — {síntoma corto} ({AAAA-MM-DD}, sesión {NNN})
- **Síntoma:** qué se observó (mensaje de error, comportamiento).
- **Causa:** causa raíz si se identificó (o "no determinada").
- **Resolución:** qué se hizo, o el workaround aplicado.
- **Estado:** resuelta | mitigada | pendiente.
- **Prevención:** cómo evitar que reaparezca (regla, validación, nota en config).
```

## Regla
Registrar **por decisión y por sesión, no por cada acción**. Las decisiones sobre la **herramienta**
van a `sistema/registro_sistema.md`; las de una **revisión** concreta, a
`revision/registro_revision.md`. La fuente de verdad de los parámetros del proyecto sigue siendo
`config/*.yaml`; esta memoria explica el *porqué* y el *cuándo*.
