"""
profile_imports.py — Mide tiempos de import individual de cada modulo vista
y reporta que dependencias son las mas lentas.

Uso: python profile_imports.py
"""

import importlib
import sys
import time
from collections import OrderedDict
from pathlib import Path

# Forzar UTF-8 para evitar UnicodeEncodeError en Windows
try:
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
except Exception:
    pass

# Asegurar que el proyecto esta en sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

# Lista de modulos vista y otros modulos pesados candidatos
MODULOS_A_PERFILAR = [
    # Vistas principales
    "views.dashboard_view",
    "views.autos_view",
    "views.rentas_view",
    "views.reservas_view",
    "views.clientes_view",
    "views.alertas_view",
    "views.calendario_view",
    "views.comparendos_view",
    "views.gastos_view",
    "views.informes_view",
    "views.mantenimiento_view",
    "views.usuarios_view",
    "views.pagos_view",
    "views.cierre_renta_view",
    "views.setup_wizard",
    # Modulos core y soporte pesados
    "views.styles",
    "views.base_widget",
    "views.components.loading_spinner",
    "views.components.modern_messagebox",
    "views.components.toast_notification",
    "views.themes.theme_manager",
    "views.themes.build_stylesheet",
    "views.layouts.form_helpers",
    # Servicios
    "services.dashboard_service",
    "services.auto_service",
    "services.renta_service",
    "services.informe_service",
    "services.financial_service",
    "services.backup_service",
    "core.config",
    "main_qt",
]

# ── Import individual con medicion ─────────────────────────────────────

def medir_import(module_name: str) -> dict:
    """Importa el modulo desde un estado limpio y mide el tiempo."""
    # Sacar el modulo de sys.modules si ya esta cached
    if module_name in sys.modules:
        del sys.modules[module_name]

    # Limpiar tambien submodulos que ya existan
    to_remove = [k for k in sys.modules.keys() if k.startswith(module_name + ".")]
    for k in to_remove:
        del sys.modules[k]

    start = time.perf_counter()
    try:
        importlib.import_module(module_name)
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "module": module_name,
            "time_ms": round(elapsed_ms, 2),
            "status": "ok",
            "error": None,
        }
    except Exception as e:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "module": module_name,
            "time_ms": round(elapsed_ms, 2),
            "status": "error",
            "error": repr(e),
        }


# ── Main ───────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  PROFILER DE IMPORTS - Modulos Vista")
    print("=" * 70)
    print()
    print("  [FASE 1] Import individual")
    print()

    resultados = OrderedDict()

    # Pre-importar PySide6 una vez (es enorme, pero necesario)
    sys.modules["PySide6"] = importlib.import_module("PySide6")

    for mod_name in MODULOS_A_PERFILAR:
        r = medir_import(mod_name)
        resultados[mod_name] = r

        # Mostrar barra visual
        bar_len = 50
        filled = min(int(r["time_ms"] / 10), bar_len)
        bar = "#" * filled + "." * (bar_len - filled)
        label = f"{r['module']:45s}"
        time_str = f"{r['time_ms']:>8.2f} ms"
        ok = "[OK]" if r["status"] == "ok" else "[ERR]"
        print(f"  {ok} {label} {bar} {time_str}")
        if r["error"]:
            print(f"       Error: {r['error']}")

    # Fase 2: Top 10 mas lentos
    print()
    print("=" * 70)
    print("  TOP 10 MAS LENTOS")
    print("=" * 70)

    sorted_results = sorted(resultados.values(), key=lambda x: x["time_ms"], reverse=True)
    for i, r in enumerate(sorted_results[:10], 1):
        print(f"  {i:2d}. {r['module']:50s} {r['time_ms']:>8.2f} ms  {r['status']}")

    # Fase 3: Candidatos a lazy import
    print()
    print("=" * 70)
    print("  ANALISIS: Candidatos a Lazy Import")
    print("=" * 70)

    heavies = [r for r in resultados.values() if r["status"] == "ok" and r["time_ms"] > 30]
    if heavies:
        print(f"\n  Modulos que tardan >30ms (candidatos a lazy import):")
        for r in sorted(heavies, key=lambda x: x["time_ms"], reverse=True):
            print(f"    - {r['module']:45s} {r['time_ms']:>8.2f} ms")
    else:
        print("\n  Todos los imports individuales estan por debajo de 30ms.")

    # Tiempo total
    total = sum(r["time_ms"] for r in resultados.values() if r["status"] == "ok")
    print(f"\n  Tiempo total de imports: {total:.2f} ms")
    print()

    # Guardar resultados a archivo
    with open("profile_imports_results.txt", "w", encoding="utf-8") as f:
        f.write("PROFILE IMPORTS RESULTS\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"{'Module':45s} {'Time (ms)':>10s} {'Status':>10s}\n")
        f.write("-" * 70 + "\n")
        for r in sorted(resultados.values(), key=lambda x: x["time_ms"], reverse=True):
            f.write(f"{r['module']:45s} {r['time_ms']:>10.2f} {r['status']:>10s}\n")
        f.write("\n\nTOP 10 SLOWEST:\n")
        for i, r in enumerate(sorted_results[:10], 1):
            f.write(f"  {i}. {r['module']} -- {r['time_ms']} ms\n")

    print("  Resultados guardados en: profile_imports_results.txt\n")


if __name__ == "__main__":
    main()
