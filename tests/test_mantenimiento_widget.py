"""Tests for MantenimientoWidget — workshop & maintenance panel."""

from unittest.mock import patch


from views.mantenimiento_view import MantenimientoWidget, NuevoMantenimientoDialog


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_MANTENIMIENTOS = [
    {
        "pieza_varias_fecha": "2026-05-20",
        "placa": "ABC123",
        "_auto_marca": "Toyota",
        "_auto_modelo": "Corolla",
        "pieza_varias_tipo": "Cambio Aceite",
        "total_mantenimiento": 250000,
        "pieza_varias_obs": "Cambio de aceite 5W30",
        "km_proximo_cambio_aceite": 20000,
    },
    {
        "pieza_varias_fecha": "2026-05-22",
        "placa": "DEF456",
        "_auto_marca": "Mazda",
        "_auto_modelo": "3",
        "pieza_varias_tipo": "Frenos",
        "total_mantenimiento": 450000,
        "pieza_varias_obs": "Cambio pastillas",
        "km_proximo_cambio_aceite": 25000,
    },
]

_MOCK_AUTOS = [
    {
        "placa": "ABC123",
        "marca": "Toyota",
        "modelo": "Corolla",
        "estado": "Disponible",
        "kilometraje": 15000,
    },
    {"placa": "DEF456", "marca": "Mazda", "modelo": "3", "estado": "Rentado", "kilometraje": 25000},
]


@patch(
    "views.mantenimiento_view.MantenimientoService.listar_historial",
    return_value=_MOCK_MANTENIMIENTOS,
)
@patch("views.mantenimiento_view.AutoService.listar", return_value=_MOCK_AUTOS)
class TestMantenimientoWidget:
    """Suite de pruebas para MantenimientoWidget."""

    def test_instancia(self, mock_autos, mock_historial, qapp):
        """MantenimientoWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = MantenimientoWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, MantenimientoWidget)
        widget.deleteLater()

    def test_tiene_banner_y_tabla(self, mock_autos, mock_historial, qapp):
        """El widget tiene buscador, combo y tabla."""
        widget = MantenimientoWidget()
        assert hasattr(widget, "txt_buscar")
        assert hasattr(widget, "cmb_filtro")
        assert hasattr(widget, "tabla")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_autos, mock_historial, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = MantenimientoWidget()
        headers = [
            widget.tabla.horizontalHeaderItem(i).text() for i in range(widget.tabla.columnCount())
        ]
        assert "Placa" in headers
        assert "Tipo Servicio" in headers
        assert "Costo" in headers
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_historial_pinta_filas(self, mock_autos, mock_historial, qapp):
        """cargar_historial() pinta filas en la tabla."""
        widget = MantenimientoWidget()
        widget.cargar_historial()
        assert widget.tabla.rowCount() == len(_MOCK_MANTENIMIENTOS)
        mock_historial.assert_called()
        widget.deleteLater()

    def test_cargar_historial_muestra_placas(self, mock_autos, mock_historial, qapp):
        """Las placas se muestran correctamente."""
        widget = MantenimientoWidget()
        widget.cargar_historial()
        assert widget.tabla.item(0, 1).text() == "ABC123"
        assert widget.tabla.item(1, 1).text() == "DEF456"
        widget.deleteLater()

    def test_cargar_historial_muestra_costos(self, mock_autos, mock_historial, qapp):
        """Los costos se muestran con formato $."""
        widget = MantenimientoWidget()
        widget.cargar_historial()
        costo = widget.tabla.item(0, 4).text()
        assert "$" in costo
        assert "250" in costo
        widget.deleteLater()

    def test_cargar_historial_vacio(self, mock_autos, mock_historial, qapp):
        """Lista vacía: 0 filas."""
        mock_historial.return_value = []
        widget = MantenimientoWidget()
        widget.cargar_historial()
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    def test_cargar_historial_con_error(self, mock_autos, mock_historial, qapp):
        """Cuando el servicio lanza excepción, no crashea."""
        from core.exceptions import DinamoBaseError

        mock_historial.side_effect = DinamoBaseError("Error DB")
        widget = MantenimientoWidget()
        widget.cargar_historial()  # No debe lanzar
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    # ── Filtro ─────────────────────────────────────────────────────────

    def test_filtrar_por_placa(self, mock_autos, mock_historial, qapp):
        """Filtrar por placa reduce resultados."""
        widget = MantenimientoWidget()
        widget.cargar_historial()
        widget.txt_buscar.setText("ABC")
        assert widget.tabla.rowCount() == 1
        widget.deleteLater()

    def test_filtrar_vacio_restaura(self, mock_autos, mock_historial, qapp):
        """Texto vacío restaura todos los registros."""
        widget = MantenimientoWidget()
        widget.cargar_historial()
        widget.txt_buscar.setText("Inexistente")
        assert widget.tabla.rowCount() == 0
        widget.txt_buscar.setText("")
        assert widget.tabla.rowCount() == len(_MOCK_MANTENIMIENTOS)
        widget.deleteLater()


# ── Tests para NuevoMantenimientoDialog ──────────────────────────────────────


class TestNuevoMantenimientoDialog:
    """Tests de instanciación del diálogo de mantenimiento."""

    def test_instancia(self, qapp):
        """NuevoMantenimientoDialog se instancia correctamente."""
        dlg = NuevoMantenimientoDialog()
        assert dlg is not None
        assert "Mantenimiento" in dlg.windowTitle()
        dlg.deleteLater()

    def test_tiene_campos(self, qapp):
        """El diálogo tiene los campos esperados."""
        dlg = NuevoMantenimientoDialog()
        assert hasattr(dlg, "cmb_placa")
        assert hasattr(dlg, "cmb_tipo")
        assert hasattr(dlg, "spin_costo")
        dlg.deleteLater()
