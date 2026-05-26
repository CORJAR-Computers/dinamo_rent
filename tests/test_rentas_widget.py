"""Tests for RentasWidget — active rentals panel."""

from unittest.mock import patch


from views.rentas_view import RentasWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_RENTAS = [
    {
        "id": 1,
        "placa": "ABC123",
        "nombre_cliente": "Juan Perez",
        "fecha_recogida": "2026-05-20",
        "fecha_retorno": "2026-05-25",
        "estado": "Activo",
        "total": 500000,
    },
    {
        "id": 2,
        "placa": "DEF456",
        "nombre_cliente": "Maria Gomez",
        "fecha_recogida": "2026-05-22",
        "fecha_retorno": "2026-05-28",
        "estado": "Activo",
        "total": 750000,
    },
]


@patch("views.rentas_view.DashboardService.obtener_activas", return_value=_MOCK_RENTAS)
class TestRentasWidget:
    """Suite de pruebas para RentasWidget."""

    def test_instancia(self, mock_activas, qapp):
        """RentasWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = RentasWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, RentasWidget)
        widget.deleteLater()

    def test_tiene_banner_y_tabla(self, mock_activas, qapp):
        """El widget tiene banner y tabla."""
        widget = RentasWidget()
        assert hasattr(widget, "tbl")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_activas, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = RentasWidget()
        headers = [
            widget.tbl.horizontalHeaderItem(i).text() for i in range(widget.tbl.columnCount())
        ]
        assert "ID" in headers
        assert "Placa" in headers
        assert "Cliente" in headers
        assert "Total" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_activas, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = RentasWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == len(_MOCK_RENTAS)
        mock_activas.assert_called()
        widget.deleteLater()

    def test_cargar_datos_muestra_ids(self, mock_activas, qapp):
        """Los IDs de renta se muestran en la tabla."""
        widget = RentasWidget()
        widget.cargar_datos()
        assert widget.tbl.item(0, 0).text() == "1"
        assert widget.tbl.item(1, 0).text() == "2"
        widget.deleteLater()

    def test_cargar_datos_muestra_totales(self, mock_activas, qapp):
        """Los totales se muestran con formato moneda."""
        widget = RentasWidget()
        widget.cargar_datos()
        total_text = widget.tbl.item(0, 6).text()
        assert "$" in total_text
        assert "500" in total_text
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_activas, qapp):
        """Lista vacía: 0 filas."""
        mock_activas.return_value = []
        widget = RentasWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()

    def test_cargar_datos_con_error(self, mock_activas, qapp):
        """Cuando la obtención falla, no crashea."""
        from core.exceptions import DinamoBaseError

        mock_activas.side_effect = DinamoBaseError("Error")
        widget = RentasWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()
