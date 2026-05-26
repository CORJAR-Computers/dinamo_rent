"""Tests for AlertasWidget — notifications & alerts center."""

from unittest.mock import patch


from views.alertas_view import AlertasWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_ALERTAS = {
    "clientes": [
        {
            "cliente": "Juan Perez",
            "titulo": "Vencimiento SOAT",
            "fecha": "2026-06-01",
            "celular": "3001112233",
            "mensaje_whatsapp": "Su SOAT vence pronto",
        },
        {
            "cliente": "Maria Gomez",
            "titulo": "Vencimiento Licencia",
            "fecha": "2026-06-15",
            "celular": "3004445566",
            "mensaje_whatsapp": "Su licencia vence pronto",
        },
    ],
    "internas": [
        {
            "nivel": "Critico",
            "titulo": "ABC123 sin SOAT",
            "descripcion": "El vehiculo ABC123 tiene el SOAT vencido",
        },
        {
            "nivel": "Advertencia",
            "titulo": "Licencia por vencer",
            "descripcion": "La licencia de Juan Perez vence en 5 dias",
        },
    ],
}


@patch("views.alertas_view.AlertaService.obtener_todas_las_alertas", return_value=_MOCK_ALERTAS)
class TestAlertasWidget:
    """Suite de pruebas para AlertasWidget."""

    def test_instancia(self, mock_alertas, qapp):
        """AlertasWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = AlertasWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, AlertasWidget)
        widget.deleteLater()

    def test_tiene_tabs_y_tablas(self, mock_alertas, qapp):
        """El widget tiene tabs con tablas de clientes e internas."""
        widget = AlertasWidget()
        assert hasattr(widget, "tabs")
        assert hasattr(widget, "tbl_cli")
        assert hasattr(widget, "tbl_int")
        assert widget.tabs.count() == 2
        widget.deleteLater()

    def test_columnas_tabla_clientes(self, mock_alertas, qapp):
        """La tabla de clientes tiene las columnas esperadas."""
        widget = AlertasWidget()
        headers = [
            widget.tbl_cli.horizontalHeaderItem(i).text()
            for i in range(widget.tbl_cli.columnCount())
        ]
        assert "Cliente" in headers
        assert "Vencimiento" in headers
        assert "Accion" in headers
        widget.deleteLater()

    def test_columnas_tabla_internas(self, mock_alertas, qapp):
        """La tabla interna tiene las columnas esperadas."""
        widget = AlertasWidget()
        headers = [
            widget.tbl_int.horizontalHeaderItem(i).text()
            for i in range(widget.tbl_int.columnCount())
        ]
        assert "Nivel de Urgencia" in headers
        assert "Asunto" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_alertas_pinta_filas(self, mock_alertas, qapp):
        """cargar_alertas() pinta filas en ambas tablas."""
        widget = AlertasWidget()
        widget.cargar_alertas()
        assert widget.tbl_cli.rowCount() == len(_MOCK_ALERTAS["clientes"])
        assert widget.tbl_int.rowCount() == len(_MOCK_ALERTAS["internas"])
        mock_alertas.assert_called()
        widget.deleteLater()

    def test_cargar_alertas_muestra_clientes(self, mock_alertas, qapp):
        """Los nombres de clientes se muestran correctamente."""
        widget = AlertasWidget()
        widget.cargar_alertas()
        assert widget.tbl_cli.item(0, 0).text() == "Juan Perez"
        assert widget.tbl_cli.item(1, 0).text() == "Maria Gomez"
        widget.deleteLater()

    def test_cargar_alertas_muestra_niveles(self, mock_alertas, qapp):
        """Los niveles de urgencia se muestran en internas."""
        widget = AlertasWidget()
        widget.cargar_alertas()
        assert "Critico" in widget.tbl_int.item(0, 0).text()
        assert "Advertencia" in widget.tbl_int.item(1, 0).text()
        widget.deleteLater()

    def test_cargar_alertas_muestra_titulos(self, mock_alertas, qapp):
        """Los títulos de las alertas se muestran."""
        widget = AlertasWidget()
        widget.cargar_alertas()
        assert widget.tbl_int.item(0, 1).text() == "ABC123 sin SOAT"
        widget.deleteLater()

    def test_tabs_actualizan_contadores(self, mock_alertas, qapp):
        """Los tabs se actualizan con los contadores de alertas."""
        widget = AlertasWidget()
        widget.cargar_alertas()
        tab0 = widget.tabs.tabText(0)
        tab1 = widget.tabs.tabText(1)
        assert "2" in tab0  # 2 alertas de clientes
        assert "2" in tab1  # 2 alertas internas
        widget.deleteLater()

    def test_cargar_alertas_vacio(self, mock_alertas, qapp):
        """Sin alertas: 0 filas en ambas tablas."""
        mock_alertas.return_value = {"clientes": [], "internas": []}
        widget = AlertasWidget()
        widget.cargar_alertas()
        assert widget.tbl_cli.rowCount() == 0
        assert widget.tbl_int.rowCount() == 0
        widget.deleteLater()

    def test_cargar_alertas_con_error(self, mock_alertas, qapp):
        """Cuando el servicio lanza excepción, no crashea."""
        mock_alertas.side_effect = Exception("Error DB")
        widget = AlertasWidget()
        widget.cargar_alertas()  # No debe lanzar
        assert widget.tbl_cli.rowCount() == 0
        assert widget.tbl_int.rowCount() == 0
        widget.deleteLater()
