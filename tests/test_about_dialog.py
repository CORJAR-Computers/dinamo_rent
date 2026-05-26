"""test_about_dialog.py — Unit tests for AboutDialog.

Run: pytest tests/test_about_dialog.py -v
"""

from unittest.mock import patch

import pytest
from PySide6.QtWidgets import QApplication, QDialog, QLabel, QPushButton


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Tests — AboutDialog
# ═══════════════════════════════════════════════════════════════════════════════


class TestAboutDialog:
    """AboutDialog instantiation, content, and interaction."""

    # ── Instantiation ──────────────────────────────────────────────────────

    def test_instancia(self, qapp):
        """Dialog instantiates without errors and is a QDialog."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            assert isinstance(dlg, QDialog)
            assert dlg.windowTitle(), "Dialog should have a window title"
        finally:
            dlg.close()

    def test_hereda_qdialog(self, qapp):
        """AboutDialog inherits from QDialog."""
        from views.about_dialog import AboutDialog

        assert issubclass(AboutDialog, QDialog)

    # ── Window title ───────────────────────────────────────────────────────

    def test_window_title_contiene_app_name(self, qapp):
        """Window title contains the application name."""
        from core.config import APP_NAME
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            assert APP_NAME in dlg.windowTitle()
            assert "Acerca de" in dlg.windowTitle()
        finally:
            dlg.close()

    # ── Content checks ─────────────────────────────────────────────────────

    def test_muestra_version(self, qapp):
        """Dialog displays the app version."""
        from core.config import APP_VERSION
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            version_str = f"v{APP_VERSION}"
            assert any(version_str in t for t in texts), (
                f"Expected version '{version_str}' in dialog labels, found: {texts}"
            )
        finally:
            dlg.close()

    def test_muestra_modo(self, qapp):
        """Dialog shows 'Desarrollo' or 'Produccion' matching PRODUCTION_MODE."""
        from core.config import PRODUCTION_MODE
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            expected = "Produccion" if PRODUCTION_MODE else "Desarrollo"
            assert any(expected in t for t in texts), (
                f"Expected mode '{expected}' in dialog labels, found: {texts}"
            )
        finally:
            dlg.close()

    def test_muestra_autor(self, qapp):
        """Dialog displays the app author."""
        from core.config import APP_AUTHOR
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            assert any(APP_AUTHOR in t for t in texts), (
                f"Expected author '{APP_AUTHOR}' in dialog labels, found: {texts}"
            )
        finally:
            dlg.close()

    def test_muestra_copyright(self, qapp):
        """Dialog shows copyright notice."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            assert any("2024" in t and "Dinamo" in t for t in texts), (
                f"Expected copyright with '2024 Dinamo' in dialog labels, found: {texts}"
            )
        finally:
            dlg.close()

    def test_muestra_build_info(self, qapp):
        """Dialog shows build/tech info."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            labels = dlg.findChildren(QLabel)
            texts = [lbl.text() for lbl in labels]
            assert any("Python" in t for t in texts), (
                f"Expected build info with 'Python' in dialog labels, found: {texts}"
            )
        finally:
            dlg.close()

    # ── DB info ────────────────────────────────────────────────────────────

    def test_get_db_info(self, qapp):
        """_get_db_info returns a non-empty connection string."""
        from views.about_dialog import _get_db_info

        info = _get_db_info()
        assert info, "DB info should not be empty"
        from core.config import DB_ENGINE

        if DB_ENGINE in ("sqlite", "sqlite3"):
            assert "SQLite" in info, (
                f"Expected 'SQLite' in DB info for engine={DB_ENGINE}, got: {info}"
            )
        else:
            assert "MySQL" in info or "SQLite" in info, (
                f"Expected 'MySQL' or 'SQLite' in DB info, got: {info}"
            )

    # ── Logo handling ──────────────────────────────────────────────────────

    def test_cargar_logo_con_archivo(self, qapp):
        """_cargar_logo sets a pixmap when a logo file exists."""
        from views.about_dialog import AboutDialog, ASSETS_DIR

        # Only test if at least one logo file exists
        candidates = [
            ASSETS_DIR / "LogoDinamo.png",
            ASSETS_DIR / "Logo_Dinamo.png",
        ]
        existing = [c for c in candidates if c.exists()]
        if not existing:
            pytest.skip("No logo file found in assets directory")

        lbl = QLabel()
        AboutDialog._cargar_logo(lbl)
        # When a file exists, a pixmap should be set (not emoji text)
        assert lbl.pixmap() is not None, "Expected a pixmap when logo file exists"
        assert not lbl.text(), "Expected no text when pixmap is set"

    @patch("os.path.exists", return_value=False)
    def test_cargar_logo_fallback(self, mock_exists, qapp):
        """_cargar_logo shows emoji fallback when no logo file exists."""
        from views.about_dialog import AboutDialog

        lbl = QLabel()
        AboutDialog._cargar_logo(lbl)
        assert "🚗" in lbl.text(), "Expected emoji fallback when no logo file exists"

    # ── Accept button ──────────────────────────────────────────────────────

    def test_boton_aceptar_cierra_con_accepted(self, qapp):
        """Clicking the Accept button closes the dialog with Accepted."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            buttons = dlg.findChildren(QPushButton)
            accept_btn = None
            for btn in buttons:
                if "Aceptar" in btn.text():
                    accept_btn = btn
                    break
            assert accept_btn is not None, "Accept button not found"
            assert accept_btn.isEnabled(), "Accept button should be enabled"

            accept_btn.click()
            assert dlg.result() == QDialog.DialogCode.Accepted or dlg.result() == QDialog.Accepted
        finally:
            dlg.close()

    # ── Centering ──────────────────────────────────────────────────────────

    def test_centrar_sin_parent_no_crash(self, qapp):
        """_centrar is not called when parent is None (no crash)."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog()
        try:
            assert isinstance(dlg, QDialog)
        finally:
            dlg.close()
