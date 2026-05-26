"""
views/autos_view.py — Gestion de flota (vista)

Solo maneja la UI. Toda la logica va a AutoService.
Estilos vía QSS class-based (temas Claro/Oscuro desde themes.py).
"""

from datetime import datetime, date

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QPlainTextEdit,
    QGridLayout,
    QMenu,
    QTabWidget,
    QHeaderView,
    QWidget,
    QFrame,
)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QColor, QBrush

from core.config import (
    TIPOS_AUTO,
    TIPOS_TRANSMISION,
    TIPOS_COMBUSTIBLE,
    ESTADOS_AUTO,
    TIPOS_ADQUISICION,
    COLOR_ESTADO_DISPONIBLE,
    COLOR_ESTADO_RENTADO,
    COLOR_ESTADO_MANTENIMIENTO,
    COLOR_ESTADO_INACTIVO,
)
from core.exceptions import DinamoBaseError
from services.auto_service import AutoService
from views.components import ModernMessageBox
from views.base_dialog import BaseDialog
from views.base_widget import BaseWidget
from views.widgets import UpperLineEdit

# Ancho minimo para las columnas de labels en los formularios del dialogo
_LABEL_MIN_WIDTH = 150


def _make_label(text: str, required: bool = False) -> QLabel:
    """Crea un QLabel con ancho minimo para evitar truncamiento."""
    if required:
        lbl = QLabel()
        lbl.setText(f"{text} *")
    else:
        lbl = QLabel(text)
    lbl.setMinimumWidth(_LABEL_MIN_WIDTH)
    return lbl


def _make_card(title: str, parent, icon: str = "") -> tuple[QFrame, QGridLayout]:
    """Card con borde de acento izquierdo, icono opcional.
    Retorna (card_frame, grid_layout) donde la fila 0 ya tiene el encabezado.
    """
    card = QFrame(parent)
    card.setFrameShape(QFrame.Shape.StyledPanel)
    card.setProperty("class", "form-card")

    layout = QGridLayout(card)
    layout.setSpacing(10)
    layout.setContentsMargins(16, 14, 16, 14)

    # --- Encabezado del card ---
    header_row = QHBoxLayout()
    header_row.setSpacing(6)

    if icon:
        ico = QLabel(icon)
        ico.setFixedSize(22, 22)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setProperty("class", "card-icon")
        header_row.addWidget(ico)

    titulo = QLabel(title)
    titulo.setProperty("class", "section")
    header_row.addWidget(titulo)
    header_row.addStretch()

    sep = QFrame()
    sep.setFrameShape(QFrame.Shape.HLine)
    sep.setProperty("class", "divider")

    header_widget = QWidget()
    header_widget.setStyleSheet("QWidget { background: transparent; border: none; }")
    hv = QVBoxLayout(header_widget)
    hv.setContentsMargins(0, 0, 0, 6)
    hv.setSpacing(6)
    hv.addLayout(header_row)
    hv.addWidget(sep)

    layout.addWidget(header_widget, 0, 0, 1, 2)
    layout.setColumnStretch(0, 0)
    layout.setColumnStretch(1, 1)

    return card, layout


class DialogoAuto(BaseDialog):
    """Dialogo para crear o editar un vehiculo."""

    def __init__(self, parent=None, placa_editar: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gestion de Vehiculo")
        self.setMinimumSize(950, 680)
        self.placa_editar = placa_editar

        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Banner de encabezado ──────────────────────────────────────────
        from views.layouts.form_helpers import build_dialog_header

        titulo = "Editar Vehiculo" if placa_editar else "Nuevo Vehiculo"
        subtitulo = (
            f"Modificando registro: {placa_editar}"
            if placa_editar
            else "Ingresa la informacion del vehiculo para agregarlo a la flota"
        )
        root.addWidget(build_dialog_header("🚗", titulo, subtitulo))

        # ── Cuerpo principal ─────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("dlg_body")
        layout = QVBoxLayout(body)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 14)

        self.tabs = QTabWidget()

        self._construir_form()

        layout.addWidget(self.tabs, stretch=1)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("class", "divider")
        layout.addWidget(sep)

        # ── Fila de botones ───────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        hint = QLabel("* Campos obligatorios")
        hint.setProperty("class", "subtitle")
        btn_row.addWidget(hint)
        btn_row.addStretch()

        btn_cancel = QPushButton("  Cancelar")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  Guardar Vehiculo")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._guardar)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        root.addWidget(body)

        if placa_editar:
            self._init_overlay("Cargando datos del vehiculo...")
            QTimer.singleShot(0, self._deferred_load)

    def _construir_form(self):
        # Pestaña 1: General y Técnico
        tab1 = QWidget()
        tab1_layout = QVBoxLayout(tab1)
        tab1_layout.setSpacing(14)
        tab1_layout.setContentsMargins(14, 14, 14, 14)

        # Card: Informacion Basica
        card_basica, g = _make_card("Informacion Basica", self, "📋")
        self.txt_placa = UpperLineEdit()
        self.txt_marca = UpperLineEdit()
        self.txt_modelo = UpperLineEdit()
        self.txt_version = UpperLineEdit()
        self.txt_color = UpperLineEdit()
        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(TIPOS_AUTO)
        if self.placa_editar:
            self.txt_placa.setReadOnly(True)
        g.addWidget(_make_label("Placa", required=True), 1, 0)
        g.addWidget(self.txt_placa, 1, 1)
        g.addWidget(_make_label("Marca:"), 2, 0)
        g.addWidget(self.txt_marca, 2, 1)
        g.addWidget(_make_label("Modelo:"), 1, 2)
        g.addWidget(self.txt_modelo, 1, 3)
        g.addWidget(_make_label("Version:"), 2, 2)
        g.addWidget(self.txt_version, 2, 3)
        g.addWidget(_make_label("Color:"), 3, 0)
        g.addWidget(self.txt_color, 3, 1)
        g.addWidget(_make_label("Tipo:"), 3, 2)
        g.addWidget(self.cmb_tipo, 3, 3)
        tab1_layout.addWidget(card_basica)

        # Card: Datos Tecnicos
        card_tecnica, g2 = _make_card("Datos Tecnicos", self, "🔧")
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
        g2.addWidget(_make_label("Cilindraje:"), 1, 0)
        g2.addWidget(self.txt_cilindraje, 1, 1)
        g2.addWidget(_make_label("Transmision:"), 1, 2)
        g2.addWidget(self.cmb_transmision, 1, 3)
        g2.addWidget(_make_label("Combustible:"), 2, 0)
        g2.addWidget(self.cmb_combustible, 2, 1)
        g2.addWidget(_make_label("Kilometraje:"), 2, 2)
        g2.addWidget(self.sp_km, 2, 3)
        g2.addWidget(_make_label("No. Motor:"), 3, 0)
        g2.addWidget(self.txt_motor, 3, 1)
        g2.addWidget(_make_label("No. Chasis:"), 3, 2)
        g2.addWidget(self.txt_chasis, 3, 3)
        tab1_layout.addWidget(card_tecnica)
        tab1_layout.addStretch()

        # Pestaña 2: Administrativo y Fechas
        tab2 = QWidget()
        tab2_layout = QVBoxLayout(tab2)
        tab2_layout.setSpacing(14)
        tab2_layout.setContentsMargins(14, 14, 14, 14)

        # Card: Administrativo y Financiero
        card_admin, g3 = _make_card("Administrativo y Financiero", self, "💼")
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
        g3.addWidget(_make_label("Propietario:"), 1, 0)
        g3.addWidget(self.txt_propietario, 1, 1)
        g3.addWidget(_make_label("Costo Fijo Mensual:"), 1, 2)
        g3.addWidget(self.sp_costo, 1, 3)
        g3.addWidget(_make_label("Estado:"), 2, 0)
        g3.addWidget(self.cmb_estado, 2, 1)
        g3.addWidget(_make_label("Tipo Adquisicion:"), 2, 2)
        g3.addWidget(self.cmb_adq, 2, 3)
        g3.addWidget(_make_label("Ubicacion Actual:"), 3, 0)
        g3.addWidget(self.txt_ubicacion, 3, 1)
        g3.addWidget(_make_label("Fecha Ingreso Flota:"), 3, 2)
        g3.addWidget(self.d_ingreso, 3, 3)
        tab2_layout.addWidget(card_admin)

        # Card: Vencimientos
        card_venc, g4 = _make_card("Vencimientos", self, "📅")

        def _date_widget():
            w = QDateEdit(QDate.currentDate().addYears(1))
            w.setCalendarPopup(True)
            w.setDisplayFormat("yyyy-MM-dd")
            return w

        self.d_soat = _date_widget()
        self.d_tecno = _date_widget()
        self.d_extintor = _date_widget()
        self.d_bateria = _date_widget()
        g4.addWidget(_make_label("SOAT:"), 1, 0)
        g4.addWidget(self.d_soat, 1, 1)
        g4.addWidget(_make_label("Tecnicomecanica:"), 1, 2)
        g4.addWidget(self.d_tecno, 1, 3)
        g4.addWidget(_make_label("Extintor:"), 2, 0)
        g4.addWidget(self.d_extintor, 2, 1)
        g4.addWidget(_make_label("Garantia Bateria:"), 2, 2)
        g4.addWidget(self.d_bateria, 2, 3)
        tab2_layout.addWidget(card_venc)

        self.txt_obs = QPlainTextEdit()
        self.txt_obs.setMaximumHeight(60)
        self.txt_obs.setPlaceholderText("Observaciones opcionales...")

        obs_row = QHBoxLayout()
        obs_row.setContentsMargins(0, 4, 0, 0)
        obs_row.setSpacing(12)
        lbl_obs = QLabel("Observaciones:")
        lbl_obs.setProperty("class", "section")
        obs_row.addWidget(lbl_obs)
        obs_row.addWidget(self.txt_obs, stretch=1)
        tab2_layout.addLayout(obs_row)
        tab2_layout.addStretch()

        self.tabs.addTab(tab1, "🚗  General y Técnico")
        self.tabs.addTab(tab2, "💼  Administrativo y Fechas")

    def _deferred_load(self):
        self._deferred_call(lambda: self._cargar(self.placa_editar))

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
            (self.d_soat, "vencimiento_soat"),
            (self.d_tecno, "vencimiento_tecnico"),
            (self.d_extintor, "vencimiento_extintor"),
            (self.d_bateria, "vencimiento_bateria"),
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Banner superior ──────────────────────────────────────────
        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            "🚗",
            "Gestion de Flota",
            "Administracion de vehiculos y flota vehicular",
            self.cargar_datos,
        )
        main_layout.addWidget(banner)

        # ── Área de contenido ─────────────────────────────────────────
        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setProperty("class", "search")
        self.txt_buscar.setPlaceholderText("Buscar por placa, marca o modelo...")
        self.txt_buscar.setMinimumWidth(220)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(
            ["Todos los vehículos", "🔧 En Mantenimiento", "✅ Disponibles", "❌ Inactivos"]
        )
        self.cmb_filtro.setCurrentIndex(0)
        self.cmb_filtro.setMinimumWidth(180)
        self.cmb_filtro.currentIndexChanged.connect(self._filtrar)
        top.addWidget(self.cmb_filtro)

        btn_act = QPushButton("Actualizar")
        btn_act.setProperty("class", "ghost")
        btn_act.clicked.connect(self.cargar_datos)
        top.addWidget(btn_act)

        btn_nuevo = QPushButton("+ Nuevo Vehiculo")
        btn_nuevo.setProperty("class", "success")
        btn_nuevo.clicked.connect(self._nuevo)
        top.addWidget(btn_nuevo)
        c_lay.addLayout(top)

        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.ajustar_tabla(
            self.tabla,
            [
                "Placa",
                "Marca / Modelo",
                "Color",
                "Estado",
                "KM",
                "Ubicacion",
                "Ingreso",
                "Vencimientos",
                "",
            ],
        )

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
        # Vencimientos
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(7, 130)
        # Columna Editar: Fixed con ancho suficiente para el boton
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(8, 90)

        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_contextual)
        c_lay.addWidget(self.tabla)

        self._lista: list[dict] = []
        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self._lista = self.ejecutar_seguro(AutoService.listar) or []
        self._pintar_filas(self._lista)

    def _pintar_filas(self, datos: list[dict]):
        self.tabla.setRowCount(0)
        today = date.today()
        for r in datos:
            i = self.tabla.rowCount()
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(r.get("placa", "")))
            self.tabla.setItem(
                i, 1, QTableWidgetItem(f"{r.get('marca', '')} {r.get('modelo', '')}")
            )
            self.tabla.setItem(i, 2, QTableWidgetItem(r.get("color", "")))
            from views.components.status_badge import StatusBadge

            estado = r.get("estado", "")
            _ESTADO_BADGE_MAP = {
                "Disponible": "success",
                "Rentado": "info",
                "Mantenimiento": "warning",
                "Inactivo": "danger",
            }
            badge = StatusBadge(estado, _ESTADO_BADGE_MAP.get(estado, "info"))
            self.tabla.setCellWidget(i, 3, badge)
            self.tabla.setItem(i, 4, QTableWidgetItem(f"{r.get('kilometraje', 0):,.0f}"))
            self.tabla.setItem(i, 5, QTableWidgetItem(r.get("ubicacion", "")))
            fecha = r.get("fecha_ingreso")
            self.tabla.setItem(i, 6, QTableWidgetItem(fecha.strftime("%Y-%m-%d") if fecha else ""))

            # ── Columna Vencimientos ──
            venc_campos = [
                ("vencimiento_soat", "SOAT"),
                ("vencimiento_tecnico", "Técnico"),
                ("vencimiento_extintor", "Extintor"),
                ("vencimiento_bateria", "Batería"),
            ]
            venc_list = []
            for campo, label in venc_campos:
                val = r.get(campo)
                if val:
                    try:
                        d = (
                            val
                            if isinstance(val, date)
                            else datetime.strptime(str(val)[:10], "%Y-%m-%d").date()
                        )
                        dias = (d - today).days
                        venc_list.append((dias, label, d))
                    except (ValueError, TypeError):
                        pass

            if venc_list:
                nearest = min(venc_list, key=lambda x: x[0])
                dias, label, fecha_venc = nearest
                if dias < 0:
                    texto = f"🔴 {label} vencido"
                elif dias <= 15:
                    texto = f"🟡 {label} en {dias}d"
                else:
                    texto = f"🟢 {label} en {dias}d"

                venc_item = QTableWidgetItem(texto)
                venc_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if dias < 0:
                    venc_item.setForeground(QBrush(QColor("#ef4444")))
                    from PySide6.QtGui import QFont

                    fnt = QFont(venc_item.font())
                    fnt.setBold(True)
                    venc_item.setFont(fnt)
                    venc_item.setToolTip(f"{label} vencido desde hace {abs(dias)} días")
                elif dias <= 15:
                    venc_item.setForeground(QBrush(QColor("#f97316")))
                    from PySide6.QtGui import QFont

                    fnt = QFont(venc_item.font())
                    fnt.setBold(True)
                    venc_item.setFont(fnt)
                    venc_item.setToolTip(f"{label} vence en {dias} días")
                elif dias <= 30:
                    venc_item.setForeground(QBrush(QColor("#eab308")))
                else:
                    venc_item.setForeground(QBrush(QColor("#22c55e")))
                self.tabla.setItem(i, 7, venc_item)
            else:
                self.tabla.setItem(i, 7, QTableWidgetItem("—"))

            # Boton Editar con estilo visible
            btn = QPushButton("Editar")
            btn.setProperty("class", "icon")
            btn.setFixedSize(78, 32)
            btn.clicked.connect(lambda _, p=r.get("placa"): self._editar(p))
            self.tabla.setCellWidget(i, 8, btn)

        # Ajustar altura de filas para que los botones se vean completos
        self.tabla.resizeRowsToContents()

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        filtro_estado = (
            self.cmb_filtro.currentIndex()
        )  # 0=Todos, 1=Mantenimiento, 2=Disponibles, 3=Inactivos

        filtrados = self._lista

        # 1. Filtrar por estado
        if filtro_estado == 1:
            filtrados = [a for a in filtrados if a.get("estado", "") == "Mantenimiento"]
        elif filtro_estado == 2:
            filtrados = [a for a in filtrados if a.get("estado", "") == "Disponible"]
        elif filtro_estado == 3:
            filtrados = [a for a in filtrados if a.get("estado", "") == "Inactivo"]

        # 2. Filtrar por texto
        if txt:
            filtrados = [
                a
                for a in filtrados
                if txt in a.get("placa", "").lower()
                or txt in a.get("marca", "").lower()
                or txt in a.get("modelo", "").lower()
                or txt in a.get("color", "").lower()
                or txt in a.get("ubicacion", "").lower()
            ]

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
            nuevo_estado = {
                acc_disp: "Disponible",
                acc_mant: "Mantenimiento",
                acc_inac: "Inactivo",
            }[acc]
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
