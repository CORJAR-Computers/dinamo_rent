"""
Profile startup performance: Measure import times and widget creation times.
Uses offscreen Qt platform for headless profiling.
"""

import sys
import os
import time

# Must set before importing Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

SEP = "=" * 60

# ── Phase 1: Module Import Times ─────────────────────────────────────────────
print(SEP)
print("PHASE 1: MODULE IMPORT TIMES")
print(SEP)

modules_to_test = [
    "core.config",
    "core.logger",
    "core.database_sa",
    "core.models",
    "core.exceptions",
    "core.security",
    "services.auth_service",
    "services.dashboard_service",
    "services.auto_service",
    "services.cliente_service",
    "services.renta_service",
    "services.reserva_service",
    "views.dashboard_view",
    "views.rentas_view",
    "views.reservas_view",
    "views.clientes_view",
    "views.autos_view",
    "views.mantenimiento_view",
    "views.gastos_view",
    "views.comparendos_view",
    "views.usuarios_view",
    "views.informes_view",
    "views.alertas_view",
    "views.calendario_view",
]

# Just measure all import times together (like real startup)
t0 = time.perf_counter()
for mod_name in modules_to_test:
    __import__(mod_name)
total_import_time = time.perf_counter() - t0
print(f"  Total import time (all modules): {total_import_time*1000:.2f}ms")

# Individual measurements
print()
print("  Individual import times:")
t0 = time.perf_counter()
last = t0
for mod_name in modules_to_test:
    __import__(mod_name)
    now = time.perf_counter()
    elapsed = now - last
    last = now
    print(f"    {mod_name:40s}  {elapsed*1000:8.2f}ms")

total_import_time2 = time.perf_counter() - t0
print(f"\n  Total import time (re-import from cache): {total_import_time2*1000:.2f}ms")
print(f"  (Second pass - all modules already cached)")

print()
print(SEP)
print("PHASE 2: Qt APPLICATION + WIDGET INIT")
print(SEP)

# Now initialize Qt
from PySide6.QtWidgets import QApplication, QWidget
from PySide6.QtCore import QTimer

# Also import the theme manager
from views.themes.theme_manager import apply_theme

t0 = time.perf_counter()
app = QApplication(sys.argv)
app.setStyle("Fusion")
# Apply theme (as done in main_qt.py)
apply_theme()
app_create_time = time.perf_counter() - t0
print(f"  QApplication create + theme apply: {app_create_time*1000:.2f}ms")

# Import widget classes
from views.dashboard_view import DashboardWidget
from views.rentas_view import RentasWidget
from views.reservas_view import ReservasWidget
from views.clientes_view import ClientesWidget
from views.autos_view import AutosWidget
from views.mantenimiento_view import MantenimientoWidget
from views.gastos_view import GastosWidget
from views.comparendos_view import ComparendosWidget
from views.usuarios_view import UsuariosWidget
from views.informes_view import InformesWidget
from views.alertas_view import AlertasWidget
from views.calendario_view import CalendarioWidget

widget_classes = [
    ("DashboardWidget", DashboardWidget),
    ("RentasWidget", RentasWidget),
    ("ReservasWidget", ReservasWidget),
    ("ClientesWidget", ClientesWidget),
    ("AutosWidget", AutosWidget),
    ("MantenimientoWidget", MantenimientoWidget),
    ("GastosWidget", GastosWidget),
    ("ComparendosWidget", ComparendosWidget),
    ("UsuariosWidget", UsuariosWidget),
    ("InformesWidget", InformesWidget),
    ("AlertasWidget", AlertasWidget),
    ("CalendarioWidget", CalendarioWidget),
]

widget_times = []
total_widget_time = 0.0

for name, cls in widget_classes:
    t0 = time.perf_counter()
    try:
        instance = cls(session_id="test")
        elapsed = time.perf_counter() - t0
        total_widget_time += elapsed
        widget_times.append((name, elapsed, "OK"))
        print(f"  + {name:30s}  {elapsed*1000:8.2f}ms")
    except Exception as e:
        elapsed = time.perf_counter() - t0
        widget_times.append((name, elapsed, f"FAILED: {e}"))
        print(f"  ! {name:30s}  {elapsed*1000:8.2f}ms  FAILED: {str(e)[:60]}")

# Process pending events to let deferred QTimer callbacks fire
t0 = time.perf_counter()
for _ in range(5):
    QApplication.processEvents()
    QTimer.singleShot(0, lambda: None)
    QApplication.processEvents()
process_time = time.perf_counter() - t0

print()
print(SEP)
print("FINAL SUMMARY")
print(SEP)
print(f"  Module imports:            {total_import_time*1000:8.2f}ms")
print(f"  QApp creation + theme:     {app_create_time*1000:8.2f}ms")
print(f"  Widget initializations:    {total_widget_time*1000:8.2f}ms")
print(f"  Deferred events processed: {process_time*1000:8.2f}ms")
print(f"  ---")
print(f"  Total (imports + widgets): {(total_import_time + total_widget_time)*1000:8.2f}ms")
print()
print("Note: Excludes splash screen rendering, login dialog, and DB init.")

# Cleanup
for _, _, status, *_ in [()]:
    pass
for name, cls in widget_classes:
    try:
        inst = cls(session_id="test")
        inst.deleteLater()
    except:
        pass

app.quit()
