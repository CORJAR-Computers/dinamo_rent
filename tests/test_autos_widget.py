"""Tests for AutosWidget — fleet management panel."""

from unittest.mock import patch

from PySide6.QtWidgets import QApplication
import pytest

from views.autos_view import AutosWidget, DialogoAuto


# ── QApplication fixture ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_AUTOS = [
    {
        "placa": "ABC123",
        "marca": "Toyota",
        "modelo": "Corolla",
        "color": "Blanco",
        "estado": "Disponible",
        "kilometraje": 15000,
        "ubicacion": "Oficina",
        "fecha_ingreso": None,
    },
    {
        "placa": "DEF456",
        "marca": "Mazda",
        "modelo": "3",
        "color": "Rojo",
        "estado": "Rentado",
        "kilometraje": 25000,
        "ubicacion": "Oficina",
        "fecha_ingreso": None,
    },
]

_MOCK_AUTO_UNICO = {
    "placa": "ABC123",
    "marca": "Toyota",
    "modelo": "Corolla",
    "color": "Blanco",
    "estado": "Disponible",
    "kilometraje": 15000,
    "ubicacion": "Oficina",
    "fecha_ingreso": None,
    "tipo": "Automovil",
    "transmision": "Automatica",
    "combustible": "Gasolina",
    "costo_fijo_mensual": 0,
    "tipo_adquisicion": "Propio",
    "no_motor": "",
    "no_chasis": "",
    "propietario": "",
    "observaciones": "",
    "vencimiento_soat": None,
    "vencimiento_tecnico": None,
    "vencimiento_extintor": None,
    "vencimiento_bateria": None,
}


@patch("views.autos_view.AutoService.listar", return_value=_MOCK_AUTOS)
class TestAutosWidget:
    """Suite de pruebas para AutosWidget."""

    # ── Instanciación ──────────────────────────────────────────────────

    def test_instancia(self, mock_listar, qapp):
        """AutosWidget se instancia y hereda de BaseWidget."""
        from tests.helpers import BaseWidgetTestMixin

        widget = AutosWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, AutosWidget)
        widget.deleteLater()

    def test_tiene_banner(self, mock_listar, qapp):
        """El widget tiene un banner principal."""
        widget = AutosWidget()
        assert hasattr(widget, "txt_buscar")
        assert hasattr(widget, "cmb_filtro")
        assert hasattr(widget, "tabla")
        widget.deleteLater()

    def test_columnas_tabla(self, mock_listar, qapp):
        """La tabla tiene las columnas esperadas."""
        widget = AutosWidget()
        headers = [
            widget.tabla.horizontalHeaderItem(i).text() for i in range(widget.tabla.columnCount())
        ]
        assert "Placa" in headers
        assert "Estado" in headers
        assert "KM" in headers
        widget.deleteLater()

    def test_combo_filtro_tiene_opciones(self, mock_listar, qapp):
        """El combo de filtro tiene opciones."""
        widget = AutosWidget()
        assert widget.cmb_filtro.count() >= 3
        widget.deleteLater()

    # ── Carga de datos ─────────────────────────────────────────────────

    def test_cargar_datos_pinta_filas(self, mock_listar, qapp):
        """cargar_datos() pinta filas en la tabla."""
        widget = AutosWidget()
        widget.cargar_datos()
        assert widget.tabla.rowCount() == len(_MOCK_AUTOS)
        mock_listar.assert_called()
        widget.deleteLater()

    def test_cargar_datos_muestra_placas(self, mock_listar, qapp):
        """Los datos cargados muestran las placas correctas."""
        widget = AutosWidget()
        widget.cargar_datos()
        for row in range(widget.tabla.rowCount()):
            item = widget.tabla.item(row, 0)
            assert item is not None
            assert item.text() in ("ABC123", "DEF456")
        widget.deleteLater()

    def test_cargar_datos_sin_resultados(self, mock_listar, qapp):
        """Con lista vacía, tabla muestra 0 filas."""
        mock_listar.return_value = []
        widget = AutosWidget()
        widget.cargar_datos()
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()

    @patch("views.base_widget.BaseWidget.mostrar_error")
    def test_cargar_datos_con_error(self, mock_error, mock_listar, qapp):
        """Cuando el servicio lanza excepción, no crashea y tabla vacía."""
        from core.exceptions import DinamoBaseError

        mock_listar.side_effect = DinamoBaseError("Error DB")
        widget = AutosWidget()
        widget.cargar_datos()  # No debe lanzar
        assert widget.tabla.rowCount() == 0
        mock_error.assert_called_once()
        widget.deleteLater()

    # ── Filtro ─────────────────────────────────────────────────────────

    def test_filtrar_por_texto(self, mock_listar, qapp):
        """Filtrar por placa muestra solo los coincidentes."""
        widget = AutosWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("ABC")
        # El filtro se aplica vía textChanged
        assert widget.tabla.rowCount() == 1
        assert widget.tabla.item(0, 0).text() == "ABC123"
        widget.deleteLater()

    def test_filtrar_por_texto_vacio_restaura(self, mock_listar, qapp):
        """Texto vacío restaura todos los registros."""
        widget = AutosWidget()
        widget.cargar_datos()
        widget.txt_buscar.setText("XYZ")
        widget.txt_buscar.setText("")
        assert widget.tabla.rowCount() == len(_MOCK_AUTOS)
        widget.deleteLater()


# ── Tests para DialogoAuto ────────────────────────────────────────────────────


class TestDialogoAuto:
    """Tests de instanciación del diálogo (no se abre)."""

    def test_instancia(self, qapp):
        """DialogoAuto se instancia como QDialog."""
        dlg = DialogoAuto()
        assert dlg is not None
        assert dlg.windowTitle() == "Gestion de Vehiculo"
        dlg.deleteLater()

    def test_instancia_con_placa(self, qapp):
        """Al pasar placa_editar, muestra título "Editar Vehiculo"."""
        dlg = DialogoAuto(placa_editar="ABC123")
        assert dlg.placa_editar == "ABC123"
        dlg.deleteLater()
