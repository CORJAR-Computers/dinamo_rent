"""
main_qt.py — Punto de entrada de Dinamo Rent ERP
"""

import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

os.environ["G_MESSAGES_DEBUG"] = "none"

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QFrame,
    QStackedWidget,
    QDialog,
    QProgressBar,
    QGraphicsDropShadowEffect,
    QToolButton,
    QScrollArea,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QPixmap, QColor

# ── Core ─────────────────────────────────────────────────────────────────────
from core.config import (
    APP_NAME,
    APP_VERSION,
    COLOR_PRIMARIO,
    FONT_FAMILY,
    FONT_SIZE,
    BACKUP_HOURS,
    BACKUP_INTERVAL_MS,
    ROLES_CON_INFORMES,
    ROLES_CON_USUARIOS,
    ASSETS_DIR,
    PRODUCTION_MODE,
)
from core.exceptions import DinamoBaseError
from core.logger import get_logger
from core.database_sa import init_db
from core.security import SecurityManager
from services.auth_service import AuthService

log = get_logger(__name__)

_active_main_window = None
_active_login_window = None

# ── Cache paralogo (evita búsquedas repetidas) ───────────────────────────────
_LOGO_CACHE = None


@lru_cache(maxsize=1)
def _buscar_logo_cached():
    """Busca el logo una sola vez y cachea el resultado."""
    for nombre in ("Logo_Dinamo.png", "LogoDinamo.png", "logo.png"):
        p = str(ASSETS_DIR / nombre)
        if os.path.exists(p):
            return p
    return ""


def _obtener_logo_ruta():
    """Obtiene la ruta del logo usando cache."""
    global _LOGO_CACHE
    if _LOGO_CACHE is None:
        _LOGO_CACHE = _buscar_logo_cached()
    return _LOGO_CACHE


# ── Thread pool para operaciones pesadas ────────────────────────────────
_backup_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="BackupWorker")


# ── Inicialización de la base de datos con SQLAlchemy ─────────────────────────
def inicializar_base_datos(force_dialog=False):
    """Inicializa la base de datos con SQLAlchemy y crea admin si no existe.

    Args:
        force_dialog: Si True, muestra el diálogo de setup aunque no sea producción.
    """
    from core.config import SETUP_COMPLETED

    if (not SETUP_COMPLETED and PRODUCTION_MODE) or force_dialog:
        log.info("Primera ejecución o force_dialog - mostrando asistente de configuración")
        return "SETUP_NEEDED"

    log.info("Inicializando base de datos con SQLAlchemy...")
    try:
        init_db()
    except Exception as e:
        log.error(f"Error conectando a la base de datos: {e}")
        if PRODUCTION_MODE:
            return "SETUP_NEEDED"
        else:
            raise e

    from core.models import Usuario
    from core.database_sa import get_session

    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == "admin").first()

        dev_password = "Admin123!"

        if not PRODUCTION_MODE:
            if not admin:
                admin = Usuario(
                    username="admin",
                    password=SecurityManager.hash_password(dev_password),
                    nombre="Administrador Principal",
                    rol="Administrador",
                    activo=1,
                    debe_cambiar_password=0,
                )
                session.add(admin)
                log.info("Usuario admin creado con contraseña de desarrollo: Admin123!")
            else:
                admin.password = SecurityManager.hash_password(dev_password)
                admin.activo = 1
                admin.debe_cambiar_password = 0
                log.info(
                    "Usuario admin verificado. Contraseña restablecida a la contraseña de desarrollo: Admin123!"
                )
            return

        if admin:
            return

        import secrets

        new_password = secrets.token_urlsafe(12)
        admin = Usuario(
            username="admin",
            password=SecurityManager.hash_password(new_password),
            nombre="Administrador Principal",
            rol="Administrador",
            activo=1,
            debe_cambiar_password=1,
        )
        session.add(admin)
        log.info("Usuario admin creado con contraseña aleatoria de producción")
        log.warning(
            "Contraseña temporal generada: %s (no almacenar, cambiarla en primer inicio)",
            new_password,
        )


# ── Vistas (importación diferida para acelerar arranque) ──────────────────────
def _cargar_vistas():
    from views.dashboard_view import DashboardWidget
    from views.calendario_view import CalendarioWidget
    from views.rentas_view import RentasWidget
    from views.reservas_view import ReservasWidget
    from views.clientes_view import ClientesWidget
    from views.autos_view import AutosWidget
    from views.mantenimiento_view import MantenimientoWidget
    from views.usuarios_view import UsuariosWidget
    from views.informes_view import InformesWidget
    from views.comparendos_view import ComparendosWidget
    from views.alertas_view import AlertasWidget
    from views.gastos_view import GastosWidget

    return (
        DashboardWidget,
        CalendarioWidget,
        RentasWidget,
        ReservasWidget,
        ClientesWidget,
        AutosWidget,
        MantenimientoWidget,
        UsuariosWidget,
        InformesWidget,
        ComparendosWidget,
        AlertasWidget,
        GastosWidget,
    )


# =============================================================================
# 1. SPLASH SCREEN
# =============================================================================
class SplashScreen(QWidget):
    """Pantalla de inicio con barra de progreso en tiempo real.

    Soporta dos modos:
    - **Externo** (predeterminado): ``set_progress(value, message)`` es llamado
      desde ``__main__`` para reflejar el progreso real de arranque.
    - **Animación**: si nunca se llama a ``set_progress``, la barra se llena
      sola en ~2.5 segundos como fallback.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 600)
        self._centrar()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        self.card = QFrame()
        self.card.setProperty("class", "login-card")
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(20)
        sombra.setColor(QColor(0, 0, 0, 60))
        self.card.setGraphicsEffect(sombra)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(40, 60, 40, 60)

        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = _obtener_logo_ruta()
        if logo_path:
            pix = QPixmap(logo_path).scaled(
                180,
                180,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl_logo.setPixmap(pix)
        else:
            lbl_logo.setText("🚗")
            lbl_logo.setStyleSheet("font-size:80px;")

        lbl_tit = QLabel(APP_NAME)
        lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_tit.setStyleSheet(
            f"font-size:28px;font-weight:900;color:{COLOR_PRIMARIO};margin-top:20px;"
        )
        lbl_sub = QLabel(f"Sistema de Gestión de Flota v{APP_VERSION}")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size:14px;color:#757575;margin-bottom:40px;")

        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.lbl_estado = QLabel("Iniciando sistema…")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size:12px;color:#9e9e9e;margin-top:10px;")

        # ── Indicador de versión / compilación (esquina inferior) ──
        self.lbl_version = QLabel(f"v{APP_VERSION}")
        self.lbl_version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_version.setStyleSheet("font-size:10px;color:#c0c0c0;margin-top:4px;")

        lay.addWidget(lbl_logo)
        lay.addWidget(lbl_tit)
        lay.addWidget(lbl_sub)
        lay.addStretch()
        lay.addWidget(self.progress)
        lay.addWidget(self.lbl_estado)
        lay.addWidget(self.lbl_version)
        outer.addWidget(self.card)

        # ── Modo externo vs animación ─────────────────────────────
        self._external_mode = False
        self._contador = 0
        self._timer = QTimer()
        self._timer.timeout.connect(self._tick_fallback)
        self._timer.start(25)

        # Iniciar backup en hilo secundario inmediatamente
        _backup_executor.submit(self._crear_backup_safe)

    # ── API pública ────────────────────────────────────────────────

    def set_progress(self, value: int, message: str) -> None:
        """Actualiza la barra de progreso y el texto de estado en tiempo real.

        Args:
            value: Porcentaje 0-100.
            message: Texto descriptivo de la fase actual.
        """
        self._external_mode = True
        self.progress.setValue(min(value, 100))
        self.lbl_estado.setText(message)
        QApplication.processEvents()

    def close_and_show_login(self) -> None:
        """Cierra el splash y abre la ventana de login."""
        self._timer.stop()
        global _active_login_window
        _active_login_window = LoginWindow()
        _active_login_window.show()
        self.close()

    # ── Internos ───────────────────────────────────────────────────

    def _crear_backup_safe(self):
        """Ejecuta backup de forma segura capturando errores."""
        try:
            from services.backup_service import BackupService

            BackupService.crear()
        except Exception as e:
            log.warning("Backup automático falló: %s", e)

    def _tick_fallback(self):
        """Animación por defecto cuando no se usa el modo externo."""
        if self._external_mode:
            return  # El progreso externo maneja la barra
        self._contador += 1
        self.progress.setValue(self._contador)
        if self._contador == 20:
            self.lbl_estado.setText("Verificando base de datos…")
        elif self._contador == 40:
            self.lbl_estado.setText("Cargando módulos…")
        elif self._contador == 70:
            self.lbl_estado.setText("Preparando interfaz…")
        elif self._contador >= 100:
            self.close_and_show_login()

    def _centrar(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center() - self.rect().center())


# =============================================================================
# 2. LOGIN
# =============================================================================
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._login_successful = False  # Flag: True cuando cerramos por login exitoso
        self.setWindowTitle(f"Acceso — {APP_NAME}")
        self.setFixedSize(450, 600)

        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center() - self.rect().center())

        ico = str(ASSETS_DIR / "LogoDinamo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(380, 500)
        self.card.setProperty("class", "login-card")
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(30)
        sombra.setColor(QColor(0, 0, 0, 50))
        sombra.setOffset(0, 5)
        self.card.setGraphicsEffect(sombra)

        lay = QVBoxLayout(self.card)
        lay.setSpacing(20)
        lay.setContentsMargins(40, 50, 40, 50)

        lbl_bienvenido = QLabel("Bienvenido")
        lbl_bienvenido.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_bienvenido.setStyleSheet(
            f"font-size:32px;font-weight:900;color:{COLOR_PRIMARIO};border:none;"
        )
        lbl_sub = QLabel("Ingresa tus credenciales para continuar")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size:14px;color:#757575;border:none;margin-bottom:10px;")

        self.txt_user = QLineEdit()
        self.txt_user.setPlaceholderText("Usuario")
        self.txt_pass = QLineEdit()
        self.txt_pass.setPlaceholderText("Contraseña")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.returnPressed.connect(self._login)

        # Estilo moderno para inputs
        input_style = (
            "QLineEdit{padding:12px 16px;border:2px solid #e0e0e0;"
            "border-radius:10px;background-color:#ffffff;font-size:11pt;"
            "selection-background-color:#004aad;selection-color:#ffffff;}"
            "QLineEdit:focus{border-color:#004aad;background-color:#f8f9ff;}"
            "QLineEdit:hover{border-color:#bbdefb;}"
        )
        self.txt_user.setStyleSheet(input_style)
        self.txt_pass.setStyleSheet(input_style)

        self.btn_login = QPushButton("INICIAR SESIÓN")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setFixedHeight(52)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color:#d32f2f;font-size:13px;font-weight:bold;border:none;")

        self.btn_config_db = QPushButton("⚙️ Configurar Base de Datos")
        self.btn_config_db.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_config_db.setFixedHeight(30)
        self.btn_config_db.setProperty("class", "ghost")
        self.btn_config_db.clicked.connect(self._open_db_config)

        lay.addWidget(lbl_bienvenido)
        lay.addWidget(lbl_sub)
        lay.addSpacing(10)
        lay.addWidget(self.txt_user)
        lay.addWidget(self.txt_pass)
        lay.addSpacing(10)
        lay.addWidget(self.btn_login)
        lay.addWidget(self.lbl_error)
        lay.addWidget(self.btn_config_db)
        lay.addStretch()
        outer.addWidget(self.card)

    def _login(self):
        user = self.txt_user.text().strip()
        pwd = self.txt_pass.text().strip()
        if not user or not pwd:
            self.lbl_error.setText("Ingresa usuario y contraseña")
            return
        self.btn_login.setText("Verificando…")
        self.btn_login.setEnabled(False)
        self.lbl_error.setText("")
        QApplication.processEvents()

        client_ip = self._obtener_ip()

        # Ejecutar en el siguiente ciclo del event loop (hilo principal garantizado)
        QTimer.singleShot(0, lambda: self._ejecutar_login(user, pwd, client_ip))

    def _ejecutar_login(self, user: str, pwd: str, client_ip: str):
        """Realiza el login en el hilo principal para evitar que MainWindow
        se cree desde un hilo secundario (crash silencioso de Qt)."""
        try:
            session = AuthService.login(user, pwd, ip=client_ip)
        except Exception as exc:
            from services.auth_service import CredencialesInvalidas
            self.btn_login.setText("INICIAR SESIÓN")
            self.btn_login.setEnabled(True)
            if isinstance(exc, CredencialesInvalidas):
                self.lbl_error.setText("Usuario o contraseña incorrectos")
            elif isinstance(exc, DinamoBaseError):
                self.lbl_error.setText(f"{exc.mensaje_usuario}")
            else:
                self.lbl_error.setText("Error inesperado al iniciar sesión")
                log.error("Error en login: %s", exc, exc_info=True)
            return

        self.btn_login.setText("INICIAR SESIÓN")
        self.btn_login.setEnabled(True)

        # Si debe cambiar contraseña, mostrar diálogo obligatorio
        if session.get("debe_cambiar_password"):
            from views.force_change_password_dialog import ForceChangePasswordDialog

            dlg = ForceChangePasswordDialog(self, session)
            if dlg.exec() != QDialog.Accepted:
                self.lbl_error.setText("Debes cambiar tu contraseña para acceder.")
                return
            session["debe_cambiar_password"] = False

        # Crear y mostrar la ventana principal desde el hilo principal
        global _active_main_window
        _active_main_window = MainWindow(session)
        _active_main_window.showMaximized()
        self._login_successful = True  # Evitar que closeEvent llame a app.quit()
        self.close()


    def _obtener_ip(self) -> str:
        """Obtiene la IP del cliente."""
        import socket

        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            return ip
        except Exception:
            return "127.0.0.1"

    def _open_db_config(self):
        from views.database_config_dialog import DatabaseConfigDialog

        dlg = DatabaseConfigDialog(self)
        dlg.exec()

    def closeEvent(self, event):
        """Al cerrar la ventana de login manualmente (X), terminar la aplicación."""
        event.accept()
        if not self._login_successful:
            # Solo salir si el usuario cerró el login sin autenticarse
            QApplication.instance().quit()


# =============================================================================
# WIDGET DE CATEGORÍA COLAPSABLE PARA EL MENÚ
# =============================================================================
class MenuCategory(QWidget):
    """Widget de categoría colapsable para el menú lateral"""

    item_selected = Signal(int)

    def __init__(self, title: str, icon: str, items: list, rol: str, parent=None):
        super().__init__(parent)
        self.items_data = []
        self.buttons = []
        self.expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Cabecera colapsable
        self.header = QToolButton()
        self.header.setText(f"▼  {title}")
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header.setFixedHeight(45)
        self.header.setProperty("class", "sidebar-category")
        self.header.setCheckable(True)
        self.header.setChecked(True)
        self.header.clicked.connect(self._toggle)

        layout.addWidget(self.header)

        # Contenedor de items
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 5, 0, 10)
        content_layout.setSpacing(2)

        for txt, idx, visible_condition in items:
            if callable(visible_condition):
                if not visible_condition(rol):
                    continue
            elif not visible_condition:
                continue

            btn = QPushButton(txt)
            btn.setFlat(True)
            btn.setFixedHeight(38)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setProperty("class", "sidebar-item")
            btn.setProperty("view_index", idx)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._on_item_clicked(i, b))
            self.buttons.append(btn)
            content_layout.addWidget(btn)
            self.items_data.append((idx, btn))

        layout.addWidget(self.content)

    def _toggle(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        arrow = "▼" if self.expanded else "▶"
        parts = self.header.text().split("  ", 1)
        text = parts[1] if len(parts) == 2 else parts[0]
        self.header.setText(f"{arrow}  {text}")

    def _on_item_clicked(self, idx, clicked_btn):
        for btn in self.buttons:
            btn.setProperty("class", "sidebar-item")
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        clicked_btn.setProperty("class", "sidebar-item-active")
        clicked_btn.style().unpolish(clicked_btn)
        clicked_btn.style().polish(clicked_btn)
        self.item_selected.emit(idx)

    def set_active_item(self, idx: int):
        for button_idx, btn in self.items_data:
            if button_idx == idx:
                btn.setProperty("class", "sidebar-item-active")
            else:
                btn.setProperty("class", "sidebar-item")
            btn.style().unpolish(btn)
            btn.style().polish(btn)


# =============================================================================
# 3. VENTANA PRINCIPAL
# =============================================================================
class MainWindow(QMainWindow):
    _MENU_STRUCTURE = [
        (
            "PRINCIPAL",
            "",
            [
                ("Dashboard", 0, True),
                ("Calendario", 1, True),
                ("Alertas", 10, True),
            ],
        ),
        (
            "OPERACIÓN",
            "",
            [
                ("Rentas", 2, True),
                ("Reservas", 3, True),
                ("Comparendos", 9, True),
            ],
        ),
        (
            "ADMINISTRACIÓN",
            "",
            [
                ("Clientes", 4, True),
                ("Flota", 5, True),
                ("Taller", 6, True),
            ],
        ),
        (
            "FINANZAS",
            "",
            [
                ("Caja Menor", 11, True),
                ("Informes", 8, lambda rol: rol in ROLES_CON_INFORMES),
            ],
        ),
        (
            "SISTEMA",
            "",
            [
                ("Usuarios", 7, lambda rol: rol in ROLES_CON_USUARIOS),
            ],
        ),
    ]

    def __init__(self, session: dict):
        super().__init__()
        self._session = session
        self._closing_to_login = False  # Flag: True cuando cerramos para volver al login
        self.setWindowTitle(f"{APP_NAME} — {session['nombre']}")
        self.resize(1366, 768)

        ico = str(ASSETS_DIR / "LogoDinamo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        central = QWidget()
        self.setCentralWidget(central)
        lay_h = QHBoxLayout(central)
        lay_h.setContentsMargins(0, 0, 0, 0)
        lay_h.setSpacing(0)

        self._menu = self._crear_menu_colapsable(session.get("rol", ""))
        lay_h.addWidget(self._menu)

        # ── Contenido derecho (QStackedWidget) ──
        self.stack = QStackedWidget()
        lay_h.addWidget(self.stack)

        self._inicializar_vistas()

        # ── Marca de inicio de sesión ───────────────────────────────────────
        self._session_start = time.time()

        # Backup automático
        self._horas_backup = set(BACKUP_HOURS)
        self._timer_backup = QTimer(self)
        self._timer_backup.timeout.connect(self._backup_auto)
        self._timer_backup.start(BACKUP_INTERVAL_MS)

        log.info(
            "Sesión iniciada: %s (rol=%s)",
            session["username"],
            session["rol"],
        )

    def _crear_menu_colapsable(self, rol: str) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(190)
        frame.setProperty("class", "sidebar-header")

        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header con logo
        hdr = QFrame()
        hdr.setProperty("class", "sidebar-header")
        hdr.setFixedHeight(80)
        h_lay = QHBoxLayout(hdr)
        h_lay.setContentsMargins(15, 10, 15, 10)
        h_lay.setSpacing(10)
        lbl_img = QLabel()
        logo_ruta = _obtener_logo_ruta()
        if logo_ruta and os.path.exists(logo_ruta):
            pix = QPixmap(logo_ruta).scaled(
                50,
                50,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            lbl_img.setPixmap(pix)
            lbl_img.setFixedSize(50, 50)
        else:
            lbl_img.setText("🚗")
        lbl_tit = QLabel("DINAMO\nRENT ERP")
        lbl_tit.setStyleSheet(f"color:{COLOR_PRIMARIO};font-weight:800;font-size:16px;")
        h_lay.addWidget(lbl_img)
        h_lay.addWidget(lbl_tit)
        h_lay.addStretch()
        main_layout.addWidget(hdr)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                background-color: #1565c0; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #42a5f5; border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #90caf9; }
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical { height: 0px; }
        """)

        categories_container = QWidget()
        categories_layout = QVBoxLayout(categories_container)
        categories_layout.setContentsMargins(0, 10, 0, 0)
        categories_layout.setSpacing(5)
        categories_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._menu_categories = []

        for title, icon, items in self._MENU_STRUCTURE:
            filtered_items = []
            for txt, idx, condition in items:
                if callable(condition):
                    if condition(rol):
                        filtered_items.append((txt, idx, True))
                elif condition:
                    filtered_items.append((txt, idx, True))

            if filtered_items:
                cat = MenuCategory(title, icon, filtered_items, rol)
                cat.item_selected.connect(self._cambiar_vista)
                categories_layout.addWidget(cat)
                self._menu_categories.append(cat)

        categories_layout.addStretch()
        scroll.setWidget(categories_container)
        main_layout.addWidget(scroll)

        # Footer
        footer = QFrame()
        footer.setProperty("class", "sidebar-footer")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.setSpacing(5)

        lbl_usr = QLabel(
            f"Usuario: {self._session.get('username', '').upper()}\nRol: {rol.upper()}"
        )
        lbl_usr.setStyleSheet("color:#bbdefb;font-size:11px;")

        # ── Botón de cambio de tema ──
        from views.themes.theme_manager import get_current_theme_name

        _current_theme = get_current_theme_name()
        _theme_icon = "☀️" if _current_theme == "dinamo" else "🌙"
        _theme_label = "Claro" if _current_theme == "dinamo" else "Oscuro"
        self._btn_theme = QPushButton(f"{_theme_icon} Tema {_theme_label}")
        self._btn_theme.setFixedHeight(32)
        self._btn_theme.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_theme.setProperty("class", "secondary")
        self._btn_theme.clicked.connect(self._toggle_theme)

        btn_about = QPushButton("ℹ️ Acerca de")
        btn_about.setFixedHeight(32)
        btn_about.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_about.setProperty("class", "ghost")
        btn_about.clicked.connect(self._open_about)

        btn_logout = QPushButton("Cerrar Sesión")
        btn_logout.setFixedHeight(36)
        btn_logout.setProperty("class", "danger")
        btn_logout.clicked.connect(self._cerrar_sesion)

        footer_layout.addWidget(lbl_usr)
        footer_layout.addWidget(self._btn_theme)
        footer_layout.addWidget(btn_about)
        footer_layout.addWidget(btn_logout)
        main_layout.addWidget(footer)

        return frame

    def _inicializar_vistas(self):
        """Prepara los placeholders para la carga perezosa (Lazy Loading)."""
        self._vistas_classes = _cargar_vistas()
        self._vistas_instancias = {}

        # Llenar el QStackedWidget con widgets vacíos (placeholders)
        for _ in range(len(self._vistas_classes)):
            self.stack.addWidget(QWidget())

        self._first_load_done = False
        
        # Cargar la vista inicial
        self._cambiar_vista(0)

    def _cambiar_vista(self, idx: int):
        if idx == 99:
            self._cerrar_sesion()
            return

        # ── Si es el mismo índice, ignorar (excepto en el primer arranque) ──
        if self.stack.currentIndex() == idx and self._first_load_done:
            return

        self._first_load_done = True

        # ── Guarda anti-re-entrada mientras la animación está en curso ──────
        if getattr(self, "_page_animating", False):
            return

        # Lazy Load: Instanciar la vista solo la primera vez que se visita
        if idx not in self._vistas_instancias:
            session_id = self._session.get("session_id")
            Cls = self._vistas_classes[idx]
            log.info("Lazy loading: %s...", Cls.__name__)
            _t0 = time.perf_counter()
            instancia = Cls(session_id=session_id)
            _elapsed_ms = (time.perf_counter() - _t0) * 1000
            log.info(
                "Vista %s cargada en %.0f ms",
                Cls.__name__,
                _elapsed_ms,
            )
            self._vistas_instancias[idx] = instancia

            # Reemplazar el placeholder por la vista real
            dummy = self.stack.widget(idx)
            self.stack.removeWidget(dummy)
            self.stack.insertWidget(idx, instancia)
            dummy.deleteLater()

        # ── Transición animada fade-out / fade-in ───────────────────────────
        current = self.stack.currentWidget()
        target = self.stack.widget(idx)

        if not current or current == target:
            # Sin animación: primer arranque o widget idéntico
            self.stack.setCurrentIndex(idx)
            for cat in self._menu_categories:
                cat.set_active_item(idx)
            return

        from PySide6.QtWidgets import QGraphicsOpacityEffect
        from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QAbstractAnimation

        self._page_animating = True

        # ── Fade-out del widget actual (1.0 → 0.0) ──────────────────────────
        effect_out = QGraphicsOpacityEffect(current)
        current.setGraphicsEffect(effect_out)

        anim_out = QPropertyAnimation(effect_out, b"opacity")
        anim_out.setParent(effect_out)
        anim_out.setDuration(120)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        anim_out.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_fade_out():
            # Limpiar efecto del widget saliente
            current.setGraphicsEffect(None)

            # Cambiar de página
            self.stack.setCurrentIndex(idx)
            for cat in self._menu_categories:
                cat.set_active_item(idx)

            # ── Fade-in del widget entrante (0.0 → 1.0) ─────────────────────
            effect_in = QGraphicsOpacityEffect(target)
            target.setGraphicsEffect(effect_in)

            anim_in = QPropertyAnimation(effect_in, b"opacity")
            anim_in.setParent(effect_in)
            anim_in.setDuration(120)
            anim_in.setStartValue(0.0)
            anim_in.setEndValue(1.0)
            anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)

            def _on_fade_in():
                target.setGraphicsEffect(None)
                self._page_animating = False

            anim_in.finished.connect(_on_fade_in)
            anim_in.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

        anim_out.finished.connect(_on_fade_out)
        anim_out.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _backup_auto(self):
        hora = time.strftime("%H:%M")
        if hora in self._horas_backup:
            log.info("Backup automático a las %s", hora)
            try:
                from services.backup_service import BackupService

                BackupService.crear()
            except Exception as e:
                log.warning("Backup automático falló: %s", e)
            self._timer_backup.stop()
            QTimer.singleShot(61_000, lambda: self._timer_backup.start(BACKUP_INTERVAL_MS))

    def _open_about(self):
        """Abre el diálogo de información del sistema."""
        from views.about_dialog import AboutDialog

        dlg = AboutDialog(self)
        dlg.exec()

    def _toggle_theme(self):
        """Cambia al tema opuesto y lo aplica en toda la app con transición suave."""
        from views.themes.theme_manager import animated_toggle_theme, THEME_LABELS, THEME_ICONS

        new = animated_toggle_theme(self.centralWidget())
        if new is None:
            return  # Animación en curso, ignorar clic
        icon = THEME_ICONS.get(new, "☀️")
        label = THEME_LABELS.get(new, "Claro")
        self._btn_theme.setText(f"{icon} Tema {label}")
        qss_len = len(QApplication.instance().styleSheet() or "")
        log.info(
            "Tema cambiado a: %s · %s caracteres QSS",
            label,
            f"{qss_len:,}",
        )

        # Notificación toast
        from views.components.toast_notification import ToastNotification

        ToastNotification.show_info(self, f'Tema cambiado a "{label}"')

    def _cerrar_sesion(self):
        elapsed = time.time() - self._session_start
        mins, secs = divmod(int(elapsed), 60)
        hrs, mins = divmod(mins, 60)
        if hrs:
            duracion = f"{hrs}h {mins}m {secs}s"
        elif mins:
            duracion = f"{mins}m {secs}s"
        else:
            duracion = f"{secs}s"
        log.info(
            "Sesión cerrada: %s · Duración: %s",
            self._session.get("username"),
            duracion,
        )
        global _active_login_window
        self._closing_to_login = True  # Suprimir el diálogo de salida
        _active_login_window = LoginWindow()
        _active_login_window.show()
        self.close()

    def closeEvent(self, event):
        # Si es un cierre programático para volver al login, no pedir confirmación
        if self._closing_to_login:
            event.accept()
            return

        from views.components import ModernMessageBox
        from PySide6.QtWidgets import QDialog

        resp = ModernMessageBox.question(self, "Salir", "¿Está seguro de salir de la aplicación?")
        if resp == QDialog.Accepted:
            event.accept()
            QApplication.instance().quit()
        else:
            event.ignore()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    try:
        from ctypes import windll

        windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"dinamo.rent.erp.{APP_VERSION}")
    except (ImportError, OSError):
        pass

    log.info("═══ Arrancando %s v%s ═══", APP_NAME, APP_VERSION)

    # ── Crear QApplication ANTES del splash ────────────────────────────
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")

    ico = str(ASSETS_DIR / "LogoDinamo.ico")
    if not os.path.exists(ico):
        ico = str(ASSETS_DIR / "Logo_Dinamo.png")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))

    # ── Splash temprano con progreso real ──────────────────────────────

    # Aplicar tema antes del splash para que las clases funcionen
    from views.themes.theme_manager import apply_theme, get_current_theme_name

    apply_theme()
    qss_len = len(app.styleSheet() or "")
    theme_name = get_current_theme_name()
    log.info(
        "Tema activo: %s · %s caracteres QSS cargados",
        theme_name,
        f"{qss_len:,}",
    )

    splash = SplashScreen()
    splash.show()
    splash.set_progress(5, "Inicializando sistema…")

    setup_result = inicializar_base_datos()

    if setup_result == "SETUP_NEEDED":
        splash.close()
        from views.setup_wizard import run_setup_wizard

        if not run_setup_wizard():
            log.warning("Setup inicial cancelado por el usuario")
            sys.exit(0)
        sys.exit(0)

    splash.set_progress(30, "Verificando base de datos…")

    splash.set_progress(50, "Validando configuraciones…")

    splash.set_progress(70, "Cargando módulos del sistema…")
    # Pre-carga de clases de vistas (no se instancian, solo se importan)
    _cargar_vistas()

    splash.set_progress(90, "Preparando interfaz…")

    splash.set_progress(100, "¡Listo!")

    # Pequeña pausa para que el usuario vea el 100% antes de la transición
    QTimer.singleShot(400, splash.close_and_show_login)

    sys.exit(app.exec())
