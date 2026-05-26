"""Tests for CalendarioWidget — fleet availability calendar."""

from unittest.mock import patch


from views.calendario_view import CalendarioWidget


# ── Mock data ─────────────────────────────────────────────────────────────────
_MOCK_AUTOS = [
    {"placa": "ABC123", "marca": "Toyota", "modelo": "Corolla", "estado": "Disponible"},
    {"placa": "DEF456", "marca": "Mazda", "modelo": "3", "estado": "Rentado"},
    {"placa": "GHI789", "marca": "Suzuki", "modelo": "Swift", "estado": "Mantenimiento"},
]

_MOCK_RENTAS = [
    {
        "placa": "ABC123",
        "fecha_recogida": "2026-05-01",
        "fecha_retorno": "2026-05-10",
        "tipo": "renta",
    },
]


@patch("views.calendario_view.AutoService.listar", return_value=_MOCK_AUTOS)
@patch("views.calendario_view.RentaService.obtener_para_calendario", return_value=_MOCK_RENTAS)
class TestCalendarioWidget:
    """Suite de pruebas para CalendarioWidget."""

    def test_instancia(self, mock_autos, mock_rentas, qapp):
        """CalendarioWidget se instancia correctamente."""
        from tests.helpers import BaseWidgetTestMixin

        widget = CalendarioWidget()
        BaseWidgetTestMixin.check_base_widget(widget)
        assert isinstance(widget, CalendarioWidget)
        widget.deleteLater()

    def test_tiene_elementos_ui(self, mock_autos, mock_rentas, qapp):
        """El widget tiene tabla, label de mes y botones."""
        widget = CalendarioWidget()
        assert hasattr(widget, "tabla")
        assert hasattr(widget, "lbl_mes")
        widget.deleteLater()

    def test_mes_actual_en_label(self, mock_autos, mock_rentas, qapp):
        """El label del mes se actualiza al cargar."""
        from views.calendario_view import CalendarioWidget as CW

        widget = CalendarioWidget()
        widget.cargar_calendario()
        mes_nombre = CW._MESES[widget.mes_vista - 1]
        assert str(mes_nombre) in widget.lbl_mes.text()
        assert str(widget.anio_vista) in widget.lbl_mes.text()
        widget.deleteLater()

    def test_columnas_segun_dias_mes(self, mock_autos, mock_rentas, qapp):
        """La tabla tiene columnas = días del mes + 1 (header Vehículo)."""
        import calendar

        widget = CalendarioWidget()
        widget.cargar_calendario()
        dias_esperados = calendar.monthrange(widget.anio_vista, widget.mes_vista)[1]
        assert widget.tabla.columnCount() == dias_esperados + 1
        widget.deleteLater()

    def test_filas_segun_autos(self, mock_autos, mock_rentas, qapp):
        """La tabla tiene filas = cantidad de autos."""
        widget = CalendarioWidget()
        widget.cargar_calendario()
        assert widget.tabla.rowCount() == len(_MOCK_AUTOS)
        widget.deleteLater()

    def test_mes_anterior_cambia_mes(self, mock_autos, mock_rentas, qapp):
        """mes_anterior() cambia el mes correctamente."""
        widget = CalendarioWidget()
        mes_original = widget.mes_vista
        widget.mes_anterior()
        if mes_original == 1:
            assert widget.mes_vista == 12
            assert widget.anio_vista == 2025  # año anterior
        else:
            assert widget.mes_vista == mes_original - 1
        widget.deleteLater()

    def test_mes_siguiente_cambia_mes(self, mock_autos, mock_rentas, qapp):
        """mes_siguiente() cambia el mes correctamente."""
        widget = CalendarioWidget()
        mes_original = widget.mes_vista
        widget.mes_siguiente()
        if mes_original == 12:
            assert widget.mes_vista == 1
            assert widget.anio_vista == 2027  # año siguiente
        else:
            assert widget.mes_vista == mes_original + 1
        widget.deleteLater()

    def test_cargar_calendario_sin_autos(self, mock_autos, mock_rentas, qapp):
        """Con lista vacía de autos, no crashea — filas vacías."""
        widget = CalendarioWidget()
        with patch("views.calendario_view.AutoService.listar", return_value=[]):
            widget.cargar_calendario()  # No debe lanzar
        assert widget.tabla.rowCount() == 0
        widget.deleteLater()
