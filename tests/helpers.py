"""
Reusable test helpers for the LoadingOverlay + QTimer.singleShot pattern.

Provides:
- **LoaderTestDialog** — Base dialog that mimics the production pattern:
  LoadingOverlay + QTimer.singleShot(0, deferred_callback) + RuntimeError guard.
  Subclass and implement _do_deferred_work() to create test dialogs.

- **LoaderTestMixin** — Mixin for pytest test classes that provides helper
  methods for common test scenarios:
  - Normal deferred callback execution
  - Stale timer after dialog destruction (single and multiple)
  - Non-RuntimeError exceptions in callbacks
  - Overlay cleanup assertions

Usage:
    from tests.helpers import LoaderTestDialog, LoaderTestMixin

    # 1. Custom test dialog
    class MiDialogoTest(LoaderTestDialog):
        GUARD_WIDGET = "lbl"
        LOADING_MESSAGE = "Cargando mi dialogo..."

        def _setup_content(self) -> None:
            self.lbl = QLabel("initial", self)
            layout = QVBoxLayout(self)
            layout.addWidget(self.lbl)

        def _do_deferred_work(self) -> None:
            self.lbl.setText("executed")

    # 2. Test class using the mixin
    class TestMiDialogo(LoaderTestMixin):
        def test_callback_normal(self) -> None:
            dlg = self.run_normal_execution(MiDialogoTest)
            assert dlg.lbl.text() == "executed"

        def test_stale_timer(self) -> None:
            self.run_stale_timer(MiDialogoTest)

    # 3. Integration test with real production dialog
    class TestRealDialogo(LoaderTestMixin):
        def test_stale_timer(self) -> None:
            self.run_stale_timer(ProdDialog, parent=None, id_renta=1)
"""

from typing import Any, TypeVar

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QWidget
from views.base_dialog import BaseDialog


# ═══════════════════════════════════════════════════════════════════════════════
# LoaderTestDialog — Base class for test dialogs with LoadingOverlay + QTimer
# ═══════════════════════════════════════════════════════════════════════════════

TLoader = TypeVar("TLoader", bound="LoaderTestDialog")
TWidget = TypeVar("TWidget", bound=QWidget)


class LoaderTestDialog(BaseDialog):
    """Base dialog for testing the LoadingOverlay + QTimer.singleShot pattern.

    Inherits from ``BaseDialog`` and adds test-specific tracking.
    Desactiva animaciones (``ENABLE_ANIMATIONS = False``) para no interferir
    con las assertions de tests.

    Subclasses must set:
      - GUARD_WIDGET: name of the widget attribute to check in the RuntimeError
                      guard (e.g., ``"lbl"`` for ``self.lbl``).
      - LOADING_MESSAGE: message shown in the LoadingOverlay.

    Subclasses must implement:
      - _setup_content(): Create widgets and layout.
      - _do_deferred_work(): The actual deferred callback logic.

    The dialog automatically:
      1. Calls _setup_content() in __init__
      2. Creates a LoadingOverlay with LOADING_MESSAGE
      3. Schedules _deferred_init() via QTimer.singleShot(0, ...)
      4. The callback has a RuntimeError guard that checks GUARD_WIDGET
      5. After _do_deferred_work(), hides the overlay in a finally block

    Tracks execution state in:
      - callback_executed: True if _do_deferred_work() ran
      - overlay_hidden: True if overlay.hide() was called in finally
      - _loading_overlay: The LoadingOverlay instance (or None)
    """

    # ── Override in subclasses ──────────────────────────────────────────────
    GUARD_WIDGET: str = ""  # e.g. "lbl"
    LOADING_MESSAGE: str = "Loading..."
    ENABLE_ANIMATIONS: bool = False  # Tests no deben depender de animaciones

    def __init__(
        self,
        parent: QDialog | None = None,
        callback_ex: BaseException | None = None,
    ) -> None:
        super().__init__(parent, callback_ex=callback_ex)
        self.callback_executed: bool = False
        self.overlay_hidden: bool = False

        self._setup_content()
        self._init_loading()

    # ── Subclass hooks ──────────────────────────────────────────────────────

    def _setup_content(self) -> None:
        """Create widgets and layout. Called from __init__."""
        raise NotImplementedError

    def _do_deferred_work(self) -> None:
        """Perform the actual deferred work. Called from _deferred_init()."""
        raise NotImplementedError

    # ── Internal ────────────────────────────────────────────────────────────

    def _init_loading(self) -> None:
        """Create LoadingOverlay and schedule deferred callback via QTimer."""
        self._init_overlay(self.LOADING_MESSAGE)
        QTimer.singleShot(0, self._deferred_init)

    def _deferred_init(self) -> None:
        """RuntimeError guard → _do_deferred_work() → hide overlay in finally."""
        # Guard: if C++ object was destroyed before timer fired, exit silently
        if self.GUARD_WIDGET:
            try:
                _ = getattr(self, self.GUARD_WIDGET)
            except RuntimeError:
                self._loading_overlay = None
                return

        try:
            if self._callback_ex:
                raise self._callback_ex
            self._do_deferred_work()
            self.callback_executed = True
        finally:
            self._hide_overlay_safe()
            self.overlay_hidden = True


# ═══════════════════════════════════════════════════════════════════════════════
# BaseWidgetTestHelper — Minimal BaseWidget subclass for testing
# ═══════════════════════════════════════════════════════════════════════════════


class BaseWidgetTestHelper(QWidget):  # type: ignore[misc]
    """Minimal BaseWidget-style helper for testing the deferred_load + overlay
    + banner pattern.

    Simulates how real production widgets (AutosWidget, ClientesWidget, etc.)
    work:
      1. Banner created in ``_setup_banner()`` (override to customize)
      2. ``_init_loading_overlay()`` called in __init__ via ``_setup_overlay()``
      3. ``QTimer.singleShot(0, self._deferred_load)`` scheduled in __init__
      4. ``_deferred_call()`` has RuntimeError guard + overlay show/hide
      5. ``cargar_datos()`` sets ``callback_executed = True``

    Subclasses can override:
      - ``BANNER_TITLE`` / ``BANNER_SUBTITLE`` / ``BANNER_ICON`` (class attrs)
      - ``_setup_banner()`` to change banner, or set ``BANNER_TITLE = ""``
        to skip banner creation.
      - ``_do_deferred_work()`` instead of cargar_datos for custom logic.
      - ``callback_executed_ex`` to raise an exception in cargar_datos.

    Usage::

        class MiWidgetTest(BaseWidgetTestHelper):
            BANNER_TITLE = "Mi Widget"
            BANNER_ICON = "🧪"

            def _setup_content(self) -> None:
                self.input = QLineEdit(self)
                layout = QVBoxLayout(self)
                layout.addWidget(self.input)
    """

    BANNER_TITLE: str = "Test Widget"
    BANNER_SUBTITLE: str = "Widget de prueba"
    BANNER_ICON: str = "🧪"
    LOADING_MESSAGE: str = "Cargando..."

    def __init__(
        self,
        parent: QWidget | None = None,
        session_id: str | None = None,
        callback_executed_ex: BaseException | None = None,
        skip_banner: bool = False,
        _no_auto_timer: bool = False,
    ) -> None:
        super().__init__(parent)
        self._session_id: str | None = session_id
        self._log = get_logger(self.__class__.__name__)
        self._form_validator: Any = None
        self._loading_overlay: Any = None
        self._datos_cargados: bool = False
        self.callback_executed: bool = False
        self._callback_ex: BaseException | None = callback_executed_ex
        self._no_auto_timer: bool = _no_auto_timer

        # ── Banner ──────────────────────────────────────────────────────
        if not skip_banner:
            self._setup_banner()

        # ── Content (widgets specific to the test) ──────────────────────
        self._setup_content()

        # ── Overlay + deferred load ────────────────────────────────────
        self._init_loading_overlay(self.LOADING_MESSAGE)
        if not self._no_auto_timer:
            QTimer.singleShot(0, self._deferred_load)

    # ── Hooks for subclasses ───────────────────────────────────────────────

    def _setup_content(self) -> None:
        """Create widgets and layout. Called from __init__."""
        pass

    def _setup_banner(self) -> None:
        """Create the banner widget using create_banner()."""
        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            self.BANNER_ICON,
            self.BANNER_TITLE,
            self.BANNER_SUBTITLE,
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(banner)

    # ── BaseWidget-compatible interface ────────────────────────────────────

    def _init_loading_overlay(self, message: str | None = None) -> None:
        """Create LoadingOverlay (mirrors BaseWidget._init_loading_overlay)."""
        if self._loading_overlay is None:
            from views.components.loading_spinner import LoadingOverlay

            self._loading_overlay = LoadingOverlay(self, message or self.LOADING_MESSAGE)
        elif message:
            self._loading_overlay.set_message(message)

    def _deferred_call(self, func: Any) -> None:
        """Run func with overlay show/hide (mirrors BaseWidget._deferred_call).

        Includes the same RuntimeError guard: checks ``isWidgetType()`` before
        proceeding, catches ``RuntimeError`` from func, and hides overlay in
        ``finally``.
        """
        # Guard: C++ object may have been deleted
        try:
            _ = self.isWidgetType()
        except RuntimeError:
            self._loading_overlay = None
            return

        self._show_overlay_safe()
        if self._loading_overlay is not None:
            try:
                self._loading_overlay.repaint()
            except RuntimeError:
                self._loading_overlay = None

        try:
            self.cargar_datos()
        except RuntimeError:
            pass
        except Exception:
            raise
        finally:
            self._hide_overlay_safe()

    def _show_overlay_safe(self) -> None:
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.show()
        except RuntimeError:
            self._loading_overlay = None

    def _hide_overlay_safe(self) -> None:
        if self._loading_overlay is None:
            return
        try:
            self._loading_overlay.hide()
        except RuntimeError:
            self._loading_overlay = None

    def _deferred_load(self) -> None:
        """Convenience wrapper (mirrors BaseWidget._deferred_load)."""
        self._deferred_call(self.cargar_datos)

    def cargar_datos(self) -> None:
        """Override in subclasses for custom data loading logic.

        Default implementation:
          - Raises ``_callback_ex`` if set
          - Otherwise sets ``callback_executed = True``
        """
        if self._callback_ex:
            raise self._callback_ex
        self.callback_executed = True

    def closeEvent(self, event: Any) -> None:
        """Ensure clean teardown (mirrors real widget behavior)."""
        self._loading_overlay = None
        super().closeEvent(event)


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: import logger inside class method to avoid circular imports
# ═══════════════════════════════════════════════════════════════════════════════


def get_logger(name: str) -> Any:
    import logging

    return logging.getLogger(name)


# ═══════════════════════════════════════════════════════════════════════════════
# LoaderTestMixin — Mixin for pytest test classes
# ═══════════════════════════════════════════════════════════════════════════════


class LoaderTestMixin:
    """Mixin providing helper methods for LoadingOverlay + QTimer test scenarios.

        Mix this into your pytest test class:

            class TestSomething(LoaderTestMixin):
                def test_normal(self) -> None:
                    self.run_normal_execution(MyDialog)

        Available helpers:
          - run_normal_execution(cls, **kwargs) — Full cycle test
          - **run_normal_execution_with_structure(cls, expected_widgets, **kwargs)** — Full cycle + header/body/widget structure
          - run_stale_timer(cls, **kwargs) — Stale timer, no crash
          - run_stale_timer_multiple(cls, count=5, **kwargs) — Bulk stale timer
          - run_callback_exception(cls, exception, **kwargs) — Exception in callback
          - check_dialog_structure(dlg) — Assert header + body + root layout
          - assert_expected_widgets(dlg, names) — Assert specific Qt widget types exist
          - assert_overlay_exists(dlg)
          - assert_callback_executed(dlg)
          - assert_overlay_hidden(dlg)

        Usage::

            class TestMisDialogos(LoaderTestMixin):
                def test_estructura_y_callback(self) -> None:
                    dlg = self.run_normal_execution_with_structure(
                        MiDialogoTest,
                        ["QLineEdit", "QComboBox"],
                    )
                    assert dlg.my_specific_widget.isEnabled()

    ---

    **BaseWidgetTestMixin** — Mixin for testing BaseWidget subclasses.

    Usage::

        class TestMisWidgets(BaseWidgetTestMixin):
            def test_banner(self) -> None:
                self.assert_has_banner(MiWidget)

            def test_deferred_load(self) -> None:
                w = self.run_deferred_load(MiWidgetTest)  # uses helper
                assert w.callback_executed

            def test_stale_widget(self) -> None:
                self.run_stale_widget(MiWidgetTest)
    """

    # ── Lifecycle helpers ───────────────────────────────────────────────────

    @staticmethod
    def process_events() -> None:
        """Process pending Qt events to fire deferred QTimer callbacks."""
        QApplication.processEvents()

    @staticmethod
    def destroy_dialog(dlg: QDialog) -> None:
        """Close and schedule C++ deletion of a dialog."""
        dlg.close()
        dlg.deleteLater()

    def create_dialog(self, dialog_cls: type[TLoader], **kwargs: Any) -> TLoader:
        """Create a dialog, ensure cleanup in finally block."""
        dlg = dialog_cls(**kwargs)
        self._created_dialogs.append(dlg)  # type: ignore[attr-defined]
        return dlg

    # ── Structure assertion helpers ─────────────────────────────────────────

    @staticmethod
    def check_dialog_structure(dlg: QDialog) -> None:
        """Assert the dialog has the standard header+body structure.

        Checks:
          1. A child widget with objectName ``"dlg_header"`` (from
             ``build_dialog_header``) exists and is visible.
          2. A child widget with objectName ``"dlg_body"`` (from
             ``dialog_body_style``) exists and is visible.
          3. The root layout has at least 2 items (header + body).
        """
        from PySide6.QtWidgets import QWidget

        header = dlg.findChild(QWidget, "dlg_header")
        assert header is not None, (
            f"{type(dlg).__name__}: missing dlg_header widget (build_dialog_header)"
        )
        assert not header.isHidden(), f"{type(dlg).__name__}: dlg_header is hidden"

        body = dlg.findChild(QWidget, "dlg_body")
        assert body is not None, (
            f"{type(dlg).__name__}: missing dlg_body widget (dialog_body_style)"
        )
        assert not body.isHidden(), f"{type(dlg).__name__}: dlg_body is hidden"

        root_layout = dlg.layout()
        assert root_layout is not None, f"{type(dlg).__name__}: no root layout"
        assert root_layout.count() >= 2, (
            f"{type(dlg).__name__}: expected >= 2 items in root layout, got {root_layout.count()}"
        )

    @staticmethod
    def assert_expected_widgets(
        dlg: QDialog,
        widget_names: list[str],
    ) -> None:
        """Verify at least one instance of each expected widget type exists.

        Supported type names:
          ``"QLineEdit"``, ``"QComboBox"``, ``"QPushButton"``,
          ``"QTableWidget"``, ``"QDoubleSpinBox"``, ``"QCheckBox"``,
          ``"QTabWidget"``, ``"QGroupBox"``, ``"QLabel"``.

        ``"UpperLineEdit"`` resolves to ``QLineEdit`` (its parent class).
        """
        from PySide6.QtWidgets import (
            QCheckBox,
            QComboBox,
            QDoubleSpinBox,
            QGroupBox,
            QLabel,
            QLineEdit,
            QPushButton,
            QTableWidget,
            QTabWidget,
        )

        type_map: dict[str, type] = {
            "QLineEdit": QLineEdit,
            "QComboBox": QComboBox,
            "QPushButton": QPushButton,
            "QTableWidget": QTableWidget,
            "QDoubleSpinBox": QDoubleSpinBox,
            "QCheckBox": QCheckBox,
            "QTabWidget": QTabWidget,
            "QGroupBox": QGroupBox,
            "QLabel": QLabel,
            "UpperLineEdit": QLineEdit,  # subclass of QLineEdit
        }

        for name in widget_names:
            qt_type = type_map.get(name)
            if qt_type is None:
                # Fallback: try to get from PySide6.QtWidgets
                import importlib

                qt_type = getattr(importlib.import_module("PySide6.QtWidgets"), name, None)
                assert qt_type is not None, f"Unknown widget type: {name}"
            count = len(dlg.findChildren(qt_type))
            assert count > 0, f"{type(dlg).__name__}: expected at least one {name} widget, found 0"

    # ── Assertion helpers ───────────────────────────────────────────────────

    @staticmethod
    def assert_overlay_exists(dlg: LoaderTestDialog) -> None:
        """Verify the LoadingOverlay was created."""
        assert dlg._loading_overlay is not None, (
            f"{type(dlg).__name__} should have created a LoadingOverlay"
        )

    @staticmethod
    def assert_callback_executed(dlg: LoaderTestDialog) -> None:
        """Verify the deferred callback ran successfully.

        Only works with LoaderTestDialog subclasses that set callback_executed.
        """
        assert dlg.callback_executed, f"Deferred callback of {type(dlg).__name__} did not execute"

    @staticmethod
    def assert_overlay_hidden(dlg: LoaderTestDialog) -> None:
        """Verify overlay was hidden in finally block after callback.

        Only works with LoaderTestDialog subclasses that set overlay_hidden.
        """
        assert dlg.overlay_hidden, (
            f"Overlay of {type(dlg).__name__} was not hidden in finally block"
        )

    # ── Complete test scenarios ─────────────────────────────────────────────

    def _cleanup(self, dlg: QDialog) -> None:
        """Close dialog, catching any RuntimeError from destroyed C++ objects."""
        try:
            dlg.close()
        except RuntimeError:
            pass

    def run_normal_execution(
        self,
        dialog_cls: type[TLoader],
        **kwargs: Any,
    ) -> TLoader:
        """Full cycle: create dialog → fire timer → assert callback.

        Returns the dialog instance for additional assertions.

        Only works with LoaderTestDialog subclasses (need callback_executed,
        overlay_hidden, and _loading_overlay attributes).
        """
        dlg = dialog_cls(**kwargs)
        try:
            self.assert_overlay_exists(dlg)
            assert not dlg.callback_executed, "Callback should NOT have run yet (timer not fired)"

            self.process_events()

            self.assert_callback_executed(dlg)
            self.assert_overlay_hidden(dlg)
            return dlg
        finally:
            self._cleanup(dlg)

    def run_stale_timer(
        self,
        dialog_cls: type[TLoader],
        **kwargs: Any,
    ) -> None:
        """Destroy dialog before timer fires → guard prevents crash.

        This simulates what happens in test suites: a dialog is created
        (scheduling a QTimer), the dialog is destroyed, then processEvents()
        fires the stale timer on the destroyed C++ object.

        The RuntimeError guard at the top of the deferred callback should
        catch this silently — no crash should occur.
        """
        dlg = dialog_cls(**kwargs)
        self.destroy_dialog(dlg)

        # The guard at the top of _deferred_init() catches RuntimeError
        # from accessing self.<GUARD_WIDGET> on the destroyed C++ object.
        self.process_events()  # Should NOT crash

    def run_stale_timer_multiple(
        self,
        dialog_cls: type[TLoader],
        count: int = 5,
        **kwargs: Any,
    ) -> None:
        """Create *count* dialogs, destroy all, verify none crash."""
        dialogs = [dialog_cls(**kwargs) for _ in range(count)]
        for d in dialogs:
            self.destroy_dialog(d)
        self.process_events()  # Should not crash

    def run_normal_execution_with_structure(
        self,
        dialog_cls: type[TLoader],
        expected_widgets: list[str] | None = None,
        **kwargs: Any,
    ) -> TLoader:
        """Full cycle + structural verification: create → check structure →
        fire timer → assert callback + overlay hidden.

        Combines ``run_normal_execution`` with:
        - ``check_dialog_structure(dlg)`` — verifies header + body widgets
        - ``assert_expected_widgets(dlg, expected_widgets)`` — verifies
          expected Qt widget types exist

        Args:
            dialog_cls: A ``LoaderTestDialog`` subclass.
            expected_widgets: Optional list of widget type names to verify
                (e.g. ``["QLineEdit", "QComboBox"]``).
            **kwargs: Passed to ``dialog_cls()``.

        Returns the dialog instance for additional assertions.

        Usage::

            dlg = self.run_normal_execution_with_structure(
                MiDialogo, ["QLineEdit", "QComboBox", "QPushButton"],
                parent=None,
            )
            assert dlg.some_widget.property_x > 0
        """
        dlg = dialog_cls(**kwargs)
        try:
            self.check_dialog_structure(dlg)
            self.assert_overlay_exists(dlg)

            if expected_widgets is not None:
                self.assert_expected_widgets(dlg, expected_widgets)

            assert not dlg.callback_executed, (
                f"{type(dlg).__name__}: callback should NOT have run yet"
            )

            self.process_events()

            self.assert_callback_executed(dlg)
            self.assert_overlay_hidden(dlg)
            return dlg
        finally:
            self._cleanup(dlg)

    def run_callback_exception(
        self,
        dialog_cls: type[TLoader],
        exception: BaseException,
        **kwargs: Any,
    ) -> TLoader:
        """Callback raises exception → overlay still hidden, no crash.

        Args:
            dialog_cls: Must accept ``callback_ex=exception`` as kwarg.
            exception: Exception instance to raise inside callback.

        Returns the dialog instance for assertion verification.
        """
        dlg = dialog_cls(callback_ex=exception, **kwargs)
        try:
            # Some PySide6 versions propagate exceptions through processEvents(),
            # others handle them internally via sys.excepthook. Handle both.
            try:
                self.process_events()
            except type(exception):
                pass  # Exception propagated — still valid

            # Callback should have failed before setting callback_executed
            assert not dlg.callback_executed, "Callback should have failed due to exception"
            # Overlay should still be hidden by the finally block
            self.assert_overlay_hidden(dlg)
            return dlg
        finally:
            self._cleanup(dlg)


# ═══════════════════════════════════════════════════════════════════════════════
# BaseWidgetTestMixin — Mixin for testing BaseWidget subclasses
# ═══════════════════════════════════════════════════════════════════════════════


class BaseWidgetTestMixin:
    """Mixin providing helper methods for BaseWidget test scenarios.

    Tests the full BaseWidget lifecycle:
      - Banner presence (fixedHeight=64 + gradient style)
      - Deferred load (``_deferred_call`` / ``_deferred_load`` / ``cargar_datos``)
      - Stale widget (destroy before timer fires, no crash)
      - Overlay show/hide in ``finally`` blocks

    Mix this into your pytest test class:

        class TestMisWidgets(BaseWidgetTestMixin):
            def test_banner(self) -> None:
                w = MiWidget()
                self.assert_has_banner(w)
                self.assert_banner_title(w, "Mi Widget")

            def test_deferred_load(self) -> None:
                w = self.run_deferred_load(MiWidgetTestHelper)
                assert w.callback_executed

            def test_stale_widget(self) -> None:
                self.run_stale_widget(MiWidgetTestHelper)

    Available helpers:
      - assert_has_banner(widget)
      - assert_banner_title(widget, expected)
      - get_banner_title(widget)
      - run_deferred_load(cls, **kwargs) — Full deferred load cycle
      - run_stale_widget(cls, **kwargs) — Stale timer, no crash
      - run_stale_widget_multiple(cls, count=5, **kwargs) — Bulk stale
      - run_deferred_call_direct(cls, exception=None) — Test _deferred_call
    """

    # ── Banner detection helpers ────────────────────────────────────────────

    @staticmethod
    def _find_banner(widget: QWidget) -> QWidget | None:
        """Find a banner QWidget child with fixedHeight=64.

        Detects banners by either:
          - ``class="banner"`` QSS property (new QSS-based styling), or
          - Inline stylesheet containing ``qlineargradient`` (legacy).

        Returns the banner widget or None.
        """
        for child in widget.findChildren(QWidget):
            if child.minimumHeight() == 64 and child.maximumHeight() == 64:
                # QSS class-based banner (post-migration)
                if child.property("class") == "banner":
                    return child
                # Legacy inline gradient fallback
                ss = child.styleSheet()
                if "qlineargradient" in ss.lower():
                    return child
        return None

    @staticmethod
    def get_banner_title(widget: QWidget) -> str:
        """Extract the title text from the banner.

        Returns the banner's title string, or empty string if not found.
        """
        banner = BaseWidgetTestMixin._find_banner(widget)
        if banner is None:
            return ""
        from PySide6.QtWidgets import QLabel

        labels = banner.findChildren(QLabel)
        for lbl in labels:
            txt = lbl.text()
            if txt and len(txt) > 3:
                return txt.strip()
        return ""

    @staticmethod
    def check_base_widget(widget: QWidget) -> None:
        """Verify a widget has the minimum BaseWidget interface.

        Checks:
          1. Widget is not None
          2. Widget is a QWidget
          3. Widget has a layout
          4. Widget has required BaseWidget methods: ``_init_loading_overlay``,
             ``_deferred_call``, ``mostrar_error``, ``ejecutar_seguro``

        This is the canonical way to verify a widget inherits from BaseWidget.
        """
        assert widget is not None, "Widget should not be None"
        assert isinstance(widget, QWidget), f"Expected QWidget, got {type(widget).__name__}"
        assert widget.layout() is not None, f"{type(widget).__name__}: widget has no layout"
        for attr in ("_init_loading_overlay", "_deferred_call", "mostrar_error", "ejecutar_seguro"):
            assert hasattr(widget, attr), (
                f"{type(widget).__name__}: missing required BaseWidget method '{attr}'"
            )

    @staticmethod
    def assert_has_banner(widget: QWidget) -> None:
        """Assert the widget has a banner (fixedHeight=64 + gradient style).

        Fails with a clear message showing the widget class name.
        """
        assert BaseWidgetTestMixin._find_banner(widget) is not None, (
            f"{type(widget).__name__}: no banner detected. "
            "Expected a QWidget child with fixedHeight=64 and gradient style. "
            "Banner should be created with create_banner() in __init__."
        )

    @staticmethod
    def assert_banner_title(widget: QWidget, expected: str) -> None:
        """Assert the banner's title matches the expected text."""
        title = BaseWidgetTestMixin.get_banner_title(widget)
        assert title == expected, (
            f"{type(widget).__name__}: banner title mismatch.\n"
            f"  Expected: {expected!r}\n"
            f"  Got:      {title!r}"
        )

    # ── Lifecycle helpers ───────────────────────────────────────────────────

    @staticmethod
    def process_events() -> None:
        """Process pending Qt events to fire deferred QTimer callbacks."""
        QApplication.processEvents()

    @staticmethod
    def destroy_widget(w: QWidget) -> None:
        """Close and schedule C++ deletion of a widget."""
        w.close()
        w.deleteLater()

    @staticmethod
    def _cleanup_widget(w: QWidget) -> None:
        """Close widget, catching any RuntimeError from destroyed C++ objects."""
        try:
            w.close()
        except RuntimeError:
            pass

    # ── Assertion helpers ───────────────────────────────────────────────────

    @staticmethod
    def assert_overlay_init(w: BaseWidgetTestHelper) -> None:
        """Verify the LoadingOverlay was initialized."""
        assert w._loading_overlay is not None, (
            f"{type(w).__name__}: _loading_overlay should not be None. "
            "Did __init__ call _init_loading_overlay()?"
        )

    @staticmethod
    def assert_callback_completed(w: BaseWidgetTestHelper) -> None:
        """Verify cargar_datos() was executed."""
        assert w.callback_executed, (
            f"{type(w).__name__}: cargar_datos() did not execute. "
            "Check that deferred load timer fired correctly."
        )

    @staticmethod
    def assert_overlay_hidden_after(w: BaseWidgetTestHelper) -> None:
        """Verify overlay was hidden after _deferred_call."""
        assert w._loading_overlay is None or not w._loading_overlay.isVisible(), (
            f"{type(w).__name__}: overlay should be hidden after deferred call"
        )

    # ── Complete test scenarios ─────────────────────────────────────────────

    def run_deferred_load(
        self,
        helper_cls: type[TWidget],
        **kwargs: Any,
    ) -> TWidget:
        """Full deferred-load cycle: create helper → process timer → assert.

        Steps:
          1. Create the helper widget (which schedules a QTimer.singleShot)
          2. Verify overlay was initialized
          3. Verify callback has NOT run yet
          4. Process events (fires the timer → _deferred_load → _deferred_call
             → cargar_datos)
          5. Verify callback completed and overlay hidden

        Returns the widget for additional assertions.
        """
        w = helper_cls(**kwargs)
        try:
            self.assert_overlay_init(w)
            assert not w.callback_executed, f"{type(w).__name__}: callback should NOT have run yet"

            self.process_events()

            self.assert_callback_completed(w)
            return w
        finally:
            self._cleanup_widget(w)

    def run_stale_widget(
        self,
        helper_cls: type[TWidget],
        **kwargs: Any,
    ) -> None:
        """Destroy widget before timer fires → guard prevents crash.

        This simulates a test scenario where a widget is created (scheduling
        a QTimer), then immediately destroyed. When processEvents() fires the
        stale QTimer, the RuntimeError guard in _deferred_call (which checks
        ``isWidgetType()``) should catch the error silently.
        """
        w = helper_cls(**kwargs)
        self.destroy_widget(w)
        self.process_events()  # Should NOT crash

    def run_stale_widget_multiple(
        self,
        helper_cls: type[TWidget],
        count: int = 5,
        **kwargs: Any,
    ) -> None:
        """Create *count* widgets, destroy all, verify none crash."""
        widgets = [helper_cls(**kwargs) for _ in range(count)]
        for w in widgets:
            self.destroy_widget(w)
        self.process_events()  # Should not crash

    def run_deferred_call_direct(
        self,
        helper_cls: type[TWidget],
        exception: BaseException | None = None,
        **kwargs: Any,
    ) -> TWidget:
        """Test _deferred_call directly (bypass QTimer, call it manually).

        Useful for testing the RuntimeError suppression and overlay lifecycle
        without waiting for QTimer.

        **Important:** ``BaseWidgetTestHelper.__init__`` schedules a
        ``QTimer.singleShot(0, self._deferred_load)``. This method creates
        the helper with a private ``_no_auto_timer=True`` flag to suppress
        that timer, preventing stale timers from leaking into subsequent
        tests.

        Args:
            helper_cls: A ``BaseWidgetTestHelper`` subclass.
            exception: If set, ``cargar_datos()`` will raise this exception.
            **kwargs: Passed to ``helper_cls()``.

        Returns the widget for assertion verification.
        """
        w = helper_cls(callback_executed_ex=exception, _no_auto_timer=True, **kwargs)
        try:
            self.assert_overlay_init(w)

            if exception:
                # Should suppress RuntimeError and propagate others
                if isinstance(exception, RuntimeError):
                    w._deferred_call(w.cargar_datos)
                    assert not w.callback_executed, (
                        "Callback should NOT have completed due to RuntimeError"
                    )
                else:
                    import pytest

                    with pytest.raises(type(exception)):
                        w._deferred_call(w.cargar_datos)
            else:
                w._deferred_call(w.cargar_datos)
                assert w.callback_executed, "Callback should have completed"

            return w
        finally:
            self._cleanup_widget(w)
