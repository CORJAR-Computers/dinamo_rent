from views.components import ModernMessageBox

"""
views/alertas_view.py — Centro de Notificaciones y Alertas
Estilos via QSS class-based (themes.py).
"""
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QVBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QTabWidget,
    QAbstractItemView,
    QWidget,
)
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_PELIGRO, COLOR_ALERTA
from services.alerta_service import AlertaService
from core.utils import abrir_whatsapp
from views.base_widget import BaseWidget


# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
# ── Paleta centralizada (CODE-02) ───────────────────────────────────


class AlertasWidget(BaseWidget):
    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self._setup_ui()
        self._init_loading_overlay("Cargando alertas...")
        QTimer.singleShot(0, lambda: self._deferred_call(self.cargar_alertas))

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            "🔔",
            "Centro de Alertas y Notificaciones",
            "Control de vencimientos y recordatorios",
            self.cargar_alertas,
        )
        main_layout.addWidget(banner)

        content = QWidget()

        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        self.tabs = QTabWidget()
        self.tab_clientes = QTableWidget()  # simplified
        self.tab_internas = QTableWidget()
        self.tabs.addTab(QWidget(), "Enviar a Clientes (WhatsApp)")
        self.tabs.addTab(QWidget(), "Alertas del Sistema (Internas)")
        c_lay.addWidget(self.tabs)

        # Tab Clientes
        lay_cli = QVBoxLayout(self.tabs.widget(0))
        self.tbl_cli = QTableWidget()
        self.tbl_cli.setColumnCount(4)
        self.tbl_cli.setHorizontalHeaderLabels(
            ["Cliente", "Vehiculo / Alerta", "Vencimiento", "Accion"]
        )
        self.tbl_cli.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cli.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_cli.verticalHeader().setVisible(False)
        self.tbl_cli.setAlternatingRowColors(True)
        lay_cli.addWidget(self.tbl_cli)

        # Tab Internas
        lay_int = QVBoxLayout(self.tabs.widget(1))
        self.tbl_int = QTableWidget()
        self.tbl_int.setColumnCount(3)
        self.tbl_int.setHorizontalHeaderLabels(
            ["Nivel de Urgencia", "Asunto", "Descripcion Detallada"]
        )
        self.tbl_int.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_int.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_int.verticalHeader().setVisible(False)
        self.tbl_int.setAlternatingRowColors(True)
        lay_int.addWidget(self.tbl_int)

    def cargar_alertas(self):
        self.tbl_cli.setRowCount(0)
        self.tbl_int.setRowCount(0)
        try:
            alertas = AlertaService.obtener_todas_las_alertas()
            for i, a in enumerate(alertas["clientes"]):
                self.tbl_cli.insertRow(i)
                self.tbl_cli.setItem(i, 0, QTableWidgetItem(a["cliente"]))
                self.tbl_cli.setItem(i, 1, QTableWidgetItem(a["titulo"]))
                fecha_val = a["fecha"]
                it_fecha = QTableWidgetItem(str(fecha_val) if fecha_val else "")
                fnt = QFont(it_fecha.font())
                fnt.setBold(True)
                it_fecha.setFont(fnt)
                self.tbl_cli.setItem(i, 2, it_fecha)
                btn_wa = QPushButton("Enviar WhatsApp")
                btn_wa.setProperty("class", "success")
                btn_wa.clicked.connect(
                    lambda checked=False, cel=a["celular"], msg=a["mensaje_whatsapp"]: (
                        self._enviar_wa(cel, msg)
                    )
                )
                self.tbl_cli.setCellWidget(i, 3, btn_wa)

            for i, a in enumerate(alertas["internas"]):
                self.tbl_int.insertRow(i)
                it_nivel = QTableWidgetItem(a["nivel"])
                fnt = QFont(it_nivel.font())
                fnt.setBold(True)
                it_nivel.setFont(fnt)
                if a["nivel"] == "Critico":
                    it_nivel.setForeground(QBrush(QColor(COLOR_PELIGRO)))
                else:
                    it_nivel.setForeground(QBrush(QColor(COLOR_ALERTA)))
                self.tbl_int.setItem(i, 0, it_nivel)
                self.tbl_int.setItem(i, 1, QTableWidgetItem(a["titulo"]))
                self.tbl_int.setItem(i, 2, QTableWidgetItem(a["descripcion"]))

            self.tabs.setTabText(0, f"Enviar a Clientes ({len(alertas['clientes'])})")
            self.tabs.setTabText(1, f"Alertas del Sistema ({len(alertas['internas'])})")
        except Exception as e:
            ModernMessageBox.warning(self, "Error", f"No se pudieron cargar las alertas:\n{e}")

    def _enviar_wa(self, celular: str, mensaje: str):
        if not celular or celular.strip() == "":
            ModernMessageBox.warning(
                self, "Sin Celular", "El cliente no tiene un numero de celular registrado."
            )
            return
        exito = abrir_whatsapp(celular, mensaje)
        if not exito:
            ModernMessageBox.warning(self, "Error", "No se pudo abrir WhatsApp.")
