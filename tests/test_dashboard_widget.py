"""test_dashboard_widget.py — Unit tests for DashboardWidget.

Run: pytest tests/test_dashboard_widget.py -v
"""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QFrame,
    QLabel,
    QTableWidget,
    QComboBox,
    QProgressBar,
)
from tests.helpers import BaseWidgetTestMixin


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — DashboardWidget
# ═══════════════════════════════════════════════════════════════════════════════


@patch("views.dashboard_view.DashboardService.kpi_globales", return_value={})
@patch("views.dashboard_view.AutoService.obtener_alertas", return_value=[])
@patch("views.dashboard_view.DashboardService.obtener_resumen_financiero", return_value={})
@patch("views.dashboard_view.DashboardService.obtener_activas_filtradas", return_value=[])
class TestDashboardWidget:
    """DashboardWidget instantiation, structure, and lifecycle."""

    # ── Instantiation ──────────────────────────────────────────────────────

    def test_instancia(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """Widget instantiates without errors and is a QWidget."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            assert isinstance(widget, QWidget)
        finally:
            widget.close()
            widget.deleteLater()

    # ── Banner ─────────────────────────────────────────────────────────────

    def test_tiene_banner(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget has a banner with gradient."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            mixin = BaseWidgetTestMixin()
            mixin.assert_has_banner(widget)
            titulo = mixin.get_banner_title(widget)
            assert titulo, "Banner should have a title"
            assert "Tablero" in titulo
        finally:
            widget.close()
            widget.deleteLater()

    # ── Structure ──────────────────────────────────────────────────────────

    def test_tiene_kpi_cards(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget has KPI cards and financial mini-cards."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            dashcards = widget.findChildren(QFrame)
            matching = [f for f in dashcards if f.property("dashcard") == "true"]
            # 5 KPIs + 4 mini-cards = 9 cards
            assert (
                len(matching) >= 9
            ), f"Expected at least 9 dashboard cards (5 KPI + 4 minicard), found {len(matching)}"
        finally:
            widget.close()
            widget.deleteLater()

    def test_tiene_barra_progreso(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget has an ocupacion progress bar."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            bars = widget.findChildren(QProgressBar)
            assert len(bars) >= 1, "Expected at least 1 progress bar"
        finally:
            widget.close()
            widget.deleteLater()

    def test_tiene_tablas(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget has alertas and rentas tables."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            tables = widget.findChildren(QTableWidget)
            assert (
                len(tables) >= 2
            ), f"Expected at least 2 tables (alertas + rentas), found {len(tables)}"
        finally:
            widget.close()
            widget.deleteLater()

    def test_tiene_filtro_rentas(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget has a filter combo for rentas."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            combos = widget.findChildren(QComboBox)
            assert len(combos) >= 1
            # At least one combo should have 'Todas' text
            found = any("Todas" in cmb.currentText() for cmb in combos)
            assert found, "Expected filter combo with 'Todas' option"
        finally:
            widget.close()
            widget.deleteLater()

    # ── Loading overlay ────────────────────────────────────────────────────

    def test_tiene_loading_overlay(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """DashboardWidget initializes a LoadingOverlay."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            assert (
                widget._loading_overlay is not None
            ), "DashboardWidget should initialize a LoadingOverlay"
        finally:
            widget.close()
            widget.deleteLater()

    # ── Data loading ───────────────────────────────────────────────────────

    def test_cargar_datos_actualiza_kpis(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """cargar_datos() updates KPI cards with service data."""
        from views.dashboard_view import DashboardWidget

        # Replace mocks with richer data
        kpis = {
            "rentas_activas": 5,
            "autos_disponibles": 10,
            "autos_mantenimiento": 2,
            "autos_rentados": 7,
            "total_flota": 20,
            "ocupacion_flota": 35.0,
        }
        finanzas = {
            "ingresos_mes": 15000000.0,
            "egresos_taller_mes": 2000000.0,
            "gastos_caja_mes": 1000000.0,
            "utilidad_mes": 12000000.0,
        }
        alertas = [
            {
                "placa": "ABC123",
                "tipo": "SOAT",
                "detalle": "Vence en 5 dias",
                "estado": "VENCE PRONTO",
            },
            {
                "placa": "XYZ789",
                "tipo": "Tecno-Mecanica",
                "detalle": "Vencido desde hace 3 dias",
                "estado": "VENCIDO",
            },
        ]

        with (
            patch(
                "views.dashboard_view.DashboardService.kpi_globales",
                return_value=kpis,
            ),
            patch(
                "views.dashboard_view.AutoService.obtener_alertas",
                return_value=alertas,
            ),
            patch(
                "views.dashboard_view.DashboardService.obtener_resumen_financiero",
                return_value=finanzas,
            ),
        ):
            widget = DashboardWidget()
            try:
                widget.cargar_datos()

                # KPI cards
                assert widget.card_activas.lbl_valor.text() == "5"
                assert widget.card_disp.lbl_valor.text() == "10"
                assert widget.card_taller.lbl_valor.text() == "2"
                assert widget.card_alertas.lbl_valor.text() == "2"

                # Ocupacion card
                assert "35" in widget.card_ocupacion.lbl_valor.text()
                assert "7 rentados" in widget.card_ocupacion.lbl_detalle.text()
                assert "35.0%" in widget.card_ocupacion.toolTip()

                # Financial cards (normalize commas for cross-locale)
                ing_text = widget.card_fin_ingresos.lbl_valor.text()
                tall_text = widget.card_fin_taller.lbl_valor.text()
                caja_text = widget.card_fin_caja.lbl_valor.text()
                util_text = widget.card_fin_utilidad.lbl_valor.text()
                assert "15000000" in ing_text.replace(",", "")
                assert "2000000" in tall_text.replace(",", "")
                assert "1000000" in caja_text.replace(",", "")
                assert "12000000" in util_text.replace(",", "")

                # Alertas table
                assert widget.tbl_alertas.rowCount() == 2
            finally:
                widget.close()
                widget.deleteLater()

    def test_cargar_datos_sin_datos(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """cargar_datos() handles empty service responses gracefully."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            widget.cargar_datos()  # mocks return empty dicts/lists

            # KPI values default to 0 (via .get(key, 0))
            assert widget.card_activas.lbl_valor.text() == "0"
            assert widget.card_disp.lbl_valor.text() == "0"
            assert widget.card_taller.lbl_valor.text() == "0"
            assert widget.card_alertas.lbl_valor.text() == "0"
            # Ocupacion: set_value(0.0, 0, 0) → "0%"
            assert widget.card_ocupacion.lbl_valor.text() == "0%"
            assert widget.tbl_alertas.rowCount() == 0
        finally:
            widget.close()
            widget.deleteLater()

    # ── Tabla filtering ────────────────────────────────────────────────────

    def test_filtrar_tabla_con_datos(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """filtrar_tabla() populates the rentas table."""
        from views.dashboard_view import DashboardWidget

        today = datetime.now().date()
        rentas = [
            {
                "id": 1,
                "placa": "ABC123",
                "nombre_cliente": "Juan Perez",
                "fecha_retorno": today + timedelta(days=3),
            },
            {"id": 2, "placa": "XYZ789", "nombre_cliente": "Maria Gomez", "fecha_retorno": today},
            {
                "id": 3,
                "placa": "DEF456",
                "nombre_cliente": "Carlos Lopez",
                "fecha_retorno": today - timedelta(days=1),
            },
        ]

        with patch(
            "views.dashboard_view.DashboardService.obtener_activas_filtradas",
            return_value=rentas,
        ):
            widget = DashboardWidget()
            try:
                widget.filtrar_tabla()

                assert widget.tbl_rentas.rowCount() == 3

                # First row: placa
                placa = widget.tbl_rentas.item(0, 1)
                assert placa is not None and placa.text() == "ABC123"

                # Third row: atrasado
                dias = widget.tbl_rentas.item(2, 4)
                assert dias is not None
                assert "Atrasado" in dias.text()
            finally:
                widget.close()
                widget.deleteLater()

    # ── Stale timer safety ─────────────────────────────────────────────────

    def test_stale_timer_no_crash(self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp):
        """Destroying widget before deferred timer fires does not crash."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        widget.close()
        widget.deleteLater()
        QApplication.processEvents()  # Should not crash

    # ── Double-click handler ───────────────────────────────────────────────

    def test_abrir_cierre_ignora_fila_vacia(
        self, mock_filtrar, mock_fin, mock_alert, mock_kpi, qapp
    ):
        """_abrir_cierre does nothing when the ID cell is empty."""
        from views.dashboard_view import DashboardWidget

        widget = DashboardWidget()
        try:
            # Simulate double-click on an empty row
            widget._abrir_cierre(0, 1)  # Should not raise
        finally:
            widget.close()
            widget.deleteLater()


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — Internal Components
# ═══════════════════════════════════════════════════════════════════════════════


class TestKpiCard:
    """Unit tests for _KpiCard."""

    def test_crear(self, qapp):
        """_KpiCard creates with dashcard property."""
        from views.dashboard_view import _KpiCard

        card = _KpiCard("Test", "🚗", "#2563eb")
        assert card.property("dashcard") == "true"
        assert card.lbl_valor is not None

    def test_set_value(self, qapp):
        """set_value updates the displayed text."""
        from views.dashboard_view import _KpiCard

        card = _KpiCard("Rentas", "🚗", "#2563eb")
        card.set_value("42")
        assert card.lbl_valor.text() == "42"

    def test_min_height(self, qapp):
        """_KpiCard has a minimum height."""
        from views.dashboard_view import _KpiCard

        card = _KpiCard("Test", "🚗", "#2563eb")
        assert card.minimumHeight() >= 80


class TestKpiCardOcupacion:
    """Unit tests for _KpiCardOcupacion."""

    def test_crear(self, qapp):
        """_KpiCardOcupacion creates with dashcard property and progress bar."""
        from views.dashboard_view import _KpiCardOcupacion

        card = _KpiCardOcupacion()
        assert card.property("dashcard") == "true"
        assert card.progress is not None
        assert card.lbl_valor is not None
        assert card.lbl_detalle is not None

    def test_set_value(self, qapp):
        """set_value updates progress, labels, and tooltip."""
        from views.dashboard_view import _KpiCardOcupacion

        card = _KpiCardOcupacion()
        card.set_value(75.5, rentados=15, activos=20)

        assert card.lbl_valor.text() == "76%"  # formatted with :.0f (rounds)
        assert card.lbl_detalle.text() == "15 rentados / 20 activos"
        assert "75.5%" in card.toolTip()
        assert card.progress.value() == 75  # int(75.5) truncates

    def test_set_value_cero(self, qapp):
        """set_value handles 0% without errors."""
        from views.dashboard_view import _KpiCardOcupacion

        card = _KpiCardOcupacion()
        card.set_value(0.0, rentados=0, activos=0)
        assert "0%" in card.lbl_valor.text()
        assert card.progress.value() == 0

    def test_set_value_cien(self, qapp):
        """set_value handles 100% without errors."""
        from views.dashboard_view import _KpiCardOcupacion

        card = _KpiCardOcupacion()
        card.set_value(100.0, rentados=20, activos=20)
        assert card.progress.value() == 100


class TestMiniCard:
    """Unit tests for _MiniCard."""

    def test_crear(self, qapp):
        """_MiniCard creates with dashcard property."""
        from views.dashboard_view import _MiniCard

        card = _MiniCard("Ingresos", "📈", "#059669")
        assert card.property("dashcard") == "true"
        assert card.lbl_valor is not None

    def test_set_value(self, qapp):
        """set_value updates the displayed text."""
        from views.dashboard_view import _MiniCard

        card = _MiniCard("Ingresos", "📈", "#059669")
        card.set_value("$ 1,000,000")
        assert card.lbl_valor.text() == "$ 1,000,000"

    def test_min_height(self, qapp):
        """_MiniCard has a minimum height."""
        from views.dashboard_view import _MiniCard

        card = _MiniCard("Gastos", "💳", "#7c3aed")
        assert card.minimumHeight() >= 68


class TestSectionHeader:
    """Unit tests for section_header helper."""

    def test_crear_sin_icono(self, qapp):
        """_section_header returns a QWidget with labels."""
        from views.dashboard_view import _section_header

        header = _section_header("Alertas")
        assert isinstance(header, QWidget)
        labels = header.findChildren(QLabel)
        assert any("Alertas" in lbl.text() for lbl in labels)

    def test_crear_con_icono(self, qapp):
        """_section_header with icon still produces a header widget."""
        from views.dashboard_view import _section_header

        header = _section_header("Rentas", "📋")
        assert isinstance(header, QWidget)
        labels = header.findChildren(QLabel)
        assert any("Rentas" in lbl.text() for lbl in labels)
