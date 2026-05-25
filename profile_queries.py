"""
profile_queries.py — Profiler de consultas DB de Dinamo Rent

Ejecuta cada consulta que se llama desde los métodos cargar_datos()
de todas las vistas, mide tiempos con time.perf_counter, y reporta
un ranking ordenado por duración para identificar cuellos de botella.

Uso:
    python profile_queries.py
"""

import time
import sys
from typing import Callable, Any

# ── Configurar logging silencioso antes de importar la app ──────────────
import logging
logging.basicConfig(level=logging.WARNING)
for name in ["core.logger", "core.database_sa", "repositories", "services"]:
    logging.getLogger(name).setLevel(logging.WARNING)


# ── Inicializar DB ─────────────────────────────────────────────────────
from core.database_sa import init_db, get_engine, get_session
from core.config import DB_ENGINE

print("=" * 70)
print("  DINAMO RENT — Profiler de Consultas DB")
print("=" * 70)
print(f"  Motor: {DB_ENGINE.upper()}")
print()

# Inicializar engine + tablas
init_db()

# Contar registros en cada tabla
from core.models import Auto, Cliente, Renta, Reserva, Comparendo, Gasto, MantenimientoVehiculo, Pago, Usuario, Inspeccion

_tables = {
    "Autos": Auto,
    "Clientes": Cliente,
    "Rentas": Renta,
    "Reservas": Reserva,
    "Comparendos": Comparendo,
    "Gastos": Gasto,
    "Mantenimiento": MantenimientoVehiculo,
    "Pagos": Pago,
    "Usuarios": Usuario,
    "Inspecciones": Inspeccion,
}

with get_session() as s:
    print("  Registros en BD:")
    for name, model in _tables.items():
        count = s.query(model).count()
        print(f"    {name:20s}: {count:>6}")
print()

# ── Utilities de profiling ──────────────────────────────────────────────

def time_query(name: str, fn: Callable, *args, **kwargs) -> float:
    """Ejecuta fn, mide tiempo en ms, imprime resultado. Retorna duración."""
    # Warmup — descartar primera ejecución (cache frío)
    try:
        fn(*args, **kwargs)
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        return 0.0

    # Medición real
    start = time.perf_counter()
    try:
        result = fn(*args, **kwargs)
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        return 0.0
    elapsed = (time.perf_counter() - start) * 1000  # ms

    row_count = 0
    if isinstance(result, list):
        row_count = len(result)
    elif isinstance(result, dict):
        row_count = len(result)
    elif hasattr(result, 'get'):
        row_count = len(result)

    label = f"  {name:55s}"
    print(f"{label} {elapsed:>8.2f} ms  ({row_count} rows)")
    return elapsed


def time_service(name: str, fn: Callable) -> float:
    """Igual que time_query pero para servicios sin args."""
    try:
        fn()
    except Exception:
        pass  # warmup descartado
    start = time.perf_counter()
    try:
        result = fn()
    except Exception as e:
        print(f"  [ERROR] {name}: {e}")
        return 0.0
    elapsed = (time.perf_counter() - start) * 1000

    row_count = 0
    if isinstance(result, list):
        row_count = len(result)
    elif isinstance(result, dict):
        row_count = len(result)

    label = f"  {name:55s}"
    print(f"{label} {elapsed:>8.2f} ms  ({row_count} rows)")
    return elapsed


# ══════════════════════════════════════════════════════════════════════════
# PERFIL DE CONSULTAS — Agrupadas por Vista/Servicio
# ══════════════════════════════════════════════════════════════════════════

results: list[tuple[str, float, int]] = []  # (name, elapsed_ms, rows)

def t(name, fn, *a, **kw):
    elapsed = time_query(name, fn, *a, **kw)
    return elapsed

def ts(name, fn):
    elapsed = time_service(name, fn)
    return elapsed

# ── Repositorios individuales ───────────────────────────────────────────

print("\n" + "-" * 70)
print("  REPOSITORIOS (queries individuales)")
print("-" * 70)

from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
    ClienteRepositorySA,
    ComparendoRepositorySA,
    GastoRepositorySA,
    ReservaRepositorySA,
    MantenimientoRepositorySA,
    AlertaRepositorySA,
    UsuarioRepositorySA,
    InformeRepositorySA,
)

t("AutoRepositorySA.obtener_todos()", AutoRepositorySA.obtener_todos)
t("AutoRepositorySA.obtener_disponibles()", AutoRepositorySA.obtener_disponibles)
t("AutoRepositorySA.obtener_alertas_flota()", AutoRepositorySA.obtener_alertas_flota)

t("RentaRepositorySA.obtener_activas()", RentaRepositorySA.obtener_activas)

t("ClienteRepositorySA.buscar('')", ClienteRepositorySA.buscar, "")

t("ComparendoRepositorySA.obtener_todos()", ComparendoRepositorySA.obtener_todos)

t("GastoRepositorySA.obtener_todos(200)", GastoRepositorySA.obtener_todos, 200)

t("ReservaRepositorySA.obtener_todas()", ReservaRepositorySA.obtener_todas)

t("MantenimientoRepositorySA.obtener_historial(50)", MantenimientoRepositorySA.obtener_historial, 50)
t("MantenimientoRepositorySA.obtener_autos_con_km()", MantenimientoRepositorySA.obtener_autos_con_km)

t("AlertaRepositorySA.obtener_rentas_por_vencer()", AlertaRepositorySA.obtener_rentas_por_vencer)
t("AlertaRepositorySA.obtener_documentos_por_vencer()", AlertaRepositorySA.obtener_documentos_por_vencer)
t("AlertaRepositorySA.obtener_mantenimientos_proximos()", AlertaRepositorySA.obtener_mantenimientos_proximos)

t("UsuarioRepositorySA.obtener_todos()", UsuarioRepositorySA.obtener_todos)

# ── Consultas compuestas (informes con SQL raw / GROUP BY) ──────────────

print()
print("  INFORMES / ANALÍTICAS (queries agrupadas)")
print("-" * 70)

t("InformeRepositorySA.obtener_balance_consolidado()", InformeRepositorySA.obtener_balance_consolidado)
t("InformeRepositorySA.obtener_ingresos_por_vehiculo()", InformeRepositorySA.obtener_ingresos_por_vehiculo)
t("InformeRepositorySA.obtener_mantenimiento_por_vehiculo()", InformeRepositorySA.obtener_mantenimiento_por_vehiculo)
t("InformeRepositorySA.obtener_gastos_por_vehiculo()", InformeRepositorySA.obtener_gastos_por_vehiculo)

# ── Servicios compuestos (múltiples queries internas) ───────────────────

print()
print("  SERVICIOS COMPUESTOS (llaman 2+ repositories)")
print("-" * 70)

from services.dashboard_service import DashboardService
from services.informe_service import InformeService
from services.financial_service import FinancialService
from services.alerta_service import AlertaService
from services.auto_service import AutoService

ts("DashboardService.kpi_globales()", DashboardService.kpi_globales)
ts("DashboardService.obtener_resumen_financiero()", DashboardService.obtener_resumen_financiero)
ts("DashboardService.obtener_alertas()", DashboardService.obtener_alertas)
ts("InformeService.balance_mensual_real()", InformeService.balance_mensual_real)
ts("FinancialService.roi_flota()", FinancialService.roi_flota)
ts("AutoService.obtener_alertas()", AutoService.obtener_alertas)
ts("AlertaService.obtener_todas_las_alertas()", AlertaService.obtener_todas_las_alertas)

# ── Resumen por Vista (simula los cargar_datos completos) ──────────────

print()
print("  SIMULACIÓN VISTAS (todo lo que carga cada pantalla)")
print("-" * 70)

# Dashboard: kpi_globales + obtener_alertas + obtener_resumen_financiero
print()
print("  >> Dashboard (3 services)")
start = time.perf_counter()
DashboardService.kpi_globales()
AutoService.obtener_alertas()
DashboardService.obtener_resumen_financiero()
elapsed = (time.perf_counter() - start) * 1000
print(f"  {'Dashboard completo':55s} {elapsed:>8.2f} ms")

# Autos: listar + obtener_alertas
print("  >> Autos (2 repos)")
start = time.perf_counter()
AutoRepositorySA.obtener_todos()
AutoRepositorySA.obtener_alertas_flota()
elapsed = (time.perf_counter() - start) * 1000
print(f"  {'Autos completo':55s} {elapsed:>8.2f} ms")

# Alertas: obtener_todas_las_alertas (3 queries internas)
print("  >> Alertas (1 service, 3 repos internos)")
start = time.perf_counter()
AlertaService.obtener_todas_las_alertas()
elapsed = (time.perf_counter() - start) * 1000
print(f"  {'Alertas completo':55s} {elapsed:>8.2f} ms")

# Informes: balance_mensual_real + roi_flota
print("  >> Informes (2 services)")
start = time.perf_counter()
InformeService.balance_mensual_real()
FinancialService.roi_flota()
elapsed = (time.perf_counter() - start) * 1000
print(f"  {'Informes completo':55s} {elapsed:>8.2f} ms")

# ══════════════════════════════════════════════════════════════════════════
# RANKING FINAL
# ══════════════════════════════════════════════════════════════════════════

print()
print("=" * 70)
print("  RANKING — Consultas más lentas")
print("=" * 70)
print(f"  {'#':>3}  {'Consulta':55s} {'Tiempo':>10}")
print("  " + "-" * 70)

all_calls = [
    ("AutoRepositorySA.obtener_todos()", None, None),
    ("AutoRepositorySA.obtener_disponibles()", None, None),
    ("AutoRepositorySA.obtener_alertas_flota()", None, None),
    ("RentaRepositorySA.obtener_activas()", None, None),
    ("ClienteRepositorySA.buscar('')", None, None),
    ("ComparendoRepositorySA.obtener_todos()", None, None),
    ("GastoRepositorySA.obtener_todos(200)", None, None),
    ("ReservaRepositorySA.obtener_todas()", None, None),
    ("MantenimientoRepositorySA.obtener_historial(50)", None, None),
    ("MantenimientoRepositorySA.obtener_autos_con_km()", None, None),
    ("AlertaRepositorySA.obtener_rentas_por_vencer()", None, None),
    ("AlertaRepositorySA.obtener_documentos_por_vencer()", None, None),
    ("AlertaRepositorySA.obtener_mantenimientos_proximos()", None, None),
    ("UsuarioRepositorySA.obtener_todos()", None, None),
    ("InformeRepositorySA.obtener_balance_consolidado()", None, None),
    ("InformeRepositorySA.obtener_ingresos_por_vehiculo()", None, None),
    ("InformeRepositorySA.obtener_mantenimiento_por_vehiculo()", None, None),
    ("InformeRepositorySA.obtener_gastos_por_vehiculo()", None, None),
]

# Time each one fresh for the ranking
ranked = []
for name, _, _ in all_calls:
    start = time.perf_counter()
    try:
        # Resolve and call
        parts = name.split("(")[0].split(".")
        mod_name = ".".join(parts[:-1])
        fn_name = parts[-1]
        # Just use eval for simplicity in a profiling script
        obj = eval(mod_name)
        fn = getattr(obj, fn_name)
        if "200" in name:
            result = fn(200)
        else:
            result = fn()
    except Exception as e:
        elapsed = 0.0
    else:
        elapsed = (time.perf_counter() - start) * 1000
    row_count = len(result) if isinstance(result, list) else 0
    ranked.append((elapsed, name, row_count))

ranked.sort(key=lambda x: x[0], reverse=True)

for i, (elapsed, name, rows) in enumerate(ranked, 1):
    print(f"  {i:>3}  {name:55s} {elapsed:>8.2f} ms  ({rows} rows)")

print()
print("=" * 70)
print("  RECOMENDACIONES")
print("=" * 70)
print()
slowest = ranked[0][0] if ranked else 0
if slowest > 200:
    print("  ⚠️  Consultas lentas detectadas (>200ms):")
    for elapsed, name, rows in ranked:
        if elapsed > 200:
            print(f"     • {name} ({elapsed:.0f} ms, {rows} rows)")
    print()
    print("  Sugerencias:")
    print("    1. Agregar índices compuestos en columnas usadas en WHERE/ORDER BY")
    print("    2. Limitar columnas SELECT (no SELECT *) si hay tablas grandes")
    print("    3. Considerar vistas materializadas o tablas resumen para informes")
else:
    print(f"  ✅ Consultas rápidas (máx {slowest:.0f} ms). Sin cuellos de botella evidentes.")
print()
print("  Nota: Los tiempos en desarrollo (SQLite local) suelen ser")
print("  menores que en producción (MySQL remoto). Monitorear en ambos entornos.")
print()
