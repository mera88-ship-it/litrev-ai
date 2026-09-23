"""Hook SessionStart — carga de la memoria del ámbito activo al abrir sesión.

Lo ejecuta Claude Code al iniciar la sesión (configurado en .claude/settings.json).
Carga la memoria del ÁMBITO activo y la imprime en stdout (se incorpora al contexto):

  - modo CONSTRUCCIÓN (tema sin definir): proyecto/sistema/  (estado + último log)
  - modo REVISIÓN     (tema definido):    proyecto/revision/ (estado + último log)

El ámbito se detecta leyendo config/proyecto.yaml (sin depender de PyYAML): si aún
contiene «TEMA POR DEFINIR», estamos construyendo el sistema; si no, ejecutando un tema.

Coste de tokens mínimo y una sola vez por sesión. Si algo no existe, no falla.
"""
import sys
from pathlib import Path

# UTF-8 en stdout para que el hook entregue acentos correctos en Windows.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PROYECTO = ROOT / "proyecto"
SISTEMA = PROYECTO / "sistema"
REVISION = PROYECTO / "revision"
PROYECTO_YAML = ROOT / "config" / "proyecto.yaml"
MAX_LINEAS = 160


def _modo_revision() -> bool:
    """True si hay un tema definido (config/proyecto.yaml ya no es plantilla)."""
    try:
        texto = PROYECTO_YAML.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "TEMA POR DEFINIR" not in texto


def _imprimir(titulo, path, max_lineas=MAX_LINEAS):
    if not path.exists():
        return
    lineas = path.read_text(encoding="utf-8", errors="replace").splitlines()
    print(f"\n===== {titulo}: {path.name} =====")
    print("\n".join(lineas[:max_lineas]))
    if len(lineas) > max_lineas:
        print(f"... ({len(lineas) - max_lineas} líneas más en {path})")


def _ultimo_log(logs_dir):
    sesiones = sorted(logs_dir.glob("sesion_*.md")) if logs_dir.exists() else []
    return sesiones[-1] if sesiones else None


def main():
    print("## Memoria del proyecto (carga automática de inicio de sesión)")

    if _modo_revision():
        print("\n_Ámbito activo: **REVISIÓN** (hay un tema definido)._")
        _imprimir("Estado de la revisión", REVISION / "estado_revision.md")
        log = _ultimo_log(REVISION / "logs")
        if log:
            _imprimir("Último log de revisión", log, max_lineas=120)
        else:
            print("\n(No hay logs de revisión todavía.)")
        print("\n> La memoria de cómo se construyó la herramienta está en proyecto/sistema/.")
    else:
        print("\n_Ámbito activo: **CONSTRUCCIÓN** del sistema (tema sin definir)._")
        _imprimir("Estado del sistema", SISTEMA / "estado_sistema.md")
        log = _ultimo_log(SISTEMA / "logs")
        if log:
            _imprimir("Último log de construcción", log, max_lineas=120)
        else:
            print("\n(No hay logs de construcción todavía.)")
        print("\n> Para definir un tema y empezar a ejecutar, sigue la Fase 0 "
              "(framework/fase0_definicion.md).")

    print("\n> Recordatorio de cierre: actualiza el estado del ámbito, registra decisiones y crea "
          "el log de sesión en la carpeta correspondiente (proyecto/sistema/ o proyecto/revision/). "
          "Ver framework/memoria_proyecto.md.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # noqa: BLE001 — el hook nunca debe romper el arranque
        print(f"(memoria_session_start: aviso: {e})", file=sys.stderr)
