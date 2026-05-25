"""test_smoke_dialogs.py — Test de humo: todos los QDialog se instancian sin errores.

Verifica que cada diálogo del proyecto puede ser construido con argumentos por
defecto/mínimos sin lanzar RuntimeError, AttributeError u otras excepciones.
"""

from __future__ import annotations

from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QDialog


# ── Registro de diálogos con sus argumentos por defecto ───────────────────────
# Cada entrada: (nombre, clase, kwargs)
# Donde kwargs son argumentos adicionales para el constructor (parent=None
# siempre se pasa automáticamente).

_DIALOGOS: list[tuple[str, type[QDialog], dict[str, Any]]] = []


def _register(
    name: str, dotted: str, kwargs: dict[str, Any] | None = None
) -> None:
    """Registra un diálogo para testeo."""

    def _loader() -> type[QDialog]:
        parts = dotted.split(".")
        mod_name = ".".join(parts[:-1])
        cls_name = parts[-1]
        import importlib
        mod = importlib.import_module(mod_name)
        cls: type[QDialog] = getattr(mod, cls_name)
        return cls

    _DIALOGOS.append((name, _loader, kwargs or {}))


# ── Registro manual (para que las importaciones sean diferidas) ────────────────
# views/autos_view.py
_register("DialogoAuto", "views.autos_view.DialogoAuto")
# views/clientes_view.py
_register("ClienteFormDialog", "views.clientes_view.ClienteFormDialog")
# views/cierre_renta_view.py
_register("CierreRentaDialog", "views.cierre_renta_view.CierreRentaDialog")
# views/comparendos_view.py
_register("NuevoComparendoDialog", "views.comparendos_view.NuevoComparendoDialog")
# views/force_change_password_dialog.py
_register(
    "ForceChangePasswordDialog",
    "views.force_change_password_dialog.ForceChangePasswordDialog",
    {"session": {"username": "admin", "nombre": "Admin Test"}},
)
# views/mantenimiento_view.py
_register("NuevoMantenimientoDialog", "views.mantenimiento_view.NuevoMantenimientoDialog")
# views/pagos_view.py
_register("PagosDialog", "views.pagos_view.PagosDialog")
# views/rentas_view.py — selector de cliente
_register("DialogoSelectorCliente(rentas)", "views.rentas_view.DialogoSelectorCliente")
# views/rentas_view.py — nueva renta
_register("NuevaRentaDialog", "views.rentas_view.NuevaRentaDialog")
# views/rentas_view.py — extender renta
_register("DialogoExtenderRenta", "views.rentas_view.DialogoExtenderRenta")
# views/rentas_view.py — cambio vehículo
_register("DialogoCambioVehiculo", "views.rentas_view.DialogoCambioVehiculo")
# views/rentas_view.py — inspección
_register("InspeccionDialog", "views.rentas_view.InspeccionDialog")
# views/reservas_view.py — selector de cliente
_register("DialogoSelectorCliente(reservas)", "views.reservas_view.DialogoSelectorCliente")
# views/reservas_view.py — nueva reserva
_register("NuevaReservaDialog", "views.reservas_view.NuevaReservaDialog")
# views/usuarios_view.py
_register("UsuarioFormDialog", "views.usuarios_view.UsuarioFormDialog")
# views/setup_wizard.py
_register("SetupWizard", "views.setup_wizard.SetupWizard")


# ── Tests ─────────────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def qapp() -> QApplication:
    """Crea/reusa QApplication para toda la suite."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.mark.parametrize(
    "nombre,loader,kwargs",
    [(e[0], e[1], e[2]) for e in _DIALOGOS],
    ids=[e[0] for e in _DIALOGOS],
)
def test_dialogo_se_instancia(
    qapp: QApplication,
    nombre: str,
    loader: Any,
    kwargs: dict[str, Any],
) -> None:
    """Verifica que el diálogo se construye sin errores."""
    cls = loader()
    dlg: QDialog | None = None
    try:
        dlg = cls(parent=None, **kwargs)
        assert isinstance(dlg, QDialog), (
            f"{nombre} no es una instancia de QDialog"
        )
        assert dlg.windowTitle(), (
            f"{nombre} no tiene windowTitle"
        )
    except RuntimeError as e:
        pytest.fail(
            f"{nombre} lanzó RuntimeError durante construcción: {e}"
        )
    except Exception as e:
        pytest.fail(
            f"{nombre} lanzó {type(e).__name__}: {e}"
        )
    finally:
        if dlg is not None:
            # Procesar eventos pendientes (timers diferidos, etc.)
            _cleanup_dialog(dlg)


def _cleanup_dialog(dlg: QDialog) -> None:
    """Limpia un diálogo cerrando y eliminando su objeto C++.

    NO llamamos processEvents() aquí porque varios diálogos tienen
    QTimer.singleShot(0, ...) en __init__ que disparan callbacks con
    _msg_box(...).exec() que abrirían un modal bloqueante.
    """
    try:
        dlg.close()
    except RuntimeError:
        pass
    try:
        dlg.deleteLater()
    except RuntimeError:
        pass
