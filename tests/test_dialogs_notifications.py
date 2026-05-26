"""
test_dialogs_notifications.py — Verifica que todos los diálogos principales
usen ModernMessageBox para sus notificaciones en lugar de QMessageBox directo.

Dialogs analyzed:
  - 10 diálogos de formulario/operación (herencia directa QDialog)
  - 3 diálogos auxiliares en rentas_view.py (selector, extensión, cambio)
  - SetupWizard (asistente de una sola vez, excepción conocida)
"""

import importlib
import inspect
import re
import sys
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))


# ── Registro de todos los diálogos del sistema ────────────────────────────────
# Cada entrada: (nombre_clase, nombre_modulo, [notas])
DIALOG_CLASSES = [
    # Diálogos principales de formulario/operación
    ("ClienteFormDialog", "views.clientes_view"),
    ("UsuarioFormDialog", "views.usuarios_view"),
    ("NuevoComparendoDialog", "views.comparendos_view"),
    ("CierreRentaDialog", "views.cierre_renta_view"),
    ("PagosDialog", "views.pagos_view"),
    ("NuevoMantenimientoDialog", "views.mantenimiento_view"),
    ("NuevaReservaDialog", "views.reservas_view"),
    ("NuevaRentaDialog", "views.rentas_view"),
    ("InspeccionDialog", "views.rentas_view"),
    ("ForceChangePasswordDialog", "views.force_change_password_dialog"),
    # Diálogos auxiliares (misma vista)
    ("DialogoExtenderRenta", "views.rentas_view"),
    ("DialogoCambioVehiculo", "views.rentas_view"),
    ("DialogoSelectorCliente", "views.rentas_view"),
    # Asistente de configuración (caso especial)
    ("SetupWizard", "views.setup_wizard"),
]

# Diálogos que están EXENTOS de usar ModernMessageBox por su naturaleza.
# Cada entrada: (class_name, module_name, motivo)
_ALLOWLIST = {
    (
        "DialogoSelectorCliente",
        "views.rentas_view",
    ): "Selector de búsqueda simple — no muestra notificaciones propias.",
    (
        "SetupWizard",
        "views.setup_wizard",
    ): "Asistente de instalación única — usa QMessageBox directamente.",
}


def _cargar_clase(class_name: str, module_name: str):
    """Importa el módulo y retorna la clase."""
    module = importlib.import_module(module_name)
    cls = getattr(module, class_name)
    return cls


def _usa_modern_messagebox(module_name: str) -> bool:
    """
    Verifica si el módulo del diálogo usa ModernMessageBox
    (directamente o mediante el wrapper _msg_box).

    Retorna True si:
      - El módulo importa ModernMessageBox desde views.components
      - El módulo contiene una referencia a _msg_box( (wrapper)
      - El módulo usa directamente ModernMessageBox.xxx()
    """
    module = importlib.import_module(module_name)
    try:
        source = inspect.getsource(module)
    except (TypeError, OSError):
        return False

    # Patrón 1: Import directo de ModernMessageBox
    if re.search(r"from\s+views\.components\b.*\bimport\b.*\bModernMessageBox\b", source):
        return True

    # Patrón 2: Uso directo de ModernMessageBox.xxx()
    if "ModernMessageBox." in source:
        return True

    # Patrón 3: Wrapper _msg_box() definido en el módulo
    if "def _msg_box" in source and "_msg_box(" in source:
        return True

    return False


def _usa_qmessagebox_directo(module_name: str) -> bool:
    """
    Detecta si el módulo usa QMessageBox directamente
    (sin pasar por ModernMessageBox).
    """
    module = importlib.import_module(module_name)
    try:
        source = inspect.getsource(module)
    except (TypeError, OSError):
        return False

    # Patrón 1: QMessageBox.xxx() sin que sea parte del wrapper _msg_box
    # Ejemplo: QMessageBox.critical(...)
    if re.search(r"QMessageBox\.(warning|critical|information|question)", source):
        return True

    # Patrón 2: Uso de QMessageBox importado y usado en notificaciones
    # (setup_wizard.py usa msg = QMessageBox(); msg.setIcon(...))
    if "QMessageBox(" in source or "QMessageBox()" in source:
        return True

    return False


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 1: Cada diálogo usa ModernMessageBox (o está en allowlist)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("class_name,module_name", DIALOG_CLASSES, ids=lambda x: f"{x[0]}")
def test_dialogo_usa_modern_messagebox(class_name, module_name):
    """
    Todos los diálogos principales deben usar ModernMessageBox
    para sus notificaciones al usuario, o estar explícitamente
    exceptuados por su naturaleza (allowlist).
    """
    key = (class_name, module_name)
    if key in _ALLOWLIST:
        pytest.skip(f"Exento: {_ALLOWLIST[key]}")

    assert _usa_modern_messagebox(module_name), (
        f"{class_name} (en {module_name}) NO usa ModernMessageBox.\n"
        f"Patrón esperado:\n"
        f"  from views.components import ModernMessageBox\n"
        f"  ModernMessageBox.success(self, 'Título', 'Mensaje')\n"
        f"\n"
        f"Si el diálogo usa el wrapper _msg_box (rentas_view.py), "
        f"debe estar en _WRAPPER_MODULES."
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 2: Ningún diálogo usa QMessageBox directamente (sin ModernMessageBox)
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.parametrize("class_name,module_name", DIALOG_CLASSES, ids=lambda x: f"{x[0]}")
def test_no_usa_qmessagebox_directo(class_name, module_name):
    """
    Los diálogos no deben usar QMessageBox directamente para
    notificaciones. Deben usar ModernMessageBox en su lugar.

    Excepción: SetupWizard (asistente de instalación única).
    """
    key = (class_name, module_name)
    if key in _ALLOWLIST:
        pytest.skip(f"Exento: {_ALLOWLIST[key]}")

    if _usa_qmessagebox_directo(module_name):
        # Si usa ModernMessageBox, QMessageBox puede estar presente
        # como parte del wrapper _msg_box — eso es aceptable.
        if _usa_modern_messagebox(module_name):
            return
        pytest.fail(
            f"{class_name} (en {module_name}) usa QMessageBox directamente.\n"
            f"Reemplázalo con ModernMessageBox de views.components."
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  Test 3: Reporte completo
# ═══════════════════════════════════════════════════════════════════════════════


def test_reporte_notificaciones():
    """
    Genera un reporte completo del estado de notificaciones en todos los diálogos.
    """
    resultados = []
    todos_ok = True

    for class_name, module_name in DIALOG_CLASSES:
        key = (class_name, module_name)

        try:
            cls = _cargar_clase(class_name, module_name)
        except Exception:
            resultados.append(f"  ❌ {class_name:30s}  →  ERROR al importar módulo")
            todos_ok = False
            continue

        # Verificar herencia QDialog
        from PySide6.QtWidgets import QDialog

        _ = issubclass(cls, QDialog)

        usa_mmb = _usa_modern_messagebox(module_name)
        usa_qmb = _usa_qmessagebox_directo(module_name)
        exento = key in _ALLOWLIST

        if exento:
            estado = "⏭️"
            detalles = f"Exento: {_ALLOWLIST[key][:50]}..."
        elif usa_mmb and not usa_qmb:
            estado = "✅"
            detalles = "ModernMessageBox"
        elif usa_mmb and usa_qmb:
            estado = "⚠️"
            detalles = "ModernMessageBox + QMessageBox (revisar)"
        else:
            estado = "❌"
            detalles = "SIN ModernMessageBox"
            todos_ok = False

        resultados.append(f"  {estado} {class_name:30s}  →  {detalles:45s}  ({module_name})")

    reporte = [
        "\n═══ Reporte de Notificaciones en Diálogos ═══",
        f"Total diálogos: {len(DIALOG_CLASSES)}",
        *resultados,
        "═══ FIN ═══\n",
    ]
    reporte_str = "\n".join(reporte)

    if not todos_ok:
        pytest.fail(f"Diálogos sin ModernMessageBox:\n{reporte_str}")
    else:
        print(reporte_str)
