"""
test_widgets_banners.py — Verifica que todos los widgets principales
del sistema tengan un banner visible en tiempo de ejecución.

Usa ``BaseWidgetTestMixin`` de ``tests.helpers`` para la detección
reutilizable de banners (fixedHeight=64 + estilo gradiente).

Run: pytest tests/test_widgets_banners.py -v
"""

import pytest
from tests.helpers import BaseWidgetTestMixin

# ── QApplication fixture (module-scoped, created once) ────────────────────────


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — Widgets principales del sistema
# ═══════════════════════════════════════════════════════════════════════════════

WIDGETS = [
    pytest.param("views.alertas_view", "AlertasWidget", id="alertas"),
    pytest.param("views.autos_view", "AutosWidget", id="autos"),
    pytest.param("views.calendario_view", "CalendarioWidget", id="calendario"),
    pytest.param("views.clientes_view", "ClientesWidget", id="clientes"),
    pytest.param("views.comparendos_view", "ComparendosWidget", id="comparendos"),
    pytest.param("views.dashboard_view", "DashboardWidget", id="dashboard"),
    pytest.param("views.gastos_view", "GastosWidget", id="gastos"),
    pytest.param("views.informes_view", "InformesWidget", id="informes"),
    pytest.param("views.mantenimiento_view", "MantenimientoWidget", id="mantenimiento"),
    pytest.param("views.rentas_view", "RentasWidget", id="rentas"),
    pytest.param("views.reservas_view", "ReservasWidget", id="reservas"),
    pytest.param("views.usuarios_view", "UsuariosWidget", id="usuarios"),
]


class TestWidgetBanners(BaseWidgetTestMixin):
    """Cada widget principal debe tener un banner con gradiente.

    Usa ``assert_has_banner`` y ``get_banner_title`` del mixin para
    detección reutilizable de banners en tiempo de ejecución.
    """

    @pytest.mark.parametrize(
        ("module_path", "class_name"),
        WIDGETS,
    )
    def test_tiene_banner(self, qapp, module_path, class_name):
        """Widget se instancia y contiene un banner QWidget con gradiente."""
        import importlib

        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        widget = cls()
        try:
            self.assert_has_banner(widget)
        finally:
            widget.close()
            widget.deleteLater()

    @pytest.mark.parametrize(
        ("module_path", "class_name"),
        WIDGETS,
    )
    def test_banner_visible(self, qapp, module_path, class_name):
        """El banner tiene contenido textual (título) visible."""
        import importlib

        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)

        widget = cls()
        try:
            titulo = self.get_banner_title(widget)
            assert titulo, f"Banner de {class_name} no tiene texto de título"
        finally:
            widget.close()
            widget.deleteLater()

    def test_report(self, qapp):
        """Genera reporte legible con el estado de banners de todos los widgets."""
        resultados = []
        todos_ok = True

        for module_path, class_name in (
            ("views.alertas_view", "AlertasWidget"),
            ("views.autos_view", "AutosWidget"),
            ("views.calendario_view", "CalendarioWidget"),
            ("views.clientes_view", "ClientesWidget"),
            ("views.comparendos_view", "ComparendosWidget"),
            ("views.dashboard_view", "DashboardWidget"),
            ("views.gastos_view", "GastosWidget"),
            ("views.informes_view", "InformesWidget"),
            ("views.mantenimiento_view", "MantenimientoWidget"),
            ("views.rentas_view", "RentasWidget"),
            ("views.reservas_view", "ReservasWidget"),
            ("views.usuarios_view", "UsuariosWidget"),
        ):
            import importlib

            mod = importlib.import_module(module_path)
            cls = getattr(mod, class_name)

            widget = cls()
            try:
                tiene = self._find_banner(widget) is not None
                titulo = self.get_banner_title(widget) if tiene else ""
                estado = "✅" if tiene else "❌"
                info = f"{titulo}" if tiene else "SIN BANNER"
                resultados.append(f"  {estado} {class_name:20s}  →  {info}")
                if not tiene:
                    todos_ok = False
            finally:
                widget.close()
                widget.deleteLater()

        reporte = [
            "\n═══ Reporte de Banners en Widgets ═══",
            f"Total widgets: {len(resultados)}",
            *resultados,
            "═══ FIN ═══\n",
        ]
        reporte_str = "\n".join(reporte)

        if not todos_ok:
            pytest.fail(f"Widgets sin banner detectado:\n{reporte_str}")
        else:
            print(reporte_str)
