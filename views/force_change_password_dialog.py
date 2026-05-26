"""
force_change_password_dialog.py — Diálogo de cambio de contraseña obligatorio.

Se muestra cuando un usuario inicia sesión con debe_cambiar_password=True.
El usuario debe cambiar su contraseña antes de acceder al sistema.
"""

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFrame,
    QProgressBar,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer

from views.base_dialog import BaseDialog

from services.auth_service import AuthService
from core.exceptions import DinamoBaseError, ValidacionError, CredencialesInvalidas
from core.logger import get_logger

from views.components import ModernMessageBox
from PySide6.QtWidgets import QGraphicsDropShadowEffect
from PySide6.QtGui import QColor

log = get_logger(__name__)

# ── Estilos ───────────────────────────────────────────────────────────────────
_LBL_REQUISITO_OK = (
    "QLabel { color: #16a34a; font-size: 10pt; font-weight: 500; padding: 2px 0px; }"
)
_LBL_REQUISITO_NOK = (
    "QLabel { color: #94a3b8; font-size: 10pt; font-weight: 400; padding: 2px 0px; }"
)


class ForceChangePasswordDialog(BaseDialog):
    """Diálogo modal que fuerza el cambio de contraseña obligatorio.

    Args:
        parent: Widget padre (normalmente None desde login).
        session: Dict con datos de sesión (username, nombre, rol, etc.)
    """

    _REQUISITOS = [
        ("longitud", "Al menos 8 caracteres"),
        ("mayuscula", "Una letra mayúscula"),
        ("minuscula", "Una letra minúscula"),
        ("numero", "Un número"),
        ("especial", "Un carácter especial (!@#$%^&*)"),
    ]

    _PASSWORD_MIN_LENGTH = 8

    def __init__(self, parent, session: dict):
        super().__init__(parent)
        self._session = session
        self._username = session.get("username", "")
        self._nombre = session.get("nombre", "")

        self.setWindowTitle("Cambio de Contraseña Requerido")
        self.setFixedSize(520, 620)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)

        self._build_ui()
        self._connect_signals()

        # Centrar en pantalla
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center() - self.rect().center())

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # Contenedor principal (card)
        outer = QFrame(self)
        outer.setObjectName("pwdCard")
        outer.setStyleSheet("""
            QFrame#pwdCard {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 20px;
            }
        """)
        _shadow = QGraphicsDropShadowEffect(outer)
        _shadow.setBlurRadius(30)
        _shadow.setColor(QColor(0, 0, 0, 30))
        _shadow.setOffset(0, 4)
        outer.setGraphicsEffect(_shadow)

        main_layout = QVBoxLayout(outer)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Encabezado gradiente ──────────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(100)
        header.setStyleSheet("""
            QFrame {
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1a3558, stop:1 #2563eb
                );
                border-top-left-radius: 20px;
                border-top-right-radius: 20px;
            }
        """)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(24, 0, 24, 0)
        h_lay.setSpacing(16)

        icono = QLabel("\U0001f512")  # 🔒
        icono.setFixedSize(48, 48)
        icono.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icono.setStyleSheet("""
            QLabel {
                background: rgba(255,255,255,0.18);
                border-radius: 24px;
                font-size: 22px;
            }
        """)
        h_lay.addWidget(icono)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(2)
        txt_col.addStretch()
        lbl_tit = QLabel("Cambio de Contraseña")
        lbl_tit.setStyleSheet(
            "QLabel { color: #ffffff; font-size: 16pt; font-weight: 700; background: transparent; }"
        )
        lbl_sub = QLabel("Por seguridad, debes cambiar tu contraseña para continuar")
        lbl_sub.setStyleSheet(
            "QLabel { color: rgba(255,255,255,0.78); font-size: 9pt; background: transparent; }"
        )
        lbl_sub.setWordWrap(True)
        txt_col.addWidget(lbl_tit)
        txt_col.addWidget(lbl_sub)
        txt_col.addStretch()
        h_lay.addLayout(txt_col)
        h_lay.addStretch()

        main_layout.addWidget(header)

        # ── Cuerpo ────────────────────────────────────────────────────────────
        body = QFrame()
        body.setStyleSheet("QFrame { background: transparent; }")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(28, 20, 28, 20)
        body_lay.setSpacing(12)

        # Info de usuario
        info_frame = QFrame()
        info_frame.setStyleSheet("""
            QFrame {
                background-color: #eff6ff;
                border: 1px solid #bfdbfe;
                border-radius: 10px;
                padding: 12px;
            }
        """)
        info_lay = QVBoxLayout(info_frame)
        info_lay.setContentsMargins(14, 10, 14, 10)
        info_lay.setSpacing(2)
        info_user = QLabel(f"Usuario: {self._username}")
        info_user.setStyleSheet(
            "QLabel { color: #1e40af; font-size: 11pt; font-weight: 600; background: transparent; }"
        )
        info_name = QLabel(self._nombre or "")
        if self._nombre:
            info_name.setStyleSheet(
                "QLabel { color: #3b82f6; font-size: 9pt; background: transparent; }"
            )
            info_lay.addWidget(info_name)
        info_lay.addWidget(info_user)
        body_lay.addWidget(info_frame)

        # ── Contraseña actual ─────────────────────────────────────────────────
        lbl_current = QLabel("Contraseña Actual:")
        lbl_current.setStyleSheet("QLabel { color: #334155; font-size: 10pt; font-weight: 600; }")
        body_lay.addWidget(lbl_current)

        self.txt_current = QLineEdit()
        self.txt_current.setPlaceholderText("Ingresa tu contraseña actual")
        self.txt_current.setEchoMode(QLineEdit.EchoMode.Password)
        body_lay.addWidget(self.txt_current)

        # ── Nueva contraseña ──────────────────────────────────────────────────
        lbl_new = QLabel("Nueva Contraseña:")
        lbl_new.setStyleSheet("QLabel { color: #334155; font-size: 10pt; font-weight: 600; }")
        body_lay.addWidget(lbl_new)

        self.txt_new = QLineEdit()
        self.txt_new.setPlaceholderText("Mínimo 8 caracteres")
        self.txt_new.setEchoMode(QLineEdit.EchoMode.Password)
        body_lay.addWidget(self.txt_new)

        # ── Indicador de fortaleza ────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        self.progress.setRange(0, len(self._REQUISITOS))
        self.progress.setValue(0)
        self.progress.setStyleSheet("""
            QProgressBar {
                background: #e2e8f0; border: none; border-radius: 3px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 #ef4444, stop:0.5 #f59e0b, stop:1 #22c55e);
                border-radius: 3px;
            }
        """)
        body_lay.addWidget(self.progress)

        # Checklist de requisitos
        self._req_labels = {}
        for key, texto in self._REQUISITOS:
            lbl = QLabel(f"  {texto}")
            lbl.setStyleSheet(_LBL_REQUISITO_NOK)
            body_lay.addWidget(lbl)
            self._req_labels[key] = lbl

        # ── Confirmar contraseña ──────────────────────────────────────────────
        lbl_confirm = QLabel("Confirmar Nueva Contraseña:")
        lbl_confirm.setStyleSheet("QLabel { color: #334155; font-size: 10pt; font-weight: 600; }")
        body_lay.addWidget(lbl_confirm)

        self.txt_confirm = QLineEdit()
        self.txt_confirm.setPlaceholderText("Repite la nueva contraseña")
        self.txt_confirm.setEchoMode(QLineEdit.EchoMode.Password)
        body_lay.addWidget(self.txt_confirm)

        # ── Error label ───────────────────────────────────────────────────────
        self.lbl_error = QLabel("")
        self.lbl_error.setWordWrap(True)
        self.lbl_error.setStyleSheet(
            "QLabel { color: #dc2626; font-size: 10pt; font-weight: 500; padding: 4px 0px; }"
        )
        self.lbl_error.setVisible(False)
        body_lay.addWidget(self.lbl_error)

        # ── Botones ───────────────────────────────────────────────────────────
        btn_lay = QHBoxLayout()
        btn_lay.setSpacing(12)
        btn_lay.addStretch()

        btn_cancel = QPushButton("  Cerrar Sesión")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)
        btn_lay.addWidget(btn_cancel)

        self.btn_save = QPushButton("  Cambiar y Entrar")
        self.btn_save.setObjectName("btnGuardar")
        self.btn_save.setProperty("class", "primary")
        self.btn_save.clicked.connect(self._guardar)
        btn_lay.addWidget(self.btn_save)

        body_lay.addSpacing(4)
        body_lay.addLayout(btn_lay)

        main_layout.addWidget(body, stretch=1)

        # Layout raíz
        root_lay = QVBoxLayout(self)
        root_lay.setContentsMargins(16, 16, 16, 16)
        root_lay.addWidget(outer)

    def _connect_signals(self):
        """Conecta señales para validación en tiempo real."""
        self.txt_new.textChanged.connect(self._actualizar_fortaleza)

    # ── Validación en tiempo real ────────────────────────────────────────────

    def _actualizar_fortaleza(self):
        """Actualiza la barra de progreso y checklist de requisitos."""
        pwd = self.txt_new.text()
        checks = {
            "longitud": len(pwd) >= self._PASSWORD_MIN_LENGTH,
            "mayuscula": any(c.isupper() for c in pwd),
            "minuscula": any(c.islower() for c in pwd),
            "numero": any(c.isdigit() for c in pwd),
            "especial": any(c in '!@#$%^&*(),.?":{}|<>' for c in pwd),
        }

        cumplidos = sum(1 for v in checks.values() if v)
        self.progress.setValue(cumplidos)

        for key, lbl in self._req_labels.items():
            ok = checks.get(key, False)
            prefijo = "\u2713" if ok else "\u2717"
            lbl.setText(f"  {prefijo}  {dict(self._REQUISITOS)[key]}")
            lbl.setStyleSheet(_LBL_REQUISITO_OK if ok else _LBL_REQUISITO_NOK)

    # ── Acción ───────────────────────────────────────────────────────────────

    def _guardar(self):
        """Valida y ejecuta el cambio de contraseña."""
        current = self.txt_current.text()
        new_pwd = self.txt_new.text()
        confirm = self.txt_confirm.text()

        # Validaciones previas
        if not current:
            self._mostrar_error("Ingresa tu contraseña actual.")
            self.txt_current.setFocus()
            return
        if not new_pwd:
            self._mostrar_error("Ingresa una nueva contraseña.")
            self.txt_new.setFocus()
            return
        if len(new_pwd) < self._PASSWORD_MIN_LENGTH:
            self._mostrar_error(
                f"La contraseña debe tener al menos {self._PASSWORD_MIN_LENGTH} caracteres."
            )
            self.txt_new.setFocus()
            return
        if new_pwd != confirm:
            self._mostrar_error("Las contraseñas nuevas no coinciden.")
            self.txt_confirm.setFocus()
            return

        self._set_loading(True)

        try:
            AuthService.cambiar_password_obligatorio(
                username=self._username,
                current_password=current,
                new_password=new_pwd,
            )
            log.info("Contraseña cambiada exitosamente por: %s", self._username)
            ModernMessageBox.success(
                self,
                "Contraseña Actualizada",
                "Tu contraseña ha sido cambiada exitosamente.\nAhora puedes acceder al sistema.",
            )
            self.accept()
        except CredencialesInvalidas as e:
            self._mostrar_error(e.mensaje_usuario)
            self.txt_current.setFocus()
            self.txt_current.selectAll()
        except ValidacionError as e:
            self._mostrar_error(e.mensaje_usuario)
            self.txt_new.setFocus()
            self.txt_new.selectAll()
        except DinamoBaseError as e:
            self._mostrar_error(e.mensaje_usuario)
        except Exception as e:
            log.error("Error inesperado en cambio de contraseña: %s", e, exc_info=True)
            self._mostrar_error(f"Error inesperado: {e}")
        finally:
            self._set_loading(False)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _mostrar_error(self, mensaje: str):
        """Muestra mensaje de error en el label y lo oculta tras 8s."""
        self.lbl_error.setText(mensaje)
        self.lbl_error.setVisible(True)
        QTimer.singleShot(8000, lambda: self.lbl_error.setVisible(False))

    def _set_loading(self, loading: bool):
        """Deshabilita/habilita controles durante la operación."""
        self.txt_current.setEnabled(not loading)
        self.txt_new.setEnabled(not loading)
        self.txt_confirm.setEnabled(not loading)
        self.btn_save.setEnabled(not loading)
        self.btn_save.setText("  Cambiando..." if loading else "  Cambiar y Entrar")
        QApplication.processEvents()
