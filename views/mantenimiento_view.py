from views.components import ModernMessageBox
"""
views/mantenimiento_view.py — Vista para el Taller y Mantenimiento.

Mejoras UI/UX:
  - Hereda de BaseWidget
  - Sin estilos inline — todo por QSS (cssClass)
  - Sin emojis
  - Font bold corregido (QFont value-type)
  - Filas alternas en tabla
  - Mejor UX: info del auto con estilo consistente
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QDialog, QFormLayout,
    QComboBox, QDateEdit, QGroupBox, QDoubleSpinBox,
    QTextEdit, QSpinBox, QAbstractItemView, QWidget,
)
from PySide6.QtCore import QDate
from PySide6.QtGui import QFont

from services.auto_service import AutoService
from services.mantenimiento_service import MantenimientoService
from core.exceptions import DinamoBaseError
from views.base_widget import BaseWidget
from views.styles import btn_danger, btn_default, btn_primary, btn_warning, lbl_section, group_box, input_combo, input_date, input_spinbox, dialog_background, table_widget

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"


# =============================================================================
# DIALOGO REGISTRO DE MANTENIMIENTO
# =============================================================================
class NuevoMantenimientoDialog(QDialog):
    """Dialogo para registrar mantenimiento/taller."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Mantenimiento / Taller")
        self.setMinimumSize(500, 600)
        dialog_background(self)
        self.datos_auto = None

        self._setup_ui()
        self._cargar_autos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. Seleccion de vehiculo
        group_veh = QGroupBox("1. Vehiculo")
        group_box(group_veh)
        lay_veh = QFormLayout()

        self.cmb_placa = QComboBox()
        self.cmb_placa.setEditable(True)
        self.cmb_placa.currentIndexChanged.connect(self._cargar_datos_auto)

        self.lbl_info_auto = QLabel("Seleccione un vehiculo...")
        lbl_section(self.lbl_info_auto)

        lay_veh.addRow("Placa:", self.cmb_placa)
        lay_veh.addRow(self.lbl_info_auto)
        group_veh.setLayout(lay_veh)
        layout.addWidget(group_veh)

        # 2. Detalles del servicio
        group_srv = QGroupBox("2. Servicio Realizado")
        group_box(group_srv)
        lay_srv = QFormLayout()

        self.cmb_tipo = QComboBox(); input_combo(self.cmb_tipo)
        self.cmb_tipo.addItems([
            "Cambio Aceite", "Frenos", "Llantas", "Bateria",
            "Tecno-Mecanica", "Lavado General", "Reparacion Mecanica", "Otro",
        ])

        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setCalendarPopup(True)
        input_date(self.date_fecha)

        self.spin_costo = QDoubleSpinBox()
        self.spin_costo.setRange(0, 100_000_000)
        self.spin_costo.setPrefix("$ ")
        input_spinbox(self.spin_costo)

        self.spin_km_actual = QSpinBox()
        self.spin_km_actual.setRange(0, 999_999)
        self.spin_km_actual.setSuffix(" km")
        input_spinbox(self.spin_km_actual)

        lay_srv.addRow("Tipo Servicio:", self.cmb_tipo)
        lay_srv.addRow("Fecha Realizacion:", self.date_fecha)
        lay_srv.addRow("Costo Total:", self.spin_costo)
        lay_srv.addRow("Kilometraje Actual:", self.spin_km_actual)
        group_srv.setLayout(lay_srv)
        layout.addWidget(group_srv)

        # 3. Proyeccion y notas
        group_proy = QGroupBox("3. Proximo Servicio (Alerta)")
        group_box(group_proy)
        lay_proy = QFormLayout()

        self.spin_prox_km = QSpinBox()
        self.spin_prox_km.setRange(0, 999_999)
        self.spin_prox_km.setSuffix(" km")
        self.spin_prox_km.setSpecialValueText("Opcional")
        input_spinbox(self.spin_prox_km)

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)

        self.chk_cambiar_estado = QComboBox()
        self.chk_cambiar_estado.addItems([
            "Mantener Estado Actual",
            "Poner en Mantenimiento",
            "Poner Disponible",
        ])
        input_combo(self.chk_cambiar_estado)

        lay_proy.addRow("Proximo Cambio (Km):", self.spin_prox_km)
        lay_proy.addRow("Observaciones:", self.txt_obs)
        lay_proy.addRow("Estado del Auto:", self.chk_cambiar_estado)
        group_proy.setLayout(lay_proy)
        layout.addWidget(group_proy)

        # Botones
        btn_box = QHBoxLayout()

        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Registrar")
        btn_primary(btn_save)
        btn_save.clicked.connect(self._guardar)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        layout.addLayout(btn_box)

    def _cargar_autos(self):
        self.cmb_placa.clear()
        self.cmb_placa.addItem("Buscar...", None)
        try:
            autos = AutoService.listar()
            for a in autos:
                self.cmb_placa.addItem(f"{a['placa']} - {a['marca']}", userData=a)
        except DinamoBaseError:
            self.lbl_info_auto.setText("Error cargando vehiculos")

    def _cargar_datos_auto(self):
        idx = self.cmb_placa.currentIndex()
        if idx > 0:
            data = self.cmb_placa.itemData(idx)
            if data:
                self.datos_auto = data
                km = float(data.get("kilometraje", 0) or 0)

                self.lbl_info_auto.setText(
                    f"{data.get('marca', '')} {data.get('modelo', '')} "
                    f"| Estado: {data.get('estado', '')} "
                    f"| KM: {km:,.0f}"
                )
                self.spin_km_actual.setValue(int(km))
                self.spin_prox_km.setValue(int(km) + 5000)
        else:
            self.lbl_info_auto.setText("Seleccione un vehiculo...")
            self.datos_auto = None

    def _guardar(self):
        if not self.datos_auto:
            ModernMessageBox.warning(self, "Validacion", "Seleccione un vehiculo")
            return

        estado_combo = self.chk_cambiar_estado.currentText()
        accion_estado = "mantener"
        if estado_combo == "Poner en Mantenimiento":
            accion_estado = "mantenimiento"
        elif estado_combo == "Poner Disponible":
            accion_estado = "disponible"

        datos = {
            "placa": self.datos_auto["placa"],
            "tipo": self.cmb_tipo.currentText(),
            "fecha": self.date_fecha.date().toString("yyyy-MM-dd"),
            "costo": self.spin_costo.value(),
            "km_actual": self.spin_km_actual.value(),
            "prox_km": self.spin_prox_km.value(),
            "obs": self.txt_obs.toPlainText(),
            "accion_estado": accion_estado,
        }

        try:
            MantenimientoService.registrar(datos)
            ModernMessageBox.success(
                self, "Exito",
                "Mantenimiento registrado y vehiculo actualizado."
            )
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL DE MANTENIMIENTO
# =============================================================================
class MantenimientoWidget(BaseWidget):
    """Panel de Taller y Mantenimiento."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner
        banner = create_banner("🛠️", "Taller y Mantenimiento", "Registro de mantenimientos y servicios de taller", self.cargar_historial)
        main_layout.addWidget(banner)

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        # ── Acciones ──
        top = QHBoxLayout()
        top.addStretch()

        btn_ref = QPushButton("Actualizar")
        btn_default(btn_ref)
        btn_ref.clicked.connect(self.cargar_historial)
        top.addWidget(btn_ref)

        btn_new = QPushButton("+ Registrar Servicio")
        btn_warning(btn_new)
        btn_new.clicked.connect(self._nuevo_servicio)
        top.addWidget(btn_new)

        c_lay.addLayout(top)

        # ── Tabla ──
        self.tabla = QTableWidget()
        table_widget(self.tabla)
        self._configurar_tabla()
        c_lay.addWidget(self.tabla)

        self.cargar_historial()

    def _configurar_tabla(self):
        cols = ["Fecha", "Placa", "Tipo Servicio", "Costo", "Observaciones"]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_historial(self):
        self.tabla.setRowCount(0)
        try:
            historial = MantenimientoService.listar_historial(50)
            for i, r in enumerate(historial):
                self.tabla.insertRow(i)

                self.tabla.setItem(
                    i, 0, QTableWidgetItem(str(r.get("pieza_varias_fecha", "")))
                )
                self.tabla.setItem(
                    i, 1, QTableWidgetItem(str(r.get("placa", "")))
                )

                item_tipo = QTableWidgetItem(str(r.get("pieza_varias_tipo", "")))
                fnt = QFont(item_tipo.font())
                fnt.setBold(True)
                item_tipo.setFont(fnt)
                self.tabla.setItem(i, 2, item_tipo)

                costo = float(r.get("total_mantenimiento", 0) or 0)
                self.tabla.setItem(i, 3, QTableWidgetItem(f"${costo:,.0f}"))
                self.tabla.setItem(
                    i, 4, QTableWidgetItem(str(r.get("pieza_varias_obs", "")))
                )

        except DinamoBaseError as e:
            self.mostrar_error(f"Error cargando historial:\n{e}")

    # ── Acciones ───────────────────────────────────────────────

    def _nuevo_servicio(self):
        dlg = NuevoMantenimientoDialog(self)
        if dlg.exec():
            self.cargar_historial()
