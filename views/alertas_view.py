"""
views/alertas_view.py — Centro de Notificaciones y Alertas del Sistema.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QTabWidget, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

from services.services_extra import AlertaService
from core.utils import abrir_whatsapp


class AlertasWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.cargar_alertas()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header
        top = QHBoxLayout()
        lbl = QLabel("🔔 Centro de Alertas y Notificaciones")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")

        btn_ref = QPushButton("Actualizar Alertas")
        btn_ref.setProperty("cssClass", "primary")
        btn_ref.clicked.connect(self.cargar_alertas)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(btn_ref)
        layout.addLayout(top)

        # Tabs (Pestañas)
        self.tabs = QTabWidget()
        self.tab_clientes = QWidget()
        self.tab_internas = QWidget()

        self.tabs.addTab(self.tab_clientes, "📲 Enviar a Clientes (WhatsApp)")
        self.tabs.addTab(self.tab_internas, "⚠️ Alertas del Sistema (Internas)")
        layout.addWidget(self.tabs)

        # --- Setup Pestaña Clientes ---
        lay_cli = QVBoxLayout(self.tab_clientes)
        self.tbl_cli = QTableWidget()
        self.tbl_cli.setColumnCount(4)
        self.tbl_cli.setHorizontalHeaderLabels(["Cliente", "Vehículo / Alerta", "Vencimiento", "Acción"])
        self.tbl_cli.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_cli.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_cli.verticalHeader().setVisible(False)
        lay_cli.addWidget(self.tbl_cli)

        # --- Setup Pestaña Internas ---
        lay_int = QVBoxLayout(self.tab_internas)
        self.tbl_int = QTableWidget()
        self.tbl_int.setColumnCount(3)
        self.tbl_int.setHorizontalHeaderLabels(["Nivel de Urgencia", "Asunto", "Descripción Detallada"])
        self.tbl_int.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl_int.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_int.verticalHeader().setVisible(False)
        lay_int.addWidget(self.tbl_int)

    def cargar_alertas(self):
        self.tbl_cli.setRowCount(0)
        self.tbl_int.setRowCount(0)

        try:
            alertas = AlertaService.obtener_todas_las_alertas()

            # 1. Llenar tabla de Clientes
            for i, a in enumerate(alertas["clientes"]):
                self.tbl_cli.insertRow(i)
                self.tbl_cli.setItem(i, 0, QTableWidgetItem(a["cliente"]))
                self.tbl_cli.setItem(i, 1, QTableWidgetItem(a["titulo"]))

                # Resaltar fecha
                it_fecha = QTableWidgetItem(a["fecha"])
                it_fecha.setFont(self.font())
                it_fecha.font().setBold(True)
                self.tbl_cli.setItem(i, 2, it_fecha)

                # Botón de WhatsApp
                btn_wa = QPushButton("Enviar WhatsApp")
                btn_wa.setProperty("cssClass", "success")  # Usa el botón verde de tu CSS
                # Truco de Python (lambda con parámetros por defecto) para que el botón sepa a quién enviar
                btn_wa.clicked.connect(
                    lambda checked=False, cel=a["celular"], msg=a["mensaje_whatsapp"]: self.enviar_wa(cel, msg))
                self.tbl_cli.setCellWidget(i, 3, btn_wa)

            # 2. Llenar tabla de Alertas Internas
            for i, a in enumerate(alertas["internas"]):
                self.tbl_int.insertRow(i)

                it_nivel = QTableWidgetItem(a["nivel"])
                it_nivel.setFont(self.font())
                it_nivel.font().setBold(True)
                if a["nivel"] == "Crítico":
                    it_nivel.setForeground(QBrush(QColor("#c62828")))  # Rojo
                else:
                    it_nivel.setForeground(QBrush(QColor("#ef6c00")))  # Naranja

                self.tbl_int.setItem(i, 0, it_nivel)
                self.tbl_int.setItem(i, 1, QTableWidgetItem(a["titulo"]))
                self.tbl_int.setItem(i, 2, QTableWidgetItem(a["descripcion"]))

            # Modificar texto de las pestañas para mostrar el contador de notificaciones
            self.tabs.setTabText(0, f"📲 Enviar a Clientes ({len(alertas['clientes'])})")
            self.tabs.setTabText(1, f"⚠️ Alertas del Sistema ({len(alertas['internas'])})")

        except Exception as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las alertas: {e}")

    def enviar_wa(self, celular, mensaje):
        if not celular or celular.strip() == "":
            QMessageBox.warning(self, "Sin Celular", "El cliente no tiene un número de celular registrado.")
            return

        exito = abrir_whatsapp(celular, mensaje)
        if not exito:
            QMessageBox.warning(self, "Error", "No se pudo abrir WhatsApp. Verifica la función en utils.py.")