"""
test_views_consistency.py — Verifica estándares de todas las vistas:

1. Todas heredan de BaseWidget
2. Todas tienen banner superior (create_banner o manual con gradiente)
"""

import importlib
import inspect
import re
import sys
from pathlib import Path

import pytest

# Asegurar que el project root esté en sys.path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from views.base_widget import BaseWidget


# ── Registro de todas las vistas del sistema ──────────────────────────────────
# Cada entrada: (nombre_clase, nombre_modulo)
WIDGET_CLASSES = [
    ("AlertasWidget", "views.alertas_view"),
    ("AutosWidget", "views.autos_view"),
    ("CalendarioWidget", "views.calendario_view"),
    ("ClientesWidget", "views.clientes_view"),
    ("ComparendosWidget", "views.comparendos_view"),
    ("DashboardWidget", "views.dashboard_view"),
    ("GastosWidget", "views.gastos_view"),
    ("InformesWidget", "views.informes_view"),
    ("MantenimientoWidget", "views.mantenimiento_view"),
    ("RentasWidget", "views.rentas_view"),
    ("ReservasWidget", "views.reservas_view"),
    ("UsuariosWidget", "views.usuarios_view"),
]


def _cargar_clase(class_name: str, module_name: str):
    """Importa el módulo y retorna la clase."""
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls


def _tiene_banner(class_name: str, module_name: str) -> bool:
    """
    Analiza el código fuente del módulo para determinar si la vista
    implementa un banner, ya sea mediante:

    - create_banner() de views.layouts.form_helpers
    - Construcción manual con variable 'banner' + gradiente (ej: calendario_view)
    """
    module = importlib.import_module(module_name)
    try:
        source = inspect.getsource(module)
    except (TypeError, OSError):
        return False

    # Patrón 1: create_banner() — usado en 10 vistas actualmente
    if "create_banner(" in source:
        return True

    # Patrón 2: Banner manual con variable 'banner' y QSS class-based or inline gradient
    # (calendario_view.py construye su banner manualmente con class="banner")
    has_banner_var = bool(re.search(r"\bbanner\s*=\s*(QWidget|QFrame)\(\)", source))
    if has_banner_var:
        # QSS class-based banner (post-migration)
        if 'setProperty("class", "banner")' in source and "FixedHeight" in source:
            return True
        # Legacy inline gradient fallback
        if "qlineargradient" in source and "FixedHeight" in source:
            return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 1: Herencia de BaseWidget
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "class_name,module_name", WIDGET_CLASSES, ids=lambda x: x if isinstance(x, str) else f"{x[0]}"
)
def test_hereda_de_base_widget(class_name, module_name):
    """Todas las vistas del sistema deben heredar de BaseWidget."""
    cls = _cargar_clase(class_name, module_name)
    assert issubclass(cls, BaseWidget), (
        f"{class_name} en {module_name} NO hereda de BaseWidget "
        f"(hereda de: {', '.join(b.__name__ for b in cls.__bases__)})"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 2: Presencia de banner
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize(
    "class_name,module_name", WIDGET_CLASSES, ids=lambda x: x if isinstance(x, str) else f"{x[0]}"
)
def test_tiene_banner(class_name, module_name):
    """
    Todas las vistas deben tener un banner superior (create_banner o manual).

    Nota: Si esta prueba falla para una vista, es porque necesita
    agregarle un banner con el patrón establecido. Ver referencias:
      - create_banner() en views/layouts/form_helpers.py
      - Banner manual en views/calendario_view.py
    """
    assert _tiene_banner(class_name, module_name), (
        f"{class_name} en {module_name} NO tiene banner detectado.\n"
        f"Agrega create_banner() en el método de construcción de la UI, "
        f"o implementa un banner manual con gradiente.\n"
        f"Patrón: banner = create_banner('📋', 'Título', 'Subtítulo', self.cargar_datos)"
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 3: Reporte completo (opcional, agrupa toda la info)
# ═══════════════════════════════════════════════════════════════════════════════


def test_reporte_completo():
    """
    Genera un reporte legible con el estado de todas las vistas.
    """
    resultados = []
    todos_ok = True

    for class_name, module_name in WIDGET_CLASSES:
        cls = _cargar_clase(class_name, module_name)
        hereda = issubclass(cls, BaseWidget)
        banner = _tiene_banner(class_name, module_name)

        estado = "✅" if (hereda and banner) else "❌"
        fallos = []
        if not hereda:
            fallos.append("no hereda de BaseWidget")
        if not banner:
            fallos.append("sin banner detectado")

        resultados.append(
            f"  {estado} {class_name:20s}  →  {', '.join(fallos) if fallos else 'OK'}"
        )
        if not (hereda and banner):
            todos_ok = False

    reporte = [
        "\n═══ Reporte de Consistencia de Vistas ═══",
        f"Total vistas: {len(WIDGET_CLASSES)}",
        *resultados,
        "═══ FIN ═══\n",
    ]
    reporte_str = "\n".join(reporte)

    if not todos_ok:
        pytest.fail(f"Vistas con incumplimientos:\n{reporte_str}")
    else:
        # Mostrar reporte incluso cuando pasa
        print(reporte_str)
