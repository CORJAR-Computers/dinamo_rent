"""
main_qt.py — Punto de entrada de Dinamo Rent ERP

Responsabilidades ÚNICAS de este archivo:
  1. Inicializar la BD y el sistema de logs
  2. Mostrar Splash Screen
  3. Mostrar Login
  4. Instanciar la ventana principal tras autenticación exitosa
"""
import sys
import os
import time

os.environ["G_MESSAGES_DEBUG"] = "none"

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFrame, QStackedWidget,
    QListWidget, QListWidgetItem, QProgressBar, QGraphicsDropShadowEffect,
    QToolButton, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, QSize, QTimer, Signal
from PySide6.QtGui import QIcon, QFont, QPixmap, QBrush, QColor

# ── Core ─────────────────────────────────────────────────────────────────────
from core.config import (
    APP_NAME, APP_VERSION, COLOR_PRIMARIO, COLOR_FONDO,
    FONT_FAMILY, FONT_SIZE, BACKUP_HOURS, BACKUP_INTERVAL_MS,
    ROLES_CON_INFORMES, ROLES_CON_USUARIOS, ASSETS_DIR,
)
from core.exceptions import DinamoBaseError, CredencialesInvalidas
from core.logger import get_logger
from core.database_sa import init_db
from core.security import SecurityManager
from services.services import AuthService, BackupService

log = get_logger(__name__)

# ── Inicialización de la base de datos con SQLAlchemy ─────────────────────────
def inicializar_base_datos():
    """Inicializa la base de datos con SQLAlchemy y crea admin si no existe."""
    log.info("Inicializando base de datos con SQLAlchemy...")
    init_db()
    
    # Crear usuario admin si no existe
    from core.models import Usuario
    from core.database_sa import get_session
    
    with get_session() as session:
        admin = session.query(Usuario).filter(Usuario.username == 'admin').first()
        if not admin:
            admin = Usuario(
                username='admin',
                password=SecurityManager.hash_password('admin123'),
                nombre='Administrador Principal',
                rol='Administrador',
                activo=1,
            )
            session.add(admin)
            log.info("Usuario admin creado con contraseña por defecto: admin/admin123")

# ── Vistas (importación diferida para acelerar arranque) ──────────────────────
def _cargar_vistas():
    # ¡Todo se importa ahora de la capa de Vistas de forma limpia!
    from views.dashboard_view      import DashboardWidget
    from views.calendario_view     import CalendarioWidget
    from views.rentas_view         import RentasWidget
    from views.reservas_view       import ReservasWidget
    from views.clientes_view       import ClientesWidget
    from views.autos_view          import AutosWidget
    from views.mantenimiento_view  import MantenimientoWidget
    from views.usuarios_view       import UsuariosWidget
    from views.informes_view       import InformesWidget
    from views.comparendos_view import ComparendosWidget
    from views.alertas_view import AlertasWidget
    from views.cierre_renta_view   import CierreRentaDialog
    from views.gastos_view import GastosWidget

    return (
        DashboardWidget, CalendarioWidget, RentasWidget, ReservasWidget, ClientesWidget, AutosWidget,
        MantenimientoWidget, UsuariosWidget, InformesWidget, ComparendosWidget, AlertasWidget, GastosWidget
    )


# =============================================================================
# 1. SPLASH SCREEN
# =============================================================================
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(450, 600)
        self._centrar()

        outer = QVBoxLayout(self)
        outer.setContentsMargins(10, 10, 10, 10)

        self.card = QFrame()
        self.card.setStyleSheet(
            "QFrame{background-color:white;border-radius:20px;border:1px solid #e0e0e0;}"
        )
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(20); sombra.setColor(QColor(0, 0, 0, 60))
        self.card.setGraphicsEffect(sombra)

        lay = QVBoxLayout(self.card)
        lay.setContentsMargins(40, 60, 40, 60)

        lbl_logo = QLabel(); lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = self._buscar_logo()
        if logo_path:
            pix = QPixmap(logo_path).scaled(180, 180, Qt.AspectRatioMode.KeepAspectRatio,
                                            Qt.TransformationMode.SmoothTransformation)
            lbl_logo.setPixmap(pix)
        else:
            lbl_logo.setText("🚗"); lbl_logo.setStyleSheet("font-size:80px;")

        lbl_tit = QLabel(APP_NAME)
        lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_tit.setStyleSheet(
            f"font-size:28px;font-weight:900;color:{COLOR_PRIMARIO};margin-top:20px;"
        )
        lbl_sub = QLabel(f"Sistema de Gestión de Flota v{APP_VERSION}")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setStyleSheet("font-size:14px;color:#757575;margin-bottom:40px;")

        self.progress = QProgressBar()
        self.progress.setTextVisible(False); self.progress.setFixedHeight(6)
        self.progress.setStyleSheet(
            f"QProgressBar{{background:#f0f0f0;border-radius:3px;}}"
            f"QProgressBar::chunk{{background:{COLOR_PRIMARIO};border-radius:3px;}}"
        )
        self.lbl_estado = QLabel("Iniciando sistema…")
        self.lbl_estado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_estado.setStyleSheet("font-size:12px;color:#9e9e9e;margin-top:10px;")

        lay.addWidget(lbl_logo); lay.addWidget(lbl_tit); lay.addWidget(lbl_sub)
        lay.addStretch(); lay.addWidget(self.progress); lay.addWidget(self.lbl_estado)
        outer.addWidget(self.card)

        self._contador = 0
        self._timer = QTimer(); self._timer.timeout.connect(self._tick); self._timer.start(25)

    def _tick(self):
        self._contador += 1
        self.progress.setValue(self._contador)
        if self._contador == 20:
            self.lbl_estado.setText("Verificando base de datos…")
        elif self._contador == 40:
            self.lbl_estado.setText("Creando copia de seguridad…")
            BackupService.crear()
        elif self._contador == 70:
            self.lbl_estado.setText("Cargando módulos…")
        elif self._contador >= 100:
            self._timer.stop()
            self.close()
            self._login = LoginWindow()
            self._login.show()

    def _centrar(self):
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center() - self.rect().center())

    @staticmethod
    def _buscar_logo() -> str:
        for nombre in ("Logo_Dinamo.png", "LogoDinamo.png", "logo.png"):
            p = str(ASSETS_DIR / nombre)
            if os.path.exists(p):
                return p
        return ""


# =============================================================================
# 2. LOGIN
# =============================================================================
class LoginWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"Acceso — {APP_NAME}")
        self.setFixedSize(450, 600)

        # Centrar
        geo = QApplication.primaryScreen().availableGeometry()
        self.move(geo.center() - self.rect().center())

        ico = str(ASSETS_DIR / "LogoDinamo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        self.setStyleSheet(f"background-color:{COLOR_FONDO};")
        central = QWidget(); self.setCentralWidget(central)
        outer   = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card = QFrame()
        self.card.setFixedSize(380, 500)
        self.card.setStyleSheet(
            "QFrame{background-color:white;border-radius:25px;border:1px solid #e0e0e0;}"
        )
        sombra = QGraphicsDropShadowEffect(self)
        sombra.setBlurRadius(25); sombra.setColor(QColor(0, 0, 0, 40))
        self.card.setGraphicsEffect(sombra)

        lay = QVBoxLayout(self.card)
        lay.setSpacing(20); lay.setContentsMargins(40, 50, 40, 50)

        lbl_bienvenido = QLabel("Bienvenido")
        lbl_bienvenido.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_bienvenido.setStyleSheet(
            f"font-size:32px;font-weight:bold;color:{COLOR_PRIMARIO};border:none;"
        )
        lbl_sub = QLabel("Ingresa tus credenciales para continuar")
        lbl_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_sub.setWordWrap(True)
        lbl_sub.setStyleSheet("font-size:14px;color:#757575;border:none;margin-bottom:10px;")

        _estilo_input = (
            "QLineEdit{border:2px solid #f0f0f0;border-radius:10px;padding:12px;"
            "font-size:15px;background:#fafafa;}"
            "QLineEdit:focus{border:2px solid #004aad;background:white;}"
        )
        self.txt_user = QLineEdit(); self.txt_user.setPlaceholderText("Usuario")
        self.txt_user.setStyleSheet(_estilo_input)
        self.txt_pass = QLineEdit(); self.txt_pass.setPlaceholderText("Contraseña")
        self.txt_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_pass.setStyleSheet(_estilo_input)
        self.txt_pass.returnPressed.connect(self._login)

        self.btn_login = QPushButton("INICIAR SESIÓN")
        self.btn_login.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_login.setFixedHeight(50)
        self.btn_login.setStyleSheet(
            f"QPushButton{{background:{COLOR_PRIMARIO};color:white;border-radius:10px;"
            f"font-size:15px;font-weight:bold;letter-spacing:1px;}}"
            f"QPushButton:hover{{background:#003380;}}"
        )
        self.btn_login.clicked.connect(self._login)

        self.lbl_error = QLabel("")
        self.lbl_error.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_error.setStyleSheet("color:#d32f2f;font-size:13px;font-weight:bold;border:none;")

        lay.addWidget(lbl_bienvenido); lay.addWidget(lbl_sub); lay.addSpacing(10)
        lay.addWidget(self.txt_user);  lay.addWidget(self.txt_pass); lay.addSpacing(10)
        lay.addWidget(self.btn_login); lay.addWidget(self.lbl_error); lay.addStretch()
        outer.addWidget(self.card)

    def _login(self):
        user = self.txt_user.text().strip()
        pwd  = self.txt_pass.text().strip()
        if not user or not pwd:
            self.lbl_error.setText("⚠️ Ingresa usuario y contraseña")
            return
        self.btn_login.setText("Verificando…"); self.btn_login.setEnabled(False)
        QApplication.processEvents()
        try:
            session = AuthService.login(user, pwd)
            self._main = MainWindow(session)
            self._main.show()
            self.close()
        except CredencialesInvalidas:
            self.lbl_error.setText("❌ Usuario o contraseña incorrectos")
        except DinamoBaseError as e:
            self.lbl_error.setText(f"❌ {e.mensaje_usuario}")
        except Exception as e:
            self.lbl_error.setText(f"❌ Error inesperado")
            log.error("Error en login: %s", e, exc_info=True)
        finally:
            self.btn_login.setText("INICIAR SESIÓN"); self.btn_login.setEnabled(True)


# =============================================================================
# WIDGET DE CATEGORÍA COLAPSABLE PARA EL MENÚ
# =============================================================================
class MenuCategory(QWidget):
    """Widget de categoría colapsable para el menú lateral"""
    item_selected = Signal(int)  # Emite el índice de la vista

    def __init__(self, title: str, icon: str, items: list, rol: str, parent=None):
        """
        items: lista de tuplas (texto_display, idx_vista, condicion_visible)
        condicion_visible: callable o True/False
        """
        super().__init__(parent)
        self.items_data = []
        self.buttons = []

        # CORRECCIÓN: Inicializar expanded ANTES de cualquier otro método
        self.expanded = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Botón de categoría (cabecera colapsable)
        self.header = QToolButton()
        self.header.setText(f"{icon}  {title}")
        self.header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.header.setFixedHeight(45)
        self.header.setStyleSheet("""
            QToolButton {
                background-color: transparent;
                color: #bbdefb;
                border: none;
                border-left: 5px solid transparent;
                padding: 0 15px;
                font-size: 13px;
                font-weight: bold;
                text-align: left;
            }
            QToolButton:hover {
                background-color: #1565c0;
                color: white;
            }
            QToolButton::menu-indicator { image: none; }
        """)
        self.header.setCheckable(True)
        self.header.setChecked(True)  # Expandido por defecto
        self.header.clicked.connect(self._toggle)

        # Indicador de expansión (▼/▶)
        self._update_arrow()

        layout.addWidget(self.header)

        # Contenedor de items
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 5, 0, 10)
        content_layout.setSpacing(2)

        # Crear botones de items
        for txt, idx, visible_condition in items:
            # Verificar condición de visibilidad (por rol)
            if callable(visible_condition):
                if not visible_condition(rol):
                    continue
            elif not visible_condition:
                continue

            btn = QPushButton(txt)
            btn.setFlat(True)
            btn.setFixedHeight(38)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #e3f2fd;
                    border: none;
                    border-left: 5px solid transparent;
                    padding: 0 30px;
                    font-size: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
            """)
            btn.setProperty("view_index", idx)
            btn.clicked.connect(lambda checked, i=idx, b=btn: self._on_item_clicked(i, b))

            self.buttons.append(btn)
            content_layout.addWidget(btn)
            self.items_data.append((idx, btn))

        layout.addWidget(self.content)

    def _update_arrow(self):
        # CORRECCIÓN: Ahora self.expanded ya está inicializado
        arrow = "▼" if self.expanded else "▶"
        # Extraer icono y texto del header actual
        parts = self.header.text().split("  ", 1)
        if len(parts) == 2:
            icon = parts[0].replace("▼ ", "").replace("▶ ", "")
            text = parts[1]
        else:
            icon = "📊"
            text = parts[0] if parts else "Categoría"
        self.header.setText(f"{arrow}  {text}")

    def _toggle(self):
        self.expanded = not self.expanded
        self.content.setVisible(self.expanded)
        self._update_arrow()

    def _on_item_clicked(self, idx, clicked_btn):
        # Desmarcar todos los botones de esta categoría
        for btn in self.buttons:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #e3f2fd;
                    border: none;
                    border-left: 5px solid transparent;
                    padding: 0 30px;
                    font-size: 14px;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                    color: white;
                }
                QPushButton:pressed {
                    background-color: #0d47a1;
                }
            """)

        # Marcar el seleccionado
        clicked_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d47a1;
                color: white;
                border: none;
                border-left: 5px solid #42a5f5;
                padding: 0 30px;
                font-size: 14px;
                font-weight: bold;
                text-align: left;
            }
        """)

        self.item_selected.emit(idx)

    def set_active_item(self, idx: int):
        """Marca visualmente el item activo"""
        for button_idx, btn in self.items_data:
            if button_idx == idx:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #0d47a1;
                        color: white;
                        border: none;
                        border-left: 5px solid #42a5f5;
                        padding: 0 30px;
                        font-size: 14px;
                        font-weight: bold;
                        text-align: left;
                    }
                """)
            else:
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #e3f2fd;
                        border: none;
                        border-left: 5px solid transparent;
                        padding: 0 30px;
                        font-size: 14px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #1565c0;
                        color: white;
                    }
                    QPushButton:pressed {
                        background-color: #0d47a1;
                    }
                """)


# =============================================================================
# 3. VENTANA PRINCIPAL
# =============================================================================
class MainWindow(QMainWindow):
    # Estructura del menú: (titulo_categoria, icono, [(texto, idx, visible), ...])
    _MENU_STRUCTURE = [
        (
            "PRINCIPAL", "📊", [
                ("Dashboard", 0, True),
                ("Alertas", 10, True),
                ("Calendario", 1, True),
            ]
        ),
        (
            "OPERACIÓN", "🚗", [
                ("Rentas", 2, True),
                ("Reservas", 3, True),
                ("Comparendos", 9, True),
            ]
        ),
        (
            "ADMINISTRACIÓN", "👥", [
                ("Clientes", 4, True),
                ("Flota", 5, True),
                ("Taller", 6, True),
            ]
        ),
        (
            "FINANZAS", "💰", [
                ("Caja Menor", 11, True),
                ("Informes", 8, lambda rol: rol in ROLES_CON_INFORMES),
            ]
        ),
        (
            "SISTEMA", "⚙️", [
                ("Usuarios", 7, lambda rol: rol in ROLES_CON_USUARIOS),
            ]
        ),
    ]

    def __init__(self, session: dict):
        super().__init__()
        self._session = session
        self.setWindowTitle(f"{APP_NAME} — {session['nombre']}")
        self.resize(1366, 768)
        self.showMaximized()

        ico = str(ASSETS_DIR / "LogoDinamo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))

        central = QWidget(); self.setCentralWidget(central)
        lay_h   = QHBoxLayout(central)
        lay_h.setContentsMargins(0, 0, 0, 0); lay_h.setSpacing(0)

        self._menu = self._crear_menu_colapsable(session.get("rol", ""))
        lay_h.addWidget(self._menu)

        self.stack = QStackedWidget()
        self.stack.setStyleSheet(f"background-color:{COLOR_FONDO};")
        lay_h.addWidget(self.stack)

        self._inicializar_vistas()

        # Backup automático
        self._horas_backup = set(BACKUP_HOURS)
        self._timer_backup = QTimer(self)
        self._timer_backup.timeout.connect(self._backup_auto)
        self._timer_backup.start(BACKUP_INTERVAL_MS)

        log.info("Sesión iniciada: %s (rol=%s)", session["username"], session["rol"])

    # ── menú colapsable ──────────────────────────────────────────────────────

    def _crear_menu_colapsable(self, rol: str) -> QFrame:
        frame = QFrame()
        frame.setFixedWidth(190)
        frame.setStyleSheet(
            f"background-color:{COLOR_PRIMARIO};color:white;border:none;"
        )

        # Layout principal del menú
        main_layout = QVBoxLayout(frame)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header con logo (igual que antes)
        hdr = QFrame()
        hdr.setStyleSheet("background-color:white;border-bottom:3px solid #002f6c;")
        hdr.setFixedHeight(80)
        h_lay = QHBoxLayout(hdr); h_lay.setContentsMargins(15, 10, 15, 10); h_lay.setSpacing(10)
        lbl_img = QLabel()
        for nombre in ("Logo_Dinamo.png", "LogoDinamo.png", "logo.png"):
            p = str(ASSETS_DIR / nombre)
            if os.path.exists(p):
                pix = QPixmap(p).scaled(50, 50, Qt.AspectRatioMode.KeepAspectRatio,
                                        Qt.TransformationMode.SmoothTransformation)
                lbl_img.setPixmap(pix); lbl_img.setFixedSize(50, 50)
                break
        else:
            lbl_img.setText("🚗")
        lbl_tit = QLabel("DINAMO\nRENT ERP")
        lbl_tit.setStyleSheet(
            f"color:{COLOR_PRIMARIO};font-weight:800;font-size:16px;"
        )
        h_lay.addWidget(lbl_img); h_lay.addWidget(lbl_tit); h_lay.addStretch()
        main_layout.addWidget(hdr)

        # Área scrollable para las categorías
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background-color: transparent; }
            QScrollBar:vertical {
                background-color: #1565c0;
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: #42a5f5;
                border-radius: 4px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover { background-color: #90caf9; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        # Contenedor de categorías
        categories_container = QWidget()
        categories_layout = QVBoxLayout(categories_container)
        categories_layout.setContentsMargins(0, 10, 0, 0)
        categories_layout.setSpacing(5)
        categories_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._menu_categories = []

        # Crear categorías
        for title, icon, items in self._MENU_STRUCTURE:
            # Filtrar items según rol
            filtered_items = []
            for txt, idx, condition in items:
                if callable(condition):
                    if condition(rol):
                        filtered_items.append((txt, idx, True))
                elif condition:
                    filtered_items.append((txt, idx, True))

            if filtered_items:  # Solo crear categoría si tiene items visibles
                cat = MenuCategory(title, icon, filtered_items, rol)
                cat.item_selected.connect(self._cambiar_vista)
                categories_layout.addWidget(cat)
                self._menu_categories.append(cat)

        categories_layout.addStretch()
        scroll.setWidget(categories_container)
        main_layout.addWidget(scroll)

        # Footer con usuario y cerrar sesión
        footer = QFrame()
        footer.setStyleSheet("background-color: #0d47a1; border-top: 1px solid #1565c0;")
        footer.setFixedHeight(90)
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(15, 10, 15, 10)
        footer_layout.setSpacing(5)

        lbl_usr = QLabel(
            f"Usuario: {self._session.get('username','').upper()}\n"
            f"Rol: {rol.upper()}"
        )
        lbl_usr.setStyleSheet("color:#bbdefb;font-size:11px;")

        btn_logout = QPushButton("🔒 Cerrar Sesión")
        btn_logout.setFlat(True)
        btn_logout.setFixedHeight(32)
        btn_logout.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #ef5350;
                border: 1px solid #ef5350;
                border-radius: 4px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ef5350;
                color: white;
            }
        """)
        btn_logout.clicked.connect(self._cerrar_sesion)

        footer_layout.addWidget(lbl_usr)
        footer_layout.addWidget(btn_logout)
        main_layout.addWidget(footer)

        return frame

    # ── vistas ────────────────────────────────────────────────────────────────

    def _inicializar_vistas(self):
        (Dashboard, Calendario, Rentas, Reservas,
         Clientes, Autos, Mantenimiento, Usuarios, Informes, Comparendos, Alertas, Gastos) = _cargar_vistas()

        for W in (Dashboard, Calendario, Rentas, Reservas,
                  Clientes, Autos, Mantenimiento, Usuarios, Informes, Comparendos, Alertas, Gastos):
            self.stack.addWidget(W())

        # Activar Dashboard por defecto
        self._cambiar_vista(0)

    def _cambiar_vista(self, idx: int):
        if idx == 99:  # Cerrar sesión
            self._cerrar_sesion()
            return

        self.stack.setCurrentIndex(idx)

        # Actualizar visualización en el menú
        for cat in self._menu_categories:
            cat.set_active_item(idx)

    # ── backup automático ────────────────────────────────────────────────────

    def _backup_auto(self):
        hora = time.strftime("%H:%M")
        if hora in self._horas_backup:
            log.info("Backup automático a las %s", hora)
            BackupService.crear()
            self._timer_backup.stop()
            QTimer.singleShot(61_000, lambda: self._timer_backup.start(BACKUP_INTERVAL_MS))

    def _cerrar_sesion(self):
        log.info("Sesión cerrada: %s", self._session.get("username"))
        self.close()
        self._login = LoginWindow()
        self._login.show()


# =============================================================================
# PUNTO DE ENTRADA
# =============================================================================
if __name__ == "__main__":
    # Icono en barra de tareas (Windows)
    try:
        from ctypes import windll
        windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            f"dinamo.rent.erp.{APP_VERSION}"
        )
    except (ImportError, OSError):
        pass

    log.info("═══ Arrancando %s v%s ═══", APP_NAME, APP_VERSION)

    # Inicializar BD
    # Inicializar base de datos con SQLAlchemy
    inicializar_base_datos()

    app = QApplication(sys.argv)

    ico = str(ASSETS_DIR / "LogoDinamo.ico")
    if not os.path.exists(ico):
        ico = str(ASSETS_DIR / "Logo_Dinamo.png")
    if os.path.exists(ico):
        app.setWindowIcon(QIcon(ico))

    app.setFont(QFont(FONT_FAMILY, FONT_SIZE))

    ruta_css = ASSETS_DIR / "styles.qss"
    if os.path.exists(ruta_css):
        with open(ruta_css, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
            log.info("Hoja de estilos global (QSS) cargada con éxito.")
    else:
        log.warning(f"No se encontró el archivo de estilos en: {ruta_css}")

    splash = SplashScreen()
    splash.show()

    sys.exit(app.exec())