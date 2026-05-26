"""Tests for ClientesWidget — client directory panel."""

from unittest.mock import patch


from views.clientes_view import ClientesWidget, ClienteFormDialog


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_CLIENTES = [
    {
        "id": 1,
        "no_doc": "12345",
        "nombre_completo": "Juan Perez",
        "celular": "3001112233",
        "nacionalidad": "Colombiana",
        "estado": "Activo",
        "no_licencia": "LIC-001",
    },
    {
        "id": 2,
        "no_doc": "67890",
        "nombre_completo": "Maria Gomez",
        "celular": "3004445566",
        "nacionalidad": "Colombiana",
        "estado": "VIP",
        "no_licencia": "LIC-002",
    },
]

_MOCK_CLIENTE_UNICO = {
    "id": 1,
    "tipo_doc": "Cedula",
    "no_doc": "12345",
    "nombres": "Juan",
    "apellidos": "Perez",
    "celular": "3001112233",
    "celular2": "",
    "email": "juan@mail.com",
    "pais": "Colombia",
    "estado_region": "Antioquia",
    "ciudad": "Medellin",
    "nacionalidad": "Colombiana",
    "dir_residencia": "Calle 123",
    "dir_temporal": "",
    "hotel": "",
    "habitacion": "",
    "no_licencia": "LIC-001",
    "tipo_licencia": "B1",
    "vencimiento_licencia": None,
    "estado": "Activo",
    "nombre_completo": "Juan Perez",
}


@patch("views.clientes_view.ClienteService.buscar", return_value=_MOCK_CLIENTES)
class TestClientesWidget:
    """Suite de pruebas para ClientesWidget."""

    def test_instancia(self, mock_buscar, qapp):
        """ClientesWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = ClientesWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, ClientesWidget)
        widget.deleteLater()

    def test_tiene_banner_y_tabla(self, mock_buscar, qapp):
        """El widget tiene banner, buscar y tabla."""
        widget = ClientesWidget()
        assert hasattr(widget, "txt_buscar")
        assert hasattr(widget, "tabla")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_buscar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = ClientesWidget()
        headers = [
            widget.tabla.horizontalHeaderItem(i).text() for i in range(widget.tabla.columnCount())
        ]
        assert "Documento" in headers
        assert "Nombre Completo" in headers
        assert "Estado" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_buscar, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = ClientesWidget()
        widget.cargar_datos()
        assert widget.tabla.rowCount() == len(_MOCK_CLIENTES)
        mock_buscar.assert_called()
        widget.deleteLater()

    def test_cargar_datos_con_documentos(self, mock_buscar, qapp):
        """Los documentos se muestran en la tabla."""
        widget = ClientesWidget()
        widget.cargar_datos()
        doc1 = widget.tabla.item(0, 0)
        assert doc1 is not None and doc1.text() == "12345"
        widget.deleteLater()

    def test_cargar_datos_vacio(self, mock_buscar, qapp):
        """Lista vacía: 0 filas."""
        mock_buscar.return_value = []
        widget = ClientesWidget()
        widget.cargar_datos()
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    # ── Filtro ─────────────────────────────────────────────────────────

    def test_filtrar_por_nombre(self, mock_buscar, qapp):
        """Filtrar por nombre muestra solo los coincidentes."""
        widget = ClientesWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("Maria")
        assert widget.tabla.rowCount() == 1
        assert widget.tabla.item(0, 0).text() == "67890"
        widget.deleteLater()

    def test_filtrar_sin_resultados(self, mock_buscar, qapp):
        """Texto sin coincidencias: 0 filas."""
        widget = ClientesWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("ZZZZ")
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()


# ── Tests para ClienteFormDialog ──────────────────────────────────────────────


@patch(
    "views.clientes_view.ClienteService.obtener_opciones_geograficas",
    return_value={"paises": [], "regiones": [], "ciudades": []},
)
class TestClienteFormDialog:
    """Tests de instanciación del formulario de cliente."""

    def test_instancia(self, mock_geo, qapp):
        """ClienteFormDialog se instancia correctamente."""
        dlg = ClienteFormDialog()
        assert dlg is not None
        assert "Cliente" in dlg.windowTitle() or "Ficha" in dlg.windowTitle()
        dlg.deleteLater()

    def test_instancia_con_datos(self, mock_geo, qapp):
        """Al crear con datos, carga los valores."""
        dlg = ClienteFormDialog(datos=_MOCK_CLIENTE_UNICO)
        assert dlg._datos["id"] == 1
        dlg.deleteLater()
