from views.components import ModernMessageBox
"""
views/autos_view.py — Gestion de flota (vista)

Solo maneja la UI. Toda la logica va a AutoService.
Estilos via views.styles.py (funciona en cualquier tema de Windows).
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QLineEdit, QDialog, QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox, QPlainTextEdit,
    QGridLayout, QMenu, QTabWidget, QHeaderView, QWidget,
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush

from core.config import (
    TIPOS_AUTO, TIPOS_TRANSMISION, TIPOS_COMBUSTIBLE,
    ESTADOS_AUTO, TIPOS_ADQUISICION,
    COLOR_ESTADO_DISPONIBLE, COLOR_ESTADO_RENTADO,
    COLOR_ESTADO_MANTENIMIENTO, COLOR_ESTADO_INACTIVO,
)
from core.exceptions import DinamoBaseError
from services.auto_service import AutoService
from views.base_widget import BaseWidget
from views.widgets import UpperLineEdit
from views.styles import (
    btn_primary, btn_success, btn_danger, btn_default, btn_icon,
    lbl_section, edit_search,
    input_field, input_combo, input_spinbox, input_date, input_textedit,
    table_widget, group_box, dialog_title, dialog_background,
    tab_widget_pane_style, tab_bar_style,
)

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"
_REQMARK = "#dc2626"

# Ancho minimo para las columnas de labels en los formularios del dialogo
_LABEL_MIN_WIDTH = 150


def _make_label(text: str) -> QLabel:
    """Crea un QLabel con ancho minimo para evitar truncamiento."""
    lbl = QLabel(text)
    lbl.setMinimumWidth(_LABEL_MIN_WIDTH)
    return lbl


class DialogoAuto(QDialog):
    """Dialogo para crear o editar un vehiculo."""

    def __init__(self, parent=None, placa_editar: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de Vehiculo")
        self.setMinimumSize(950, 680)
        self.placa_editar = placa_editar

        dialog_background(self)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        titulo = QLabel("Nuevo Vehiculo" if not placa_editar else f"Editar Vehiculo: {placa_editar}")
        dialog_title(titulo)
        layout.addWidget(titulo)

        self.tabs = QTabWidget()
        tab_widget_pane_style(self.tabs)
        tab_bar_style(self.tabs.tabBar())

        self._construir_form()

        layout.addWidget(self.tabs, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_cancel = QPushButton("Cancelar")
        btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("GUARDAR VEHICULO")
        btn_primary(btn_save, large=True)
        btn_save.clicked.connect(self._guardar)

        btn_row.addStretch()
        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        if placa_editar:
            self._cargar(placa_editar)

    def _construir_form(self):
        # Pestaña 1: General y Técnico
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setSpacing(14)
        tab1_layout.setContentsMargins(14, 14, 14, 14)

        gb = QGroupBox("Informacion Basica")
        group_box(gb)
        g = QGridLayout()
        g.setHorizontalSpacing(16)
        g.setVerticalSpacing(10)
        self.txt_placa = UpperLineEdit()
        self.txt_marca = UpperLineEdit()
        self.txt_modelo = UpperLineEdit()
        self.txt_version = UpperLineEdit()
        self.txt_color = UpperLineEdit()
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS_AUTO)
        input_field(self.txt_placa)
        input_field(self.txt_marca)
        input_field(self.txt_modelo)
        input_field(self.txt_version)
        input_field(self.txt_color)
        input_combo(self.cmb_tipo)
        if self.placa_editar:
            self.txt_placa.setReadOnly(True)
        # Labels con ancho minimo y columnas input con stretch
        g.setColumnMinimumWidth(0, _LABEL_MIN_WIDTH)
        g.setColumnMinimumWidth(2, _LABEL_MIN_WIDTH)
        g.setColumnStretch(1, 1)
        g.setColumnStretch(3, 1)
        g.addWidget(_make_label("Placa (*):"), 0, 0); g.addWidget(self.txt_placa, 0, 1)
        g.addWidget(_make_label("Marca:"), 0, 2); g.addWidget(self.txt_marca, 0, 3)
        g.addWidget(_make_label("Modelo:"), 1, 0); g.addWidget(self.txt_modelo, 1, 1)
        g.addWidget(_make_label("Version:"), 1, 2); g.addWidget(self.txt_version, 1, 3)
        g.addWidget(_make_label("Color:"), 2, 0); g.addWidget(self.txt_color, 2, 1)
        g.addWidget(_make_label("Tipo:"), 2, 2); g.addWidget(self.cmb_tipo, 2, 3)
        gb.setLayout(g)
        tab1_layout.addWidget(gb)

        gb2 = QGroupBox("Datos Tecnicos")
        group_box(gb2)
        g2 = QGridLayout()
        g2.setHorizontalSpacing(16)
        g2.setVerticalSpacing(10)
        self.txt_cilindraje = UpperLineEdit()
        self.cmb_transmision = QComboBox()
        self.cmb_transmision.addItems(TIPOS_TRANSMISION)
        self.cmb_combustible = QComboBox()
        self.cmb_combustible.addItems(TIPOS_COMBUSTIBLE)
        self.txt_motor = UpperLineEdit()
        self.txt_chasis = UpperLineEdit()
        self.sp_km = QDoubleSpinBox()
        self.sp_km.setRange(0, 1e7)
        self.sp_km.setDecimals(0)
        self.sp_km.setSingleStep(1000)
        input_field(self.txt_cilindraje)
        input_combo(self.cmb_transmision)
        input_combo(self.cmb_combustible)
        input_field(self.txt_motor)
        input_field(self.txt_chasis)
        input_spinbox(self.sp_km)
        g2.setColumnMinimumWidth(0, _LABEL_MIN_WIDTH)
        g2.setColumnMinimumWidth(2, _LABEL_MIN_WIDTH)
        g2.setColumnStretch(1, 1)
        g2.setColumnStretch(3, 1)
        g2.addWidget(_make_label("Cilindraje:"), 0, 0); g2.addWidget(self.txt_cilindraje, 0, 1)
        g2.addWidget(_make_label("Transmision:"), 0, 2); g2.addWidget(self.cmb_transmision, 0, 3)
        g2.addWidget(_make_label("Combustible:"), 1, 0); g2.addWidget(self.cmb_combustible, 1, 1)
        g2.addWidget(_make_label("Kilometraje:"), 1, 2); g2.addWidget(self.sp_km, 1, 3)
        g2.addWidget(_make_label("No. Motor:"), 2, 0); g2.addWidget(self.txt_motor, 2, 1)
        g2.addWidget(_make_label("No. Chasis:"), 2, 2); g2.addWidget(self.txt_chasis, 2, 3)
        gb2.setLayout(g2)
        tab1_layout.addWidget(gb2)
        tab1_layout.addStretch()

        # Pestaña 2: Administrativo y Fechas
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setSpacing(14)
        tab2_layout.setContentsMargins(14, 14, 14, 14)

        gb3 = QGroupBox("Administrativo y Financiero")
        group_box(gb3)
        g3 = QGridLayout()
        g3.setHorizontalSpacing(16)
        g3.setVerticalSpacing(10)
        self.txt_propietario = UpperLineEdit()
        self.sp_costo = QDoubleSpinBox()
        self.sp_costo.setRange(0, 1e9)
        self.sp_costo.setPrefix("$ ")
        self.sp_costo.setDecimals(0)
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(ESTADOS_AUTO)
        self.cmb_adq = QComboBox()
        self.cmb_adq.addItems(TIPOS_ADQUISICION)
        self.txt_ubicacion = UpperLineEdit()
        self.d_ingreso = QDateEdit(QDate.currentDate())
        self.d_ingreso.setCalendarPopup(True)
        self.d_ingreso.setDisplayFormat("yyyy-MM-dd")
        input_field(self.txt_propietario)
        input_spinbox(self.sp_costo)
        input_combo(self.cmb_estado)
        input_combo(self.cmb_adq)
        input_field(self.txt_ubicacion)
        input_date(self.d_ingreso)
        g3.setColumnMinimumWidth(0, _LABEL_MIN_WIDTH)
        g3.setColumnMinimumWidth(2, _LABEL_MIN_WIDTH)
        g3.setColumnStretch(1, 1)
        g3.setColumnStretch(3, 1)
        g3.addWidget(_make_label("Propietario:"), 0, 0); g3.addWidget(self.txt_propietario, 0, 1)
        g3.addWidget(_make_label("Costo Fijo Mensual:"), 0, 2); g3.addWidget(self.sp_costo, 0, 3)
        g3.addWidget(_make_label("Estado:"), 1, 0); g3.addWidget(self.cmb_estado, 1, 1)
        g3.addWidget(_make_label("Tipo Adquisicion:"), 1, 2); g3.addWidget(self.cmb_adq, 1, 3)
        g3.addWidget(_make_label("Ubicacion Actual:"), 2, 0); g3.addWidget(self.txt_ubicacion, 2, 1)
        g3.addWidget(_make_label("Fecha Ingreso Flota:"), 2, 2); g3.addWidget(self.d_ingreso, 2, 3)
        gb3.setLayout(g3)
        tab2_layout.addWidget(gb3)

        gb4 = QGroupBox("Vencimientos")
        group_box(gb4)
        g4 = QGridLayout()
        g4.setHorizontalSpacing(16)
        g4.setVerticalSpacing(10)
        def _date_widget():
            w = QDateEdit(QDate.currentDate().addYears(1))
            w.setCalendarPopup(True)
            w.setDisplayFormat("yyyy-MM-dd")
            return w
        self.d_soat = _date_widget()
        self.d_tecno = _date_widget()
        self.d_extintor = _date_widget()
        self.d_bateria = _date_widget()
        input_date(self.d_soat)
        input_date(self.d_tecno)
        input_date(self.d_extintor)
        input_date(self.d_bateria)
        g4.setColumnMinimumWidth(0, _LABEL_MIN_WIDTH)
        g4.setColumnMinimumWidth(2, _LABEL_MIN_WIDTH)
        g4.setColumnStretch(1, 1)
        g4.setColumnStretch(3, 1)
        g4.addWidget(_make_label("SOAT:"), 0, 0); g4.addWidget(self.d_soat, 0, 1)
        g4.addWidget(_make_label("Tecnicomecanica:"), 0, 2); g4.addWidget(self.d_tecno, 0, 3)
        g4.addWidget(_make_label("Extintor:"), 1, 0); g4.addWidget(self.d_extintor, 1, 1)
        g4.addWidget(_make_label("Garantia Bateria:"), 1, 2); g4.addWidget(self.d_bateria, 1, 3)
        gb4.setLayout(g4)
        tab2_layout.addWidget(gb4)

        self.txt_obs = QPlainTextEdit()
        self.txt_obs.setMaximumHeight(60)
        self.txt_obs.setPlaceholderText("Observaciones opcionales...")
        input_textedit(self.txt_obs)

        obs_row = QHBoxLayout()
        obs_row.setContentsMargins(0, 4, 0, 0)
        obs_row.setSpacing(12)
        lbl_obs = QLabel("Observaciones:")
        lbl_section(lbl_obs)
        obs_row.addWidget(lbl_obs)
        obs_row.addWidget(self.txt_obs, stretch=1)
        tab2_layout.addLayout(obs_row)
        tab2_layout.addStretch()

        self.tabs.addTab(tab1, "🚗  General y Técnico")
        self.tabs.addTab(tab2, "💼  Administrativo y Fechas")

    def _cargar(self, placa: str):
        try:
            d = AutoService.obtener(placa)
        except DinamoBaseError as e:
            self._msg_critical("Error", e.mensaje_usuario)
            return
        self.txt_placa.setText(d.get("placa", ""))
        self.txt_marca.setText(d.get("marca", ""))
        self.txt_modelo.setText(d.get("modelo", ""))
        self.txt_version.setText(d.get("version", ""))
        self.txt_color.setText(d.get("color", ""))
        self.cmb_tipo.setCurrentText(d.get("tipo", "Automovil"))
        self.txt_cilindraje.setText(d.get("cilindraje", ""))
        self.cmb_transmision.setCurrentText(d.get("transmision", "Automatica"))
        self.cmb_combustible.setCurrentText(d.get("combustible", "Gasolina"))
        self.txt_motor.setText(d.get("no_motor", ""))
        self.txt_chasis.setText(d.get("no_chasis", ""))
        self.txt_propietario.setText(d.get("propietario", ""))
        self.sp_costo.setValue(float(d.get("costo_fijo_mensual", 0)))
        self.cmb_estado.setCurrentText(d.get("estado", "Disponible"))
        self.sp_km.setValue(float(d.get("kilometraje", 0)))
        self.txt_ubicacion.setText(d.get("ubicacion", ""))
        self.cmb_adq.setCurrentText(d.get("tipo_adquisicion", "Propio"))
        self.txt_obs.setPlainText(d.get("observaciones", ""))
        for widget, key in [
            (self.d_soat, "vencimiento_soat"), (self.d_tecno, "vencimiento_tecnico"),
            (self.d_extintor, "vencimiento_extintor"), (self.d_bateria, "vencimiento_bateria"),
            (self.d_ingreso, "fecha_ingreso"),
        ]:
            val = d.get(key)
            if val:
                try:
                    widget.setDate(datetime.strptime(str(val)[:10], "%Y-%m-%d").date())
                except ValueError:
                    pass

    def _guardar(self):
        if not self.txt_placa.text().strip():
            self._msg_warning("Validacion", "La placa es obligatoria")
            self.txt_placa.setFocus()
            return
        datos = {
            "placa": self.txt_placa.text().strip(),
            "marca": self.txt_marca.text().strip(),
            "modelo": self.txt_modelo.text().strip(),
            "version": self.txt_version.text().strip(),
            "color": self.txt_color.text().strip(),
            "tipo": self.cmb_tipo.currentText(),
            "cilindraje": self.txt_cilindraje.text().strip(),
            "transmision": self.cmb_transmision.currentText(),
            "combustible": self.cmb_combustible.currentText(),
            "no_motor": self.txt_motor.text().strip(),
            "no_chasis": self.txt_chasis.text().strip(),
            "propietario": self.txt_propietario.text().strip(),
            "estado": self.cmb_estado.currentText(),
            "costo_fijo_mensual": self.sp_costo.value(),
            "kilometraje": self.sp_km.value(),
            "ubicacion": self.txt_ubicacion.text().strip(),
            "vencimiento_soat": self.d_soat.date().toString("yyyy-MM-dd"),
            "vencimiento_tecnico": self.d_tecno.date().toString("yyyy-MM-dd"),
            "vencimiento_extintor": self.d_extintor.date().toString("yyyy-MM-dd"),
            "vencimiento_bateria": self.d_bateria.date().toString("yyyy-MM-dd"),
            "observaciones": self.txt_obs.toPlainText(),
            "tipo_adquisicion": self.cmb_adq.currentText(),
            "fecha_ingreso": self.d_ingreso.date().toString("yyyy-MM-dd"),
        }
        try:
            AutoService.guardar(datos)
            self._msg_info("Exito", "Vehiculo guardado correctamente")
            self.accept()
        except DinamoBaseError as e:
            self._msg_critical("Error", e.mensaje_usuario)

    def _msg_critical(self, titulo, mensaje):
        ModernMessageBox.error(self, titulo, mensaje)

    def _msg_warning(self, titulo, mensaje):
        ModernMessageBox.warning(self, titulo, mensaje)

    def _msg_info(self, titulo, mensaje):
        ModernMessageBox.success(self, titulo, mensaje)


class AutosWidget(BaseWidget):
    """Panel principal de gestion de flota."""

    _COLOR_ESTADO = {
        "Disponible": COLOR_ESTADO_DISPONIBLE,
        "Rentado": COLOR_ESTADO_RENTADO,
        "Mantenimiento": COLOR_ESTADO_MANTENIMIENTO,
        "Inactivo": COLOR_ESTADO_INACTIVO,
    }

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Banner superior ──────────────────────────────────────────
        banner = QWidget()
        banner.setFixedHeight(64)
        banner.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {_NAV}, stop:1 {_BLUE});
        """)
        b_lay = QHBoxLayout(banner)
        b_lay.setContentsMargins(22, 0, 22, 0)
        b_lay.setSpacing(14)

        ico = QLabel("🚗")
        ico.setFixedSize(40, 40)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setStyleSheet("""
            QLabel {
                background: rgba(255,255,255,0.15);
                border-radius: 20px;
                font-size: 18px;
            }
        """)
        b_lay.addWidget(ico)

        t_col = QVBoxLayout()
        t_col.setSpacing(1)
        t_col.addStretch()
        lbl_t = QLabel("Gestion de Flota")
        lbl_t.setStyleSheet("QLabel { color:#fff; font-size:14pt; font-weight:700; background:transparent; }")
        lbl_s = QLabel("Administracion de vehiculos y flota vehicular")
        lbl_s.setStyleSheet("QLabel { color:rgba(255,255,255,0.72); font-size:9pt; background:transparent; }")
        t_col.addWidget(lbl_t)
        t_col.addWidget(lbl_s)
        t_col.addStretch()
        b_lay.addLayout(t_col)
        b_lay.addStretch()

        btn_ref = QPushButton("↻  Actualizar")
        btn_ref.setStyleSheet("""
            QPushButton {
                background: rgba(255,255,255,0.15);
                color: #ffffff;
                border: 1px solid rgba(255,255,255,0.35);
                border-radius: 7px;
                padding: 7px 18px;
                font-size: 9.5pt;
                font-weight: 600;
            }
            QPushButton:hover { background: rgba(255,255,255,0.25); }
            QPushButton:pressed { background: rgba(255,255,255,0.10); }
        """)
        btn_ref.clicked.connect(self.cargar_datos)
        b_lay.addWidget(btn_ref)
        main_layout.addWidget(banner)

        # ── Área de contenido ─────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        edit_search(self.txt_buscar)
        self.txt_buscar.setPlaceholderText("Buscar por placa, marca o modelo...")
        self.txt_buscar.setMinimumWidth(300)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        btn_act = QPushButton("Actualizar")
        btn_default(btn_act)
        btn_act.clicked.connect(self.cargar_datos)
        top.addWidget(btn_act)

        btn_nuevo = QPushButton("+ Nuevo Vehiculo")
        btn_success(btn_nuevo)
        btn_nuevo.clicked.connect(self._nuevo)
        top.addWidget(btn_nuevo)
        c_lay.addLayout(top)

        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        table_widget(self.tabla)
        self.ajustar_tabla(self.tabla, ["Placa", "Marca / Modelo", "Color", "Estado", "KM", "Ubicacion", "Ingreso", ""])

        # --- Configurar columnas individualmente para que el boton Editar sea visible ---
        header = self.tabla.horizontalHeader()
        # Placa: ancho fijo
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(0, 90)
        # Marca/Modelo: stretch para ocupar espacio disponible
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Color
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(2, 120)
        # Estado
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(3, 120)
        # KM
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(4, 100)
        # Ubicacion
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(5, 140)
        # Ingreso
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(6, 110)
        # Columna Editar: Fixed con ancho suficiente para el boton
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(7, 90)

        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_contextual)
        c_lay.addWidget(self.tabla)

        self._lista: list[dict] = []
        self.cargar_datos()

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self._lista = self.ejecutar_seguro(AutoService.listar) or []
        self._pintar_filas(self._lista)

    def _pintar_filas(self, datos: list[dict]):
        self.tabla.setRowCount(0)
        for r in datos:
            i = self.tabla.rowCount()
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(r.get("placa", "")))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"{r.get('marca', '')} {r.get('modelo', '')}"))
            self.tabla.setItem(i, 2, QTableWidgetItem(r.get("color", "")))
            estado = r.get("estado", "")
            st = QTableWidgetItem(estado)
            color_estado = self._COLOR_ESTADO.get(estado)
            if color_estado:
                st.setForeground(QBrush(QColor(color_estado)))
                from PySide6.QtGui import QFont
                fnt = QFont(st.font())
                fnt.setBold(True)
                st.setFont(fnt)
            self.tabla.setItem(i, 3, st)
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{r.get('kilometraje', 0):,.0f}"))
            self.tabla.setItem(i, 5, QTableWidgetItem(r.get("ubicacion", "")))
            fecha = r.get("fecha_ingreso")
            self.tabla.setItem(i, 6, QTableWidgetItem(fecha.strftime("%Y-%m-%d") if fecha else ""))

            # Boton Editar con estilo visible
            btn = QPushButton("Editar")
            btn_icon(btn)
            btn.setFixedSize(78, 32)
            btn.clicked.connect(lambda _, p=r.get("placa"): self._editar(p))
            self.tabla.setCellWidget(i, 7, btn)

        # Ajustar altura de filas para que los botones se vean completos
        self.tabla.resizeRowsToContents()

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        if not txt:
            self._pintar_filas(self._lista)
            return
        filtrados = [a for a in self._lista if txt in a.get("placa", "").lower() or txt in a.get("marca", "").lower() or txt in a.get("modelo", "").lower() or txt in a.get("color", "").lower() or txt in a.get("ubicacion", "").lower()]
        self._pintar_filas(filtrados)

    def _nuevo(self):
        if DialogoAuto(self).exec():
            self.cargar_datos()

    def _editar(self, placa: str):
        if DialogoAuto(self, placa).exec():
            self.cargar_datos()

    def _menu_contextual(self, pos):
        row = self.tabla.rowAt(pos.y())
        if row < 0 or row >= len(self._lista):
            return
        placa = self._lista[row].get("placa", "")
        menu = QMenu(self)
        acc_edit = menu.addAction("Editar vehiculo")
        acc_disp = menu.addAction("Marcar Disponible")
        acc_mant = menu.addAction("Marcar Mantenimiento")
        acc_inac = menu.addAction("Marcar Inactivo")
        acc = menu.exec(self.tabla.viewport().mapToGlobal(pos))
        if acc == acc_edit:
            self._editar(placa)
        elif acc in (acc_disp, acc_mant, acc_inac):
            nuevo_estado = {acc_disp: "Disponible", acc_mant: "Mantenimiento", acc_inac: "Inactivo"}[acc]
            self._cambiar_estado(placa, nuevo_estado)

    def _cambiar_estado(self, placa: str, nuevo_estado: str):
        try:
            datos = AutoService.obtener(placa)
            datos["estado"] = nuevo_estado
            AutoService.guardar(datos)
            self.mostrar_exito(f"Estado actualizado a {nuevo_estado}")
            self.cargar_datos()
        except DinamoBaseError as e:
            self.mostrar_error(e.mensaje_usuario)
        except Exception as e:
            self.mostrar_error(str(e))
