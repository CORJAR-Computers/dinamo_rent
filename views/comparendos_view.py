"""
views/comparendos_view.py — Vista para la gestión de Multas y Comparendos.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QDialog, QFormLayout,
    QComboBox, QMessageBox, QDateEdit, QTimeEdit, QGroupBox, QDoubleSpinBox,
    QTextEdit, QAbstractItemView, QMenu
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor, QBrush, QAction, QCursor

from services.services import AutoService
from services.services_extra import ComparendoService
from core.exceptions import DinamoBaseError


# =============================================================================
# DIÁLOGO NUEVO COMPARENDO
# =============================================================================
class NuevoComparendoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Foto-Multa / Comparendo")
        self.setFixedSize(450, 500)
        self._setup_ui()
        self.cargar_autos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        form_layout = QFormLayout()

        self.cmb_placa = QComboBox()
        self.cmb_placa.setEditable(True)

        self.d_fecha = QDateEdit(QDate.currentDate())
        self.d_fecha.setCalendarPopup(True)

        self.t_hora = QTimeEdit(QTime.currentTime())

        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(0, 100000000)
        self.sp_monto.setPrefix("$ ")

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(80)
        self.txt_obs.setPlaceholderText("Lugar de la infracción, código, etc...")

        form_layout.addRow("Placa del Vehículo:", self.cmb_placa)
        form_layout.addRow("Fecha Infracción:", self.d_fecha)
        form_layout.addRow("Hora Infracción:", self.t_hora)
        form_layout.addRow("Monto de Multa:", self.sp_monto)
        form_layout.addRow("Observaciones:", self.txt_obs)

        gb = QGroupBox("Datos de la Infracción")
        gb.setLayout(form_layout)
        layout.addWidget(gb)

        # Botones
        h_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Registrar y Buscar Culpable 🔍")
        btn_save.setProperty("cssClass", "primary")
        btn_save.clicked.connect(self.guardar)

        h_btn.addStretch()
        h_btn.addWidget(btn_cancel)
        h_btn.addWidget(btn_save)
        layout.addLayout(h_btn)

    def cargar_autos(self):
        self.cmb_placa.addItem("Seleccione placa...", None)
        try:
            autos = AutoService.listar()
            for a in autos:
                self.cmb_placa.addItem(f"{a['placa']} - {a['marca']}", userData=a['placa'])
        except Exception:
            pass

    def guardar(self):
        placa = self.cmb_placa.currentData()
        if not placa:
            return QMessageBox.warning(self, "Error", "Debe seleccionar un vehículo.")

        datos = {
            "placa": placa,
            "fecha": self.d_fecha.date().toString("yyyy-MM-dd"),
            "hora": self.t_hora.time().toString("HH:mm"),
            "monto": self.sp_monto.value(),
            "observaciones": self.txt_obs.toPlainText()
        }

        try:
            resultado = ComparendoService.registrar(datos)

            # Mostrar la magia al usuario
            if resultado["vinculado"]:
                mensaje = (
                    "✅ ¡Comparendo Registrado!\n\n"
                    "El sistema detectó automáticamente que el vehículo estaba "
                    f"rentado (Renta #{resultado['id_renta']}).\n"
                    "La multa ha sido vinculada al cliente correspondiente."
                )
                QMessageBox.information(self, "Cliente Encontrado", mensaje)
            else:
                mensaje = (
                    "⚠️ Comparendo Registrado.\n\n"
                    "El sistema NO encontró ninguna renta activa para esa fecha y hora. "
                    "El comparendo quedó sin cliente asignado."
                )
                QMessageBox.warning(self, "Sin Asignar", mensaje)

            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL
# =============================================================================
class ComparendosWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        lbl = QLabel("Control de Comparendos y Fotomultas")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")

        btn_new = QPushButton("+ Registrar Multa")
        btn_new.setProperty("cssClass", "warning")
        btn_new.clicked.connect(self.nuevo)

        btn_ref = QPushButton("Actualizar")
        btn_ref.clicked.connect(self.cargar_datos)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(btn_ref)
        top.addWidget(btn_new)
        layout.addLayout(top)

        self.tbl = QTableWidget()
        self.configurar_tabla()
        layout.addWidget(self.tbl)

        self.cargar_datos()

    def configurar_tabla(self):
        cols = ["ID", "Fecha/Hora", "Placa", "Monto", "Cliente Responsable", "Estado"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self.mostrar_menu)

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        try:
            multas = ComparendoService.listar()
            for i, c in enumerate(multas):
                self.tbl.insertRow(i)

                fecha_hora = f"{c.get('fecha_infraccion', '')} {c.get('hora_infraccion', '')}"
                cliente = c.get('cliente_nombre') or "SIN ASIGNAR (Empresa)"
                monto = float(c.get('monto', 0))
                estado = c.get('estado', 'Pendiente')

                self.tbl.setItem(i, 0, QTableWidgetItem(str(c.get('id'))))
                self.tbl.setItem(i, 1, QTableWidgetItem(fecha_hora))
                self.tbl.setItem(i, 2, QTableWidgetItem(str(c.get('placa'))))
                self.tbl.setItem(i, 3, QTableWidgetItem(f"$ {monto:,.0f}"))

                it_cli = QTableWidgetItem(cliente)
                if not c.get('cliente_nombre'):
                    it_cli.setForeground(QBrush(QColor("gray")))
                self.tbl.setItem(i, 4, it_cli)

                it_est = QTableWidgetItem(estado)
                if estado == 'Pendiente':
                    it_est.setForeground(QBrush(QColor("red")))
                elif estado == 'Pagado':
                    it_est.setForeground(QBrush(QColor("green")))
                self.tbl.setItem(i, 5, it_est)

        except DinamoBaseError as e:
            pass

    def nuevo(self):
        if NuevoComparendoDialog(self).exec():
            self.cargar_datos()

    def mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item: return
        row = item.row()
        id_comp = int(self.tbl.item(row, 0).text())

        menu = QMenu(self)
        ac_pagar = QAction("✅ Marcar como Pagado", self)
        ac_pagar.triggered.connect(lambda: self.cambiar_estado(id_comp, "Pagado"))

        ac_apelar = QAction("⚖️ Marcar como Apelado", self)
        ac_apelar.triggered.connect(lambda: self.cambiar_estado(id_comp, "Apelado"))

        menu.addAction(ac_pagar)
        menu.addAction(ac_apelar)
        menu.exec(QCursor.pos())

    def cambiar_estado(self, id_comp, estado):
        try:
            ComparendoService.cambiar_estado(id_comp, estado)
            self.cargar_datos()
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", str(e))