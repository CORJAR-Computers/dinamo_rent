"""Tests for ReservasWidget — reservations panel."""

from unittest.mock import patch


from views.reservas_view import ReservasWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_RESERVAS = [
    {
        "id": 1,
        "nombre_cliente": "Juan Perez",
        "placa_asignada": "ABC123",
        "categoria_vehiculo": "Sedan",
        "fecha_recogida": "2026-06-01",
        "fecha_retorno": "2026-06-05",
        "abono": 100000,
        "estado": "Confirmada",
    },
    {
        "id": 2,
        "nombre_cliente": "Maria Gomez",
        "placa_asignada": "",
        "categoria_vehiculo": "Camioneta",
        "fecha_recogida": "2026-06-10",
        "fecha_retorno": "2026-06-15",
        "abono": 50000,
        "estado": "Pendiente",
    },
]


@patch("views.reservas_view.ReservaService.listar", return_value=_MOCK_RESERVAS)
class TestReservasWidget:
    """Suite de pruebas para ReservasWidget."""

    def test_instancia(self, mock_listar, qapp):
        """ReservasWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = ReservasWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, ReservasWidget)
        widget.deleteLater()

    def test_tiene_elementos_ui(self, mock_listar, qapp):
        """El widget tiene buscador, combo y tabla."""
        widget = ReservasWidget()
        assert hasattr(widget, "txt_buscar")
        assert hasattr(widget, "tbl")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_listar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = ReservasWidget()
        headers = [
            widget.tbl.horizontalHeaderItem(i).text() for i in range(widget.tbl.columnCount())
        ]
        assert "Cliente" in headers
        assert "Estado" in headers
        assert "Abono" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_listar, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = ReservasWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == len(_MOCK_RESERVAS)
        mock_listar.assert_called()
        widget.deleteLater()

    def test_cargar_datos_muestra_clientes(self, mock_listar, qapp):
        """Nombres de clientes se muestran correctamente."""
        widget = ReservasWidget()
        widget.cargar_datos()
        assert widget.tbl.item(0, 1).text() == "Juan Perez"
        assert widget.tbl.item(1, 1).text() == "Maria Gomez"
        widget.deleteLater()

    def test_cargar_datos_vehiculo_fallback(self, mock_listar, qapp):
        """Sin placa asignada, muestra la categoría entre corchetes."""
        widget = ReservasWidget()
        widget.cargar_datos()
        assert widget.tbl.item(1, 2).text() == "[Camioneta]"
        widget.deleteLater()

    def test_cargar_datos_muestra_abono(self, mock_listar, qapp):
        """El abono se muestra con formato '$'."""
        widget = ReservasWidget()
        widget.cargar_datos()
        abono = widget.tbl.item(0, 5).text()
        assert "$" in abono
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_listar, qapp):
        """Lista vacía: 0 filas."""
        mock_listar.return_value = []
        widget = ReservasWidget()
        widget.cargar_datos()
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()

    # ── Filtro ─────────────────────────────────────────────────────────

    def test_filtrar_por_texto(self, mock_listar, qapp):
        """Filtrar por nombre reduce los resultados."""
        widget = ReservasWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("Juan")
        assert widget.tbl.rowCount() == 1
        widget.deleteLater()

    def test_filtrar_vacio_restaura(self, mock_listar, qapp):
        """Texto vacío muestra todos los registros."""
        widget = ReservasWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("Inexistente")
        assert widget.tbl.rowCount() == 0
        widget.txt_buscar.setText("")
        assert widget.tbl.rowCount() == len(_MOCK_RESERVAS)
        widget.deleteLater()

    def test_cargar_datos_con_error(self, mock_listar, qapp):
        """Error en servicio no crashea."""
        from core.exceptions import DinamoBaseError

        mock_listar.side_effect = DinamoBaseError("Error DB")
        widget = ReservasWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tbl.rowCount() == 0
        widget.deleteLater()
