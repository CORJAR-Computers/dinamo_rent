from views.components import ModernMessageBox
"""
views/rentas_view.py — Vista refactorizada para gestión de rentas.
F1E: Estilos migrados a QSS global (assets/styles.qss).
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox,
    QPlainTextEdit, QFrame, QAbstractItemView, QGridLayout, QTimeEdit, QMenu, QCheckBox, QTextEdit, QMessageBox
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QCursor

from core.config import NIVEL_TANQUE
from services.renta_service import RentaService
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.dashboard_service import DashboardService
from services.inspeccion_service import InspeccionService
from core.exceptions import DinamoBaseError
from views.styles import (
    btn_danger, btn_primary, btn_success, btn_default, frame_summary, input_field, input_combo,
    input_spinbox, input_date, group_box, dialog_background, table_widget, input_textedit,
    lbl_total_renta, lbl_extra_info, lbl_new_total_extension, view_background, input_time
)
from core import utils


from views.pagos_view import PagosDialog

class _MsgBoxWrapper:
    def __init__(self, fn, parent, title, message):
        self.fn = fn
        self.parent = parent
        self.title = title
        self.message = message
    def exec(self):
        return self.fn(self.parent, self.title, self.message)

def _msg_box(icon, title, message, parent=None):
    if icon == QMessageBox.Icon.Warning:
        return _MsgBoxWrapper(ModernMessageBox.warning, parent, title, message)
    elif icon == QMessageBox.Icon.Critical:
        return _MsgBoxWrapper(ModernMessageBox.error, parent, title, message)
    elif icon == QMessageBox.Icon.Question:
        return _MsgBoxWrapper(ModernMessageBox.question, parent, title, message)
    else:
        return _MsgBoxWrapper(ModernMessageBox.success, parent, title, message)

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"

# Constants for UI elements
_DIALOG_MIN_WIDTH = 600
_DIALOG_MIN_HEIGHT = 450
_BUTTON_FIXED_WIDTH = 80
_MESSAGE_BOX_FIXED_WIDTH = 320
_MESSAGE_BOX_FIXED_HEIGHT = 160
_RENTAS_WIDGET_BANNER_HEIGHT = 64
_RENTAS_WIDGET_BANNER_MARGINS = (22, 0, 22, 0)
_RENTAS_WIDGET_BANNER_SPACING = 14
_RENTAS_WIDGET_ICO_SIZE = 40
_RENTAS_WIDGET_CONTENT_MARGINS = (20, 16, 20, 16)
_RENTAS_WIDGET_CONTENT_SPACING = 14
_TEXT_EDIT_MAX_HEIGHT = 60



class UpperLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.to_upper)

    def to_upper(self, text):
        if not text.isupper():
            self.setText(text.upper())


# =============================================================================
# DIÁLOGOS DE CLIENTE
# =============================================================================
class DialogoSelectorCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Cliente")
        self.setMinimumSize(_DIALOG_MIN_WIDTH, _DIALOG_MIN_HEIGHT)
        self.cliente_seleccionado = None

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.txt = UpperLineEdit()
        self.txt.setPlaceholderText("BUSCAR POR NOMBRE O DOC...")
        self.txt.textChanged.connect(self.buscar)

        btn = QPushButton("+ NUEVO")
        btn_success(btn)
        btn.clicked.connect(self.nuevo)

        top.addWidget(self.txt)
        top.addWidget(btn)
        layout.addLayout(top)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["ID", "Doc", "Nombre"])
        self.tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.cellDoubleClicked.connect(self.sel)
        layout.addWidget(self.tbl)
        self.buscar()

    def buscar(self):
        try:
            res = ClienteService.buscar(self.txt.text())
        except DinamoBaseError:
            res = []

        self.tbl.setRowCount(0)
        self.data_temp = res
        for i, d in enumerate(res):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(d.get('id', ''))))
            self.tbl.setItem(i, 1, QTableWidgetItem(d.get('no_doc', '')))
            nom = (d.get('nombre_completo')
                   or f"{d.get('nombres', '')} {d.get('apellidos', '')}")
            self.tbl.setItem(i, 2, QTableWidgetItem(nom))

    def sel(self, r, c):
        if 0 <= r < len(self.data_temp):
            self.cliente_seleccionado = self.data_temp[r]
            self.accept()

    def nuevo(self):
        from views.clientes_view import ClienteFormDialog
        dlg = ClienteFormDialog(self)
        if (dlg.exec() and hasattr(dlg, 'datos_cliente')
                and dlg.datos_cliente.get('id')):
            self.cliente_seleccionado = dlg.datos_cliente
            self.accept()


# =============================================================================
# NUEVA RENTA
# =============================================================================
class NuevaRentaDialog(QDialog):
    def __init__(self, parent=None, placa_preseleccionada=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Renta - Cálculo Inteligente")
        self.setMinimumSize(1000, 700)
        dialog_background(self)

        self.cliente_id = None
        self.cliente_lic = ""
        self.cliente_nac = ""
        self._updating = False

        self._setup_ui()
        self.cargar_autos(placa_preseleccionada)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── CLIENTE Y AUTO ───────────────────────────────────────────
        gb_info = QGroupBox("Datos Principales")
        group_box(gb_info)
        l_info = QHBoxLayout()
        self.txt_cli = QLineEdit()
        self.txt_cli.setReadOnly(True)
        self.txt_cli.setPlaceholderText("Seleccionar Cliente...")
        input_field(self.txt_cli)
        btn_cli = QPushButton("Buscar")
        btn_primary(btn_cli)
        btn_cli.setFixedWidth(_BUTTON_FIXED_WIDTH)
        btn_cli.clicked.connect(self.sel_cli)
        self.cmb_auto = QComboBox()
        self.cmb_auto.setMinimumWidth(300)
        input_combo(self.cmb_auto)
        self.cmb_auto.currentIndexChanged.connect(self.act_auto)

        l_info.addWidget(QLabel("Cliente:"))
        l_info.addWidget(self.txt_cli)
        l_info.addWidget(btn_cli)
        l_info.addSpacing(20)
        l_info.addWidget(QLabel("Auto:"))
        l_info.addWidget(self.cmb_auto)
        gb_info.setLayout(l_info)
        layout.addWidget(gb_info)

        # ── TIEMPO ───────────────────────────────────────────────────
        gb_time = QGroupBox("Tiempo y Fechas")
        group_box(gb_time)
        l_time = QGridLayout()
        self.d_sal = QDateEdit(QDate.currentDate())
        self.d_sal.setCalendarPopup(True)
        input_date(self.d_sal)
        self.h_sal = QTimeEdit(QTime.currentTime())
        input_spinbox(self.h_sal)
        self.sp_dias = QDoubleSpinBox()
        self.sp_dias.setRange(1, 365)
        self.sp_dias.setValue(1)
        self.sp_dias.setSuffix(" días")
        input_spinbox(self.sp_dias)
        self.d_ret = QDateEdit(QDate.currentDate().addDays(1))
        self.d_ret.setCalendarPopup(True)
        input_date(self.d_ret)
        self.h_ret = QTimeEdit(QTime.currentTime())
        input_spinbox(self.h_ret)

        self.d_sal.dateChanged.connect(self.calc_fechas)
        self.h_sal.timeChanged.connect(self.calc_fechas)
        self.sp_dias.valueChanged.connect(self.calc_fechas)
        self.d_ret.dateChanged.connect(self.calc_dias)
        self.h_ret.timeChanged.connect(self.calc_dias)

        l_time.setColumnStretch(1, 1)
        l_time.setColumnStretch(4, 1)
        l_time.addWidget(QLabel("Salida:"), 0, 0)
        l_time.addWidget(self.d_sal, 0, 1)
        l_time.addWidget(self.h_sal, 0, 2)
        l_time.addWidget(QLabel("Duración:"), 0, 3)
        l_time.addWidget(self.sp_dias, 0, 4)
        l_time.addWidget(QLabel("Retorno:"), 1, 0)
        l_time.addWidget(self.d_ret, 1, 1)
        l_time.addWidget(self.h_ret, 1, 2)
        self.lbl_horas_extra = QLabel("Extras: 0h")
        lbl_extra_info(self.lbl_horas_extra)
        l_time.addWidget(self.lbl_horas_extra, 1, 4)
        gb_time.setLayout(l_time)
        layout.addWidget(gb_time)

        # ── COSTOS ───────────────────────────────────────────────────
        gb_costos = QGroupBox("Tarifas y Extras")
        group_box(gb_costos)
        l_costos = QGridLayout()
        self.sp_km = QDoubleSpinBox()
        self.sp_km.setRange(0, 1e7)
        self.sp_km.setPrefix("KM: ")
        input_spinbox(self.sp_km)
        self.cmb_tanque = QComboBox()
        self.cmb_tanque.addItems(NIVEL_TANQUE)
        input_combo(self.cmb_tanque)
        self.sp_val_dia = QDoubleSpinBox()
        self.sp_val_dia.setRange(0, 1e9)
        self.sp_val_dia.setPrefix("$ ")
        self.sp_val_dia.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_val_dia)
        self.sp_val_hora = QDoubleSpinBox()
        self.sp_val_hora.setRange(0, 1e9)
        self.sp_val_hora.setPrefix("$ H: ")
        self.sp_val_hora.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_val_hora)

        self.sp_lavado = QDoubleSpinBox()
        self.sp_lavado.setRange(0, 1e6)
        self.sp_lavado.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_lavado)
        self.sp_silla = QDoubleSpinBox()
        self.sp_silla.setRange(0, 1e6)
        self.sp_silla.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_silla)
        self.sp_cables = QDoubleSpinBox()
        self.sp_cables.setRange(0, 1e6)
        self.sp_cables.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_cables)
        self.sp_inversor = QDoubleSpinBox()
        self.sp_inversor.setRange(0, 1e6)
        self.sp_inversor.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_inversor)
        self.sp_domicilio = QDoubleSpinBox()
        self.sp_domicilio.setRange(0, 1e6)
        self.sp_domicilio.valueChanged.connect(self.calc_total)
        input_spinbox(self.sp_domicilio)

        l_costos.setColumnStretch(1, 1)
        l_costos.setColumnStretch(3, 1)
        l_costos.addWidget(QLabel("KM Salida:"), 0, 0)
        l_costos.addWidget(self.sp_km, 0, 1)
        l_costos.addWidget(QLabel("Tanque:"), 0, 2)
        l_costos.addWidget(self.cmb_tanque, 0, 3)
        l_costos.addWidget(QLabel("Valor Día:"), 1, 0)
        l_costos.addWidget(self.sp_val_dia, 1, 1)
        l_costos.addWidget(QLabel("V. Hora Extra:"), 1, 2)
        l_costos.addWidget(self.sp_val_hora, 1, 3)
        l_costos.addWidget(QLabel("Lavado:"), 2, 0)
        l_costos.addWidget(self.sp_lavado, 2, 1)
        l_costos.addWidget(QLabel("Silla bebé:"), 2, 2)
        l_costos.addWidget(self.sp_silla, 2, 3)
        l_costos.addWidget(QLabel("Domicilio:"), 3, 0)
        l_costos.addWidget(self.sp_domicilio, 3, 1)
        l_costos.addWidget(QLabel("Cables:"), 3, 2)
        l_costos.addWidget(self.sp_cables, 3, 3)
        l_costos.addWidget(QLabel("Inversor:"), 4, 0)
        l_costos.addWidget(self.sp_inversor, 4, 1)
        gb_costos.setLayout(l_costos)
        layout.addWidget(gb_costos)

        # ── TOTAL BAR ────────────────────────────────────────────────
        bottom_frame = QFrame()
        frame_summary(bottom_frame)
        l_bottom = QHBoxLayout(bottom_frame)
        self.lbl_total = QLabel("$ 0")
        lbl_total_renta(self.lbl_total)
        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("CREAR RENTA")
        btn_success(btn_save)
        btn_save.clicked.connect(self.guardar)

        l_bottom.addWidget(QLabel("TOTAL A PAGAR:"))
        l_bottom.addWidget(self.lbl_total)
        l_bottom.addStretch()
        l_bottom.addWidget(btn_cancel)
        l_bottom.addWidget(btn_save)
        layout.addStretch()
        layout.addWidget(bottom_frame)

    def sel_cli(self):
        dlg = DialogoSelectorCliente(self)
        if dlg.exec() and dlg.cliente_seleccionado:
            c = dlg.cliente_seleccionado
            self.cliente_id = c.get('id')
            self.txt_cli.setText(c.get('nombre_completo', ''))
            self.cliente_lic = c.get('no_licencia', '')
            self.cliente_nac = c.get('nacionalidad', '')

    def cargar_autos(self, pre=None):
        self.cmb_auto.blockSignals(True)
        self.cmb_auto.clear()
        # Placeholder — no se puede guardar sin seleccionar un auto
        self.cmb_auto.addItem("— Seleccionar auto —", userData=None)
        try:
            autos = AutoService.listar_disponibles()
            for a in autos:
                self.cmb_auto.addItem(
                    f"{a['placa']} - {a['marca']}", userData=a
                )
                if pre and a['placa'] == pre:
                    self.cmb_auto.setCurrentIndex(self.cmb_auto.count() - 1)
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Warning, "Aviso", str(e), self).exec()
        finally:
            self.cmb_auto.blockSignals(False)
            # Disparar act_auto manualmente solo si hay un auto real seleccionado
            self.act_auto()

    def act_auto(self):
        d = self.cmb_auto.currentData()
        if not d:          # placeholder seleccionado — no hacer nada
            return
        self.sp_km.setValue(float(d.get('kilometraje', 0)))
        self.calc_total()

    def calc_fechas(self):
        if self._updating:
            return
        self._updating = True
        ini = datetime.combine(
            self.d_sal.date().toPython(), self.h_sal.time().toPython()
        )
        fin = ini + timedelta(days=self.sp_dias.value())
        self.d_ret.setDate(fin.date())
        self.h_ret.setTime(fin.time())
        self.lbl_horas_extra.setText("Extras: 0h")
        self.calc_total()
        self._updating = False

    def calc_dias(self):
        if self._updating:
            return
        self._updating = True
        ini = datetime.combine(
            self.d_sal.date().toPython(), self.h_sal.time().toPython()
        )
        fin = datetime.combine(
            self.d_ret.date().toPython(), self.h_ret.time().toPython()
        )
        diff_h = (fin - ini).total_seconds() / 3600
        dias = max(1, int(diff_h // 24))
        self.sp_dias.setValue(dias)
        extras = int(diff_h % 24)
        self.lbl_horas_extra.setText(
            f"Extras: {extras}h" if extras > 2 else "Extras: 0h (Tol)"
        )
        self.calc_total()
        self._updating = False

    def calc_total(self):
        dias = self.sp_dias.value()
        extras = 0
        ini = datetime.combine(
            self.d_sal.date().toPython(), self.h_sal.time().toPython()
        )
        fin = datetime.combine(
            self.d_ret.date().toPython(), self.h_ret.time().toPython()
        )
        diff_h = (fin - ini).total_seconds() / 3600
        if (diff_h % 24) > 2:
            extras = int(diff_h % 24)

        adicionales = sum([
            self.sp_lavado.value(), self.sp_silla.value(),
            self.sp_cables.value(), self.sp_inversor.value(),
            self.sp_domicilio.value(),
        ])
        total = ((dias * self.sp_val_dia.value())
                 + (extras * self.sp_val_hora.value())
                 + adicionales)
        self.lbl_total.setText(f"$ {total:,.0f}")
        return total, extras

    def guardar(self):
        if not self.cliente_id or not self.cmb_auto.currentData():
            return _msg_box(
                QMessageBox.Icon.Warning,
                "Error", "Faltan datos (Cliente o Auto)", self
            ).exec()

        total, horas_extra = self.calc_total()
        auto = self.cmb_auto.currentData()

        datos = {
            "placa": auto['placa'],
            "id_cliente": self.cliente_id,
            "nombre_cliente": self.txt_cli.text(),
            "no_licencia": self.cliente_lic,
            "nacionalidad": self.cliente_nac,
            "fecha_recogida": self.d_sal.date().toString("yyyy-MM-dd"),
            "hora_recogida": self.h_sal.text(),
            "ubicacion_recogida": "Oficina",
            "fecha_retorno": self.d_ret.date().toString("yyyy-MM-dd"),
            "hora_retorno": self.h_ret.text(),
            "ubicacion_retorno": "Oficina",
            "dias_calculados": self.sp_dias.value(),
            "horas_extras": horas_extra,
            "valor_dia": self.sp_val_dia.value(),
            "valor_hora_extra": self.sp_val_hora.value(),
            "costo_lavado": self.sp_lavado.value(),
            "costo_silla": self.sp_silla.value(),
            "costo_domicilio": self.sp_domicilio.value(),
            "costo_cables": self.sp_cables.value(),
            "costo_inversor": self.sp_inversor.value(),
            "km_salida": self.sp_km.value(),
            "tanque_salida": self.cmb_tanque.currentText(),
            "abono": 0,
            "descuento": 0,
            "estado": "Activo",
        }

        try:
            id_nuevo = RentaService.crear(datos)

            msg_box = ModernMessageBox(
                self, "Renta Creada",
                "La renta se ha guardado correctamente.\n\n¿Qué desea hacer a continuación?",
                "success",
                buttons=[
                    {'text': "Hacer Inspección (Check-out)", 'role': 1, 'class': 'primary'},
                    {'text': "Imprimir Orden", 'role': 2, 'class': 'secondary'},
                    {'text': "Imprimir Contrato", 'role': 3, 'class': 'secondary'},
                    {'text': "Cerrar", 'role': 0, 'class': 'ghost'}
                ]
            )
            msg_box.exec()
            clicked = msg_box._result_code

            if clicked in (2, 3):
                tipo_doc = "orden" if clicked == 2 else "contrato"
                if hasattr(self.parent(), 'generar_doc'):
                    self.parent().generar_doc(id_nuevo, tipo_doc)

            elif clicked == 1:
                dlg_insp = InspeccionDialog(self.parent(), id_nuevo)
                dlg_insp.cmb_tipo.setCurrentText("Entrega (Check-out)")
                dlg_insp.spin_km.setValue(self.sp_km.value())
                dlg_insp.cmb_gasolina.setCurrentText(
                    self.cmb_tanque.currentText()
                )
                dlg_insp.exec()

            self.accept()
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Critical, "Error", str(e), self).exec()


# =============================================================================
# EXTENDER RENTA
# =============================================================================
class DialogoExtenderRenta(QDialog):
    def __init__(self, parent=None, id_renta=None):
        super().__init__(parent)
        self.setWindowTitle(f"Extender Renta #{id_renta}")
        self.setMinimumSize(450, 400)
        self.id_renta = id_renta

        try:
            self.datos = RentaService.obtener(id_renta)
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Critical, "Error", str(e), self).exec()
            self.reject()
            return

        self._setup_ui()
        self.calcular()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        gb = QGroupBox("Detalles de Extensión")
        group_box(gb)

        form = QFormLayout()

        self.lbl_actual = QLabel(
            f"{self.datos.get('fecha_retorno', '')} "
            f"(Total días: {self.datos.get('dias_calculados', 0)})"
        )

        fecha_ret = str(self.datos.get('fecha_retorno', ''))[:10]
        try:
            dt_ret = datetime.strptime(fecha_ret, "%Y-%m-%d").date()
        except ValueError:
            dt_ret = QDate.currentDate().toPython()

        self.d_nueva = QDateEdit(dt_ret)
        self.d_nueva.setCalendarPopup(True)
        input_date(self.d_nueva)
        self.d_nueva.dateChanged.connect(self.calcular)

        hora_ret = str(self.datos.get('hora_retorno', '12:00'))[:5]
        try:
            tm_ret = datetime.strptime(hora_ret, "%H:%M").time()
        except ValueError:
            tm_ret = QTime.currentTime().toPython()

        self.t_nueva = QTimeEdit(tm_ret)
        input_time(self.t_nueva)

        self.lbl_dias_add = QLabel("0 días adicionales")
        lbl_extra_info(self.lbl_dias_add)

        self.lbl_nuevo_total = QLabel(
            f"$ {float(self.datos.get('total', 0)):,.0f}"
        )
        lbl_new_total_extension(self.lbl_nuevo_total)

        form.addRow("Retorno Actual:", self.lbl_actual)
        form.addRow("Nueva Fecha:", self.d_nueva)
        form.addRow("Nueva Hora:", self.t_nueva)
        form.addRow("Adicionales:", self.lbl_dias_add)
        form.addRow("NUEVO TOTAL:", self.lbl_nuevo_total)
        gb.setLayout(form)
        layout.addWidget(gb)

        btn = QPushButton("CONFIRMAR EXTENSIÓN")
        btn_success(btn)
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

    def calcular(self):
        fecha_rec = str(self.datos.get('fecha_recogida', ''))[:10]
        try:
            f_inicio = datetime.strptime(fecha_rec, "%Y-%m-%d").date()
        except ValueError:
            f_inicio = QDate.currentDate().toPython()

        f_nueva = self.d_nueva.date().toPython()
        dias_totales = max(1, (f_nueva - f_inicio).days)
        dias_calculados = int(self.datos.get('dias_calculados', 0))
        dias_adicionales = dias_totales - dias_calculados

        self.lbl_dias_add.setText(f"{dias_adicionales} días extra")

        valor_dia = float(self.datos.get('valor_dia', 0))
        total_actual = float(self.datos.get('total', 0))
        abono = float(self.datos.get('abono', 0))

        nuevo_total = total_actual + (dias_adicionales * valor_dia)
        self.lbl_nuevo_total.setText(f"$ {nuevo_total:,.0f}")

        self.nuevos_datos = {
            'dias': dias_totales,
            'total': nuevo_total,
            'saldo': nuevo_total - abono,
        }

    def guardar(self):
        try:
            RentaService.extender(
                self.id_renta,
                self.d_nueva.date().toString("yyyy-MM-dd"),
                self.t_nueva.time().toString("HH:mm"),
                self.nuevos_datos['dias'],
                self.nuevos_datos['total'],
                self.nuevos_datos['saldo'],
            )
            _msg_box(QMessageBox.Icon.Information, "Éxito", "Renta extendida correctamente", self).exec()
            self.accept()
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Critical, "Error", str(e), self).exec()


# =============================================================================
# CAMBIO DE VEHÍCULO
# =============================================================================
class DialogoCambioVehiculo(QDialog):
    def __init__(self, parent=None, id_renta=None, placa_actual=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio de Vehículo (Sustitución)")
        self.setMinimumSize(_DIALOG_MIN_WIDTH, 500)
        self.id_renta = id_renta
        self.placa_actual = placa_actual

        self._setup_ui()
        self.cargar_datos_iniciales()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        gb_out = QGroupBox(
            f"1. Recepción Vehículo Actual: {self.placa_actual}"
        )
        group_box(gb_out)
        l_out = QGridLayout()
        self.sp_km = QDoubleSpinBox()
        self.sp_km.setRange(0, 1e7)
        self.sp_km.setPrefix("KM: ")
        input_spinbox(self.sp_km)
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems([
            "Mantenimiento (Avería)", "Disponible (Cambio simple)"
        ])
        input_combo(self.cmb_estado)
        self.txt_motivo = QPlainTextEdit()
        self.txt_motivo.setPlaceholderText("Describa el motivo del cambio...")
        input_textedit(self.txt_motivo)

        l_out.setColumnStretch(1, 1)
        l_out.addWidget(QLabel("Kilometraje Retorno:"), 0, 0)
        l_out.addWidget(self.sp_km, 0, 1)
        l_out.addWidget(QLabel("Estado al recibir:"), 1, 0)
        l_out.addWidget(self.cmb_estado, 1, 1)
        l_out.addWidget(QLabel("Motivo del Cambio:"), 2, 0)
        l_out.addWidget(self.txt_motivo, 2, 1)
        gb_out.setLayout(l_out)
        layout.addWidget(gb_out)

        gb_in = QGroupBox("2. Asignar Nuevo Vehículo")
        group_box(gb_in)
        l_in = QHBoxLayout()
        self.cmb_nuevo = QComboBox()
        input_combo(self.cmb_nuevo)
        l_in.addWidget(QLabel("Seleccionar:"))
        l_in.addWidget(self.cmb_nuevo)
        gb_in.setLayout(l_in)
        layout.addWidget(gb_in)

        btn = QPushButton("REALIZAR CAMBIO")
        btn_danger(btn)
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

    def cargar_datos_iniciales(self):
        try:
            auto_actual = AutoService.obtener(self.placa_actual)
            if auto_actual:
                self.sp_km.setValue(
                    float(auto_actual.get('kilometraje', 0))
                )

            disponibles = AutoService.listar_disponibles()
            for a in disponibles:
                self.cmb_nuevo.addItem(
                    f"{a['placa']} - {a['marca']} {a['modelo']}",
                    userData=a['placa'],
                )
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Warning, "Aviso", str(e), self).exec()

    def guardar(self):
        if not self.txt_motivo.toPlainText().strip():
            return _msg_box(
                QMessageBox.Icon.Warning, "Atención", "Debe describir el motivo", self
            ).exec()

        placa_nueva = self.cmb_nuevo.currentData()
        if not placa_nueva:
            return _msg_box(
                QMessageBox.Icon.Warning, "Error", "No hay vehículo seleccionado", self
            ).exec()

        estado_recepcion = (
            "Mantenimiento"
            if "Mantenimiento" in self.cmb_estado.currentText()
            else "Disponible"
        )

        try:
            RentaService.cambiar_vehiculo(
                self.id_renta,
                self.placa_actual,
                self.sp_km.value(),
                estado_recepcion,
                placa_nueva,
                self.txt_motivo.toPlainText(),
            )
            _msg_box(
                QMessageBox.Icon.Information, "Proceso Completado",
                f"Cambio realizado.\nNuevo vehículo: {placa_nueva}", self
            ).exec()
            self.accept()
        except DinamoBaseError as e:
            _msg_box(QMessageBox.Icon.Critical, "Error", str(e), self).exec()


# =============================================================================
# INSPECCIÓN
# =============================================================================
class InspeccionDialog(QDialog):
    def __init__(self, parent=None, id_renta=None):
        super().__init__(parent)
        self.id_renta = id_renta
        self.setWindowTitle(f"Inspección Vehicular - Renta #{id_renta}")
        self.setMinimumSize(550, 680)
        dialog_background(self)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # ── Datos Generales ──────────────────────────────────────────
        gb_basico = QGroupBox("1. Datos Generales")
        group_box(gb_basico)
        form_basico = QFormLayout(gb_basico)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems([
            "Entrega (Check-out)", "Recepción (Check-in)"
        ])
        input_combo(self.cmb_tipo)

        self.spin_km = QDoubleSpinBox()
        self.spin_km.setRange(0, 10000000)
        self.spin_km.setSuffix(" km")
        input_spinbox(self.spin_km)

        self.cmb_gasolina = QComboBox()
        self.cmb_gasolina.addItems(NIVEL_TANQUE)
        input_combo(self.cmb_gasolina)

        self.cmb_limpieza = QComboBox()
        self.cmb_limpieza.addItems([
            "Limpio", "Sucio", "Requiere Lavado Profundo"
        ])
        input_combo(self.cmb_limpieza)

        form_basico.addRow("Tipo de Inspección:", self.cmb_tipo)
        form_basico.addRow("Kilometraje actual:", self.spin_km)
        form_basico.addRow("Nivel de Gasolina:", self.cmb_gasolina)
        form_basico.addRow("Estado de Limpieza:", self.cmb_limpieza)
        layout.addWidget(gb_basico)

        # ── Inventario ───────────────────────────────────────────────
        gb_inv = QGroupBox("2. Inventario (Marcar si el vehículo lo tiene)")
        group_box(gb_inv)
        grid_inv = QGridLayout(gb_inv)

        self.chk_repuesto = QCheckBox("Llanta de repuesto")
        self.chk_repuesto.setChecked(True)
        self.chk_gato = QCheckBox("Gato y Cruceta")
        self.chk_gato.setChecked(True)
        self.chk_kit = QCheckBox("Kit de Carretera")
        self.chk_kit.setChecked(True)
        self.chk_docs = QCheckBox("Documentos del Vehículo")
        self.chk_docs.setChecked(True)

        grid_inv.addWidget(self.chk_repuesto, 0, 0)
        grid_inv.addWidget(self.chk_gato, 0, 1)
        grid_inv.addWidget(self.chk_kit, 1, 0)
        grid_inv.addWidget(self.chk_docs, 1, 1)
        layout.addWidget(gb_inv)

        # ── Observaciones ────────────────────────────────────────────
        gb_obs = QGroupBox("3. Daños y Observaciones")
        group_box(gb_obs)
        form_obs = QVBoxLayout(gb_obs)

        form_obs.addWidget(QLabel("Daños en carrocería:"))
        self.txt_danos = QTextEdit()
        self.txt_danos.setMaximumHeight(_TEXT_EDIT_MAX_HEIGHT)
        input_textedit(self.txt_danos)
        form_obs.addWidget(self.txt_danos)

        form_obs.addWidget(QLabel("Observaciones generales:"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(_TEXT_EDIT_MAX_HEIGHT)
        input_textedit(self.txt_obs)
        form_obs.addWidget(self.txt_obs)

        layout.addWidget(gb_obs)

        # ── Botones ──────────────────────────────────────────────────
        h_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar Inspección")
        btn_success(btn_save)
        btn_save.clicked.connect(self.guardar)

        h_btn.addStretch()
        h_btn.addWidget(btn_cancel)
        h_btn.addWidget(btn_save)
        layout.addLayout(h_btn)

    def guardar(self):
        datos = {
            "id_renta": self.id_renta,
            "tipo": self.cmb_tipo.currentText(),
            "kilometraje": self.spin_km.value(),
            "nivel_gasolina": self.cmb_gasolina.currentText(),
            "limpieza": self.cmb_limpieza.currentText(),
            "tiene_repuesto": self.chk_repuesto.isChecked(),
            "tiene_gato_cruceta": self.chk_gato.isChecked(),
            "tiene_kit_carretera": self.chk_kit.isChecked(),
            "tiene_documentos": self.chk_docs.isChecked(),
            "danos_carroceria": self.txt_danos.toPlainText(),
            "observaciones": self.txt_obs.toPlainText(),
        }

        try:
            InspeccionService.registrar(datos)
            _msg_box(QMessageBox.Icon.Information, "Éxito",
                    "Inspección guardada en el sistema correctamente.", self).exec()
            self.accept()
        except Exception as e:
            _msg_box(QMessageBox.Icon.Critical, "Error", str(e), self).exec()


# =============================================================================
# WIDGET PRINCIPAL DE RENTAS
# =============================================================================
class RentasWidget(QWidget):
    def __init__(self, session_id: str = None):
        super().__init__()
        view_background(self)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Banner superior ──────────────────────────────────────────
        from views.layouts.form_helpers import create_banner
        banner = create_banner("📋", "Control de Rentas Activas", "Gestion de Rentas y Devoluciones", self.cargar_tabla)
        main_layout.addWidget(banner)

        # ── Área de contenido ─────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}") # This can be replaced by a style function if needed
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(*_RENTAS_WIDGET_CONTENT_MARGINS)
        c_lay.setSpacing(_RENTAS_WIDGET_CONTENT_SPACING)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        btn_nueva = QPushButton("+ Nueva Renta")
        btn_primary(btn_nueva)
        btn_nueva.clicked.connect(self.nueva)
        btn_act = QPushButton("Actualizar")
        btn_default(btn_act)
        btn_act.clicked.connect(self.cargar_tabla)
        top.addStretch()
        top.addWidget(btn_nueva)
        top.addWidget(btn_act)
        c_lay.addLayout(top)

        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Placa", "Cliente", "Salida", "Retorno", "Estado", "Total"
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.tbl.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.tbl.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.tbl.customContextMenuRequested.connect(self.mostrar_menu)
        table_widget(self.tbl)

        c_lay.addWidget(self.tbl)
        self.cargar_tabla()

    def cargar_tabla(self):
        self.tbl.setRowCount(0)
        try:
            activas = DashboardService.obtener_activas()
            for r in activas:
                i = self.tbl.rowCount()
                self.tbl.insertRow(i)
                self.tbl.setItem(i, 0, QTableWidgetItem(str(r.get('id'))))
                self.tbl.setItem(i, 1, QTableWidgetItem(r.get('placa')))
                self.tbl.setItem(
                    i, 2, QTableWidgetItem(r.get('nombre_cliente'))
                )
                self.tbl.setItem(
                    i, 3, QTableWidgetItem(str(r.get('fecha_recogida'))[:10])
                )
                self.tbl.setItem(
                    i, 4, QTableWidgetItem(str(r.get('fecha_retorno'))[:10])
                )
                self.tbl.setItem(i, 5, QTableWidgetItem(r.get('estado')))
                self.tbl.setItem(
                    i, 6,
                    QTableWidgetItem(f"$ {float(r.get('total', 0)):,.0f}")
                )
        except DinamoBaseError:
            pass

    def nueva(self):
        if NuevaRentaDialog(self).exec():
            self.cargar_tabla()

    def mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item:
            return
        row = item.row()

        id_renta = int(self.tbl.item(row, 0).text())
        placa = self.tbl.item(row, 1).text()

        item_cliente = self.tbl.item(row, 2)
        cliente = item_cliente.text() if item_cliente else "Cliente"

        item_total = self.tbl.item(row, 6)
        if item_total:
            total_str = (
                item_total.text().replace('$', '').replace(',', '')
                .replace('.', '').strip()
            )
            total_renta = float(total_str) if total_str.isdigit() else 0.0
        else:
            total_renta = 0.0

        menu = QMenu(self)

        ac_pdf = menu.addAction("Imprimir Orden")
        ac_pdf.triggered.connect(
            lambda: self.generar_doc(id_renta, "orden")
        )

        ac_con = menu.addAction("Imprimir Contrato")
        ac_con.triggered.connect(
            lambda: self.generar_doc(id_renta, "contrato")
        )

        menu.addSeparator()

        ac_ext = menu.addAction("Extender Renta")
        ac_ext.triggered.connect(lambda: self.abrir_extension(id_renta))

        ac_cam = menu.addAction("Cambio Vehículo")
        ac_cam.triggered.connect(
            lambda: self.abrir_cambio(id_renta, placa)
        )

        ac_insp = menu.addAction("Inspección Vehicular")
        ac_insp.triggered.connect(
            lambda: self.abrir_inspeccion(id_renta)
        )

        menu.addSeparator()

        ac_pagos = menu.addAction("Historial de Pagos")
        ac_pagos.triggered.connect(
            lambda: self.abrir_pagos(id_renta, total_renta, cliente)
        )

        menu.exec(QCursor.pos())

    def abrir_inspeccion(self, id_renta):
        dlg = InspeccionDialog(self, id_renta)
        dlg.exec()

    def abrir_extension(self, id_renta):
        dlg = DialogoExtenderRenta(self, id_renta)
        if dlg.exec():
            self.cargar_tabla()

    def abrir_cambio(self, id_renta, placa):
        dlg = DialogoCambioVehiculo(self, id_renta, placa)
        if dlg.exec():
            self.cargar_tabla()

    def abrir_pagos(self, id_renta, total, cliente):
        try:
            dlg = PagosDialog(self, id_renta, total, cliente)
            dlg.exec()
        except Exception:
            pass

    def generar_doc(self, id_renta, tipo):
        try:
            datos = RentaService.obtener_datos_documento(id_renta)
            datos['fecha_inicio'] = datos.get('fecha_recogida')
            datos['fecha_fin'] = datos.get('fecha_retorno')
            datos['hora_retorno'] = datos.get('hora_retorno', '12:00')
            datos['valor_total'] = utils.fmt_moneda(datos.get('total', 0))

            ruta = None
            if tipo == "contrato":
                ok, msg, ruta = utils.generar_contrato_temp(datos)
            elif tipo == "orden":
                ruta = utils.generar_orden_renta_jinja(datos)

            if ruta:
                utils.abrir_archivo(ruta)
        except Exception as e:
            _msg_box(
                QMessageBox.Icon.Critical, "Error", f"Error generando documento: {e}", self
            ).exec()
