from views.components import ModernMessageBox

"""
views/gastos_view.py — Vista para el registro de Caja Menor y Egresos Operativos.

Mejoras UI/UX:
  - Hereda de BaseWidget
  - Sin estilos inline — todo por QSS (cssClass)
  - Sin emojis en labels/botones
  - Colores desde config.py
  - Font bold corregido
  - Usa QGroupBox en vez de QFrame con inline styles
"""
from PySide6.QtWidgets import (
    QVBoxLayout,
    QGridLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QHeaderView,
    QLabel,
    QComboBox,
    QDateEdit,
    QDoubleSpinBox,
    QGroupBox,
    QLineEdit,
    QAbstractItemView,
    QWidget,
)
from PySide6.QtCore import QDate, QTimer
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_PELIGRO
from services.gasto_service import GastoService
from core.exceptions import DinamoBaseError
from views.base_widget import BaseWidget
# Estilos via QSS global (sin styles.py inline)


class GastosWidget(BaseWidget):
    """Panel de Control de Gastos y Caja Menor."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self._setup_ui()
        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner

        banner = create_banner(
            "💸",
            "Control de Gastos y Caja Menor",
            "Registro de Egresos Operativos y de Oficina",
            self.cargar_datos,
        )
        main_layout.addWidget(banner)

        content = QWidget()
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        # ── Formulario nuevo gasto ──
        gb_form = QGroupBox("Registrar Nuevo Gasto")
        grid = QGridLayout()
        grid.setHorizontalSpacing(20)
        grid.setVerticalSpacing(10)

        # Widgets del formulario
        self.d_fecha = QDateEdit(QDate.currentDate())
        self.d_fecha.setCalendarPopup(True)
        self.d_fecha.setMinimumHeight(32)

        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(1, 100_000_000)
        self.sp_monto.setPrefix("$ ")
        self.sp_monto.setMinimumHeight(32)

        self.txt_comp = QLineEdit()
        self.txt_comp.setPlaceholderText("N Factura/Recibo (Opcional)")
        self.txt_comp.setMinimumHeight(32)

        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setMinimumHeight(32)
        self.cmb_categoria.addItems(
            [
                "Lavadero y Aseo",
                "Parqueadero / Peajes",
                "Mantenimiento Menor",
                "Papeleria y Oficina",
                "Servicios e Internet",
                "Impuestos y Seguros",
                "Nomina / Comisiones",
                "Otros",
            ]
        )

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ej: Lavado del vehiculo ABC-123")
        self.txt_desc.setMinimumHeight(32)

        btn_save = QPushButton("Registrar Salida de Dinero")
        btn_save.setProperty("class", "danger")
        btn_save.setMinimumHeight(36)
        btn_save.clicked.connect(self._guardar)

        # Colocar widgets en el grid
        # Fila 0: Labels
        grid.addWidget(QLabel("Fecha:"), 0, 0)
        grid.addWidget(QLabel("Monto:"), 0, 1)
        grid.addWidget(QLabel("Comprobante:"), 0, 2)

        # Fila 1: Campos
        grid.addWidget(self.d_fecha, 1, 0)
        grid.addWidget(self.sp_monto, 1, 1)
        grid.addWidget(self.txt_comp, 1, 2)

        # Fila 2: Labels
        grid.addWidget(QLabel("Categoria:"), 2, 0)
        grid.addWidget(QLabel("Descripcion:"), 2, 1)

        # Fila 3: Campos + boton
        grid.addWidget(self.cmb_categoria, 3, 0)
        grid.addWidget(self.txt_desc, 3, 1)
        grid.addWidget(btn_save, 3, 2)

        # Stretch de columnas
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(1, 3)
        grid.setColumnStretch(2, 2)

        gb_form.setLayout(grid)
        c_lay.addWidget(gb_form)

        # ── Tabla historial ──
        lbl_hist = QLabel("Historial de Gastos Recientes")
        lbl_hist.setProperty("class", "section")
        c_lay.addWidget(lbl_hist)

        self.tbl = QTableWidget()
        self.tbl.setAlternatingRowColors(True)
        cols = ["ID", "Fecha", "Categoria", "Descripcion", "Comprobante", "Monto"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        c_lay.addWidget(self.tbl)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        try:
            gastos = GastoService.listar_recientes()
            for i, g in enumerate(gastos):
                self.tbl.insertRow(i)
                monto = float(g.get("monto", 0))

                self.tbl.setItem(i, 0, QTableWidgetItem(str(g.get("id", ""))))
                self.tbl.setItem(i, 1, QTableWidgetItem(str(g.get("fecha", ""))))
                self.tbl.setItem(i, 2, QTableWidgetItem(str(g.get("categoria", ""))))
                self.tbl.setItem(i, 3, QTableWidgetItem(str(g.get("descripcion", ""))))
                self.tbl.setItem(i, 4, QTableWidgetItem(str(g.get("comprobante", ""))))

                # Monto en rojo y negrita
                it_monto = QTableWidgetItem(f"$ {monto:,.0f}")
                it_monto.setForeground(QBrush(QColor(COLOR_PELIGRO)))
                fnt = QFont(it_monto.font())
                fnt.setBold(True)
                it_monto.setFont(fnt)
                self.tbl.setItem(i, 5, it_monto)

        except DinamoBaseError as e:
            self.mostrar_error(str(e))

    # ── Guardar ────────────────────────────────────────────────

    def _guardar(self):
        datos = {
            "fecha": self.d_fecha.date().toString("yyyy-MM-dd"),
            "categoria": self.cmb_categoria.currentText(),
            "monto": self.sp_monto.value(),
            "descripcion": self.txt_desc.text().strip(),
            "comprobante": self.txt_comp.text().strip(),
        }

        if not datos["descripcion"]:
            ModernMessageBox.warning(
                self, "Faltan datos", "Por favor ingrese una descripcion del gasto."
            )
            self.txt_desc.setFocus()
            return

        try:
            GastoService.registrar(datos)
            self.mostrar_exito("Gasto registrado correctamente en caja.")

            self.txt_desc.clear()
            self.txt_comp.clear()
            self.sp_monto.setValue(1)

            self.cargar_datos()
        except DinamoBaseError as e:
            self.mostrar_error(str(e))
