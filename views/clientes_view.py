"""
views/clientes_view.py — Directorio de clientes

Estilos via QSS class-based (themes.py).
"""

from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QLineEdit,
    QComboBox,
    QTabWidget,
    QDateEdit,
    QWidget,
    QTableWidget,
    QMenu,
    QScrollArea,
    QHeaderView,
    QGridLayout,
    QFrame,
    QApplication,
)
from PySide6.QtCore import Qt, QDate, QTimer
from views.base_dialog import BaseDialog
from core.config import (
    TIPOS_DOC,
    ESTADOS_CLIENTE,
    COLOR_ESTADO_ACTIVO,
    COLOR_ESTADO_VIP,
    COLOR_ESTADO_LISTA_NEGRA,
    COLOR_PELIGRO,
)
from core.exceptions import DinamoBaseError
from services.cliente_service import ClienteService
from views.base_widget import BaseWidget
from views.components.form_validators import (
    FormValidator,
    Required,
    Email,
    Phone,
    make_error_label,
)
from views.components import ModernMessageBox
# Estilos via QSS global (sin styles.py inline)


_CLR_REQMARK = COLOR_PELIGRO  # Rojo para asterisco obligatorio


def _make_label(text: str, required: bool = False) -> QLabel:
    """Crea un QLabel de campo; si required=True agrega asterisco rojo."""
    if required:
        lbl = QLabel()
        lbl.setText(f"{text} *")
    else:
        lbl = QLabel(text)
    lbl.setMinimumWidth(125)
    return lbl


def _make_card(title: str, parent, icon: str = "") -> tuple[QFrame, QGridLayout]:
    """
    Card con borde de acento izquierdo, icono opcional y sombra sutil.
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
    layout.setColumnStretch(0, 0)  # columna de etiquetas: tamaño fijo
    layout.setColumnStretch(1, 1)  # columna de inputs:    se expande

    return card, layout


class ClienteFormDialog(BaseDialog):
    # BUGFIX: heredar de QDialog *y* BaseWidget (que también hereda de QWidget)
    # hace que shiboken/PySide6 intente inicializar el objeto C++ dos veces →
    # RuntimeError "You can't initialize a QDialog object twice".
    # Solución: heredar solo de QDialog y llamar a ModernMessageBox directamente.
    """Dialogo para crear o editar un cliente — UI refinada."""

    def __init__(self, parent=None, datos: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ficha de Cliente")
        self._datos = datos or {}
        is_edit = bool(datos)

        screen = QApplication.primaryScreen().availableGeometry()
        self.setMinimumSize(int(screen.width() * 0.75), int(screen.height() * 0.80))
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Banner de encabezado ──────────────────────────────────────────
        from views.layouts.form_helpers import build_dialog_header

        if is_edit and datos:
            nombre = (
                datos.get("nombre_completo")
                or f"{datos.get('nombres', '')} {datos.get('apellidos', '')}".strip()
            )
            titulo = "Editar Cliente"
            subtitulo = nombre or "Sin nombre registrado"
        else:
            titulo = "Nuevo Cliente"
            subtitulo = "Completa la información para registrar al cliente"
        root.addWidget(build_dialog_header("👤", titulo, subtitulo))

        # ── Cuerpo principal ─────────────────────────────────────────────
        body = QWidget()
        body.setObjectName("dlg_body")
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(12)
        body_lay.setContentsMargins(20, 16, 20, 14)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("main_tabs")

        tab1 = QWidget()
        self._construir_tab_personal(tab1)
        tab2 = QWidget()
        self._construir_tab_licencia(tab2)
        self.tabs.addTab(tab1, "👤   Datos Personales")
        self.tabs.addTab(tab2, "🚗   Licencia / Ubicación / Estado")
        body_lay.addWidget(self.tabs)

        # Separador
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("class", "divider")
        body_lay.addWidget(sep)

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

        btn_save = QPushButton("💾  Guardar Ficha")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._guardar)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        body_lay.addLayout(btn_row)

        root.addWidget(body)

        # ── Validador de formulario ──────────────────────────────────────────
        self._validator = FormValidator()
        self._construir_validacion()

        if datos:
            self._cargar()

        # Carga diferida de opciones geograficas
        self._init_overlay("Cargando opciones geograficas...")
        QTimer.singleShot(0, lambda: self._deferred_call(self._deferred_load_geo))

    # ------------------------------------------------------------------ #
    #  PESTAÑA 1 — Datos Personales (11 campos, 2 columnas de cards)     #
    # ------------------------------------------------------------------ #
    def _construir_tab_personal(self, tab):
        # QScrollArea para que los cards nunca queden cortados
        scroll = QScrollArea(tab)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )

        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        outer = QGridLayout(container)
        outer.setSpacing(14)
        outer.setContentsMargins(14, 14, 14, 14)

        # --- Columna 0: Documentación + Contacto ---
        card_doc, grid_doc = _make_card("Documentación", self, "🪪")
        self.cmb_tipo_doc = QComboBox()
        self.cmb_tipo_doc.addItems(TIPOS_DOC)
        self.txt_no_doc = QLineEdit()
        self.txt_no_doc.setPlaceholderText("Número único de documento")

        self._error_no_doc = make_error_label()
        grid_doc.addWidget(_make_label("Tipo de Documento:"), 1, 0)
        grid_doc.addWidget(self.cmb_tipo_doc, 1, 1)
        grid_doc.addWidget(_make_label("No. Documento", required=True), 2, 0)
        grid_doc.addWidget(self.txt_no_doc, 2, 1)
        grid_doc.addWidget(self._error_no_doc, 3, 0, 1, 2)

        card_cont, grid_cont = _make_card("Contacto", self, "📞")
        self.txt_celular = QLineEdit()
        self.txt_celular.setPlaceholderText("Ej: 300 000 0000")
        self.txt_celular2 = QLineEdit()
        self.txt_celular2.setPlaceholderText("Opcional")
        self.txt_email = QLineEdit()
        self.txt_email.setPlaceholderText("correo@ejemplo.com")

        self._error_celular = make_error_label()
        self._error_email = make_error_label()
        grid_cont.addWidget(_make_label("Celular Principal"), 1, 0)
        grid_cont.addWidget(self.txt_celular, 1, 1)
        grid_cont.addWidget(self._error_celular, 2, 0, 1, 2)
        grid_cont.addWidget(_make_label("Celular Secundario"), 3, 0)
        grid_cont.addWidget(self.txt_celular2, 3, 1)
        grid_cont.addWidget(_make_label("Email"), 4, 0)
        grid_cont.addWidget(self.txt_email, 4, 1)
        grid_cont.addWidget(self._error_email, 5, 0, 1, 2)

        outer.addWidget(card_doc, 0, 0)
        outer.addWidget(card_cont, 1, 0)

        # --- Columna 1: Nombres + Ubicación ---
        card_nom, grid_nom = _make_card("Nombres", self, "✍️")
        self.txt_nombres = QLineEdit()
        self.txt_nombres.setPlaceholderText("Nombres del cliente")
        self.txt_apellidos = QLineEdit()
        self.txt_apellidos.setPlaceholderText("Apellidos del cliente")

        self._error_nombres = make_error_label()
        grid_nom.addWidget(_make_label("Nombres", required=True), 1, 0)
        grid_nom.addWidget(self.txt_nombres, 1, 1)
        grid_nom.addWidget(self._error_nombres, 2, 0, 1, 2)
        grid_nom.addWidget(_make_label("Apellidos"), 3, 0)
        grid_nom.addWidget(self.txt_apellidos, 3, 1)

        card_geo, grid_geo = _make_card("Ubicación", self, "🌍")
        self.txt_nacion = QLineEdit()
        self.txt_nacion.setPlaceholderText("Ej: Colombiana")
        self.cmb_pais = QComboBox()
        self.cmb_pais.setEditable(True)
        self.cmb_estado_reg = QComboBox()
        self.cmb_estado_reg.setEditable(True)
        self.cmb_ciudad = QComboBox()
        self.cmb_ciudad.setEditable(True)

        grid_geo.addWidget(_make_label("Nacionalidad"), 1, 0)
        grid_geo.addWidget(self.txt_nacion, 1, 1)
        grid_geo.addWidget(_make_label("País Origen"), 2, 0)
        grid_geo.addWidget(self.cmb_pais, 2, 1)
        grid_geo.addWidget(_make_label("Estado/Región"), 3, 0)
        grid_geo.addWidget(self.cmb_estado_reg, 3, 1)
        grid_geo.addWidget(_make_label("Ciudad"), 4, 0)
        grid_geo.addWidget(self.cmb_ciudad, 4, 1)

        self.cmb_pais.currentTextChanged.connect(self._on_pais_changed)
        self.cmb_estado_reg.currentTextChanged.connect(self._on_region_changed)

        outer.addWidget(card_nom, 0, 1)
        outer.addWidget(card_geo, 1, 1)

        # Columnas iguales
        outer.setColumnStretch(0, 1)
        outer.setColumnStretch(1, 1)
        outer.setRowStretch(2, 1)

        scroll.setWidget(container)
        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)

    # ------------------------------------------------------------------ #
    #  PESTAÑA 2 — Licencia/Ubicación/Estado (8 campos, 2 columnas)      #
    # ------------------------------------------------------------------ #
    def _construir_tab_licencia(self, tab):
        # QScrollArea para que los cards nunca queden cortados
        scroll = QScrollArea(tab)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet(
            "QScrollArea { background: transparent; border: none; }"
            "QScrollArea > QWidget > QWidget { background: transparent; }"
        )

        container = QWidget()
        container.setStyleSheet("QWidget { background: transparent; }")
        outer = QGridLayout(container)
        outer.setSpacing(14)
        outer.setContentsMargins(14, 14, 14, 14)

        # --- Columna 0: Licencia + Estado ---
        card_lic, grid_lic = _make_card("Licencia de Conducción", self, "🪪")
        self.txt_licencia = QLineEdit()
        self.txt_licencia.setPlaceholderText("Número de licencia")
        self.txt_tipo_lic = QLineEdit()
        self.txt_tipo_lic.setPlaceholderText("Ej: B1, C1, Internacional")
        self.date_venc_lic = QDateEdit(QDate.currentDate().addYears(1))
        self.date_venc_lic.setCalendarPopup(True)
        self.date_venc_lic.setDisplayFormat("yyyy-MM-dd")

        grid_lic.addWidget(_make_label("No. Licencia"), 1, 0)
        grid_lic.addWidget(self.txt_licencia, 1, 1)
        grid_lic.addWidget(_make_label("Categoría / Tipo"), 2, 0)
        grid_lic.addWidget(self.txt_tipo_lic, 2, 1)
        grid_lic.addWidget(_make_label("Vencimiento"), 3, 0)
        grid_lic.addWidget(self.date_venc_lic, 3, 1)

        card_est, grid_est = _make_card("Estado del Cliente", self, "🏷️")
        self.cmb_estado = QComboBox()
        self.cmb_estado.addItems(ESTADOS_CLIENTE)

        grid_est.addWidget(_make_label("Estado"), 1, 0)
        grid_est.addWidget(self.cmb_estado, 1, 1)

        outer.addWidget(card_lic, 0, 0)
        outer.addWidget(card_est, 1, 0)

        # --- Columna 1: Dirección + Hospedaje ---
        card_dir, grid_dir = _make_card("Dirección", self, "📍")
        self.txt_dir_res = QLineEdit()
        self.txt_dir_res.setPlaceholderText("Dirección de residencia")
        self.txt_dir_temp = QLineEdit()
        self.txt_dir_temp.setPlaceholderText("Dirección temporal (turista)")

        grid_dir.addWidget(_make_label("Residencia"), 1, 0)
        grid_dir.addWidget(self.txt_dir_res, 1, 1)
        grid_dir.addWidget(_make_label("Temporal"), 2, 0)
        grid_dir.addWidget(self.txt_dir_temp, 2, 1)

        card_hosp, grid_hosp = _make_card("Hospedaje", self, "🏨")
        self.txt_hotel = QLineEdit()
        self.txt_hotel.setPlaceholderText("Nombre del hotel")
        self.txt_habitacion = QLineEdit()
        self.txt_habitacion.setPlaceholderText("Ej: 101")

        grid_hosp.addWidget(_make_label("Hotel / Hospedaje"), 1, 0)
        grid_hosp.addWidget(self.txt_hotel, 1, 1)
        grid_hosp.addWidget(_make_label("No. Habitación"), 2, 0)
        grid_hosp.addWidget(self.txt_habitacion, 2, 1)

        outer.addWidget(card_dir, 0, 1)
        outer.addWidget(card_hosp, 1, 1)

        # Columnas iguales
        outer.setColumnStretch(0, 1)
        outer.setColumnStretch(1, 1)
        outer.setRowStretch(2, 1)

        scroll.setWidget(container)
        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)

    def _deferred_load_geo(self):
        """Carga diferida de opciones geograficas."""
        try:
            geo_opts = ClienteService.obtener_opciones_geograficas()
            self.cmb_pais.addItems(geo_opts.get("paises", []))
            self.cmb_estado_reg.addItems(geo_opts.get("regiones", []))
            self.cmb_ciudad.addItems(geo_opts.get("ciudades", []))
        except Exception:
            pass

    def _on_pais_changed(self, pais: str):
        try:
            regiones = ClienteService.obtener_regiones_por_pais(pais)
            # Guardamos lo que está escrito para no borrarlo si el usuario estaba escribiendo
            actual = self.cmb_estado_reg.currentText()
            self.cmb_estado_reg.clear()
            self.cmb_estado_reg.addItems(regiones)
            self.cmb_estado_reg.setCurrentText(actual)
        except Exception:
            pass

    def _on_region_changed(self, region: str):
        try:
            pais = self.cmb_pais.currentText()
            ciudades = ClienteService.obtener_ciudades_por_region(pais, region)
            actual = self.cmb_ciudad.currentText()
            self.cmb_ciudad.clear()
            self.cmb_ciudad.addItems(ciudades)
            self.cmb_ciudad.setCurrentText(actual)
        except Exception:
            pass

    def _cargar(self):
        self._validator.clear_all()
        d = self._datos
        self.cmb_tipo_doc.setCurrentText(str(d.get("tipo_doc", "Cedula")))
        self.txt_no_doc.setText(str(d.get("no_doc", "")))
        self.txt_nombres.setText(str(d.get("nombres", "")))
        self.txt_apellidos.setText(str(d.get("apellidos", "")))
        self.txt_nacion.setText(str(d.get("nacionalidad", "")))
        self.cmb_pais.setCurrentText(str(d.get("pais", "Colombia")))
        self.cmb_estado_reg.setCurrentText(str(d.get("estado_region", "")))
        self.cmb_ciudad.setCurrentText(str(d.get("ciudad", "")))
        self.txt_celular.setText(str(d.get("celular", "")))
        self.txt_celular2.setText(str(d.get("celular2", "")))
        self.txt_email.setText(str(d.get("email", "")))
        self.txt_licencia.setText(str(d.get("no_licencia", "")))
        self.txt_tipo_lic.setText(str(d.get("tipo_licencia", "")))
        self.txt_dir_res.setText(str(d.get("dir_residencia", "")))
        self.txt_dir_temp.setText(str(d.get("dir_temporal", "")))
        self.txt_hotel.setText(str(d.get("hotel", "")))
        self.txt_habitacion.setText(str(d.get("habitacion", "")))
        self.cmb_estado.setCurrentText(str(d.get("estado", "Activo")))
        venc = d.get("vencimiento_licencia")
        if venc:
            try:
                self.date_venc_lic.setDate(datetime.strptime(str(venc)[:10], "%Y-%m-%d").date())
            except ValueError:
                pass

    def _construir_validacion(self) -> None:
        """Registra campos en el FormValidator."""
        self._validator.add_field(
            self.txt_no_doc, [Required()], "Documento", error_label=self._error_no_doc
        )
        self._validator.add_field(
            self.txt_nombres, [Required()], "Nombres", error_label=self._error_nombres
        )
        self._validator.add_field(self.txt_email, [Email()], "Email", error_label=self._error_email)
        self._validator.add_field(
            self.txt_celular, [Phone()], "Celular", error_label=self._error_celular
        )

    def _guardar(self):
        if not self._validator.validate_all():
            self._validator.focus_first_error()
            return
        datos = {
            "tipo_doc": self.cmb_tipo_doc.currentText(),
            "no_doc": self.txt_no_doc.text().strip(),
            "nombres": self.txt_nombres.text().strip(),
            "apellidos": self.txt_apellidos.text().strip(),
            "celular": self.txt_celular.text().strip(),
            "celular2": self.txt_celular2.text().strip(),
            "email": self.txt_email.text().strip(),
            "pais": self.cmb_pais.currentText().strip(),
            "estado_region": self.cmb_estado_reg.currentText().strip(),
            "ciudad": self.cmb_ciudad.currentText().strip(),
            "nacionalidad": self.txt_nacion.text().strip(),
            "dir_residencia": self.txt_dir_res.text().strip(),
            "dir_temporal": self.txt_dir_temp.text().strip(),
            "hotel": self.txt_hotel.text().strip(),
            "habitacion": self.txt_habitacion.text().strip(),
            "no_licencia": self.txt_licencia.text().strip(),
            "tipo_licencia": self.txt_tipo_lic.text().strip(),
            "vencimiento_licencia": self.date_venc_lic.date().toString("yyyy-MM-dd"),
            "estado": self.cmb_estado.currentText(),
        }
        try:
            ClienteService.guardar(datos)
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", e.mensaje_usuario)
        except Exception as e:
            ModernMessageBox.error(self, "Error", str(e))


class ClientesWidget(BaseWidget):
    """Panel principal de gestion de clientes."""

    _COLOR_ESTADO = {
        "Activo": COLOR_ESTADO_ACTIVO,
        "VIP": COLOR_ESTADO_VIP,
        "Lista Negra": COLOR_ESTADO_LISTA_NEGRA,
    }

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Banner superior ──────────────────────────────────────────
        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            "👥",
            "Directorio de Clientes",
            "Gestion de clientes y registro de visitantes",
            self.cargar_datos,
        )
        main_layout.addWidget(banner)

        # ── Área de contenido ─────────────────────────────────────────
        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(12)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        top.addStretch()

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setProperty("class", "search")
        self.txt_buscar.setPlaceholderText("Buscar por nombre o cedula...")
        self.txt_buscar.setMinimumWidth(260)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        btn_ref = QPushButton("Recargar")
        btn_ref.setProperty("class", "ghost")
        btn_ref.clicked.connect(self.cargar_datos)
        top.addWidget(btn_ref)

        btn_nuevo = QPushButton("+ Nuevo Cliente")
        btn_nuevo.setProperty("class", "success")
        btn_nuevo.clicked.connect(self._nuevo)
        top.addWidget(btn_nuevo)
        c_lay.addLayout(top)

        self.tabla = QTableWidget()
        self.tabla.setAlternatingRowColors(True)
        self.ajustar_tabla(
            self.tabla,
            ["Documento", "Nombre Completo", "Celular", "Nacionalidad", "Estado", "Licencia", ""],
        )

        # --- Configurar columnas individualmente ---
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(0, 120)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(2, 120)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(3, 120)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(4, 110)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Interactive)
        self.tabla.setColumnWidth(5, 110)
        # Columna Editar: Fixed
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.tabla.setColumnWidth(6, 90)

        self.tabla.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabla.customContextMenuRequested.connect(self._menu_contextual)
        c_lay.addWidget(self.tabla)

        self._lista: list[dict] = []
        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self._lista = self.ejecutar_seguro(ClienteService.buscar) or []
        self._pintar_filas(self._lista)

    def _pintar_filas(self, datos: list[dict]):
        self.tabla.setRowCount(0)
        for cli in datos:
            i = self.tabla.rowCount()
            self.tabla.insertRow(i)
            items = [
                QTableWidgetItem(str(cli.get("no_doc", ""))),
                QTableWidgetItem(str(cli.get("nombre_completo", ""))),
                QTableWidgetItem(str(cli.get("celular", ""))),
                QTableWidgetItem(str(cli.get("nacionalidad", ""))),
                QTableWidgetItem(str(cli.get("estado", ""))),
                QTableWidgetItem(str(cli.get("no_licencia", ""))),
            ]
            for j, it in enumerate(items):
                if j == 4:  # Columna Estado — se maneja con StatusBadge abajo
                    continue
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(i, j, it)
            from views.components.status_badge import StatusBadge

            _ESTADO_BADGE_MAP = {"Activo": "success", "VIP": "info", "Lista Negra": "danger"}
            estado = str(cli.get("estado", ""))
            badge = StatusBadge(estado, _ESTADO_BADGE_MAP.get(estado, "info"))
            self.tabla.setCellWidget(i, 4, badge)

            # Boton Editar visible
            btn = QPushButton("Editar")
            btn.setProperty("class", "icon")
            btn.setFixedSize(78, 32)
            cli_id = cli.get("id")
            btn.clicked.connect(lambda _, cid=cli_id: self._editar_por_id(cid))
            self.tabla.setCellWidget(i, 6, btn)

        self.tabla.resizeRowsToContents()

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        if not txt:
            self._pintar_filas(self._lista)
            return
        filtrados = [
            c
            for c in self._lista
            if txt in str(c.get("no_doc", "")).lower()
            or txt in str(c.get("nombre_completo", "")).lower()
            or txt in str(c.get("celular", "")).lower()
        ]
        self._pintar_filas(filtrados)

    def _nuevo(self):
        if ClienteFormDialog(self).exec():
            self.cargar_datos()
            self.mostrar_exito("Cliente registrado correctamente")

    def _editar_por_id(self, cli_id):
        datos = self.ejecutar_seguro(ClienteService.obtener, cli_id)
        if datos and ClienteFormDialog(self, datos).exec():
            self.cargar_datos()

    def _editar_doble_click(self, row: int, _col: int):
        if row >= len(self._lista):
            return
        datos = self.ejecutar_seguro(ClienteService.obtener, self._lista[row]["id"])
        if datos and ClienteFormDialog(self, datos).exec():
            self.cargar_datos()

    def _menu_contextual(self, pos):
        row = self.tabla.rowAt(pos.y())
        if row < 0 or row >= len(self._lista):
            return
        cli = self._lista[row]
        cli_id = cli.get("id")
        menu = QMenu(self)
        acc_edit = menu.addAction("Editar cliente")
        acc_vip = menu.addAction("Marcar VIP")
        acc_ln = menu.addAction("Agregar a Lista Negra")
        acc = menu.exec(self.tabla.viewport().mapToGlobal(pos))
        if acc == acc_edit:
            datos = self.ejecutar_seguro(ClienteService.obtener, cli_id)
            if datos and ClienteFormDialog(self, datos).exec():
                self.cargar_datos()
        elif acc in (acc_vip, acc_ln):
            self._cambiar_estado(cli_id, "VIP" if acc == acc_vip else "Lista Negra")

    def _cambiar_estado(self, cli_id, nuevo_estado: str):
        try:
            datos = ClienteService.obtener(cli_id)
            datos["estado"] = nuevo_estado
            ClienteService.guardar(datos)
            self.mostrar_exito(f"Estado actualizado a {nuevo_estado}")
            self.cargar_datos()
        except DinamoBaseError as e:
            self.mostrar_error(e.mensaje_usuario)
        except Exception as e:
            self.mostrar_error(str(e))
