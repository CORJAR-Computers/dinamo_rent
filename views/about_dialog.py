"""
views/about_dialog.py — Dialogo Acerca de / Informacion del Sistema
"""
import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QDialog, QApplication,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap

from core.config import (
    APP_NAME, APP_VERSION, APP_AUTHOR, DB_ENGINE,
    DB_MYSQL, PRODUCTION_MODE, ASSETS_DIR,
)
from core.logger import get_logger

log = get_logger(__name__)

_COPYRIGHT = "(C) 2024 Dinamo Rent a Car"
_DESCRIPTION = (
    "Sistema de Gestion de Flota para renta de vehiculos.\n"
    "Administracion integral: flota, clientes, rentas,\n"
    "reservas, finanzas, taller y mas."
)
_BUILD_INFO = "Build 2026.05.25 - Python 3.12 - PySide6"


def _get_db_info() -> str:
    """Retorna un resumen de la conexion actual a base de datos."""
    if DB_ENGINE == "mysql":
        cfg = DB_MYSQL
        host = cfg.get("host", "localhost")
        port = cfg.get("port", 3306)
        name = cfg.get("database", "dinamo_rent")
        user = cfg.get("user", "root")
        return f"MySQL - {host}:{port}/{name} ({user})"
    return "SQLite - Base local"


class AboutDialog(QDialog):
    """Dialogo informativo del sistema.

    Muestra version, descripcion, informacion de base de datos
    y creditos del sistema.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Acerca de - {APP_NAME}")
        self.setFixedSize(460, 520)
        self.setWindowFlags(
            Qt.WindowType.Dialog
            | Qt.WindowType.WindowCloseButtonHint
            | Qt.WindowType.WindowTitleHint
        )

        if parent:
            self._centrar(parent)

        self._setup_ui()

    def _centrar(self, parent):
        """Centra el dialogo sobre el widget padre."""
        try:
            parent_geo = parent.geometry()
            self.move(
                parent_geo.center().x() - self.width() // 2,
                parent_geo.center().y() - self.height() // 2,
            )
        except (RuntimeError, AttributeError):
            geo = QApplication.primaryScreen().availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #ffffff, stop:1 #f8faff);
                border-radius: 16px;
                border: 1px solid #e0e0e0;
            }
        """)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(32, 36, 32, 28)
        card_lay.setSpacing(12)

        # Logo icono
        lbl_logo = QLabel()
        lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._cargar_logo(lbl_logo)
        lbl_logo.setFixedHeight(90)
        card_lay.addWidget(lbl_logo)

        # Nombre de la app
        lbl_app = QLabel(APP_NAME)
        lbl_app.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_app.setStyleSheet(
            "font-size: 24px; font-weight: 800; color: #1a3558;"
            " letter-spacing: 0.5px;"
        )
        card_lay.addWidget(lbl_app)

        # Descripcion
        lbl_desc = QLabel(_DESCRIPTION)
        lbl_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_desc.setWordWrap(True)
        lbl_desc.setStyleSheet(
            "font-size: 11px; color: #64748b; line-height: 1.5;"
        )
        card_lay.addWidget(lbl_desc)

        # Separador
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.HLine)
        sep1.setStyleSheet(
            "QFrame { background: #e2e8f0; max-height: 1px; border: none;"
            " margin: 4px 0; }"
        )
        card_lay.addWidget(sep1)

        # Grid informativo
        info_items = [
            ("Version", f"v{APP_VERSION}"),
            ("Modo", "Produccion" if PRODUCTION_MODE else "Desarrollo"),
            ("Base de Datos", _get_db_info()),
            ("Autor", APP_AUTHOR),
        ]

        for label, value in info_items:
            row = QHBoxLayout()
            row.setSpacing(8)
            lbl_k = QLabel(label)
            lbl_k.setStyleSheet(
                "font-size: 11px; font-weight: 700; color: #475569;"
                " min-width: 100px;"
            )
            lbl_v = QLabel(value)
            lbl_v.setStyleSheet(
                "font-size: 11px; color: #1e293b; font-weight: 500;"
            )
            lbl_v.setWordWrap(True)
            row.addWidget(lbl_k)
            row.addWidget(lbl_v, stretch=1)
            card_lay.addLayout(row)

        # Separador
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(
            "QFrame { background: #e2e8f0; max-height: 1px; border: none;"
            " margin: 4px 0; }"
        )
        card_lay.addWidget(sep2)

        # Build info
        lbl_build = QLabel(_BUILD_INFO)
        lbl_build.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_build.setStyleSheet("font-size: 10px; color: #94a3b8;")
        card_lay.addWidget(lbl_build)

        # Copyright
        lbl_copy = QLabel(_COPYRIGHT)
        lbl_copy.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_copy.setStyleSheet("font-size: 10px; color: #94a3b8;")
        card_lay.addWidget(lbl_copy)

        # Boton cerrar
        card_lay.addSpacing(8)
        btn_ok = QPushButton("Aceptar")
        btn_ok.setFixedHeight(38)
        btn_ok.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ok.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #1a3558, stop:1 #0d3c7a);
                color: white;
                font-weight: 700;
                font-size: 12px;
                border: none;
                border-radius: 8px;
                padding: 8px 0;
            }
            QPushButton:hover {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #0d3c7a, stop:1 #092a54);
            }
            QPushButton:pressed {
                background: #061f3d;
            }
        """)
        btn_ok.clicked.connect(self.accept)
        card_lay.addWidget(btn_ok)

        main_layout.addWidget(card)

    @staticmethod
    def _cargar_logo(lbl_logo: QLabel) -> None:
        """Carga el logo desde assets, con fallback a emoji."""
        candidates = [
            str(ASSETS_DIR / "LogoDinamo.png"),
            str(ASSETS_DIR / "Logo_Dinamo.png"),
        ]
        path = ""
        for c in candidates:
            if os.path.exists(c):
                path = c
                break

        try:
            if path:
                pix = QPixmap(path).scaled(
                    80, 80,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                lbl_logo.setPixmap(pix)
            else:
                lbl_logo.setText("🚗")
                lbl_logo.setStyleSheet("font-size: 48px;")
        except Exception as e:
            log.warning("No se pudo cargar el logo: %s", e)
            lbl_logo.setText("🚗")
            lbl_logo.setStyleSheet("font-size: 48px;")
