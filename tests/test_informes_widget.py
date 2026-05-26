"""Tests for InformesWidget — financial reports panel."""

from unittest.mock import patch


from views.informes_view import InformesWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_BALANCE = [
    {
        "mes": "2026-05",
        "ingresos": 5000000,
        "taller": 1200000,
        "caja_menor": 300000,
        "utilidad": 3500000,
    },
    {
        "mes": "2026-04",
        "ingresos": 4500000,
        "taller": 800000,
        "caja_menor": 200000,
        "utilidad": 3500000,
    },
]

_MOCK_ROI = [
    {
        "placa": "ABC123",
        "vehiculo": "Toyota Corolla",
        "ingresos": 3000000,
        "mantenimiento": 500000,
        "costos_fijos": 200000,
        "utilidad": 2300000,
        "equilibrio": 12.5,
    },
    {
        "placa": "DEF456",
        "vehiculo": "Mazda 3",
        "ingresos": 2000000,
        "mantenimiento": 800000,
        "costos_fijos": 200000,
        "utilidad": 1000000,
        "equilibrio": 18.0,
    },
]


@patch("views.informes_view.InformeService.balance_mensual_real", return_value=_MOCK_BALANCE)
@patch("views.informes_view.FinancialService.roi_flota", return_value=_MOCK_ROI)
class TestInformesWidget:
    """Suite de pruebas para InformesWidget."""

    def test_instancia(self, mock_balance, mock_roi, qapp):
        """InformesWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = InformesWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, InformesWidget)
        widget.deleteLater()

    def test_tiene_tabs_y_tablas(self, mock_balance, mock_roi, qapp):
        """El widget tiene tabs con tablas de balance y ROI."""
        widget = InformesWidget()
        assert hasattr(widget, "tabs")
        assert hasattr(widget, "tbl_bal")
        assert hasattr(widget, "tbl_roi")
        assert widget.tabs.count() == 2
        widget.deleteLater()

    def test_columnas_tabla_balance(self, mock_balance, mock_roi, qapp):
        """La tabla de balance tiene las columnas esperadas."""
        widget = InformesWidget()
        headers = [
            widget.tbl_bal.horizontalHeaderItem(i).text()
            for i in range(widget.tbl_bal.columnCount())
        ]
        assert "Ingresos (Rentas)" in headers
        assert "Utilidad Neta" in headers
        widget.deleteLater()

    def test_columnas_tabla_roi(self, mock_balance, mock_roi, qapp):
        """La tabla de ROI tiene las columnas esperadas."""
        widget = InformesWidget()
        headers = [
            widget.tbl_roi.horizontalHeaderItem(i).text()
            for i in range(widget.tbl_roi.columnCount())
        ]
        assert "Placa" in headers
        assert "Utilidad Total" in headers
        assert "Punto Equilibrio" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_balance(self, mock_balance, mock_roi, qapp):
        """cargar_datos() pinta filas de balance."""
        widget = InformesWidget()
        widget.cargar_datos()
        assert widget.tbl_bal.rowCount() == len(_MOCK_BALANCE)
        mock_balance.assert_called()
        widget.deleteLater()

    def test_cargar_datos_pinta_roi(self, mock_balance, mock_roi, qapp):
        """cargar_datos() pinta filas de ROI."""
        widget = InformesWidget()
        widget.cargar_datos()
        assert widget.tbl_roi.rowCount() == len(_MOCK_ROI)
        mock_roi.assert_called()
        widget.deleteLater()

    def test_balance_muestra_utilidad(self, mock_balance, mock_roi, qapp):
        """La utilidad se muestra con formato $."""
        widget = InformesWidget()
        widget.cargar_datos()
        util = widget.tbl_bal.item(0, 4).text()
        assert "$" in util
        assert "3,500" in util or "3500" in util
        widget.deleteLater()

    def test_roi_muestra_placas(self, mock_balance, mock_roi, qapp):
        """Las placas se muestran en ROI."""
        widget = InformesWidget()
        widget.cargar_datos()
        assert widget.tbl_roi.item(0, 0).text() == "ABC123"
        assert widget.tbl_roi.item(1, 0).text() == "DEF456"
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_balance, mock_roi, qapp):
        """Datos vacíos: 0 filas en ambas tablas."""
        mock_balance.return_value = []
        mock_roi.return_value = []
        widget = InformesWidget()
        widget.cargar_datos()
        assert widget.tbl_bal.rowCount() == 0
        assert widget.tbl_roi.rowCount() == 0
        widget.deleteLater()

    def test_cargar_datos_con_error(self, mock_balance, mock_roi, qapp):
        """Cuando los servicios fallan, no crashea."""
        from core.exceptions import DinamoBaseError

        mock_balance.side_effect = DinamoBaseError("Error DB")
        mock_roi.side_effect = DinamoBaseError("Error DB")
        widget = InformesWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tbl_bal.rowCount() == 0
        assert widget.tbl_roi.rowCount() == 0
        widget.deleteLater()
