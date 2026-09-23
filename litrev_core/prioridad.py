"""
litrev_core.prioridad — Motor híbrido de clasificación de prioridad.

Parte determinista (regex + reglas + score) del esquema híbrido. Lee
TODA su lógica de config/prioridad.yaml, de modo que cambiar de tema no
toca el código. Lo que queda en zona gris (franja de score límite,
señales en conflicto, texto insuficiente) se marca como DUDOSO para que
Claude lo desempate leyendo el artículo (parte LLM del híbrido).

Seguridad: 'condicion' se evalúa con eval restringido (sin builtins) y
solo con los flags de vocabulario como nombres. El archivo de prioridad
lo escribe el investigador; no cargar reglas de fuentes no confiables.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field


class ConfigPrioridadError(ValueError):
    """Error de configuración en prioridad.yaml (regex inválida, nombre desconocido, etc.)."""


@dataclass
class ResultadoPrioridad:
    prioridad: str
    razon: str
    score: int
    confianza: str            # "alta" | "dudosa"
    regla_idx: int            # índice de la regla que coincidió (-1 si fallback)
    flags: dict = field(default_factory=dict)


class MotorPrioridad:
    def __init__(self, cfg: dict):
        self.niveles = cfg.get("niveles", {}) or {}
        if not self.niveles:
            raise ConfigPrioridadError("prioridad.yaml: falta la sección 'niveles'.")
        self.nivel_fallback = list(self.niveles)[-1]

        # Compilar vocabularios
        self.vocab: dict[str, list[re.Pattern]] = {}
        for nombre, patrones in (cfg.get("vocabularios", {}) or {}).items():
            if isinstance(patrones, str):
                patrones = [patrones]
            compilados = []
            for p in patrones:
                try:
                    compilados.append(re.compile(p, re.IGNORECASE))
                except re.error as e:
                    raise ConfigPrioridadError(
                        f"Regex inválida en vocabulario '{nombre}': {e}")
            self.vocab[nombre] = compilados

        score_cfg = cfg.get("score", {}) or {}
        self.score_base = int(score_cfg.get("base", 0))
        self.score_pesos = score_cfg.get("pesos", {}) or {}

        self.reglas = cfg.get("reglas", []) or []
        fd = cfg.get("franja_dudosa", {}) or {}
        self.score_min = fd.get("score_min")
        self.score_max = fd.get("score_max")
        self.conflictos = fd.get("conflictos", []) or []
        self.sin_texto_dudoso = bool(fd.get("marcar_sin_texto_como_dudoso", True))

    # ── evaluación ──────────────────────────────────────────────
    def _flags(self, texto: str) -> dict:
        return {nombre: any(p.search(texto) for p in patrones)
                for nombre, patrones in self.vocab.items()}

    def _score(self, flags: dict) -> int:
        total = self.score_base
        for nombre, activo in flags.items():
            if activo:
                total += int(self.score_pesos.get(nombre, 0))
        return max(0, min(100, total))

    def _eval(self, condicion: str, flags: dict) -> bool:
        try:
            return bool(eval(condicion, {"__builtins__": {}}, flags))  # noqa: S307 (config confiable)
        except NameError as e:
            raise ConfigPrioridadError(
                f"Condición usa un vocabulario inexistente: {condicion!r} → {e}")
        except SyntaxError as e:
            raise ConfigPrioridadError(f"Condición mal formada: {condicion!r} → {e}")

    def _en_franja(self, score: int) -> bool:
        return (self.score_min is not None and self.score_max is not None
                and self.score_min <= score <= self.score_max)

    def _hay_conflicto(self, flags: dict) -> bool:
        for par in self.conflictos:
            if len(par) == 2 and flags.get(par[0]) and flags.get(par[1]):
                return True
        return False

    def clasificar(self, articulo: dict) -> ResultadoPrioridad:
        titulo = articulo.get("titulo") or ""
        abstract = articulo.get("abstract") or ""
        texto = f"{titulo}. {abstract}"

        if len(texto.strip()) < 20:
            conf = "dudosa" if self.sin_texto_dudoso else "alta"
            return ResultadoPrioridad(self.nivel_fallback,
                                      "Sin título ni abstract suficiente para clasificar",
                                      0, conf, -1, {})

        flags = self._flags(texto)
        score = self._score(flags)

        prioridad, razon, regla_idx, regla = self.nivel_fallback, \
            "Sin coincidencia con reglas", -1, None
        for idx, r in enumerate(self.reglas):
            if self._eval(r.get("condicion", "False"), flags):
                prioridad = r.get("nivel", self.nivel_fallback)
                razon = r.get("razon", "")
                regla_idx, regla = idx, r
                break

        confianza = "alta"
        if (self._en_franja(score) or self._hay_conflicto(flags)
                or (regla and str(regla.get("confianza", "")).lower() == "dudosa")):
            confianza = "dudosa"

        return ResultadoPrioridad(prioridad, razon, score, confianza, regla_idx, flags)


def build_motor() -> MotorPrioridad:
    """Construye el motor desde config/prioridad.yaml."""
    from litrev_core.config import cfg_prioridad
    return MotorPrioridad(cfg_prioridad())
