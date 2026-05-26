"""Tests for GastosWidget — expense & petty cash panel."""

from unittest.mock import patch


from views.gastos_view import GastosWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_GASTOS = [
    {
        "id": 1,
        "fecha": "2026-05-20",
        "categoria": "Lavadero y Aseo",
        "descripcion": "Lavado ABC123",
        "comprobante": "F001",
        "monto": 50000,
    },
    {
        "id": 2,
        "fecha": "2026-05-22",
        "categoria": "Papeleria y Oficina",
        "descripcion": "Resma papel",
        "comprobante": "F002",
        "monto": 15000,
    },
]


@patch("views.gastos_view.GastoService.listar_recientes", return_value=_MOCK_GASTOS)
class TestGastosWidget:
    """Suite de pruebas para GastosWidget."""

    def test_instancia(self, mock_listar, qapp):
        """GastosWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = GastosWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, GastosWidget)
        widget.deleteLater()

    def test_tiene_formulario_y_tabla(self, mock_listar, qapp):
        """El widget tiene formulario de registro y tabla."""
        widget = GastosWidget()
        assert hasattr(widget, "tbl")
        assert hasattr(widget, "d_fecha")
        assert hasattr(widget, "sp_monto")
        assert hasattr(widget, "cmb_categoria")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_listar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = GastosWidget()
        headers = [
            widget.tbl.horizontalHeaderItem(i).text() for i in range(widget.tbl.columnCount())
        ]
        assert "Fecha" in headers
        assert "Categoria" in headers
        assert "Monto" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_listar, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = GastosWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == len(_MOCK_GASTOS)
        mock_listar.assert_called()
        widget.deleteLater()

    def test_cargar_datos_muestra_categorias(self, mock_listar, qapp):
        """Las categorías se muestran correctamente."""
        widget = GastosWidget()
        widget.cargar_datos()
        assert widget.tbl.item(0, 2).text() == "Lavadero y Aseo"
        assert widget.tbl.item(1, 2).text() == "Papeleria y Oficina"
        widget.deleteLater()

    def test_cargar_datos_muestra_montos(self, mock_listar, qapp):
        """Los montos se muestran con formato $."""
        widget = GastosWidget()
        widget.cargar_datos()
        monto = widget.tbl.item(0, 5).text()
        assert "$" in monto
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_listar, qapp):
        """Lista vacía: 0 filas."""
        mock_listar.return_value = []
        widget = GastosWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()

    def test_cargar_datos_con_error(self, mock_listar, qapp):
        """Cuando el servicio lanza excepción, no crashea."""
        from core.exceptions import DinamoBaseError

        mock_listar.side_effect = DinamoBaseError("Error DB")
        widget = GastosWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()

    # ── Validación del formulario ──────────────────────────────────────

    def test_cmb_categoria_tiene_opciones(self, mock_listar, qapp):
        """El combo de categorías tiene opciones."""
        widget = GastosWidget()
        assert widget.cmb_categoria.count() >= 5
        widget.deleteLater()
