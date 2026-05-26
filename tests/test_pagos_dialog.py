"""
test_pagos_dialog.py — Unit tests for PagosDialog (Estado de Cuenta)

Tests the full lifecycle:
  - Instantiation with renta data
  - Deferred loading of payment history via QTimer.singleShot(0, ...)
  - cargar_pagos() updates labels and table
  - _registrar_pago() validates monto > 0
  - _registrar_pago() calls PagoService.registrar on success
  - Error handling (DinamoBaseError)

Run: pytest tests/test_pagos_dialog.py -v
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

FAKE_PAGOS = [
    {
        "id": 1,
        "fecha": "2026-05-21 10:30",
        "monto": 100000.0,
        "metodo_pago": "Efectivo",
        "concepto": "Abono / Anticipo",
        "observaciones": "",
    },
    {
        "id": 2,
        "fecha": "2026-05-22 14:00",
        "monto": 200000.0,
        "metodo_pago": "Transferencia / Nequi",
        "concepto": "Pago Final",
        "observaciones": "Ref: NEQUI123",
    },
]

TOTAL_RENTA = 500000.0


def _process_events():
    """Process pending Qt events to fire deferred QTimer callbacks."""
    from PySide6.QtWidgets import QApplication

    QApplication.processEvents()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagosDialogInstancia:
    """Instantiation and basic properties."""

    def test_crear_con_datos(self, qapp):
        """Dialog can be created with renta data."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Juan Perez")
        try:
            assert dlg.id_renta == 1
            assert dlg.total_renta == TOTAL_RENTA
            assert dlg.cliente == "Juan Perez"
            assert "Estado de Cuenta" in dlg.windowTitle()
        finally:
            dlg.close()

    def test_window_title_con_renta(self, qapp):
        """Window title includes renta ID."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=42, total_renta=0, cliente="")
        try:
            assert "#42" in dlg.windowTitle()
        finally:
            dlg.close()

    def test_minimum_size(self, qapp):
        """Dialog has a minimum size for usability."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            assert dlg.minimumWidth() >= 650
            assert dlg.minimumHeight() >= 600
        finally:
            dlg.close()

    def test_tiene_elementos_ui(self, qapp):
        """Dialog contains expected UI widgets: labels, table, combos, spinbox."""
        from PySide6.QtWidgets import (
            QLabel,
            QTableWidget,
            QComboBox,
            QDoubleSpinBox,
            QPushButton,
        )
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            assert len(dlg.findChildren(QLabel)) >= 3  # total, abonado, saldo
            assert len(dlg.findChildren(QTableWidget)) >= 1
            assert len(dlg.findChildren(QComboBox)) >= 2  # metodo + concepto
            assert len(dlg.findChildren(QDoubleSpinBox)) >= 1
            buttons = dlg.findChildren(QPushButton)
            assert any("Registrar" in btn.text() for btn in buttons)
            assert any("Cerrar" in btn.text() for btn in buttons)
        finally:
            dlg.close()

    def test_tiene_header_y_body(self, qapp):
        """Dialog has the standard header+body structure from BaseDialog."""
        from PySide6.QtWidgets import QWidget
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            header = dlg.findChild(QWidget, "dlg_header")
            assert header is not None, "Missing dlg_header widget"
            body = dlg.findChild(QWidget, "dlg_body")
            assert body is not None, "Missing dlg_body widget"
        finally:
            dlg.close()

    def test_init_overlay_creado(self, qapp):
        """Dialog creates a LoadingOverlay in __init__."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            assert dlg._loading_overlay is not None, "LoadingOverlay should be created in __init__"
        finally:
            dlg.close()

    def test_resumen_labels_muestran_total(self, qapp):
        """Financial summary labels show the total rental amount."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=750000.0, cliente="Test")
        try:
            assert "750,000" in dlg.lbl_total.text().replace(" ", "")
            assert "Abonado" in dlg.lbl_abonado.text()
            assert "Saldo" in dlg.lbl_saldo.text()
        finally:
            dlg.close()


class TestPagosDialogCargaPagos:
    """Deferred loading of payment history."""

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=[])
    def test_cargar_pagos_vacio(self, mock_listar, qapp):
        """cargar_pagos() with empty results shows 0 rows and abonado=0."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()

            mock_listar.assert_called_once_with(1)
            assert dlg.tbl.rowCount() == 0
            assert "$ 0" in dlg.lbl_abonado.text()
            assert "Pendiente" in dlg.lbl_saldo.text()
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=FAKE_PAGOS)
    def test_cargar_pagos_con_datos(self, mock_listar, qapp):
        """cargar_pagos() with payment data populates table and updates labels."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()

            # Table should have 2 rows
            assert dlg.tbl.rowCount() == 2

            # First row should show first payment
            item_fecha0 = dlg.tbl.item(0, 0)
            assert item_fecha0 is not None
            assert "2026-05-21" in item_fecha0.text()

            item_monto0 = dlg.tbl.item(0, 1)
            assert item_monto0 is not None
            assert "100,000" in item_monto0.text()

            # Abonado should sum both payments
            assert "300,000" in dlg.lbl_abonado.text().replace(" ", "")

            # Saldo: 500000 - 300000 = 200000
            assert "200,000" in dlg.lbl_saldo.text().replace(" ", "")
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=FAKE_PAGOS)
    def test_cargar_pagos_paz_y_salvo(self, mock_listar, qapp):
        """When total paid equals total renta, saldo shows 'PAZ Y SALVO'."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=300000.0, cliente="Test")
        try:
            _process_events()

            # Total paid = 300000, total renta = 300000 -> PAZ Y SALVO
            assert "PAZ Y SALVO" in dlg.lbl_saldo.text()
        finally:
            dlg.close()

    @patch(
        "views.pagos_view.PagoService.listar_por_renta",
        side_effect=DinamoBaseError("Error de conexion"),
    )
    @patch("views.pagos_view.ModernMessageBox.warning")
    def test_cargar_pagos_error_dinamo(self, mock_warning, mock_listar, qapp):
        """cargar_pagos() handles DinamoBaseError gracefully (no crash)."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()  # Should not crash
            assert dlg.tbl.rowCount() == 0
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=[])
    def test_timer_stale_no_crash(self, mock_listar, qapp):
        """Destroying dialog before timer fires should NOT crash."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        dlg.close()
        dlg.deleteLater()
        _process_events()  # Should not crash


class TestPagosDialogRegistrarPago:
    """Payment registration logic."""

    def test_spinbox_monto_minimo_es_uno(self, qapp):
        """Spinbox minimum is 1 (prevents monto <= 0 via UI)."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            assert dlg.sp_monto.minimum() == 1, "QDoubleSpinBox range should prevent monto <= 0"
            assert dlg.sp_monto.value() >= 1
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=FAKE_PAGOS)
    @patch("views.pagos_view.PagoService.registrar")
    def test_registrar_pago_exitoso(self, mock_registrar, mock_listar, qapp):
        """_registrar_pago() calls PagoService.registrar with correct data."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()
            dlg.sp_monto.setValue(150000.0)
            dlg.cmb_metodo.setCurrentText("Tarjeta de Credito")
            dlg.cmb_concepto.setCurrentText("Abono / Anticipo")
            dlg._registrar_pago()

            # Verify PagoService.registrar was called with correct data
            mock_registrar.assert_called_once()
            args = mock_registrar.call_args[0][0]
            assert args["id_renta"] == 1
            assert args["monto"] == 150000.0
            assert args["metodo_pago"] == "Tarjeta de Credito"
            assert args["concepto"] == "Abono / Anticipo"
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=FAKE_PAGOS)
    @patch(
        "views.pagos_view.PagoService.registrar",
        side_effect=DinamoBaseError("Error al registrar pago"),
    )
    @patch("views.pagos_view.ModernMessageBox.error")
    def test_registrar_pago_error_dinamo(self, mock_error, mock_registrar, mock_listar, qapp):
        """_registrar_pago() handles DinamoBaseError from service gracefully."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()
            dlg.sp_monto.setValue(50000.0)
            dlg._registrar_pago()  # Should show error, not crash
            mock_error.assert_called_once()
            assert dlg.result() != dlg.DialogCode.Accepted
        finally:
            dlg.close()

    @patch("views.pagos_view.PagoService.listar_por_renta", return_value=FAKE_PAGOS)
    @patch("views.pagos_view.PagoService.registrar")
    def test_registrar_pago_limpia_observaciones(self, mock_registrar, mock_listar, qapp):
        """After successful registration, the observaciones field is cleared."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            _process_events()
            dlg.sp_monto.setValue(50000.0)
            dlg.txt_obs.setText("Nota de prueba")

            dlg._registrar_pago()
            mock_registrar.assert_called_once()

            # Observaciones should be cleared after successful registration
            assert dlg.txt_obs.text() == ""
        finally:
            dlg.close()

    def test_cmb_metodo_tiene_opciones(self, qapp):
        """Metodo de pago combo has expected payment options."""
        from views.pagos_view import PagosDialog

        dlg = PagosDialog(parent=None, id_renta=1, total_renta=TOTAL_RENTA, cliente="Test")
        try:
            items = [dlg.cmb_metodo.itemText(i) for i in range(dlg.cmb_metodo.count())]
            assert "Efectivo" in items
            assert "Tarjeta de Credito" in items
            assert "Tarjeta de Debito" in items
            assert "Transferencia / Nequi" in items
        finally:
            dlg.close()
