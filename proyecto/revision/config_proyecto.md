# Configuración del proyecto

> La configuración **operativa** (queries, criterios, prioridad, umbrales) vive en
> archivos YAML legibles y versionables:
>
> - [`config/proyecto.yaml`](../config/proyecto.yaml) — tema, objetivos, alcance, descarga, LLM, umbrales
> - [`config/busqueda.yaml`](../config/busqueda.yaml) — queries de OpenAlex / Semantic Scholar, filtros
> - [`config/prioridad.yaml`](../config/prioridad.yaml) — vocabularios, pesos y reglas de la escala P0–P4
>
> Los archivos de `config/` están comentados campo por campo.

Este documento es para el **contexto narrativo** que no cabe en el YAML: justificación del
recorte, decisiones de alcance, notas de las fuentes, supuestos. La fuente de verdad de los
parámetros es siempre el YAML.

## Contexto del proyecto

_(Completar en la Fase 0.)_

- **Tema y por qué importa:** [...]
- **Recorte y supuestos:** [...]
- **Fuentes consideradas más allá de las APIs:** [...]
- **Notas sobre la escala de prioridad:** [por qué se definieron así los niveles P0–P4]
