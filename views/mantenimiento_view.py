"""
views/mantenimiento_view.py — Vista refactorizada para el Taller y Mantenimiento.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QDialog, QFormLayout,
    QComboBox, QMessageBox, QDateEdit, QGroupBox, QDoubleSpinBox,
    QTextEdit, QSpinBox, QAbstractItemView
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QFont

# IMPORTACIONES A LA CAPA DE SERVICIOS
from services.services import AutoService
from services.services_extra import MantenimientoService
from core.exceptions import DinamoBaseError

# =============================================================================
# DIÁLOGO REGISTRO DE MANTENIMIENTO
# =============================================================================
class NuevoMantenimientoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Mantenimiento / Taller")
        self.setFixedSize(500, 600)
        self.datos_auto = None

        self._setup_ui()
        self.cargar_autos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. SELECCIÓN DE VEHÍCULO
        group_veh = QGroupBox("1. Vehículo")
        lay_veh = QFormLayout()

        self.cmb_placa = QComboBox()
        self.cmb_placa.setEditable(True)
        self.cmb_placa.currentIndexChanged.connect(self.cargar_datos_auto)

        self.lbl_info_auto = QLabel("Seleccione un vehículo...")
        self.lbl_info_auto.setStyleSheet("color: gray; font-style: italic;")

        lay_veh.addRow("Placa:", self.cmb_placa)
        lay_veh.addRow(self.lbl_info_auto)
        group_veh.setLayout(lay_veh)
        layout.addWidget(group_veh)

        # 2. DETALLES DEL SERVICIO
        group_srv = QGroupBox("2. Servicio Realizado")
        lay_srv = QFormLayout()

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems([
            "Cambio Aceite", "Frenos", "Llantas", "Batería",
            "Tecno-Mecánica", "Lavado General", "Reparación Mecánica", "Otro"
        ])

        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setCalendarPopup(True)

        self.spin_costo = QDoubleSpinBox()
        self.spin_costo.setRange(0, 100000000)
        self.spin_costo.setPrefix("$ ")

        self.spin_km_actual = QSpinBox()
        self.spin_km_actual.setRange(0, 999999)
        self.spin_km_actual.setSuffix(" km")

        lay_srv.addRow("Tipo Servicio:", self.cmb_tipo)
        lay_srv.addRow("Fecha Realización:", self.date_fecha)
        lay_srv.addRow("Costo Total:", self.spin_costo)
        lay_srv.addRow("Kilometraje Actual:", self.spin_km_actual)
        group_srv.setLayout(lay_srv)
        layout.addWidget(group_srv)

        # 3. PROYECCIÓN Y NOTAS
        group_proy = QGroupBox("3. Próximo Servicio (Alerta)")
        lay_proy = QFormLayout()

        self.spin_prox_km = QSpinBox()
        self.spin_prox_km.setRange(0, 999999)
        self.spin_prox_km.setSuffix(" km")
        self.spin_prox_km.setSpecialValueText("Opcional")

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)

        self.chk_cambiar_estado = QComboBox()
        self.chk_cambiar_estado.addItems(["Mantener Estado Actual", "Poner en Mantenimiento", "Poner Disponible"])

        lay_proy.addRow("Próximo Cambio (Km):", self.spin_prox_km)
        lay_proy.addRow("Observaciones:", self.txt_obs)
        lay_proy.addRow("Estado del Auto:", self.chk_cambiar_estado)
        group_proy.setLayout(lay_proy)
        layout.addWidget(group_proy)

        # BOTONES
        btn_box = QHBoxLayout()
        btn_save = QPushButton("Registrar")
        btn_save.setStyleSheet("background-color: #004aad; color: white; padding: 10px; font-weight: bold;")
        btn_save.clicked.connect(self.guardar)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def cargar_autos(self):
        self.cmb_placa.clear()
        self.cmb_placa.addItem("Buscar...", None)
        try:
            autos = AutoService.listar()
            for a in autos:
                self.cmb_placa.addItem(f"{a['placa']} - {a['marca']}", userData=a)
        except DinamoBaseError as e:
            self.lbl_info_auto.setText("Error cargando vehículos")

    def cargar_datos_auto(self):
        idx = self.cmb_placa.currentIndex()
        if idx > 0:
            data = self.cmb_placa.itemData(idx)
            if data:
                self.datos_auto = data
                km = float(data.get('kilometraje', 0) or 0)

                self.lbl_info_auto.setText(f"{data.get('marca', '')} {data.get('modelo', '')} | Estado: {data.get('estado', '')}")
                self.spin_km_actual.setValue(int(km))

                # Sugerencia automática
                self.spin_prox_km.setValue(int(km) + 5000)
        else:
            self.lbl_info_auto.setText("Seleccione un vehículo...")
            self.datos_auto = None

    def guardar(self):
        if not self.datos_auto:
            return QMessageBox.warning(self, "Error", "Seleccione un vehículo")

        estado_combo = self.chk_cambiar_estado.currentText()
        accion_estado = "mantener"
        if estado_combo == "Poner en Mantenimiento":
            accion_estado = "mantenimiento"
        elif estado_combo == "Poner Disponible":
            accion_estado = "disponible"

        datos = {
            "placa": self.datos_auto['placa'],
            "tipo": self.cmb_tipo.currentText(),
            "fecha": self.date_fecha.date().toString("yyyy-MM-dd"),
            "costo": self.spin_costo.value(),
            "km_actual": self.spin_km_actual.value(),
            "prox_km": self.spin_prox_km.value(),
            "obs": self.txt_obs.toPlainText(),
            "accion_estado": accion_estado
        }

        try:
            MantenimientoService.registrar(datos)
            QMessageBox.information(self, "Éxito", "Mantenimiento registrado y vehículo actualizado.")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL DE MANTENIMIENTO
# =============================================================================
class MantenimientoWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        # Header
        top = QHBoxLayout()
        lbl = QLabel("Taller y Mantenimiento")
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")

        btn_new = QPushButton("+ Registrar Servicio")
        btn_new.setStyleSheet("background-color: orange; color: black; font-weight: bold; padding: 8px;")
        btn_new.clicked.connect(self.nuevo_servicio)

        btn_ref = QPushButton("Actualizar")
        btn_ref.clicked.connect(self.cargar_historial)

        top.addWidget(lbl)
        top.addStretch()
        top.addWidget(btn_ref)
        top.addWidget(btn_new)
        layout.addLayout(top)

        # Tabla Historial
        self.tabla = QTableWidget()
        self.configurar_tabla()
        layout.addWidget(self.tabla)

        self.cargar_historial()

    def configurar_tabla(self):
        cols = ["Fecha", "Placa", "Tipo Servicio", "Costo", "Observaciones"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)

    def cargar_historial(self):
        self.tabla.setRowCount(0)
        try:
            historial = MantenimientoService.listar_historial(50)
            for i, r in enumerate(historial):
                self.tabla.insertRow(i)
                self.tabla.setItem(i, 0, QTableWidgetItem(str(r.get('pieza_varias_fecha', ''))))
                self.tabla.setItem(i, 1, QTableWidgetItem(str(r.get('placa', ''))))

                item_tipo = QTableWidgetItem(str(r.get('pieza_varias_tipo', '')))
                font = self.font()
                font.setBold(True)
                item_tipo.setFont(font)
                self.tabla.setItem(i, 2, item_tipo)

                costo = float(r.get('total_mantenimiento', 0) or 0)
                self.tabla.setItem(i, 3, QTableWidgetItem(f"${costo:,.0f}"))
                self.tabla.setItem(i, 4, QTableWidgetItem(str(r.get('pieza_varias_obs', ''))))

        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", f"Error cargando historial: {e}")

    def nuevo_servicio(self):
        dlg = NuevoMantenimientoDialog(self)
        if dlg.exec():
            self.cargar_historial()