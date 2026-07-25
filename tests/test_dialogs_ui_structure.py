"""
test_dialogs_ui_structure.py — Verifies that standardised dialogs:
1. Instantiate without errors
2. Have a header widget (objectName="dlg_header") from build_dialog_header
3. Have a body widget (objectName="dlg_body") from dialog_body_style
4. Contain expected key UI elements

Run: pytest tests/test_dialogs_ui_structure.py -v

Requires conftest.py for in-memory database and qapp fixture.
"""

import pytest
from core.exceptions import DinamoBaseError
from unittest.mock import patch

# ── QApplication fixture (module-scoped, created once) ────────────────────────


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _check_dialog_structure(dlg):
    """Assert that the dialog has the standard header+body structure."""
    from PySide6.QtWidgets import QWidget

    # Header from build_dialog_header
    header = dlg.findChild(QWidget, "dlg_header")
    assert header is not None, "Missing dlg_header widget (build_dialog_header)"
    assert not header.isHidden()

    # Body from dialog_body_style
    body = dlg.findChild(QWidget, "dlg_body")
    assert body is not None, "Missing dlg_body widget (dialog_body_style)"
    assert not body.isHidden()

    # Should have a layout with the header as first major child
    root_layout = dlg.layout()
    assert root_layout is not None
    assert root_layout.count() >= 2, "Expected at least 2 items in root layout (header + body)"


def _count_widgets(dlg, widget_type=type(None)):
    """Count widgets matching a given type in the dialog."""
    return len(dlg.findChildren(widget_type))


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — Simple dialogs (parent=None only)
# ═══════════════════════════════════════════════════════════════════════════════

SIMPLE_DIALOGS = [
    # (test_id, import_module, class_name, key_ui_checks)
    pytest.param(
        "DialogoSelectorCliente_rentas",
        "views.rentas_view",
        "DialogoSelectorCliente",
        ["UpperLineEdit", "QTableWidget"],
        id="rentas-selector-cliente",
    ),
    pytest.param(
        "DialogoSelectorCliente_reservas",
        "views.reservas_view",
        "DialogoSelectorCliente",
        ["UpperLineEdit", "QTableWidget"],
        id="reservas-selector-cliente",
    ),
    pytest.param(
        "UsuarioFormDialog",
        "views.usuarios_view",
        "UsuarioFormDialog",
        ["QLineEdit", "QComboBox", "QPushButton"],
        id="usuario-form",
    ),
    pytest.param(
        "ClienteFormDialog",
        "views.clientes_view",
        "ClienteFormDialog",
        ["QLineEdit", "QComboBox", "QTabWidget"],
        id="cliente-form",
    ),
    pytest.param(
        "NuevoMantenimientoDialog",
        "views.mantenimiento_view",
        "NuevoMantenimientoDialog",
        ["QComboBox", "QDoubleSpinBox", "QPushButton"],
        id="mantenimiento-nuevo",
    ),
    pytest.param(
        "NuevaReservaDialog",
        "views.reservas_view",
        "NuevaReservaDialog",
        ["QComboBox", "QDoubleSpinBox", "QPushButton"],
        id="reservas-nueva",
    ),
    pytest.param(
        "InspeccionDialog",
        "views.rentas_view",
        "InspeccionDialog",
        ["QComboBox", "QDoubleSpinBox", "QCheckBox"],
        id="inspeccion",
    ),
    pytest.param(
        "NuevoComparendoDialog",
        "views.comparendos_view",
        "NuevoComparendoDialog",
        ["QComboBox", "QDoubleSpinBox"],
        id="comparendo-nuevo",
    ),
    pytest.param(
        "DialogoAuto_nuevo",
        "views.autos_view",
        "DialogoAuto",
        ["QLineEdit", "QComboBox", "QDoubleSpinBox", "QTabWidget", "QPushButton"],
        id="auto-nuevo",
    ),
]


class TestSimpleDialogs:
    """Dialogs that require only parent=None to instantiate."""

    @pytest.mark.parametrize(
        ("_test_id", "module_path", "class_name", "expected_widgets"),
        SIMPLE_DIALOGS,
    )
    def test_instancia_y_estructura(
        self, qapp, _test_id, module_path, class_name, expected_widgets
    ):
        """Dialog instantiates, has header+body structure, and expected widgets."""
        import importlib

        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        dlg = cls(parent=None)
        try:
            _check_dialog_structure(dlg)
            self._assert_expected_widgets(dlg, expected_widgets)
        finally:
            dlg.close()

    @staticmethod
    def _assert_expected_widgets(dlg, widget_names):
        """Verify at least one instance of each expected widget type exists."""
        from PySide6.QtWidgets import (
            QLineEdit,
            QComboBox,
            QPushButton,
            QTableWidget,
            QDoubleSpinBox,
            QCheckBox,
            QTabWidget,
        )

        type_map = {
            "QLineEdit": QLineEdit,
            "QComboBox": QComboBox,
            "QPushButton": QPushButton,
            "QTableWidget": QTableWidget,
            "QDoubleSpinBox": QDoubleSpinBox,
            "QCheckBox": QCheckBox,
            "QTabWidget": QTabWidget,
            "UpperLineEdit": QLineEdit,  # subclass of QLineEdit
        }
        for name in widget_names:
            qt_type = type_map.get(name)
            if qt_type is None:
                # Import the specific widget class (e.g. UpperLineEdit)
                from PySide6.QtWidgets import QLineEdit

                qt_type = QLineEdit
            count = len(dlg.findChildren(qt_type))
            assert count > 0, f"Expected at least one {name} widget, found 0"


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — NuevaRentaDialog (calls services internally)
# ═══════════════════════════════════════════════════════════════════════════════


class TestNuevaRentaDialog:
    """NuevaRentaDialog loads autos from AutoService on init."""

    @patch("views.rentas_view.AutoService.listar_disponibles", return_value=[])
    def test_instancia_y_estructura(self, mock_autos, qapp):
        """Dialog instantiates with mocked AutoService and has header+body."""
        from views.rentas_view import NuevaRentaDialog

        dlg = NuevaRentaDialog(parent=None)
        try:
            _check_dialog_structure(dlg)
            # Should have key financial widgets
            from PySide6.QtWidgets import QGroupBox

            gboxes = dlg.findChildren(QGroupBox)
            assert len(gboxes) >= 2, "Expected at least 2 QGroupBox sections"
            from PySide6.QtWidgets import QGroupBox

            gboxes = dlg.findChildren(QGroupBox)
            assert len(gboxes) >= 2, "Expected at least 2 QGroupBox sections"
        finally:
            dlg.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — CierreRentaDialog (needs id_renta, mocks service)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCierreRentaDialog:
    """CierreRentaDialog requires an id_renta and fetches renta data."""

    FAKE_RENTA = {
        "id": 1,
        "placa": "ABC123",
        "nombre_cliente": "Test Client",
        "fecha_recogida": "2026-05-20",
        "fecha_retorno": "2026-05-25",
        "total": 500000.0,
        "abono": 100000.0,
        "km_salida": 50000,
        "tanque_salida": "Lleno",
    }

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_instancia_y_estructura(self, mock_renta, qapp):
        """Dialog instantiates with mocked services and has header+body.

        Note: _cargar_datos() is deferred via QTimer.singleShot(0, ...),
        so we need to process events to trigger the deferred call.
        """
        from PySide6.QtWidgets import QApplication

        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _check_dialog_structure(dlg)

            # Process pending events so the deferred _cargar_datos() runs
            QApplication.processEvents()

            # Should have labels for renta info
            from PySide6.QtWidgets import QLabel

            labels = dlg.findChildren(QLabel)
            assert any(
                "ABC123" in lbl.text() for lbl in labels
            ), "Expected placa to appear in a label"
        finally:
            dlg.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — PagosDialog (needs id_renta, total, cliente)
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagosDialog:
    """PagosDialog requires renta data but doesn't fetch from service on init."""

    def test_instancia_y_estructura(self, qapp):
        """Dialog instantiates with provided data and has header+body."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=500000.0, cliente="Test")
        try:
            _check_dialog_structure(dlg)
            # Should show the total
            from PySide6.QtWidgets import QLabel

            labels = dlg.findChildren(QLabel)
            # Expected format: "Total Renta:\n$ 500,000" or similar
            assert any(
                "500" in lbl.text().replace(",", "") for lbl in labels
            ), "Expected total amount to appear in a label"
        finally:
            dlg.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — DialogoExtenderRenta (needs id_renta, mocks RentaService)
# ═══════════════════════════════════════════════════════════════════════════════


class TestDialogoExtenderRenta:
    """DialogoExtenderRenta fetches renta data from RentaService on init."""

    FAKE_RENTA = {
        "id": 1,
        "placa": "ABC123",
        "fecha_recogida": "2026-05-20",
        "fecha_retorno": "2026-05-25",
        "hora_retorno": "12:00",
        "dias_calculados": 5,
        "valor_dia": 100000.0,
        "total": 500000.0,
        "abono": 100000.0,
    }

    @patch("views.rentas_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_instancia_y_estructura(self, mock_renta, qapp):
        """Dialog instantiates with mocked service and has header+body."""
        from views.rentas_view import DialogoExtenderRenta

        dlg = DialogoExtenderRenta(parent=None, id_renta=1)
        try:
            _check_dialog_structure(dlg)
            from PySide6.QtWidgets import QGroupBox, QPushButton

            assert len(dlg.findChildren(QGroupBox)) >= 1
            buttons = dlg.findChildren(QPushButton)
            assert any("CONFIRMAR" in btn.text().upper() for btn in buttons)
        finally:
            dlg.close()

    @patch("views.rentas_view.RentaService.obtener", side_effect=DinamoBaseError("Not found"))
    def test_rechaza_si_renta_no_existe(self, mock_renta, qapp):
        """Dialog rejects immediately when RentaService.obtener fails."""
        from views.rentas_view import DialogoExtenderRenta
        from PySide6.QtWidgets import QDialog

        dlg = DialogoExtenderRenta(parent=None, id_renta=999)
        assert dlg.result() == QDialog.Rejected


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — DialogoCambioVehiculo
# ═══════════════════════════════════════════════════════════════════════════════


class TestDialogoCambioVehiculo:
    """DialogoCambioVehiculo loads data from AutoService on init."""

    @patch("views.rentas_view.AutoService.obtener", return_value={"kilometraje": 50000})
    @patch("views.rentas_view.AutoService.listar_disponibles", return_value=[])
    def test_instancia_y_estructura(self, mock_listar, mock_obtener, qapp):
        """Dialog instantiates with mocked services and has header+body."""
        from views.rentas_view import DialogoCambioVehiculo

        dlg = DialogoCambioVehiculo(parent=None, id_renta=1, placa_actual="ABC123")
        try:
            _check_dialog_structure(dlg)
            from PySide6.QtWidgets import QGroupBox, QPushButton

            gboxes = dlg.findChildren(QGroupBox)
            assert len(gboxes) >= 2, "Expected 2 QGroupBox sections (out + in)"
            buttons = dlg.findChildren(QPushButton)
            assert any("CAMBIO" in btn.text().upper() for btn in buttons)
        finally:
            dlg.close()


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════
