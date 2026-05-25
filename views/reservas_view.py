from views.components import ModernMessageBox
"""
views/reservas_view.py — Vista para la gestion de Reservas.

Mejoras UI/UX:
  - Hereda de BaseWidget
  - Sin estilos inline — todo por QSS (cssClass)
  - UpperLineEdit compartido desde views.widgets
  - Sin emojis en combo items
  - Font bold corregido (QFont value-type)
  - Busqueda en tabla de reservas
  - Colores de estado desde config.py
  - Filas alternas en tablas
"""
from datetime import datetime, timedelta

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog, QComboBox, QDateEdit, QTimeEdit, QGroupBox,
    QDoubleSpinBox, QTextEdit, QMenu, QAbstractItemView, QGridLayout, QWidget,
)
from PySide6.QtCore import Qt, QDate, QTime, QTimer
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_EXITO, COLOR_PELIGRO, COLOR_ALERTA
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.reserva_service import ReservaService
from core.exceptions import DinamoBaseError
from views.base_widget import BaseWidget
from views.styles import (
    btn_danger, btn_default, btn_primary, btn_success, edit_search, lbl_section, status_active, status_inactive, status_warning,
    input_field, input_combo, input_date, input_spinbox, input_time, input_textedit,
    group_box, table_widget,
)
from views.widgets import UpperLineEdit
from core import utils

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"


# =============================================================================
# DIALOGO SELECTOR DE CLIENTE
# =============================================================================

from views.base_dialog import BaseDialog


class DialogoSelectorCliente(BaseDialog):
    """Dialogo para buscar y seleccionar un cliente."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Seleccionar Cliente")
        self.setMinimumSize(600, 450)
        self.cliente_seleccionado = None

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        from views.layouts.form_helpers import build_dialog_header
        root.addWidget(build_dialog_header("👤", "Seleccionar Cliente", "Busque y seleccione un cliente del registro para asociarlo a la operación"))

        from views.styles import dialog_body_style
        body = QWidget()
        body.setObjectName("dlg_body")
        dialog_body_style(body)
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(14)
        body_lay.setContentsMargins(20, 16, 20, 14)

        # Barra de busqueda
        top = QHBoxLayout()
        self.txt = UpperLineEdit()
        edit_search(self.txt)
        self.txt.setPlaceholderText("Buscar por nombre o documento...")
        self.txt.textChanged.connect(self._buscar)

        btn_new = QPushButton("+ Nuevo")
        btn_success(btn_new)
        btn_new.clicked.connect(self._nuevo_cliente)

        top.addWidget(self.txt)
        top.addWidget(btn_new)
        body_lay.addLayout(top)

        # Tabla
        self.tbl = QTableWidget(0, 3)
        self.tbl.setHorizontalHeaderLabels(["ID", "Documento", "Nombre"])
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.cellDoubleClicked.connect(self._seleccionar)
        body_lay.addWidget(self.tbl)

        root.addWidget(body)

        self._init_overlay("Buscando clientes...")
        QTimer.singleShot(0, lambda: self._deferred_call(self._buscar))

    def _buscar(self):
        try:
            res = ClienteService.buscar(self.txt.text())
        except DinamoBaseError:
            res = []

        self.tbl.setRowCount(0)
        self.data_temp = res
        for i, d in enumerate(res):
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(str(d.get("id", ""))))
            self.tbl.setItem(i, 1, QTableWidgetItem(d.get("no_doc", "")))
            nom = d.get("nombre_completo") or f"{d.get('nombres','')} {d.get('apellidos','')}"
            self.tbl.setItem(i, 2, QTableWidgetItem(nom))

    def _seleccionar(self, r, c):
        if 0 <= r < len(self.data_temp):
            self.cliente_seleccionado = self.data_temp[r]
            self.accept()

    def _nuevo_cliente(self):
        from views.clientes_view import ClienteFormDialog
        dlg = ClienteFormDialog(self)
        if dlg.exec() and hasattr(dlg, "datos_cliente") and dlg.datos_cliente.get("id"):
            self.cliente_seleccionado = dlg.datos_cliente
            self.accept()


# =============================================================================
# DIALOGO NUEVA RESERVA
# =============================================================================

class NuevaReservaDialog(BaseDialog):
    """Dialogo para crear una nueva reserva."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Crear Nueva Reserva")
        self.setMinimumSize(850, 700)

        self.cliente_id = None
        self._updating = False
        self._setup_ui()
        self._init_overlay("Cargando vehiculos disponibles...")
        QTimer.singleShot(0, lambda: self._deferred_call(self._cargar_opciones_vehiculo))

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        from views.layouts.form_helpers import build_dialog_header
        root.addWidget(build_dialog_header("📅", "Crear Nueva Reserva", "Registro de reserva vehicular — cliente, vehículo y valores"))

        from views.styles import dialog_body_style
        body = QWidget()
        body.setObjectName("dlg_body")
        dialog_body_style(body)
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(14)
        body_lay.setContentsMargins(20, 16, 20, 14)

        # --- 1. Cliente ---
        gb_cli = QGroupBox("1. Cliente")
        group_box(gb_cli)
        l_cli = QHBoxLayout()
        self.txt_cliente = QLineEdit()
        self.txt_cliente.setReadOnly(True)
        self.txt_cliente.setPlaceholderText("Seleccione un cliente...")
        input_field(self.txt_cliente)

        btn_cli = QPushButton("Buscar Cliente")
        btn_primary(btn_cli)
        btn_cli.clicked.connect(self._buscar_cliente)
        l_cli.addWidget(self.txt_cliente)
        l_cli.addWidget(btn_cli)
        gb_cli.setLayout(l_cli)
        body_lay.addWidget(gb_cli)

        # --- 2. Vehiculo ---
        gb_auto = QGroupBox("2. Asignacion de Vehiculo")
        group_box(gb_auto)
        l_auto = QGridLayout()

        self.cmb_auto = QComboBox()

        self.d_inicio = QDateEdit(QDate.currentDate().addDays(1))
        self.d_inicio.setCalendarPopup(True)
        self.t_inicio = QTimeEdit(QTime(8, 0))
        self.sp_dias = QDoubleSpinBox()
        self.sp_dias.setRange(1, 365)
        self.sp_dias.setValue(1)
        self.sp_dias.setSuffix(" dias")
        self.d_fin = QDateEdit(QDate.currentDate().addDays(2))
        self.d_fin.setCalendarPopup(True)
        self.t_fin = QTimeEdit(QTime(8, 0))

        input_combo(self.cmb_auto)
        input_date(self.d_inicio)
        input_time(self.t_inicio)
        input_spinbox(self.sp_dias)
        input_date(self.d_fin)
        input_time(self.t_fin)

        self.d_inicio.dateChanged.connect(self._calc_fechas)
        self.t_inicio.timeChanged.connect(self._calc_fechas)
        self.sp_dias.valueChanged.connect(self._calc_fechas)
        self.d_fin.dateChanged.connect(self._calc_dias)
        self.t_fin.timeChanged.connect(self._calc_dias)

        self.lbl_extras = QLabel("Extras: 0h")
        status_warning(self.lbl_extras)

        l_auto.setColumnStretch(1, 1)
        l_auto.setColumnStretch(4, 1)

        l_auto.addWidget(QLabel("Seleccion (Categoria o Placa):"), 0, 0)
        l_auto.addWidget(self.cmb_auto, 0, 1, 1, 4)
        l_auto.addWidget(QLabel("Recogida:"), 1, 0)
        l_auto.addWidget(self.d_inicio, 1, 1)
        l_auto.addWidget(self.t_inicio, 1, 2)
        l_auto.addWidget(QLabel("Duracion:"), 1, 3)
        l_auto.addWidget(self.sp_dias, 1, 4)
        l_auto.addWidget(QLabel("Devolucion:"), 2, 0)
        l_auto.addWidget(self.d_fin, 2, 1)
        l_auto.addWidget(self.t_fin, 2, 2)
        l_auto.addWidget(QLabel("Tiempo Extra:"), 2, 3)
        l_auto.addWidget(self.lbl_extras, 2, 4)

        gb_auto.setLayout(l_auto)
        body_lay.addWidget(gb_auto)

        # --- 3. Valores ---
        gb_val = QGroupBox("3. Valores Financieros")
        group_box(gb_val)
        l_val = QGridLayout()

        self.sp_valor_dia = QDoubleSpinBox()
        self.sp_valor_dia.setRange(0, 1e8)
        self.sp_valor_dia.setPrefix("$ ")
        self.sp_valor_dia.valueChanged.connect(self._calc_total)

        self.sp_valor_hora = QDoubleSpinBox()
        self.sp_valor_hora.setRange(0, 1e8)
        self.sp_valor_hora.setPrefix("$ ")
        self.sp_valor_hora.valueChanged.connect(self._calc_total)

        self.sp_abono = QDoubleSpinBox()
        self.sp_abono.setRange(0, 1e8)
        self.sp_abono.setPrefix("$ ")
        self.sp_abono.valueChanged.connect(self._calc_total)

        input_spinbox(self.sp_valor_dia)
        input_spinbox(self.sp_valor_hora)
        input_spinbox(self.sp_abono)

        self.lbl_total = QLabel("$ 0")
        status_active(self.lbl_total)

        self.lbl_saldo = QLabel("$ 0")
        status_inactive(self.lbl_saldo)

        l_val.setColumnStretch(1, 1)
        l_val.setColumnStretch(3, 1)
        l_val.addWidget(QLabel("Valor Dia:"), 0, 0)
        l_val.addWidget(self.sp_valor_dia, 0, 1)
        l_val.addWidget(QLabel("Valor Hora Extra:"), 0, 2)
        l_val.addWidget(self.sp_valor_hora, 0, 3)
        l_val.addWidget(QLabel("Abono / Sena:"), 1, 0)
        l_val.addWidget(self.sp_abono, 1, 1)
        l_val.addWidget(QLabel("TOTAL ESTIMADO:"), 2, 0)
        l_val.addWidget(self.lbl_total, 2, 1)
        l_val.addWidget(QLabel("SALDO PENDIENTE:"), 2, 2)
        l_val.addWidget(self.lbl_saldo, 2, 3)

        gb_val.setLayout(l_val)
        body_lay.addWidget(gb_val)

        # Observaciones
        lbl_obs = QLabel("Observaciones:")
        from views.styles import lbl_section
        lbl_section(lbl_obs)
        body_lay.addWidget(lbl_obs)
        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(50)
        input_textedit(self.txt_obs)
        body_lay.addWidget(self.txt_obs)

        body_lay.addStretch()

        # Separador
        from PySide6.QtWidgets import QFrame
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { background: #cbd5e1; max-height: 1px; border: none; }")
        body_lay.addWidget(sep)

        # Botones
        h_btn = QHBoxLayout()
        h_btn.setSpacing(10)
        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("CREAR RESERVA")
        btn_primary(btn_save)
        btn_save.clicked.connect(self._guardar)

        h_btn.addStretch()
        h_btn.addWidget(btn_cancel)
        h_btn.addWidget(btn_save)
        body_lay.addLayout(h_btn)

        root.addWidget(body)

        self._calc_total()

    def _buscar_cliente(self):
        s = DialogoSelectorCliente(self)
        if s.exec() and s.cliente_seleccionado:
            self.cliente_id = s.cliente_seleccionado["id"]
            nom = (
                s.cliente_seleccionado.get("nombre_completo")
                or f"{s.cliente_seleccionado.get('nombres','')} {s.cliente_seleccionado.get('apellidos','')}"
            )
            self.txt_cliente.setText(nom)

    def _cargar_opciones_vehiculo(self):
        self.cmb_auto.clear()

        categorias = [
            "--- CATEGORIAS GENERICAS ---",
            "Sedan Mecanico", "Sedan Automatico",
            "Camioneta 5 Pasajeros", "Camioneta 7 Pasajeros",
            "HatchBack Mecanico", "HatchBack Automatico",
            "--- VEHICULOS ESPECIFICOS DISPONIBLES ---",
        ]

        for cat in categorias:
            if cat.startswith("---"):
                self.cmb_auto.addItem(cat, userData=None)
            else:
                self.cmb_auto.addItem(f"[Cat] {cat}", userData={"es_generico": True, "valor": cat})

        try:
            autos = AutoService.listar_disponibles()
            for a in autos:
                item_text = f"{a['placa']} - {a['marca']} {a['modelo']}"
                self.cmb_auto.addItem(
                    item_text,
                    userData={"es_generico": False, "placa": a["placa"], "marca": a["marca"]},
                )
        except DinamoBaseError:
            pass

    def _calc_fechas(self):
        if self._updating:
            return
        self._updating = True
        ini = datetime.combine(
            self.d_inicio.date().toPython(), self.t_inicio.time().toPython()
        )
        fin = ini + timedelta(days=self.sp_dias.value())
        self.d_fin.setDate(fin.date())
        self.t_fin.setTime(fin.time())
        self.lbl_extras.setText("Extras: 0h")
        self._calc_total()
        self._updating = False

    def _calc_dias(self):
        if self._updating:
            return
        self._updating = True
        ini = datetime.combine(
            self.d_inicio.date().toPython(), self.t_inicio.time().toPython()
        )
        fin = datetime.combine(
            self.d_fin.date().toPython(), self.t_fin.time().toPython()
        )

        diff_h = (fin - ini).total_seconds() / 3600
        days = max(1, int(diff_h // 24))
        self.sp_dias.setValue(days)

        extras = int(diff_h % 24)
        if extras > 2:
            self.lbl_extras.setText(f"Extras: {extras}h")
        else:
            self.lbl_extras.setText("Extras: 0h (Tol.)")

        self._calc_total()
        self._updating = False

    def _calc_total(self):
        dias = self.sp_dias.value()
        val_dia = self.sp_valor_dia.value()
        val_hora = self.sp_valor_hora.value()

        ini = datetime.combine(
            self.d_inicio.date().toPython(), self.t_inicio.time().toPython()
        )
        fin = datetime.combine(
            self.d_fin.date().toPython(), self.t_fin.time().toPython()
        )
        diff_h = (fin - ini).total_seconds() / 3600
        horas_extra = int(diff_h % 24) if (diff_h % 24) > 2 else 0

        total = (dias * val_dia) + (horas_extra * val_hora)
        saldo = total - self.sp_abono.value()

        self.lbl_total.setText(f"$ {total:,.0f}")
        self.lbl_saldo.setText(f"$ {saldo:,.0f}")
        return total, horas_extra

    def _guardar(self):
        if not self.cliente_id:
            ModernMessageBox.warning(self, "Validacion", "Seleccione un Cliente")
            return

        seleccion = self.cmb_auto.currentData()
        if not seleccion:
            ModernMessageBox.warning(
                self, "Validacion", "Seleccione una opcion valida de vehiculo"
            )
            return

        total, horas_extra = self._calc_total()

        categoria = seleccion["valor"] if seleccion["es_generico"] else seleccion["marca"]
        placa = None if seleccion["es_generico"] else seleccion["placa"]

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
            "estado": "Confirmada",
        }

        try:
            ReservaService.crear(datos)
            from views.components.toast_notification import ToastNotification
            ToastNotification(self.window(), "Reserva creada correctamente", "success")
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", str(e))


# =============================================================================
# WIDGET PRINCIPAL
# =============================================================================

class ReservasWidget(BaseWidget):
    """Panel de Gestion de Reservas."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner
        banner = create_banner("📅", "Gestion de Reservas", "Administracion de reservas vehiculares", self.cargar_datos)
        main_layout.addWidget(banner)

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        # ── Busqueda y acciones ──
        top = QHBoxLayout()

        # Busqueda
        self.txt_buscar = QLineEdit()
        edit_search(self.txt_buscar)
        self.txt_buscar.setPlaceholderText("Buscar reserva...")
        self.txt_buscar.setMinimumWidth(250)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        btn_refresh = QPushButton("Actualizar")
        btn_default(btn_refresh)
        btn_refresh.clicked.connect(self.cargar_datos)
        top.addWidget(btn_refresh)

        btn_nueva = QPushButton("+ Nueva Reserva")
        btn_primary(btn_nueva)
        btn_nueva.clicked.connect(self._nueva_reserva)
        top.addWidget(btn_nueva)

        c_lay.addLayout(top)

        # ── Tabla ──
        self.tbl = QTableWidget(0, 7)
        table_widget(self.tbl)
        self.tbl.setHorizontalHeaderLabels([
            "ID", "Cliente", "Vehiculo/Cat.", "Inicio", "Fin", "Abono", "Estado",
        ])
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.setAlternatingRowColors(True)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self._mostrar_menu)
        c_lay.addWidget(self.tbl)

        self._lista: list[dict] = []
        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        self._lista = []
        try:
            reservas = ReservaService.listar()
            self._lista = reservas
            self._pintar_filas(reservas)
        except DinamoBaseError as e:
            self.mostrar_error(f"No se pudieron cargar las reservas:\n{e}")

    def _pintar_filas(self, reservas: list[dict]):
        self.tbl.setRowCount(0)
        for r in reservas:
            row = self.tbl.rowCount()
            self.tbl.insertRow(row)
            self.tbl.setItem(row, 0, QTableWidgetItem(str(r.get("id"))))
            self.tbl.setItem(row, 1, QTableWidgetItem(r.get("nombre_cliente", "")))

            vehiculo = r.get("placa_asignada")
            if not vehiculo:
                vehiculo = f"[{r.get('categoria_vehiculo', 'Pendiente')}]"
            self.tbl.setItem(row, 2, QTableWidgetItem(vehiculo))
            self.tbl.setItem(row, 3, QTableWidgetItem(str(r.get("fecha_recogida", ""))[:10]))
            self.tbl.setItem(row, 4, QTableWidgetItem(str(r.get("fecha_retorno", ""))[:10]))
            self.tbl.setItem(row, 5, QTableWidgetItem(f"$ {float(r.get('abono', 0)):,.0f}"))

            est = r.get("estado", "")
            from views.components.status_badge import StatusBadge
            _ESTADO_BADGE_MAP = {"Confirmada": "success", "Pendiente": "warning", "Cancelada": "danger"}
            badge = StatusBadge(est, _ESTADO_BADGE_MAP.get(est, "info"))
            self.tbl.setCellWidget(row, 6, badge)

    # ── Filtro ─────────────────────────────────────────────────

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        if not txt:
            self._pintar_filas(self._lista)
            return
        filtrados = [
            r for r in self._lista
            if txt in str(r.get("nombre_cliente", "")).lower()
            or txt in str(r.get("placa_asignada", "")).lower()
            or txt in str(r.get("categoria_vehiculo", "")).lower()
            or txt in str(r.get("id", "")).lower()
        ]
        self._pintar_filas(filtrados)

    # ── Acciones ───────────────────────────────────────────────

    def _nueva_reserva(self):
        if NuevaReservaDialog(self).exec():
            self.cargar_datos()

    def _mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item:
            return

        row = item.row()
        id_reserva = int(self.tbl.item(row, 0).text())

        try:
            contacto = ReservaService.obtener_contacto(id_reserva)
            celular = contacto.get("celular", "")
            nombre = contacto.get("nombre_cliente", "Cliente")
        except DinamoBaseError:
            celular = ""
            nombre = "Cliente"

        menu = QMenu(self)
        ac_pdf = menu.addAction("Imprimir Voucher")
        ac_ws = menu.addAction("Enviar WhatsApp")
        menu.addSeparator()

        acc = menu.exec(self.tbl.viewport().mapToGlobal(pos))
        if acc == ac_pdf:
            self._imprimir(id_reserva)
        elif acc == ac_ws:
            utils.abrir_whatsapp(
                celular,
                f"Hola {nombre}, confirmamos su reserva #{id_reserva} en Dinamo Rent a Car.",
            )

    def _imprimir(self, rid):
        try:
            d = ReservaService.obtener_para_pdf(rid)

            nombre = d.get("nombre_cliente", "")
            celular = d.get("celular", "")
            doc = d.get("documento", d.get("tipo_doc", "") + " " + d.get("numero_doc", ""))
            if doc.strip() == "":
                doc = "No registrado"

            vehiculo = d.get("placa_asignada") or f"Categoría: {d.get('categoria_vehiculo', 'No asignada')}"
            vehiculo_tipo = d.get("categoria_vehiculo", "Vehículo")

            dias = d.get("dias_calculados", 1)
            valor_dia = float(d.get("valor_dia", 0))
            total = float(d.get("total", 0))
            abono = float(d.get("abono", 0))
            saldo = total - abono

            seguro = max(0, valor_dia * dias * 0.1)
            adicionales = max(0, (valor_dia * dias + seguro) - total + abono) if total > 0 else 0

            datos = {
                "id_reserva": str(d["id"]),
                "cliente_nombre": nombre,
                "cliente_doc": doc,
                "cliente_celular": celular,
                "cliente_email": d.get("email", "No registrado"),
                "vehiculo": vehiculo,
                "vehiculo_tipo": vehiculo_tipo,
                "f_inicio": d.get("fecha_recogida", ""),
                "f_fin": d.get("fecha_retorno", ""),
                "h_inicio": d.get("hora_recogida", ""),
                "h_fin": d.get("hora_retorno", ""),
                "dias": dias,
                "valor_dia": valor_dia,
                "valor_dias": valor_dia * dias,
                "seguro": seguro,
                "adicionales": adicionales,
                "total": total,
                "abono": abono,
                "saldo": saldo,
                "notas": d.get("observaciones", ""),
            }

            ok, path = utils.generar_reserva_jinja(datos)
            if ok:
                utils.abrir_archivo(path)
        except DinamoBaseError as e:
            self.mostrar_error(f"No se pudo generar el voucher:\n{e}")
        except Exception as e:
            self.mostrar_error(f"Error al generar voucher:\n{e}")
