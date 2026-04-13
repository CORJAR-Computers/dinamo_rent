"""
views/rentas_view.py — Vista refactorizada para gestión de rentas.
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QMessageBox, QDateEdit, QDoubleSpinBox, QGroupBox,
    QPlainTextEdit, QFrame, QAbstractItemView, QGridLayout, QScrollArea,
    QTimeEdit, QMenu, QCheckBox, QTextEdit
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QCursor, QAction
from views.pagos_view import PagosDialog

# IMPORTACIONES A LA CAPA DE SERVICIOS
from services.services import RentaService, AutoService, ClienteService
from services.services_extra import InspeccionService
from core.exceptions import DinamoBaseError
try:
    from core import utils
except ImportError:
    import utils

class UpperLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(self.to_upper)
    def to_upper(self, text):
        if not text.isupper(): self.setText(text.upper())


# =============================================================================
# DIÁLOGOS DE CLIENTE (Usando ClienteService)
# =============================================================================
class DialogoSelectorCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Buscar Cliente")
        self.setFixedSize(600, 450)
        self.cliente_seleccionado = None

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.txt = UpperLineEdit()
        self.txt.setPlaceholderText("BUSCAR POR NOMBRE O DOC...")
        self.txt.textChanged.connect(self.buscar)

        btn = QPushButton("+ NUEVO")
        btn.clicked.connect(self.nuevo)

        top.addWidget(self.txt)
        top.addWidget(btn)
        layout.addLayout(top)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["ID", "Doc", "Nombre"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.verticalHeader().setVisible(False)
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
            nom = d.get('nombre_completo') or f"{d.get('nombres','')} {d.get('apellidos','')}"
            self.tbl.setItem(i, 2, QTableWidgetItem(nom))

    def sel(self, r, c):
        if 0 <= r < len(self.data_temp):
            self.cliente_seleccionado = self.data_temp[r]
            self.accept()

    def nuevo(self):
        # Para mantener la migración limpia, puedes llamar a la vista completa de clientes
        # o mantener el diálogo rápido conectándolo a ClienteService.guardar()
        from views.clientes_view import ClienteFormDialog
        dlg = ClienteFormDialog(self)
        if dlg.exec() and hasattr(dlg, 'datos_cliente') and dlg.datos_cliente.get('id'):
            self.cliente_seleccionado = dlg.datos_cliente
            self.accept()


# =============================================================================
# NUEVA RENTA (Usando RentaService y AutoService)
# =============================================================================
class NuevaRentaDialog(QDialog):
    def __init__(self, parent=None, placa_preseleccionada=None):
        super().__init__(parent)
        self.setWindowTitle("Nueva Renta - Cálculo Inteligente")
        self.setFixedSize(1000, 650)

        self.cliente_id = None
        self.cliente_lic = ""
        self.cliente_nac = ""
        self._updating = False

        self._setup_ui()
        self.cargar_autos(placa_preseleccionada)

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- CLIENTE Y AUTO ---
        gb_info = QGroupBox("Datos Principales")
        l_info = QHBoxLayout()
        self.txt_cli = QLineEdit(); self.txt_cli.setReadOnly(True); self.txt_cli.setPlaceholderText("Seleccionar Cliente...")
        btn_cli = QPushButton("🔍"); btn_cli.setFixedWidth(40); btn_cli.clicked.connect(self.sel_cli)
        self.cmb_auto = QComboBox(); self.cmb_auto.setMinimumWidth(300)
        self.cmb_auto.currentIndexChanged.connect(self.act_auto)

        l_info.addWidget(QLabel("Cliente:")); l_info.addWidget(self.txt_cli); l_info.addWidget(btn_cli); l_info.addSpacing(20)
        l_info.addWidget(QLabel("Auto:")); l_info.addWidget(self.cmb_auto)
        gb_info.setLayout(l_info); layout.addWidget(gb_info)

        # --- TIEMPO ---
        gb_time = QGroupBox("Tiempo y Fechas")
        l_time = QGridLayout()
        self.d_sal = QDateEdit(QDate.currentDate()); self.d_sal.setCalendarPopup(True)
        self.h_sal = QTimeEdit(QTime.currentTime())
        self.sp_dias = QDoubleSpinBox(); self.sp_dias.setRange(1, 365); self.sp_dias.setValue(1); self.sp_dias.setSuffix(" días")
        self.d_ret = QDateEdit(QDate.currentDate().addDays(1)); self.d_ret.setCalendarPopup(True)
        self.h_ret = QTimeEdit(QTime.currentTime())

        self.d_sal.dateChanged.connect(self.calc_fechas); self.h_sal.timeChanged.connect(self.calc_fechas)
        self.sp_dias.valueChanged.connect(self.calc_fechas)
        self.d_ret.dateChanged.connect(self.calc_dias); self.h_ret.timeChanged.connect(self.calc_dias)

        l_time.addWidget(QLabel("Salida:"), 0, 0); l_time.addWidget(self.d_sal, 0, 1); l_time.addWidget(self.h_sal, 0, 2)
        l_time.addWidget(QLabel("Duración:"), 0, 3); l_time.addWidget(self.sp_dias, 0, 4)
        l_time.addWidget(QLabel("Retorno:"), 1, 0); l_time.addWidget(self.d_ret, 1, 1); l_time.addWidget(self.h_ret, 1, 2)
        self.lbl_horas_extra = QLabel("Extras: 0h"); self.lbl_horas_extra.setStyleSheet("color: red; font-weight: bold")
        l_time.addWidget(self.lbl_horas_extra, 1, 4)
        gb_time.setLayout(l_time); layout.addWidget(gb_time)

        # --- COSTOS ---
        gb_costos = QGroupBox("Tarifas y Extras")
        l_costos = QGridLayout()
        self.sp_km = QDoubleSpinBox(); self.sp_km.setRange(0, 1e7); self.sp_km.setPrefix("KM: ")
        self.cmb_tanque = QComboBox(); self.cmb_tanque.addItems(["Lleno", "3/4", "1/2", "1/4", "Reserva"])
        self.sp_val_dia = QDoubleSpinBox(); self.sp_val_dia.setRange(0, 1e9); self.sp_val_dia.setPrefix("$ "); self.sp_val_dia.valueChanged.connect(self.calc_total)
        self.sp_val_hora = QDoubleSpinBox(); self.sp_val_hora.setRange(0, 1e9); self.sp_val_hora.setPrefix("$ H: "); self.sp_val_hora.valueChanged.connect(self.calc_total)

        self.sp_lavado = QDoubleSpinBox(); self.sp_lavado.setRange(0, 1e6); self.sp_lavado.valueChanged.connect(self.calc_total)
        self.sp_silla = QDoubleSpinBox(); self.sp_silla.setRange(0, 1e6); self.sp_silla.valueChanged.connect(self.calc_total)
        self.sp_cables = QDoubleSpinBox(); self.sp_cables.setRange(0, 1e6); self.sp_cables.valueChanged.connect(self.calc_total)
        self.sp_inversor = QDoubleSpinBox(); self.sp_inversor.setRange(0, 1e6); self.sp_inversor.valueChanged.connect(self.calc_total)
        self.sp_domicilio = QDoubleSpinBox(); self.sp_domicilio.setRange(0, 1e6); self.sp_domicilio.valueChanged.connect(self.calc_total)

        l_costos.addWidget(QLabel("KM Salida:"),0,0); l_costos.addWidget(self.sp_km,0,1)
        l_costos.addWidget(QLabel("Tanque:"),0,2); l_costos.addWidget(self.cmb_tanque,0,3)
        l_costos.addWidget(QLabel("Valor Día:"),1,0); l_costos.addWidget(self.sp_val_dia,1,1)
        l_costos.addWidget(QLabel("V. Hora Extra:"),1,2); l_costos.addWidget(self.sp_val_hora,1,3)
        l_costos.addWidget(QLabel("Lavado:"), 2, 0); l_costos.addWidget(self.sp_lavado, 2, 1)
        l_costos.addWidget(QLabel("Silla bebé:"), 2, 2); l_costos.addWidget(self.sp_silla, 2, 3)
        l_costos.addWidget(QLabel("Domicilio:"), 3, 0); l_costos.addWidget(self.sp_domicilio, 3, 1)
        gb_costos.setLayout(l_costos); layout.addWidget(gb_costos)

        # --- TOTAL ---
        bottom_frame = QFrame(); bottom_frame.setStyleSheet("background-color: #f0f0f0; border-radius: 8px;")
        l_bottom = QHBoxLayout(bottom_frame)
        self.lbl_total = QLabel("$ 0"); self.lbl_total.setStyleSheet("font-size: 24px; color: #004aad; font-weight: bold;")
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("CREAR RENTA"); btn_save.setStyleSheet("background-color:#2e7d32; color:white; padding: 12px; font-weight:bold;")
        btn_save.clicked.connect(self.guardar)

        l_bottom.addWidget(QLabel("TOTAL A PAGAR:")); l_bottom.addWidget(self.lbl_total)
        l_bottom.addStretch(); l_bottom.addWidget(btn_cancel); l_bottom.addWidget(btn_save)
        layout.addStretch(); layout.addWidget(bottom_frame)

    def sel_cli(self):
        dlg = DialogoSelectorCliente(self)
        if dlg.exec() and dlg.cliente_seleccionado:
            c = dlg.cliente_seleccionado
            self.cliente_id = c.get('id')
            self.txt_cli.setText(c.get('nombre_completo', ''))
            self.cliente_lic = c.get('no_licencia', '')
            self.cliente_nac = c.get('nacionalidad', '')

    def cargar_autos(self, pre=None):
        self.cmb_auto.clear()
        try:
            autos = AutoService.listar_disponibles()
            for a in autos:
                self.cmb_auto.addItem(f"{a['placa']} - {a['marca']}", userData=a)
                if pre and a['placa'] == pre:
                    self.cmb_auto.setCurrentIndex(self.cmb_auto.count()-1)
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Aviso", str(e))

    def act_auto(self):
        d = self.cmb_auto.currentData()
        if d: self.sp_km.setValue(float(d.get('kilometraje', 0)))
        self.calc_total()

    def calc_fechas(self):
        if self._updating: return
        self._updating = True
        ini = datetime.combine(self.d_sal.date().toPython(), self.h_sal.time().toPython())
        fin = ini + timedelta(days=self.sp_dias.value())
        self.d_ret.setDate(fin.date()); self.h_ret.setTime(fin.time())
        self.lbl_horas_extra.setText("Extras: 0h")
        self.calc_total(); self._updating = False

    def calc_dias(self):
        if self._updating: return
        self._updating = True
        ini = datetime.combine(self.d_sal.date().toPython(), self.h_sal.time().toPython())
        fin = datetime.combine(self.d_ret.date().toPython(), self.h_ret.time().toPython())
        diff_h = (fin - ini).total_seconds() / 3600
        dias = max(1, int(diff_h // 24))
        self.sp_dias.setValue(dias)
        extras = int(diff_h % 24)
        self.lbl_horas_extra.setText(f"Extras: {extras}h" if extras > 2 else "Extras: 0h (Tol)")
        self.calc_total(); self._updating = False

    def calc_total(self):
        dias = self.sp_dias.value()
        extras = 0
        ini = datetime.combine(self.d_sal.date().toPython(), self.h_sal.time().toPython())
        fin = datetime.combine(self.d_ret.date().toPython(), self.h_ret.time().toPython())
        diff_h = (fin - ini).total_seconds() / 3600
        if (diff_h % 24) > 2: extras = int(diff_h % 24)

        adicionales = sum([self.sp_lavado.value(), self.sp_silla.value(), self.sp_cables.value(), self.sp_inversor.value(), self.sp_domicilio.value()])
        total = (dias * self.sp_val_dia.value()) + (extras * self.sp_val_hora.value()) + adicionales
        self.lbl_total.setText(f"$ {total:,.0f}")
        return total, extras

    def guardar(self):
        if not self.cliente_id or not self.cmb_auto.currentData():
            return QMessageBox.warning(self, "Error", "Faltan datos (Cliente o Auto)")

        total, horas_extra = self.calc_total()
        auto = self.cmb_auto.currentData()

        # Diccionario para enviar a RentaService
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
            "estado": "Activo"
        }

        try:
            id_nuevo = RentaService.crear(datos)

            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Renta Creada")
            msg_box.setText("La renta se ha guardado correctamente.\n\n¿Qué desea hacer a continuación?")

            btn_inspeccion = msg_box.addButton("📋 Hacer Inspección (Check-out)", QMessageBox.ActionRole)
            btn_imprimir = msg_box.addButton("🖨️ Imprimir Orden", QMessageBox.ActionRole)
            btn_contrato = msg_box.addButton("📝 Imprimir Contrato", QMessageBox.ActionRole)
            btn_cerrar = msg_box.addButton("Cerrar", QMessageBox.RejectRole)

            msg_box.exec()
            clicked = msg_box.clickedButton()

            if clicked in (btn_imprimir, btn_contrato):
                tipo_doc = "orden" if clicked == btn_imprimir else "contrato"
                if hasattr(self.parent(), 'generar_doc'):
                    self.parent().generar_doc(id_nuevo, tipo_doc)

            elif clicked == btn_inspeccion:
                # Instanciamos el diálogo pasándole el ID recién creado
                dlg_insp = InspeccionDialog(self.parent(), id_nuevo)
                # Magia: pre-seleccionamos que es una entrega y le pasamos el KM de salida
                dlg_insp.cmb_tipo.setCurrentText("Entrega (Check-out)")
                dlg_insp.spin_km.setValue(self.sp_km.value())
                dlg_insp.cmb_gasolina.setCurrentText(self.cmb_tanque.currentText())
                dlg_insp.exec()

            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))

# =============================================================================
# DIÁLOGO EXTENDER RENTA (Usando RentaService)
# =============================================================================
class DialogoExtenderRenta(QDialog):
    def __init__(self, parent=None, id_renta=None):
        super().__init__(parent)
        self.setWindowTitle(f"Extender Renta #{id_renta}")
        self.setFixedSize(450, 400)
        self.id_renta = id_renta

        try:
            self.datos = RentaService.obtener(id_renta)
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))
            self.reject()
            return

        self._setup_ui()
        self.calcular()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        gb = QGroupBox("Detalles de Extensión")
        form = QFormLayout()

        self.lbl_actual = QLabel(f"{self.datos.get('fecha_retorno', '')} (Total días: {self.datos.get('dias_calculados', 0)})")

        # Parsear fecha actual
        fecha_ret = str(self.datos.get('fecha_retorno', ''))[:10]
        try:
            dt_ret = datetime.strptime(fecha_ret, "%Y-%m-%d").date()
        except ValueError:
            dt_ret = QDate.currentDate().toPython()

        self.d_nueva = QDateEdit(dt_ret)
        self.d_nueva.setCalendarPopup(True)
        self.d_nueva.dateChanged.connect(self.calcular)

        # Parsear hora actual
        hora_ret = str(self.datos.get('hora_retorno', '12:00'))[:5]
        try:
            tm_ret = datetime.strptime(hora_ret, "%H:%M").time()
        except ValueError:
            tm_ret = QTime.currentTime().toPython()

        self.t_nueva = QTimeEdit(tm_ret)

        self.lbl_dias_add = QLabel("0 días adicionales")
        self.lbl_dias_add.setStyleSheet("color: blue; font-weight: bold;")

        self.lbl_nuevo_total = QLabel(f"$ {float(self.datos.get('total', 0)):,.0f}")
        self.lbl_nuevo_total.setStyleSheet("color: green; font-size: 16px; font-weight: bold;")

        form.addRow("Retorno Actual:", self.lbl_actual)
        form.addRow("Nueva Fecha:", self.d_nueva)
        form.addRow("Nueva Hora:", self.t_nueva)
        form.addRow("Adicionales:", self.lbl_dias_add)
        form.addRow("NUEVO TOTAL:", self.lbl_nuevo_total)
        gb.setLayout(form)
        layout.addWidget(gb)

        btn = QPushButton("CONFIRMAR EXTENSIÓN")
        btn.setStyleSheet("background-color: #2e7d32; color: white; padding: 10px; font-weight: bold;")
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
            'saldo': nuevo_total - abono
        }

    def guardar(self):
        try:
            RentaService.extender(
                self.id_renta,
                self.d_nueva.date().toString("yyyy-MM-dd"),
                self.t_nueva.time().toString("HH:mm"),
                self.nuevos_datos['dias'],
                self.nuevos_datos['total'],
                self.nuevos_datos['saldo']
            )
            QMessageBox.information(self, "Éxito", "Renta extendida correctamente")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# DIÁLOGO CAMBIO DE VEHÍCULO (Usando AutoService y RentaService)
# =============================================================================
class DialogoCambioVehiculo(QDialog):
    def __init__(self, parent=None, id_renta=None, placa_actual=None):
        super().__init__(parent)
        self.setWindowTitle("Cambio de Vehículo (Sustitución)")
        self.setFixedSize(600, 500)
        self.id_renta = id_renta
        self.placa_actual = placa_actual

        self._setup_ui()
        self.cargar_datos_iniciales()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        gb_out = QGroupBox(f"1. Recepción Vehículo Actual: {self.placa_actual}")
        l_out = QGridLayout()
        self.sp_km = QDoubleSpinBox()
        self.sp_km.setRange(0, 1e7)
        self.sp_km.setPrefix("KM: ")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(["Mantenimiento (Avería)", "Disponible (Cambio simple)"])
        self.txt_motivo = QPlainTextEdit()
        self.txt_motivo.setPlaceholderText("Describa el motivo del cambio...")

        l_out.addWidget(QLabel("Kilometraje Retorno:"), 0, 0)
        l_out.addWidget(self.sp_km, 0, 1)
        l_out.addWidget(QLabel("Estado al recibir:"), 1, 0)
        l_out.addWidget(self.cmb_estado, 1, 1)
        l_out.addWidget(QLabel("Motivo del Cambio:"), 2, 0)
        l_out.addWidget(self.txt_motivo, 2, 1)
        gb_out.setLayout(l_out)
        layout.addWidget(gb_out)

        gb_in = QGroupBox("2. Asignar Nuevo Vehículo")
        l_in = QHBoxLayout()
        self.cmb_nuevo = QComboBox()
        l_in.addWidget(QLabel("Seleccionar:"))
        l_in.addWidget(self.cmb_nuevo)
        gb_in.setLayout(l_in)
        layout.addWidget(gb_in)

        btn = QPushButton("REALIZAR CAMBIO")
        btn.setStyleSheet("background-color: #d32f2f; color: white; padding: 12px; font-weight: bold;")
        btn.clicked.connect(self.guardar)
        layout.addWidget(btn)

    def cargar_datos_iniciales(self):
        try:
            # Cargar KM del auto actual
            auto_actual = AutoService.obtener(self.placa_actual)
            if auto_actual:
                self.sp_km.setValue(float(auto_actual.get('kilometraje', 0)))

            # Cargar autos disponibles
            disponibles = AutoService.listar_disponibles()
            for a in disponibles:
                self.cmb_nuevo.addItem(f"{a['placa']} - {a['marca']} {a['modelo']}", userData=a['placa'])
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Aviso", str(e))

    def guardar(self):
        if not self.txt_motivo.toPlainText().strip():
            return QMessageBox.warning(self, "Atención", "Debe describir el motivo")

        placa_nueva = self.cmb_nuevo.currentData()
        if not placa_nueva:
            return QMessageBox.warning(self, "Error", "No hay vehículo seleccionado")

        estado_recepcion = "Mantenimiento" if "Mantenimiento" in self.cmb_estado.currentText() else "Disponible"

        try:
            RentaService.cambiar_vehiculo(
                self.id_renta,
                self.placa_actual,
                self.sp_km.value(),
                estado_recepcion,
                placa_nueva,
                self.txt_motivo.toPlainText()
            )
            QMessageBox.information(self, "Proceso Completado", f"Cambio realizado.\nNuevo vehículo: {placa_nueva}")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))

# =============================================================================
# DIÁLOGO DE INSPECCIÓN (CHECK-IN / CHECK-OUT)
# =============================================================================
class InspeccionDialog(QDialog):
    def __init__(self, parent=None, id_renta=None):
        super().__init__(parent)
        self.id_renta = id_renta
        self.setWindowTitle(f"Inspección Vehicular - Renta #{id_renta}")
        self.setFixedSize(550, 650)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- 1. TIPO Y DATOS BÁSICOS ---
        gb_basico = QGroupBox("1. Datos Generales")
        form_basico = QFormLayout(gb_basico)

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(["Entrega (Check-out)", "Recepción (Check-in)"])

        self.spin_km = QDoubleSpinBox()
        self.spin_km.setRange(0, 10000000)
        self.spin_km.setSuffix(" km")

        self.cmb_gasolina = QComboBox()
        self.cmb_gasolina.addItems(["Lleno", "3/4", "1/2", "1/4", "Reserva"])

        self.cmb_limpieza = QComboBox()
        self.cmb_limpieza.addItems(["Limpio", "Sucio", "Requiere Lavado Profundo"])

        form_basico.addRow("Tipo de Inspección:", self.cmb_tipo)
        form_basico.addRow("Kilometraje actual:", self.spin_km)
        form_basico.addRow("Nivel de Gasolina:", self.cmb_gasolina)
        form_basico.addRow("Estado de Limpieza:", self.cmb_limpieza)
        layout.addWidget(gb_basico)

        # --- 2. INVENTARIO ---
        gb_inv = QGroupBox("2. Inventario (Marcar si el vehículo lo tiene)")
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

        # --- 3. OBSERVACIONES ---
        gb_obs = QGroupBox("3. Daños y Observaciones")
        form_obs = QVBoxLayout(gb_obs)

        form_obs.addWidget(QLabel("Daños en carrocería (Rayones, golpes, etc.):"))
        self.txt_danos = QTextEdit()
        self.txt_danos.setMaximumHeight(60)
        form_obs.addWidget(self.txt_danos)

        form_obs.addWidget(QLabel("Observaciones generales:"))
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)
        form_obs.addWidget(self.txt_obs)

        layout.addWidget(gb_obs)

        # --- BOTONES ---
        h_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Guardar Inspección")
        btn_save.setProperty("cssClass", "success")
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
            "observaciones": self.txt_obs.toPlainText()
        }

        try:
            InspeccionService.registrar(datos)
            QMessageBox.information(self, "Éxito", "Inspección guardada en el sistema correctamente.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

# =============================================================================
# WIDGET PRINCIPAL DE RENTAS
# =============================================================================
class RentasWidget(QWidget):
    def __init__(self):
        super().__init__()
        l = QVBoxLayout(self)
        top = QHBoxLayout()
        top.addWidget(QLabel("Control de Rentas Activas", styleSheet="font-size:18px;font-weight:bold"))
        btn_nueva = QPushButton("+ Nueva Renta")
        btn_nueva.clicked.connect(self.nueva)
        btn_act = QPushButton("Actualizar")
        btn_act.clicked.connect(self.cargar_tabla)
        top.addStretch()
        top.addWidget(btn_nueva)
        top.addWidget(btn_act)
        l.addLayout(top)

        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["ID", "Placa", "Cliente", "Salida", "Retorno", "Estado", "Total"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self.mostrar_menu)

        l.addWidget(self.tbl)
        self.cargar_tabla()

    def cargar_tabla(self):
        self.tbl.setRowCount(0)
        try:
            activas = RentaService.obtener_activas()
            for r in activas:
                i = self.tbl.rowCount(); self.tbl.insertRow(i)
                self.tbl.setItem(i,0,QTableWidgetItem(str(r.get('id'))))
                self.tbl.setItem(i,1,QTableWidgetItem(r.get('placa')))
                self.tbl.setItem(i,2,QTableWidgetItem(r.get('nombre_cliente')))
                self.tbl.setItem(i,3,QTableWidgetItem(str(r.get('fecha_recogida'))[:10]))
                self.tbl.setItem(i,4,QTableWidgetItem(str(r.get('fecha_retorno'))[:10]))
                self.tbl.setItem(i,5,QTableWidgetItem(r.get('estado')))
                self.tbl.setItem(i,6,QTableWidgetItem(f"$ {float(r.get('total',0)):,.0f}"))
        except DinamoBaseError as e:
            pass

    def nueva(self):
        if NuevaRentaDialog(self).exec():
            self.cargar_tabla()

    def mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item: return
        row = item.row()

        # 1. Extraer los datos básicos de la fila seleccionada
        id_renta = int(self.tbl.item(row, 0).text())
        placa = self.tbl.item(row, 1).text()

        # 2. Extraer el Cliente (Asumiendo que está en la columna 2)
        item_cliente = self.tbl.item(row, 2)
        cliente = item_cliente.text() if item_cliente else "Cliente"

        # 3. Extraer el Total (Asumiendo que está en la columna 5 o 6)
        # NOTA: Cambia el '5' por el número de columna donde esté tu Total si es diferente
        item_total = self.tbl.item(row, 5)
        if item_total:
            total_str = item_total.text().replace('$', '').replace(',', '').replace('.', '').strip()
            total_renta = float(total_str) if total_str.isdigit() else 0.0
        else:
            total_renta = 0.0

        # 4. Crear el menú contextual
        menu = QMenu(self)
        ac_pdf = QAction("📄 Imprimir Orden", self)
        ac_pdf.triggered.connect(lambda: self.generar_doc(id_renta, "orden"))

        ac_con = QAction("📝 Imprimir Contrato", self)
        ac_con.triggered.connect(lambda: self.generar_doc(id_renta, "contrato"))

        ac_ext = QAction("📅 Extender Renta", self)
        ac_ext.triggered.connect(lambda: self.abrir_extension(id_renta))

        ac_cam = QAction("🔄 Cambio Vehículo", self)
        ac_cam.triggered.connect(lambda: self.abrir_cambio(id_renta, placa))

        ac_insp = QAction("📋 Inspección Vehicular", self)
        ac_insp.triggered.connect(lambda: self.abrir_inspeccion(id_renta))

        # --- EL BOTÓN DE PAGOS (Ya conoce las variables) ---
        ac_pagos = QAction("💰 Historial de Pagos", self)
        ac_pagos.triggered.connect(lambda: self.abrir_pagos(id_renta, total_renta, cliente))

        # 5. Ensamblar el menú
        menu.addAction(ac_pdf)
        menu.addAction(ac_con)
        menu.addSeparator()
        menu.addAction(ac_ext)
        menu.addAction(ac_cam)
        menu.addAction(ac_insp)
        menu.addSeparator()
        menu.addAction(ac_pagos)

        menu.exec(QCursor.pos())

    def abrir_inspeccion(self, id_renta):
        dlg = InspeccionDialog(self, id_renta)
        dlg.exec()

    def abrir_extension(self, id_renta):
        # Aquí puedes portar el DialogoExtenderRenta conectándolo a RentaService.extender()
        pass

    def abrir_cambio(self, id_renta, placa):
        # Aquí puedes portar DialogoCambioVehiculo conectándolo a RentaService.cambiar_vehiculo()
        pass

    def generar_doc(self, id_renta, tipo):
        try:
            datos = RentaService.obtener_datos_documento(id_renta)
            # Formateo necesario para utils
            datos['fecha_inicio'] = datos.get('fecha_recogida')
            datos['fecha_fin'] = datos.get('fecha_retorno')
            datos['hora_retorno'] = datos.get('hora_retorno', '12:00')
            datos['valor_total'] = utils.fmt_moneda(datos.get('total', 0))

            ruta = None
            if tipo == "contrato":
                ok, msg, ruta = utils.generar_contrato_temp(datos)
            elif tipo == "orden":
                ruta = utils.generar_orden_alquiler_pdf(datos)

            if ruta:
                utils.abrir_archivo(ruta)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error generando documento: {e}")