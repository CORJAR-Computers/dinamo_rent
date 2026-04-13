"""
views/reservas_view.py — Vista refactorizada para la gestión de Reservas.
"""
from datetime import datetime, timedelta
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QMessageBox, QDateEdit, QTimeEdit, QGroupBox, QDoubleSpinBox,
    QTextEdit, QMenu, QAbstractItemView, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, QDate, QTime
from PySide6.QtGui import QColor, QBrush, QAction, QCursor, QFont

# IMPORTACIONES A LA CAPA DE SERVICIOS
from services.services import AutoService, ClienteService
from services.services_extra import ReservaService
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
# DIÁLOGOS DE CLIENTE (Manejados vía ClienteService)
# =============================================================================

class DialogoSelectorCliente(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Cliente")
        self.setFixedSize(600, 450)
        self.cliente_seleccionado = None

        layout = QVBoxLayout(self)
        top = QHBoxLayout()
        self.txt = UpperLineEdit()
        self.txt.setPlaceholderText("Buscar por nombre o documento...")
        self.txt.textChanged.connect(self.buscar)
        btn_new = QPushButton("+ Nuevo")
        btn_new.clicked.connect(self.nuevo_cliente)

        top.addWidget(self.txt); top.addWidget(btn_new)
        layout.addLayout(top)

        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["ID", "Documento", "Nombre"])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        self.tbl.cellDoubleClicked.connect(self.seleccionar)
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

    def seleccionar(self, r, c):
        if 0 <= r < len(self.data_temp):
            self.cliente_seleccionado = self.data_temp[r]
            self.accept()

    def nuevo_cliente(self):
        # Utiliza la vista centralizada de clientes
        from views.clientes_view import ClienteFormDialog
        dlg = ClienteFormDialog(self)
        if dlg.exec() and hasattr(dlg, 'datos_cliente') and dlg.datos_cliente.get('id'):
            self.cliente_seleccionado = dlg.datos_cliente
            self.accept()


# =============================================================================
# DIÁLOGO NUEVA RESERVA
# =============================================================================

class NuevaReservaDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Reserva")
        self.setFixedSize(850, 700)

        self.cliente_id = None
        self._updating = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- 1. CLIENTE ---
        gb_cli = QGroupBox("1. Cliente")
        l_cli = QHBoxLayout()
        self.txt_cliente = QLineEdit()
        self.txt_cliente.setReadOnly(True)
        self.txt_cliente.setPlaceholderText("Seleccione un cliente...")
        self.txt_cliente.setStyleSheet("background-color: #e3f2fd; color: #1565c0; font-weight: bold;")

        btn_cli = QPushButton("🔍 Buscar")
        btn_cli.clicked.connect(self.buscar_cliente)
        l_cli.addWidget(self.txt_cliente); l_cli.addWidget(btn_cli)
        gb_cli.setLayout(l_cli)
        layout.addWidget(gb_cli)

        # --- 2. VEHÍCULO (CATEGORÍA O PLACA) ---
        gb_auto = QGroupBox("2. Asignación de Vehículo")
        l_auto = QGridLayout()

        self.cmb_auto = QComboBox()
        self.cmb_auto.setStyleSheet("font-size: 14px; padding: 5px;")
        self.cargar_opciones_vehiculo()

        self.d_inicio = QDateEdit(QDate.currentDate().addDays(1)); self.d_inicio.setCalendarPopup(True)
        self.t_inicio = QTimeEdit(QTime(8, 0))
        self.sp_dias = QDoubleSpinBox(); self.sp_dias.setRange(1, 365); self.sp_dias.setValue(1); self.sp_dias.setSuffix(" días")
        self.d_fin = QDateEdit(QDate.currentDate().addDays(2)); self.d_fin.setCalendarPopup(True)
        self.t_fin = QTimeEdit(QTime(8, 0))

        self.d_inicio.dateChanged.connect(self.calc_fechas); self.t_inicio.timeChanged.connect(self.calc_fechas)
        self.sp_dias.valueChanged.connect(self.calc_fechas)
        self.d_fin.dateChanged.connect(self.calc_dias); self.t_fin.timeChanged.connect(self.calc_dias)

        self.lbl_extras = QLabel("Extras: 0h"); self.lbl_extras.setStyleSheet("color: red; font-weight: bold")

        l_auto.addWidget(QLabel("Selección (Categoría o Placa):"), 0, 0)
        l_auto.addWidget(self.cmb_auto, 0, 1, 1, 4)
        l_auto.addWidget(QLabel("Recogida:"), 1, 0); l_auto.addWidget(self.d_inicio, 1, 1); l_auto.addWidget(self.t_inicio, 1, 2)
        l_auto.addWidget(QLabel("Duración:"), 1, 3); l_auto.addWidget(self.sp_dias, 1, 4)
        l_auto.addWidget(QLabel("Devolución:"), 2, 0); l_auto.addWidget(self.d_fin, 2, 1); l_auto.addWidget(self.t_fin, 2, 2)
        l_auto.addWidget(QLabel("Tiempo Extra:"), 2, 3); l_auto.addWidget(self.lbl_extras, 2, 4)

        gb_auto.setLayout(l_auto)
        layout.addWidget(gb_auto)

        # --- 3. VALORES ---
        gb_val = QGroupBox("3. Valores Financieros")
        l_val = QGridLayout()

        self.sp_valor_dia = QDoubleSpinBox(); self.sp_valor_dia.setRange(0, 1e8); self.sp_valor_dia.setPrefix("$ "); self.sp_valor_dia.valueChanged.connect(self.calc_total)
        self.sp_valor_hora = QDoubleSpinBox(); self.sp_valor_hora.setRange(0, 1e8); self.sp_valor_hora.setPrefix("$ "); self.sp_valor_hora.valueChanged.connect(self.calc_total)
        self.sp_abono = QDoubleSpinBox(); self.sp_abono.setRange(0, 1e8); self.sp_abono.setPrefix("$ "); self.sp_abono.valueChanged.connect(self.calc_total)

        self.lbl_total = QLabel("$ 0"); self.lbl_total.setStyleSheet("font-size: 16px; font-weight: bold; color: green;")
        self.lbl_saldo = QLabel("$ 0"); self.lbl_saldo.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")

        l_val.addWidget(QLabel("Valor Día:"), 0, 0); l_val.addWidget(self.sp_valor_dia, 0, 1)
        l_val.addWidget(QLabel("Valor Hora Extra:"), 0, 2); l_val.addWidget(self.sp_valor_hora, 0, 3)
        l_val.addWidget(QLabel("Abono / Seña:"), 1, 0); l_val.addWidget(self.sp_abono, 1, 1)
        l_val.addWidget(QLabel("TOTAL ESTIMADO:"), 2, 0); l_val.addWidget(self.lbl_total, 2, 1)
        l_val.addWidget(QLabel("SALDO PENDIENTE:"), 2, 2); l_val.addWidget(self.lbl_saldo, 2, 3)

        gb_val.setLayout(l_val)
        layout.addWidget(gb_val)

        layout.addWidget(QLabel("Observaciones:"))
        self.txt_obs = QTextEdit(); self.txt_obs.setMaximumHeight(50)
        layout.addWidget(self.txt_obs)

        h_btn = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("CREAR RESERVA")
        btn_save.setStyleSheet("background-color: #004aad; color: white; font-weight: bold; padding: 10px;")
        btn_save.clicked.connect(self.guardar)
        h_btn.addStretch(); h_btn.addWidget(btn_cancel); h_btn.addWidget(btn_save)
        layout.addLayout(h_btn)

        self.calc_total()

    def buscar_cliente(self):
        s = DialogoSelectorCliente(self)
        if s.exec() and s.cliente_seleccionado:
            self.cliente_id = s.cliente_seleccionado['id']
            nom = s.cliente_seleccionado.get('nombre_completo') or f"{s.cliente_seleccionado.get('nombres','')} {s.cliente_seleccionado.get('apellidos','')}"
            self.txt_cliente.setText(nom)

    def cargar_opciones_vehiculo(self):
        self.cmb_auto.clear()

        categorias = [
            "--- CATEGORÍAS GENÉRICAS ---",
            "Sedan Mecánico", "Sedan Automático",
            "Camioneta 5 Pasajeros", "Camioneta 7 Pasajeros",
            "HatchBack Mecánico", "HatchBack Automático",
            "--- VEHÍCULOS ESPECÍFICOS DISPONIBLES ---"
        ]

        for cat in categorias:
            if cat.startswith("---"):
                self.cmb_auto.addItem(cat, userData=None)
            else:
                self.cmb_auto.addItem(f"📁 {cat}", userData={'es_generico': True, 'valor': cat})

        try:
            autos = AutoService.listar_disponibles()
            for a in autos:
                item_text = f"🚗 {a['placa']} - {a['marca']} {a['modelo']}"
                self.cmb_auto.addItem(item_text, userData={'es_generico': False, 'placa': a['placa'], 'marca': a['marca']})
        except DinamoBaseError:
            pass

    def calc_fechas(self):
        if self._updating: return
        self._updating = True
        ini = datetime.combine(self.d_inicio.date().toPython(), self.t_inicio.time().toPython())
        fin = ini + timedelta(days=self.sp_dias.value())
        self.d_fin.setDate(fin.date()); self.t_fin.setTime(fin.time())
        self.lbl_extras.setText("Extras: 0h")
        self.calc_total(); self._updating = False

    def calc_dias(self):
        if self._updating: return
        self._updating = True
        ini = datetime.combine(self.d_inicio.date().toPython(), self.t_inicio.time().toPython())
        fin = datetime.combine(self.d_fin.date().toPython(), self.t_fin.time().toPython())

        diff_h = (fin - ini).total_seconds() / 3600
        days = max(1, int(diff_h // 24))
        self.sp_dias.setValue(days)

        extras = int(diff_h % 24)
        if extras > 2:
            self.lbl_extras.setText(f"Extras: {extras}h")
        else:
            self.lbl_extras.setText("Extras: 0h (Tol)")

        self.calc_total(); self._updating = False

    def calc_total(self):
        dias = self.sp_dias.value()
        val_dia = self.sp_valor_dia.value()
        val_hora = self.sp_valor_hora.value()

        ini = datetime.combine(self.d_inicio.date().toPython(), self.t_inicio.time().toPython())
        fin = datetime.combine(self.d_fin.date().toPython(), self.t_fin.time().toPython())
        diff_h = (fin - ini).total_seconds() / 3600
        horas_extra = int(diff_h % 24) if (diff_h % 24) > 2 else 0

        total = (dias * val_dia) + (horas_extra * val_hora)
        saldo = total - self.sp_abono.value()

        self.lbl_total.setText(f"$ {total:,.0f}")
        self.lbl_saldo.setText(f"$ {saldo:,.0f}")
        return total, horas_extra

    def guardar(self):
        if not self.cliente_id: return QMessageBox.warning(self, "Error", "Seleccione Cliente")

        seleccion = self.cmb_auto.currentData()
        if not seleccion:
            return QMessageBox.warning(self, "Error", "Seleccione una opción válida de vehículo")

        total, horas_extra = self.calc_total()

        categoria = seleccion['valor'] if seleccion['es_generico'] else seleccion['marca']
        placa = None if seleccion['es_generico'] else seleccion['placa']

        datos = {
            "id_cliente": self.cliente_id,
            "nombre_cliente": self.txt_cliente.text(),
            "nacionalidad": "COLOMBIA",
            "categoria_vehiculo": categoria,
            "placa_asignada": placa,
            "fecha_recogida": self.d_inicio.date().toString("yyyy-MM-dd"),
            "hora_recogida": self.t_inicio.time().toString("HH:mm"),
            "ubicacion_recogida": "Oficina",
            "fecha_retorno": self.d_fin.date().toString("yyyy-MM-dd"),
            "hora_retorno": self.t_fin.time().toString("HH:mm"),
            "ubicacion_retorno": "Oficina",
            "dias_calculados": self.sp_dias.value(),
            "horas_extras": horas_extra,
            "valor_dia": self.sp_valor_dia.value(),
            "valor_hora_adic": self.sp_valor_hora.value(),
            "abono": self.sp_abono.value(),
            "total": total,
            "observaciones": self.txt_obs.toPlainText(),
            "estado": "Confirmada"
        }

        try:
            ReservaService.crear(datos)
            QMessageBox.information(self, "Éxito", "Reserva creada correctamente")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL
# =============================================================================

class ReservasWidget(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Gestión de Reservas", styleSheet="font-size:18px;font-weight:bold"))

        btn_nueva = QPushButton("+ Nueva Reserva")
        btn_nueva.setStyleSheet("background-color: #004aad; color: white; font-weight: bold; padding: 5px 15px;")
        btn_nueva.clicked.connect(self.nueva_reserva)

        btn_refresh = QPushButton("Actualizar")
        btn_refresh.clicked.connect(self.cargar_datos)

        top.addStretch()
        top.addWidget(btn_nueva)
        top.addWidget(btn_refresh)
        layout.addLayout(top)

        self.tbl = QTableWidget(0, 7)
        self.tbl.setHorizontalHeaderLabels(["ID", "Cliente", "Vehículo/Cat.", "Inicio", "Fin", "Abono", "Estado"])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self.mostrar_menu)

        layout.addWidget(self.tbl)
        self.cargar_datos()

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        try:
            reservas = ReservaService.listar()
            for r in reservas:
                row = self.tbl.rowCount()
                self.tbl.insertRow(row)
                self.tbl.setItem(row, 0, QTableWidgetItem(str(r.get('id'))))
                self.tbl.setItem(row, 1, QTableWidgetItem(r.get('nombre_cliente')))

                vehiculo = r.get('placa_asignada')
                if not vehiculo:
                    vehiculo = f"[{r.get('categoria_vehiculo', 'Pendiente')}]"

                self.tbl.setItem(row, 2, QTableWidgetItem(vehiculo))
                self.tbl.setItem(row, 3, QTableWidgetItem(str(r.get('fecha_recogida'))[:10]))
                self.tbl.setItem(row, 4, QTableWidgetItem(str(r.get('fecha_retorno'))[:10]))
                self.tbl.setItem(row, 5, QTableWidgetItem(f"$ {float(r.get('abono',0)):,.0f}"))

                est = r.get('estado')
                item_est = QTableWidgetItem(est)
                if est == 'Confirmada':
                    item_est.setForeground(QBrush(QColor("green")))
                    item_est.setFont(QFont("Arial", 9, QFont.Bold))
                self.tbl.setItem(row, 6, item_est)
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", f"No se pudieron cargar las reservas: {e}")

    def nueva_reserva(self):
        if NuevaReservaDialog(self).exec():
            self.cargar_datos()

    def mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item: return

        row = item.row()
        id_reserva = int(self.tbl.item(row, 0).text())

        try:
            contacto = ReservaService.obtener_contacto(id_reserva)
            celular = contacto.get('celular', '')
            nombre = contacto.get('nombre_cliente', 'Cliente')
        except DinamoBaseError:
            celular = ""
            nombre = "Cliente"

        menu = QMenu(self)
        ac_pdf = QAction(f"📄 Imprimir Voucher", self)
        ac_pdf.triggered.connect(lambda: self.imprimir(id_reserva))

        ac_ws = QAction(f"💬 WhatsApp", self)
        ac_ws.triggered.connect(lambda: utils.abrir_whatsapp(celular, f"Hola {nombre}, confirmamos su reserva #{id_reserva} en Dinamo Rent a Car."))

        menu.addAction(ac_pdf)
        menu.addSeparator()
        menu.addAction(ac_ws)
        menu.exec(QCursor.pos())

    def imprimir(self, rid):
        try:
            d = ReservaService.obtener_para_pdf(rid)
            datos = {
                'id_reserva': str(d['id']),
                'cliente_nombre': d['nombre_cliente'],
                'vehiculo': d.get('placa_asignada') or f"Categoría: {d.get('categoria_vehiculo')}",
                'f_inicio': d['fecha_recogida'], 'f_fin': d['fecha_retorno'],
                'h_inicio': d['hora_recogida'], 'h_fin': d['hora_retorno'],
                'abono': d['abono'], 'total': d['total']
            }
            ok, path = utils.generar_pdf_reserva(datos)
            if ok: utils.abrir_archivo(path)
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", f"No se pudo generar el voucher: {e}")