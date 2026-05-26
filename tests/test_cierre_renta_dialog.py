"""
test_cierre_renta_dialog.py — Unit tests for CierreRentaDialog

Tests the full lifecycle:
  - Instantiation with/without id_renta
  - Deferred data loading via QTimer.singleShot(0, ...)
  - _recalcular() updates totals correctly
  - _guardar() validates km_final input
  - _guardar() calls RentaService.cerrar on success
  - Error handling (DinamoBaseError, missing renta)

Run: pytest tests/test_cierre_renta_dialog.py -v
"""

import pytest
from unittest.mock import patch

from core.exceptions import DinamoBaseError


# ── QApplication fixture (module-scoped) ──────────────────────────────────────


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

FAKE_RENTA = {
    "id": 1,
    "placa": "ABC123",
    "nombre_cliente": "Juan Perez",
    "fecha_recogida": "2026-05-20",
    "fecha_retorno": "2026-05-25",
    "hora_retorno": "12:00",
    "total": 500000.0,
    "abono": 100000.0,
    "valor_dia": 100000.0,
    "km_salida": 50000,
    "tanque_salida": "Lleno",
}


def _process_events():
    """Process pending Qt events to fire deferred QTimer callbacks."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestCierreRentaDialogInstancia:
    """Instantiation and basic properties."""

    def test_crear_sin_id_renta(self, qapp):
        """Dialog can be created without id_renta (None)."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=None)
        try:
            assert dlg.id_renta is None
            assert "Procesar Devolucion" in dlg.windowTitle()
        finally:
            dlg.close()

    def test_crear_con_id_renta(self, qapp):
        """Dialog shows renta ID in window title."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=42)
        try:
            assert dlg.id_renta == 42
            assert "#42" in dlg.windowTitle()
        finally:
            dlg.close()

    def test_minimum_size(self, qapp):
        """Dialog has a minimum size for usability."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            assert dlg.minimumWidth() >= 600
            assert dlg.minimumHeight() >= 700
        finally:
            dlg.close()

    def test_tiene_elementos_ui(self, qapp):
        """Dialog contains expected UI widgets: date/time, km, tanque, buttons."""
        from PySide6.QtWidgets import (
            QDateEdit,
            QTimeEdit,
            QLineEdit,
            QComboBox,
            QDoubleSpinBox,
            QPushButton,
        )
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            assert len(dlg.findChildren(QDateEdit)) >= 1
            assert len(dlg.findChildren(QTimeEdit)) >= 1
            assert len(dlg.findChildren(QLineEdit)) >= 1
            assert len(dlg.findChildren(QComboBox)) >= 1
            assert len(dlg.findChildren(QDoubleSpinBox)) >= 2
            buttons = dlg.findChildren(QPushButton)
            assert any("Finalizar" in btn.text() for btn in buttons)
            assert any("Cancelar" in btn.text() for btn in buttons)
        finally:
            dlg.close()

    def test_tiene_header_y_body(self, qapp):
        """Dialog has the standard header+body structure from BaseDialog."""
        from PySide6.QtWidgets import QWidget
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            header = dlg.findChild(QWidget, "dlg_header")
            assert header is not None, "Missing dlg_header widget"
            body = dlg.findChild(QWidget, "dlg_body")
            assert body is not None, "Missing dlg_body widget"
        finally:
            dlg.close()

    def test_init_overlay_creado(self, qapp):
        """Dialog creates a LoadingOverlay in __init__."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            assert dlg._loading_overlay is not None, "LoadingOverlay should be created in __init__"
        finally:
            dlg.close()


class TestCierreRentaDialogCarga:
    """Deferred data loading (QTimer.singleShot -> _deferred_load -> _cargar_datos)."""

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_cargar_datos_exitoso(self, mock_obtener, qapp):
        """_cargar_datos() loads renta and updates info label and pactado label."""
        from PySide6.QtWidgets import QLabel
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            mock_obtener.assert_called_once_with(1)

            # Info label should contain client name and plate
            labels = dlg.findChildren(QLabel)
            assert any("Juan Perez" in lbl.text() for lbl in labels), (
                "Expected client name in info label"
            )
            assert any("ABC123" in lbl.text() for lbl in labels), "Expected plate in info label"
            # Pactado label should show the total
            assert "500,000" in dlg.lbl_pactado.text().replace(" ", ""), (
                "Expected pactado label to show 500,000"
            )
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener")
    def test_cargar_datos_sin_id_rechaza(self, mock_obtener, qapp):
        """Dialog rejects immediately when id_renta is None."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=None)
        try:
            _process_events()
            # Should have called reject() -> result is Rejected
            assert dlg.result() == dlg.DialogCode.Rejected
        finally:
            dlg.close()

    @patch(
        "views.cierre_renta_view.RentaService.obtener",
        side_effect=DinamoBaseError("Renta no encontrada"),
    )
    def test_cargar_datos_error_dinamo(self, mock_obtener, qapp):
        """Dialog rejects when RentaService raises DinamoBaseError."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=999)
        try:
            _process_events()
            assert dlg.result() == dlg.DialogCode.Rejected
        finally:
            dlg.close()

    @patch(
        "views.cierre_renta_view.RentaService.obtener", side_effect=Exception("Unexpected error")
    )
    def test_cargar_datos_error_inesperado(self, mock_obtener, qapp):
        """Dialog rejects when an unexpected exception occurs."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            assert dlg.result() == dlg.DialogCode.Rejected
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_timer_stale_no_crash(self, mock_obtener, qapp):
        """Destroying dialog before timer fires should NOT cause a crash."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        dlg.close()
        dlg.deleteLater()
        _process_events()  # Should not crash


class TestCierreRentaDialogRecalcular:
    """_recalcular() updates total/detalle labels correctly."""

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_recalcular_sin_cambios(self, mock_obtener, qapp):
        """With same return date, extra days = 0 and total = pactado."""
        from PySide6.QtCore import QDate
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()

            # Set date to same as pactada (no delay)
            dlg.date_retorno.setDate(QDate(2026, 5, 25))
            dlg._recalcular()

            assert dlg.sp_dias_extra.value() == 0
            assert dlg.sp_mora.value() == 0
            assert "500,000" in dlg.lbl_total.text().replace(" ", "")
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_recalcular_con_mora(self, mock_obtener, qapp):
        """With delayed return (3 days), mora = 3 * valor_dia."""
        from PySide6.QtCore import QDate
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()

            # 3 days late
            dlg.date_retorno.setDate(QDate(2026, 5, 28))
            dlg._recalcular()

            assert dlg.sp_dias_extra.value() == 3
            # mora = 3 * 100000
            assert dlg.sp_mora.value() == 300000.0
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_recalcular_con_otros_cobros(self, mock_obtener, qapp):
        """Adding 'otros' cobros increases total."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()

            dlg.sp_otros.setValue(50000.0)
            dlg._recalcular()

            # total = 500000 + 0 mora + 50000
            assert "550,000" in dlg.lbl_total.text().replace(" ", "")
            assert "50,000" in dlg.lbl_detalle.text()
        finally:
            dlg.close()


class TestCierreRentaDialogGuardar:
    """_guardar() validation and service calls."""

    FAKE_RENTA = FAKE_RENTA

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_guardar_rechaza_sin_km(self, mock_obtener, qapp):
        """_guardar() shows warning when km_final is empty."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            dlg.txt_km_final.setText("")  # Empty km
            dlg._guardar()
            # Dialog should NOT be accepted
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_guardar_rechaza_sin_id_renta(self, mock_obtener, qapp):
        """_guardar() warns when id_renta is None."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=None)
        try:
            _process_events()
            dlg._guardar()
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    @patch("views.cierre_renta_view.RentaService.cerrar")
    def test_guardar_exitoso(self, mock_cerrar, mock_obtener, qapp):
        """_guardar() calls RentaService.cerrar and accepts dialog."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            dlg.txt_km_final.setText("51000")
            dlg._guardar()

            mock_cerrar.assert_called_once()
            args, _ = mock_cerrar.call_args
            assert args[0] == 1  # id_renta
            datos = args[1]
            assert "km_final" in datos
            assert datos["km_final"] == "51000"
            assert "km_final_float" in datos
            assert datos["km_final_float"] == 51000.0
            assert dlg.result() == dlg.DialogCode.Accepted
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    def test_guardar_rechaza_km_invalido(self, mock_obtener, qapp):
        """_guardar() warns when km_final has invalid format."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            dlg.txt_km_final.setText("ABC")  # Invalid km
            dlg._guardar()
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.close()

    @patch("views.cierre_renta_view.RentaService.obtener", return_value=FAKE_RENTA)
    @patch(
        "views.cierre_renta_view.RentaService.cerrar",
        side_effect=DinamoBaseError("Error al cerrar"),
    )
    def test_guardar_error_dinamo(self, mock_cerrar, mock_obtener, qapp):
        """_guardar() shows error when RentaService.cerrar raises DinamoBaseError."""
        from views.cierre_renta_view import CierreRentaDialog

        dlg = CierreRentaDialog(parent=None, id_renta=1)
        try:
            _process_events()
            dlg.txt_km_final.setText("51000")
            dlg._guardar()
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.close()
