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
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QLabel,
    QFormLayout,
    QComboBox,
    QDateEdit,
    QGroupBox,
    QDoubleSpinBox,
    QTextEdit,
    QSpinBox,
    QAbstractItemView,
    QWidget,
    QLineEdit,
)
from PySide6.QtCore import QDate, QTimer
from PySide6.QtGui import QFont

from services.auto_service import AutoService
from services.mantenimiento_service import MantenimientoService
from core.exceptions import DinamoBaseError
from views.base_widget import BaseWidget
from views.base_dialog import BaseDialog
# Estilos via QSS global (sin styles.py inline)


# =============================================================================
# DIALOGO REGISTRO DE MANTENIMIENTO
# =============================================================================
class NuevoMantenimientoDialog(BaseDialog):
    """Dialogo para registrar mantenimiento/taller."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Mantenimiento / Taller")
        self.setMinimumSize(500, 600)
        self.datos_auto = None

        self._setup_ui()
        self._init_overlay("Cargando vehiculos...")
        QTimer.singleShot(0, self._deferred_load)

    def _deferred_load(self):
        self._deferred_call(self._cargar_autos)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        from views.layouts.form_helpers import build_dialog_header

        root.addWidget(
            build_dialog_header(
                "🛠️",
                "Registrar Mantenimiento / Taller",
                "Registro de servicios de taller y mantenimiento vehicular",
            )
        )

        body = QWidget()
        body.setObjectName("dlg_body")
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(14)
        body_lay.setContentsMargins(20, 16, 20, 14)

        # 1. Seleccion de vehiculo
        group_veh = QGroupBox("1. Vehiculo")
        lay_veh = QFormLayout()

        self.cmb_placa = QComboBox()
        self.cmb_placa.setEditable(True)
        self.cmb_placa.currentIndexChanged.connect(self._cargar_datos_auto)

        self.lbl_info_auto = QLabel("Seleccione un vehiculo...")
        self.lbl_info_auto.setProperty("class", "section")

        lay_veh.addRow("Placa:", self.cmb_placa)
        lay_veh.addRow(self.lbl_info_auto)
        group_veh.setLayout(lay_veh)
        body_lay.addWidget(group_veh)

        # 2. Detalles del servicio
        group_srv = QGroupBox("2. Servicio Realizado")
        lay_srv = QFormLayout()

        self.cmb_tipo = QComboBox()
        self.cmb_tipo.addItems(
            [
                "Cambio Aceite",
                "Frenos",
                "Llantas",
                "Bateria",
                "Tecno-Mecanica",
                "Lavado General",
                "Reparacion Mecanica",
                "Otro",
            ]
        )

        self.date_fecha = QDateEdit(QDate.currentDate())
        self.date_fecha.setCalendarPopup(True)

        self.spin_costo = QDoubleSpinBox()
        self.spin_costo.setRange(0, 100_000_000)
        self.spin_costo.setPrefix("$ ")

        self.spin_km_actual = QSpinBox()
        self.spin_km_actual.setRange(0, 999_999)
        self.spin_km_actual.setSuffix(" km")

        lay_srv.addRow("Tipo Servicio:", self.cmb_tipo)
        lay_srv.addRow("Fecha Realizacion:", self.date_fecha)
        lay_srv.addRow("Costo Total:", self.spin_costo)
        lay_srv.addRow("Kilometraje Actual:", self.spin_km_actual)
        group_srv.setLayout(lay_srv)
        body_lay.addWidget(group_srv)

        # 3. Proyeccion y notas
        group_proy = QGroupBox("3. Proximo Servicio (Alerta)")
        lay_proy = QFormLayout()

        self.spin_prox_km = QSpinBox()
        self.spin_prox_km.setRange(0, 999_999)
        self.spin_prox_km.setSuffix(" km")
        self.spin_prox_km.setSpecialValueText("Opcional")

        self.txt_obs = QTextEdit()
        self.txt_obs.setMaximumHeight(60)

        self.chk_cambiar_estado = QComboBox()
        self.chk_cambiar_estado.addItems(
            [
                "Mantener Estado Actual",
                "Poner en Mantenimiento",
                "Poner Disponible",
            ]
        )

        lay_proy.addRow("Proximo Cambio (Km):", self.spin_prox_km)
        lay_proy.addRow("Observaciones:", self.txt_obs)
        lay_proy.addRow("Estado del Auto:", self.chk_cambiar_estado)
        group_proy.setLayout(lay_proy)
        body_lay.addWidget(group_proy)

        body_lay.addStretch()

        # Separador
        from PySide6.QtWidgets import QFrame

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setProperty("class", "divider")
        body_lay.addWidget(sep)

        # Botones
        btn_box = QHBoxLayout()
        btn_box.setSpacing(10)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("class", "danger")
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("Registrar")
        btn_save.setProperty("class", "primary")
        btn_save.clicked.connect(self._guardar)

        btn_box.addStretch()
        btn_box.addWidget(btn_cancel)
        btn_box.addWidget(btn_save)
        body_lay.addLayout(btn_box)

        root.addWidget(body)

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
            from views.components.toast_notification import ToastNotification

            ToastNotification(
                self.window(), "Mantenimiento registrado y vehículo actualizado.", "success"
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

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            "🛠️",
            "Taller y Mantenimiento",
            "Registro de mantenimientos y servicios de taller",
            self.cargar_historial,
        )
        main_layout.addWidget(banner)

        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        # ── Barra de búsqueda y filtros ──
        top = QHBoxLayout()

        self.txt_buscar = QLineEdit()
        self.txt_buscar.setProperty("class", "search")
        self.txt_buscar.setPlaceholderText("Buscar por placa, tipo de servicio...")
        self.txt_buscar.setMinimumWidth(220)
        self.txt_buscar.textChanged.connect(self._filtrar)
        top.addWidget(self.txt_buscar)

        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems(
            [
                "Todos los servicios",
                "Cambio Aceite",
                "Frenos",
                "Llantas",
                "Batería",
                "Tecno-Mecánica",
                "Lavado General",
                "Reparación Mecánica",
                "Otro",
            ]
        )
        self.cmb_filtro.setCurrentIndex(0)
        self.cmb_filtro.setMinimumWidth(180)
        self.cmb_filtro.currentIndexChanged.connect(self._filtrar)
        top.addWidget(self.cmb_filtro)

        top.addStretch()

        btn_ref = QPushButton("Actualizar")
        btn_ref.setProperty("class", "ghost")
        btn_ref.clicked.connect(self.cargar_historial)
        top.addWidget(btn_ref)

        btn_new = QPushButton("+ Registrar Servicio")
        btn_new.setProperty("class", "warning")
        btn_new.clicked.connect(self._nuevo_servicio)
        top.addWidget(btn_new)

        c_lay.addLayout(top)

        # ── Tabla ──
        self.tabla = QTableWidget()
        self._configurar_tabla()
        c_lay.addWidget(self.tabla)

        self._lista: list[dict] = []
        self._init_loading_overlay("Cargando historial...")
        QTimer.singleShot(0, lambda: self._deferred_call(self.cargar_historial))

    def _configurar_tabla(self):
        cols = ["Fecha", "Placa", "Auto", "Tipo Servicio", "Costo", "Observaciones", "KM Próx."]
        self.tabla.setColumnCount(len(cols))
        self.tabla.setHorizontalHeaderLabels(cols)
        self.tabla.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setColumnWidth(1, 100)
        self.tabla.setColumnWidth(2, 140)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_historial(self):
        self.tabla.setRowCount(0)
        self._lista = []
        try:
            # Build auto lookup for enriching mantenimiento data
            auto_lookup = {}
            try:
                for a in AutoService.listar():
                    auto_lookup[a["placa"]] = a
            except DinamoBaseError:
                pass

            historial = MantenimientoService.listar_historial(50)
            # Enrich with auto data
            for r in historial:
                placa = r.get("placa", "")
                auto_data = auto_lookup.get(placa, {})
                r["_auto_marca"] = auto_data.get("marca", "")
                r["_auto_modelo"] = auto_data.get("modelo", "")
                r["_auto_estado"] = auto_data.get("estado", "")
            self._lista = historial
            self._pintar_filas(historial)
        except DinamoBaseError as e:
            self.mostrar_error(f"Error cargando historial:\n{e}")

    def _pintar_filas(self, datos: list[dict]):
        """Renderiza las filas de la tabla con los datos filtrados."""
        self.tabla.setRowCount(0)
        for i, r in enumerate(datos):
            self.tabla.insertRow(i)

            self.tabla.setItem(i, 0, QTableWidgetItem(str(r.get("pieza_varias_fecha", ""))))
            self.tabla.setItem(i, 1, QTableWidgetItem(str(r.get("placa", ""))))

            # Auto (Marca / Modelo)
            marca = r.get("_auto_marca", "")
            modelo = r.get("_auto_modelo", "")
            auto_text = f"{marca} {modelo}".strip() or "—"
            self.tabla.setItem(i, 2, QTableWidgetItem(auto_text))

            # Tipo Servicio (bold)
            item_tipo = QTableWidgetItem(str(r.get("pieza_varias_tipo", "")))
            fnt = QFont(item_tipo.font())
            fnt.setBold(True)
            item_tipo.setFont(fnt)
            self.tabla.setItem(i, 3, item_tipo)

            costo = float(r.get("total_mantenimiento", 0) or 0)
            self.tabla.setItem(i, 4, QTableWidgetItem(f"${costo:,.0f}"))
            self.tabla.setItem(i, 5, QTableWidgetItem(str(r.get("pieza_varias_obs", ""))))

            # KM Próximo
            km_prox = r.get("km_proximo_cambio_aceite", 0) or 0
            km_text = f"{km_prox:,.0f} km" if km_prox else "—"
            self.tabla.setItem(i, 6, QTableWidgetItem(km_text))

    def _filtrar(self):
        """Filtra la tabla por texto y tipo de servicio."""
        txt = self.txt_buscar.text().lower()
        filtro_tipo = self.cmb_filtro.currentIndex()  # 0=Todos, 1+ = tipo específico

        filtrados = self._lista

        # 1. Filtrar por tipo de servicio
        if filtro_tipo > 0:
            tipo_seleccionado = self.cmb_filtro.currentText()
            filtrados = [
                r for r in filtrados if r.get("pieza_varias_tipo", "") == tipo_seleccionado
            ]

        # 2. Filtrar por texto
        if txt:
            filtrados = [
                r
                for r in filtrados
                if txt in str(r.get("placa", "")).lower()
                or txt in str(r.get("pieza_varias_tipo", "")).lower()
                or txt in str(r.get("_auto_marca", "")).lower()
                or txt in str(r.get("_auto_modelo", "")).lower()
                or txt in str(r.get("pieza_varias_obs", "")).lower()
            ]

        self._pintar_filas(filtrados)

    # ── Acciones ───────────────────────────────────────────────

    def _nuevo_servicio(self):
        dlg = NuevoMantenimientoDialog(self)
        if dlg.exec():
            self.cargar_historial()
