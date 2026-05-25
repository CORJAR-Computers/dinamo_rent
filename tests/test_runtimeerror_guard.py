"""
Tests for the RuntimeError guard pattern in deferred loading via QTimer.singleShot.

The pattern (applied to 10+ dialogs across the codebase):
1. A dialog/widget creates a LoadingOverlay and schedules a callback via
   QTimer.singleShot(0, callback) in its __init__
2. The callback starts with a RuntimeError guard:
       try:
           _ = self.some_widget
       except RuntimeError:
           self._loading_overlay = None
           return
3. BaseWidget._deferred_call() also catches and suppresses RuntimeError from
   the deferred callback (via except RuntimeError: pass)

This prevents crashes when QApplication.processEvents() triggers stale
QTimers from already-destroyed C++ widgets — a scenario that occurs in
test suites when one test calls processEvents() and processes timers
left behind by dialogs created in previous tests.

Uses LoaderTestMixin + LoaderTestDialog from tests.helpers for reusable
test patterns.

Run: pytest tests/test_runtimeerror_guard.py -v
"""

from typing import Any

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout

from tests.helpers import (
    BaseWidgetTestHelper,
    BaseWidgetTestMixin,
    LoaderTestDialog,
    LoaderTestMixin,
)


# ── QApplication singleton (created once at module level) ──────────────────
_app: QApplication | None = QApplication.instance()
if _app is None:
    _app = QApplication([])


# ═══════════════════════════════════════════════════════════════════════════════
# Helper dialog — reuses LoaderTestDialog from tests/helpers
# ═══════════════════════════════════════════════════════════════════════════════

class _DialogoConTimer(LoaderTestDialog):
    """Test dialog that mimics the standard LoadingOverlay + QTimer.singleShot
    pattern using the reusable LoaderTestDialog base class."""

    GUARD_WIDGET: str = "lbl"
    LOADING_MESSAGE: str = "Test loading..."

    def _setup_content(self) -> None:
        self.lbl = QLabel("initial", self)
        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl)

    def _do_deferred_work(self) -> None:
        self.lbl.setText("executed")


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — RuntimeError guard at the top of deferred callbacks
# ═══════════════════════════════════════════════════════════════════════════════

class TestGuardEnDialogo(LoaderTestMixin):
    """Verifies the RuntimeError guard pattern inside dialog deferred callbacks.
    Uses LoaderTestMixin helpers for standard test scenarios."""

    def test_callback_ejecuta_normal(self) -> None:
        """Dialog with timer fires normally — callback runs and overlay hides.

        Uses run_normal_execution() which handles the full lifecycle:
        create → assert overlay exists → processEvents → verify callback.
        """
        dlg = self.run_normal_execution(_DialogoConTimer)
        # Additional assertions specific to this dialog's behavior
        assert dlg.lbl.text() == "executed", "Callback did not update label"

    def test_guard_timer_stale(self) -> None:
        """Dialog destroyed before timer fires — guard prevents crash.

        Uses run_stale_timer() which handles: create → destroy → processEvents.
        The RuntimeError guard at the top of _deferred_init() catches
        the RuntimeError from accessing self.lbl on the destroyed C++ object.
        """
        self.run_stale_timer(_DialogoConTimer)

    def test_guard_timer_stale_multiple(self) -> None:
        """Multiple stale timers from destroyed dialogs all suppressed."""
        self.run_stale_timer_multiple(_DialogoConTimer, count=5)

    def test_cleanup_despues_de_callback_no_crashea(self) -> None:
        """Deferred callback ran normally, then dialog is destroyed cleanly.

        QTimer.singleShot(0, ...) only fires once. After the first
        processEvents(), the callback has already executed. This test
        verifies that destroy + processEvents() still doesn't crash even
        when the dialog is destroyed after its deferred callback already ran.
        """
        dlg = _DialogoConTimer()
        try:
            self.process_events()
            assert dlg.callback_executed

            self.destroy_dialog(dlg)
            self.process_events()  # Should not crash (deferred delete only)
        finally:
            try:
                dlg.close()
            except RuntimeError:
                pass

    def test_guard_no_false_positives(self) -> None:
        """Guard does NOT catch legitimate RuntimeErrors from non-C++ sources.

        Uses run_callback_exception() which creates the dialog with a
        callback_ex exception, fires the timer, then verifies the overlay
        was hidden even though the callback failed.
        """
        self.run_callback_exception(_DialogoConTimer, ValueError("test error"))


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — BaseWidget._deferred_call() suppression of RuntimeError
# ═══════════════════════════════════════════════════════════════════════════════

class TestDeferredCall(BaseWidgetTestMixin):
    """Verifies BaseWidget._deferred_call() suppresses RuntimeError from callback.

    Uses ``BaseWidgetTestHelper`` for lightweight test widgets and
    ``BaseWidgetTestMixin`` methods (``run_deferred_call_direct``,
    ``run_deferred_load``) for consistent test patterns.
    """

    def test_suprime_runtimeerror_en_func(self) -> None:
        """_deferred_call catches RuntimeError from func() without re-raising.

        Uses ``run_deferred_call_direct`` with ``RuntimeError`` exception.
        """
        w = self.run_deferred_call_direct(
            BaseWidgetTestHelper,
            exception=RuntimeError("Simulated C++ deletion"),
            skip_banner=True,
        )
        assert not w.callback_executed, (
            "Callback should NOT have completed due to RuntimeError"
        )

    def test_deferred_load_suprime_runtimeerror(self) -> None:
        """_deferred_load (convenience wrapper) also suppresses RuntimeError.

        Uses custom helper that raises RuntimeError in cargar_datos.
        """
        class _WidgetCrashHelper(BaseWidgetTestHelper):
            def _setup_content(self) -> None:
                pass

            def cargar_datos(self) -> None:
                self.callback_executed = True
                raise RuntimeError("Simulated C++ deletion")

        w = _WidgetCrashHelper(skip_banner=True)
        try:
            self.assert_overlay_init(w)
            w._deferred_load()  # Should not crash
            assert w.callback_executed, "Callback should have run before RuntimeError"
        finally:
            self._cleanup_widget(w)

    def test_no_suprime_otras_excepciones(self) -> None:
        """_deferred_call does NOT suppress non-RuntimeError exceptions.

        Uses ``run_deferred_call_direct`` with ``ValueError`` exception.
        """
        w = self.run_deferred_call_direct(
            BaseWidgetTestHelper,
            exception=ValueError("Real error — should propagate"),
            skip_banner=True,
        )
        assert not w.callback_executed, (
            "Callback should NOT have completed due to ValueError"
        )

    def test_overlay_se_oculta_en_finally(self) -> None:
        """_deferred_call hides overlay in finally even if callback crashes.

        Uses custom helper that tracks _hide_overlay_safe execution.
        """
        class _WidgetOverlayHelper(BaseWidgetTestHelper):
            def __init__(self: Any) -> None:
                self._finally_ejecutado: bool = False
                super().__init__(skip_banner=True)

            def _setup_content(self) -> None:
                pass

            def cargar_datos(self: Any) -> None:
                raise RuntimeError("Simulated crash")

        w = _WidgetOverlayHelper()
        try:
            # Monkey-patch _hide_overlay_safe to track execution
            self.assert_overlay_init(w)
            original_hide = w._hide_overlay_safe

            def _tracking_hide() -> None:
                w._finally_ejecutado = True
                original_hide()

            w._hide_overlay_safe = _tracking_hide

            w._deferred_call(w.cargar_datos)  # Should not crash
            assert w._finally_ejecutado, (
                "_hide_overlay_safe should have been called in finally"
            )
        finally:
            self._cleanup_widget(w)


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — Integration with real production dialogs
# ═══════════════════════════════════════════════════════════════════════════════

class TestIntegracionDialogosReales(LoaderTestMixin):
    """Integration tests using real production dialogs that implement the guard
    pattern. Uses run_stale_timer() from LoaderTestMixin for consistent cleanup."""

    def test_comparendo_guard_con_timer_stale(self) -> None:
        """NuevoComparendoDialog's RuntimeError guard handles stale timer."""
        from views.comparendos_view import NuevoComparendoDialog
        self.run_stale_timer(NuevoComparendoDialog, parent=None)

    def test_mantenimiento_guard_con_timer_stale(self) -> None:
        """NuevoMantenimientoDialog's RuntimeError guard handles stale timer."""
        from views.mantenimiento_view import NuevoMantenimientoDialog
        self.run_stale_timer(NuevoMantenimientoDialog, parent=None)

    def test_pagos_guard_con_timer_stale(self) -> None:
        """PagosDialog's RuntimeError guard handles stale timer."""
        from views.pagos_view import PagosDialog
        self.run_stale_timer(PagosDialog, parent=None, id_renta=1,
                             total_renta=100000.0, cliente="Test")

    def test_reservas_selector_guard_con_timer_stale(self) -> None:
        """DialogoSelectorCliente (reservas) guard handles stale timer."""
        from views.reservas_view import DialogoSelectorCliente
        self.run_stale_timer(DialogoSelectorCliente, parent=None)

    def test_rentas_selector_guard_con_timer_stale(self) -> None:
        """DialogoSelectorCliente (rentas) guard handles stale timer."""
        from views.rentas_view import DialogoSelectorCliente
        self.run_stale_timer(DialogoSelectorCliente, parent=None)

    @pytest.mark.parametrize("module_path,class_name,kwargs", [
        pytest.param("views.rentas_view", "DialogoExtenderRenta",
                     {"id_renta": 1}, id="extender-renta"),
        pytest.param("views.rentas_view", "DialogoCambioVehiculo",
                     {"id_renta": 1, "placa_actual": "ABC123"}, id="cambio-vehiculo"),
        pytest.param("views.autos_view", "DialogoAuto",
                     {"placa_editar": "ABC123"}, id="auto-editar"),
        pytest.param("views.clientes_view", "ClienteFormDialog",
                     {}, id="cliente-form"),
    ])
    def test_dialogo_guard_con_timer_stale(
        self,
        module_path: str,
        class_name: str,
        kwargs: dict[str, Any],
    ) -> None:
        """Parameterized test: various dialogs handle stale timer gracefully."""
        import importlib
        mod = importlib.import_module(module_path)
        cls = getattr(mod, class_name)
        kwargs["parent"] = None
        self.run_stale_timer(cls, **kwargs)
