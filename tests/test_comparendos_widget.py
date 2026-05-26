"""Tests for ComparendosWidget — tickets & fines panel."""

from unittest.mock import patch


from views.comparendos_view import ComparendosWidget, NuevoComparendoDialog


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_COMPARENDOS = [
    {
        "id": 1,
        "fecha_infraccion": "2026-05-20",
        "hora_infraccion": "10:30",
        "placa": "ABC123",
        "monto": 500000,
        "cliente_nombre": "Juan Perez",
        "estado": "Pendiente",
    },
    {
        "id": 2,
        "fecha_infraccion": "2026-05-22",
        "hora_infraccion": "14:00",
        "placa": "DEF456",
        "monto": 300000,
        "cliente_nombre": None,
        "estado": "Pendiente",
    },
]

_MOCK_AUTOS = [
    {"placa": "ABC123", "marca": "Toyota"},
    {"placa": "DEF456", "marca": "Mazda"},
]


@patch("views.comparendos_view.ComparendoService.listar", return_value=_MOCK_COMPARENDOS)
class TestComparendosWidget:
    """Suite de pruebas para ComparendosWidget."""

    def test_instancia(self, mock_listar, qapp):
        """ComparendosWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = ComparendosWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, ComparendosWidget)
        widget.deleteLater()

    def test_tiene_tabla(self, mock_listar, qapp):
        """El widget tiene tabla y métodos esperados."""
        widget = ComparendosWidget()
        assert hasattr(widget, "tbl")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_listar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = ComparendosWidget()
        headers = [
            widget.tbl.horizontalHeaderItem(i).text() for i in range(widget.tbl.columnCount())
        ]
        assert "Placa" in headers
        assert "Monto" in headers
        assert "Cliente Responsable" in headers
        assert "Estado" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_listar, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = ComparendosWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == len(_MOCK_COMPARENDOS)
        mock_listar.assert_called()
        widget.deleteLater()

    def test_cargar_datos_muestra_placas(self, mock_listar, qapp):
        """Las placas se muestran correctamente."""
        widget = ComparendosWidget()
        widget.cargar_datos()
        assert widget.tbl.item(0, 2).text() == "ABC123"
        assert widget.tbl.item(1, 2).text() == "DEF456"
        widget.deleteLater()

    def test_cargar_datos_cliente_sin_asignar(self, mock_listar, qapp):
        """Sin cliente asignado, muestra texto informativo."""
        widget = ComparendosWidget()
        widget.cargar_datos()
        assert "SIN ASIGNAR" in widget.tbl.item(1, 4).text()
        widget.deleteLater()

    def test_cargar_datos_muestra_montos(self, mock_listar, qapp):
        """Los montos se muestran con formato $."""
        widget = ComparendosWidget()
        widget.cargar_datos()
        monto = widget.tbl.item(0, 3).text()
        assert "$" in monto
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_listar, qapp):
        """Lista vacía: 0 filas."""
        mock_listar.return_value = []
        widget = ComparendosWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()

    def test_cargar_datos_con_error(self, mock_listar, qapp):
        """Error en servicio no crashea."""
        from core.exceptions import DinamoBaseError

        mock_listar.side_effect = DinamoBaseError("Error DB")
        widget = ComparendosWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()


# ── Tests para NuevoComparendoDialog ─────────────────────────────────────────


class TestNuevoComparendoDialog:
    """Tests de instanciación del diálogo de comparendos."""

    def test_instancia(self, qapp):
        """NuevoComparendoDialog se instancia correctamente."""
        dlg = NuevoComparendoDialog()
        assert dlg is not None
        assert "Comparendo" in dlg.windowTitle() or "Multa" in dlg.windowTitle()
        dlg.deleteLater()

    def test_tiene_campos(self, qapp):
        """El diálogo tiene los campos esperados."""
        dlg = NuevoComparendoDialog()
        assert hasattr(dlg, "cmb_placa")
        assert hasattr(dlg, "d_fecha")
        assert hasattr(dlg, "sp_monto")
        dlg.deleteLater()
