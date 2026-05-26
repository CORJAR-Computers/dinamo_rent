"""
test_force_change_password_dialog.py — Unit tests for ForceChangePasswordDialog

Requires conftest.py to set up the in-memory SQLite database and a QApplication.
Run: pytest tests/test_force_change_password_dialog.py -v

NOTE: We use `not widget.isHidden()` instead of `widget.isVisible()` because
widgets that haven't been shown yet (e.g., dialog never exec()ed) have
isVisible() = False even if setVisible(True) was called. isHidden() checks
the widget's own visibility flag regardless of parent visibility.
"""

import pytest
from unittest.mock import patch

# ── QApplication fixture ──────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def qapp():
    """Create a QApplication instance for Qt widget testing."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


# ═══════════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestForceChangePasswordDialog:
    _SESSION = {
        "username": "testuser",
        "nombre": "Test User",
        "rol": "Operador",
        "session_id": "fake-sid-123",
    }

    # ── Creación ──────────────────────────────────────────────────────────

    def test_crear_dialogo(self, qapp):
        """Dialog can be instantiated with a valid session dict."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        assert dlg._username == "testuser"
        assert dlg._nombre == "Test User"
        assert dlg.windowTitle() == "Cambio de Contraseña Requerido"
        dlg.close()

    def test_crear_dialogo_sin_nombre(self, qapp):
        """Dialog handles session without 'nombre' gracefully."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        session = {"username": "nouser", "rol": "Operador", "session_id": "x"}
        dlg = ForceChangePasswordDialog(None, session)
        assert dlg._username == "nouser"
        assert dlg._nombre == ""
        dlg.close()

    def test_crear_dialogo_session_vacia(self, qapp):
        """Dialog handles empty session dict without crashing."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, {})
        assert dlg._username == ""
        assert dlg._nombre == ""
        dlg.close()

    # ── _actualizar_fortaleza ─────────────────────────────────────────────

    def test_fortaleza_vacia(self, qapp):
        """Strength meter shows 0/5 for empty password."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        # Set non-empty first to ensure textChanged signal fires on clear
        dlg.txt_new.setText("x")
        dlg.txt_new.setText("")
        dlg._actualizar_fortaleza()  # ensure synchronous
        assert dlg.progress.value() == 0

        # Todos los requisitos deben mostrar ✗
        for key in [k for k, _ in dlg._REQUISITOS]:
            lbl = dlg._req_labels[key]
            assert "\u2717" in lbl.text()
        dlg.close()

    def test_fortaleza_solo_longitud_y_minuscula(self, qapp):
        """Strength meter shows 2/5 for a long lowercase password (longitud + minúscula)."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_new.setText("aaaaaaaa")  # 8 chars, all lowercase
        dlg._actualizar_fortaleza()
        # 2 checks pass: longitud (8) + minúscula (all lowercase)
        assert dlg.progress.value() == 2
        dlg.close()

    def test_fortaleza_tres_criterios(self, qapp):
        """Strength meter shows 3/5 for length + lowercase + number."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_new.setText("abc12345")  # length, lowercase, number
        dlg._actualizar_fortaleza()
        assert dlg.progress.value() == 3
        dlg.close()

    def test_fortaleza_todos_los_criterios(self, qapp):
        """Strength meter shows 5/5 for a fully compliant password."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_new.setText("Strong1@#")
        dlg._actualizar_fortaleza()
        assert dlg.progress.value() == 5

        # Todos los requisitos deben mostrar ✓
        for key in [k for k, _ in dlg._REQUISITOS]:
            lbl = dlg._req_labels[key]
            assert "\u2713" in lbl.text()
        dlg.close()

    # ── _guardar validaciones (cliente-side) ──────────────────────────────

    def test_guardar_sin_actual(self, qapp):
        """_guardar() rejects empty current password field."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("")
        dlg.txt_new.setText("Strong1@#")
        dlg.txt_confirm.setText("Strong1@#")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "actual" in dlg.lbl_error.text().lower()
        dlg.close()

    def test_guardar_sin_nueva(self, qapp):
        """_guardar() rejects empty new password field."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("")
        dlg.txt_confirm.setText("")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "nueva" in dlg.lbl_error.text().lower()
        dlg.close()

    def test_guardar_nueva_corta(self, qapp):
        """_guardar() rejects short new password."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("Ab1!")
        dlg.txt_confirm.setText("Ab1!")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "8 caracteres" in dlg.lbl_error.text().lower()
        dlg.close()

    def test_guardar_no_coinciden(self, qapp):
        """_guardar() rejects non-matching confirmation."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("Strong1@#")
        dlg.txt_confirm.setText("Different1@#")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "coinciden" in dlg.lbl_error.text().lower()
        dlg.close()

    # ── _guardar con AuthService mockeado ─────────────────────────────────

    @patch("views.force_change_password_dialog.AuthService.cambiar_password_obligatorio")
    @patch("views.force_change_password_dialog.ModernMessageBox.success")
    def test_guardar_exitoso(self, mock_success, mock_cambiar, qapp):
        """_guardar() calls AuthService and accepts dialog on success."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("Strong1@#")
        dlg.txt_confirm.setText("Strong1@#")

        dlg._guardar()

        # AuthService debe haber sido llamado con los argumentos correctos
        mock_cambiar.assert_called_once_with(
            username="testuser",
            current_password="OldPass123!",
            new_password="Strong1@#",
        )
        mock_success.assert_called_once()
        assert dlg.result() == dlg.DialogCode.Accepted
        dlg.close()

    @patch("views.force_change_password_dialog.AuthService.cambiar_password_obligatorio")
    def test_guardar_credenciales_invalidas(self, mock_cambiar, qapp):
        """_guardar() shows error when AuthService raises CredencialesInvalidas."""
        from core.exceptions import CredencialesInvalidas
        from views.force_change_password_dialog import ForceChangePasswordDialog

        mock_cambiar.side_effect = CredencialesInvalidas(
            mensaje_usuario="La contraseña actual no es correcta."
        )

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("WrongOld!")
        dlg.txt_new.setText("Strong1@#")
        dlg.txt_confirm.setText("Strong1@#")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "no es correcta" in dlg.lbl_error.text()
        dlg.close()

    @patch("views.force_change_password_dialog.AuthService.cambiar_password_obligatorio")
    def test_guardar_validacion_error(self, mock_cambiar, qapp):
        """_guardar() shows error when AuthService raises ValidacionError.
        Password must be >= 8 chars to pass client-side validation first."""
        from core.exceptions import ValidacionError
        from views.force_change_password_dialog import ForceChangePasswordDialog

        mock_cambiar.side_effect = ValidacionError(
            mensaje_usuario="La contraseña no cumple los requisitos."
        )

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("weakpass12")  # >= 8 chars, passes client-side
        dlg.txt_confirm.setText("weakpass12")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "requisitos" in dlg.lbl_error.text()
        dlg.close()

    @patch("views.force_change_password_dialog.AuthService.cambiar_password_obligatorio")
    def test_guardar_error_inesperado(self, mock_cambiar, qapp):
        """_guardar() handles unexpected exceptions gracefully."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        mock_cambiar.side_effect = RuntimeError("Unexpected DB error")

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.txt_current.setText("OldPass123!")
        dlg.txt_new.setText("Strong1@#")
        dlg.txt_confirm.setText("Strong1@#")

        dlg._guardar()

        assert not dlg.lbl_error.isHidden()
        assert "inesperado" in dlg.lbl_error.text().lower()
        dlg.close()

    # ── _set_loading ──────────────────────────────────────────────────────

    def test_set_loading_deshabilita_controles(self, qapp):
        """_set_loading(True) disables all form controls."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg._set_loading(True)

        assert not dlg.txt_current.isEnabled()
        assert not dlg.txt_new.isEnabled()
        assert not dlg.txt_confirm.isEnabled()
        assert not dlg.btn_save.isEnabled()
        assert "cambiando" in dlg.btn_save.text().lower()
        dlg.close()

    def test_set_loading_restaura_controles(self, qapp):
        """_set_loading(False) re-enables all form controls."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg._set_loading(True)
        dlg._set_loading(False)

        assert dlg.txt_current.isEnabled()
        assert dlg.txt_new.isEnabled()
        assert dlg.txt_confirm.isEnabled()
        assert dlg.btn_save.isEnabled()
        assert "cambiar y entrar" in dlg.btn_save.text().lower()
        dlg.close()

    # ── Botón Cerrar Sesión ───────────────────────────────────────────────

    def test_boton_cerrar_sesion(self, qapp):
        """The 'Cerrar Sesión' button is connected to reject()."""
        from views.force_change_password_dialog import ForceChangePasswordDialog

        dlg = ForceChangePasswordDialog(None, self._SESSION)
        dlg.reject()
        assert dlg.result() == dlg.DialogCode.Rejected
        dlg.close()
