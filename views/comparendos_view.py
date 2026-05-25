from views.components import ModernMessageBox
"""
views/comparendos_view.py — Gestion de Multas y Comparendos. Estilos via views.styles.py.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QDialog, QFormLayout,
    QComboBox, QDateEdit, QTimeEdit, QGroupBox, QWidget,
    QDoubleSpinBox, QTextEdit, QAbstractItemView, QMenu,
)
from PySide6.QtCore import Qt, QDate, QTime, QTimer
from PySide6.QtGui import QColor, QBrush, QFont
from core.config import COLOR_PELIGRO, COLOR_EXITO, COLOR_ALERTA
from core.exceptions import DinamoBaseError
from core.logger import get_logger
from services.auto_service import AutoService
from services.comparendo_service import ComparendoService
from views.base_widget import BaseWidget
from views.styles import (
    btn_primary, btn_danger, btn_warning, btn_default,
    group_box, input_combo, input_date, input_spinbox, input_time, input_textedit, table_widget
)

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"

log = get_logger(__name__)


from views.base_dialog import BaseDialog


class NuevoComparendoDialog(BaseDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Registrar Foto-Multa / Comparendo")
        self.setMinimumSize(450, 500)
        self._setup_ui()
        self._init_overlay("Cargando vehiculos...")
        QTimer.singleShot(0, lambda: self._deferred_call(self._cargar_autos))

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        from views.layouts.form_helpers import build_dialog_header
        root.addWidget(build_dialog_header("🚔", "Registrar Nueva Infracción", "Foto-multas y comparendos — vinculación automática al cliente"))

        from views.styles import dialog_body_style
        body = QWidget()
        body.setObjectName("dlg_body")
        dialog_body_style(body)
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(14)
        body_lay.setContentsMargins(20, 16, 20, 14)

        # ── Formulario ──
        form_layout = QFormLayout()
        self.cmb_placa = QComboBox(); self.cmb_placa.setEditable(True); input_combo(self.cmb_placa)
        self.d_fecha = QDateEdit(QDate.currentDate()); self.d_fecha.setCalendarPopup(True); input_date(self.d_fecha)
        self.t_hora = QTimeEdit(QTime.currentTime()); input_time(self.t_hora)
        self.sp_monto = QDoubleSpinBox(); self.sp_monto.setRange(0, 100_000_000); self.sp_monto.setPrefix("$ "); input_spinbox(self.sp_monto)
        self.txt_obs = QTextEdit(); self.txt_obs.setMaximumHeight(80); self.txt_obs.setPlaceholderText("Lugar de la infraccion, codigo, etc..."); input_textedit(self.txt_obs)
        form_layout.addRow("Placa del Vehículo:", self.cmb_placa)
        form_layout.addRow("Fecha Infracción:", self.d_fecha)
        form_layout.addRow("Hora Infracción:", self.t_hora)
        form_layout.addRow("Monto de Multa:", self.sp_monto)
        form_layout.addRow("Observaciones:", self.txt_obs)
        gb = QGroupBox("Datos de la Infracción"); group_box(gb); gb.setLayout(form_layout); body_lay.addWidget(gb)

        body_lay.addStretch()

        # Separador
        from PySide6.QtWidgets import QFrame as QSepFrame
        sep = QSepFrame()
        sep.setFrameShape(QSepFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { background: #cbd5e1; max-height: 1px; border: none; }")
        body_lay.addWidget(sep)

        # Botones
        h_btn = QHBoxLayout()
        h_btn.setSpacing(10)
        btn_cancel = QPushButton("Cancelar"); btn_danger(btn_cancel); btn_cancel.clicked.connect(self.reject)
        btn_save = QPushButton("Registrar y Buscar Culpable"); btn_primary(btn_save); btn_save.clicked.connect(self._guardar)
        h_btn.addStretch(); h_btn.addWidget(btn_cancel); h_btn.addWidget(btn_save)
        body_lay.addLayout(h_btn)

        root.addWidget(body)

    def _cargar_autos(self):
        self.cmb_placa.addItem("Seleccione placa...", None)
        try:
            for a in AutoService.listar():
                self.cmb_placa.addItem(f"{a['placa']} - {a['marca']}", userData=a['placa'])
        except Exception as e:
            log.error("Error cargando autos en comparendos: %s", e, exc_info=True)
            ModernMessageBox.warning(self, "Error", "No se pudo cargar la lista de vehículos.")

    def _guardar(self):
        placa = self.cmb_placa.currentData()
        if not placa:
            placa = self.cmb_placa.currentText().strip()
            if not placa or placa.lower().startswith("seleccione"):
                placa = None
        if not placa:
            ModernMessageBox.warning(self, "Validacion", "Debe seleccionar un vehiculo.")
            return
        datos = {"placa": placa, "fecha": self.d_fecha.date().toString("yyyy-MM-dd"),
                 "hora": self.t_hora.time().toString("HH:mm"), "monto": self.sp_monto.value(),
                 "observaciones": self.txt_obs.toPlainText()}
        try:
            resultado = ComparendoService.registrar(datos)
            if resultado["vinculado"]:
                ModernMessageBox.success(self, "Cliente Encontrado",
                    f"Comparendo Registrado!\n\nVinculado a Renta #{resultado['id_renta']}.")
            else:
                ModernMessageBox.warning(self, "Sin Asignar", "Comparendo Registrado.\n\nSin renta activa para esa fecha.")
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", str(e))


class ComparendosWidget(BaseWidget):
    _COLOR_ESTADO = {"Pendiente": COLOR_PELIGRO, "Pagado": COLOR_EXITO, "Apelado": COLOR_ALERTA}

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner
        banner = create_banner("🚔", "Control de Comparendos y Fotomultas", "Gestion de multas y asignacion a clientes", self.cargar_datos)
        main_layout.addWidget(banner)

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        top.addStretch()
        btn_ref = QPushButton("Actualizar"); btn_default(btn_ref); btn_ref.clicked.connect(self.cargar_datos); top.addWidget(btn_ref)
        btn_new = QPushButton("+ Registrar Multa"); btn_warning(btn_new); btn_new.clicked.connect(self._nuevo); top.addWidget(btn_new)
        c_lay.addLayout(top)

        self.tbl = QTableWidget(); table_widget(self.tbl)
        self._configurar_tabla(); c_lay.addWidget(self.tbl)
        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    def _configurar_tabla(self):
        cols = ["ID", "Fecha/Hora", "Placa", "Monto", "Cliente Responsable", "Estado"]
        self.tbl.setColumnCount(len(cols)); self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tbl.customContextMenuRequested.connect(self._mostrar_menu)

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        try:
            for i, c in enumerate(ComparendoService.listar()):
                self.tbl.insertRow(i)
                fecha_hora = f"{c.get('fecha_infraccion', '')} {c.get('hora_infraccion', '')}"
                cliente = c.get("cliente_nombre") or "SIN ASIGNAR (Empresa)"
                monto = float(c.get("monto", 0)); estado = c.get("estado", "Pendiente")
                self.tbl.setItem(i, 0, QTableWidgetItem(str(c.get("id"))))
                self.tbl.setItem(i, 1, QTableWidgetItem(fecha_hora))
                self.tbl.setItem(i, 2, QTableWidgetItem(str(c.get("placa"))))
                self.tbl.setItem(i, 3, QTableWidgetItem(f"$ {monto:,.0f}"))
                it_cli = QTableWidgetItem(cliente)
                if not c.get("cliente_nombre"): it_cli.setForeground(QBrush(QColor("#888888")))
                self.tbl.setItem(i, 4, it_cli)
                from views.components.status_badge import StatusBadge
                _ESTADO_BADGE_MAP = {"Pagado": "success", "Pendiente": "warning", "Apelado": "info"}
                badge = StatusBadge(estado, _ESTADO_BADGE_MAP.get(estado, "warning"))
                self.tbl.setCellWidget(i, 5, badge)
        except DinamoBaseError: pass

    def _nuevo(self):
        if NuevoComparendoDialog(self).exec(): self.cargar_datos()

    def _mostrar_menu(self, pos):
        item = self.tbl.itemAt(pos)
        if not item: return
        row = item.row(); id_comp = int(self.tbl.item(row, 0).text())
        menu = QMenu(self)
        ac_pagar = menu.addAction("Marcar como Pagado")
        ac_apelar = menu.addAction("Marcar como Apelado")
        acc = menu.exec(self.tbl.viewport().mapToGlobal(pos))
        if acc == ac_pagar: self._cambiar_estado(id_comp, "Pagado")
        elif acc == ac_apelar: self._cambiar_estado(id_comp, "Apelado")

    def _cambiar_estado(self, id_comp: int, estado: str):
        try:
            ComparendoService.cambiar_estado(id_comp, estado)
            self.mostrar_exito(f"Estado actualizado a {estado}"); self.cargar_datos()
        except DinamoBaseError as e:
            self.mostrar_error(str(e))
