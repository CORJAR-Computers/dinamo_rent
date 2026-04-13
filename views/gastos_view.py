"""
views/gastos_view.py — Vista para el registro de Caja Menor y Egresos Operativos.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QComboBox, QMessageBox,
    QDateEdit, QDoubleSpinBox, QGroupBox, QLineEdit, QAbstractItemView, QSizePolicy,
    QFrame
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush

from services.services_extra import GastoService
from core.exceptions import DinamoBaseError


class GastosWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._setup_ui()
        self.cargar_datos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # --- CABECERA ---
        top = QHBoxLayout()
        lbl_titulo = QLabel("💸 Control de Gastos y Caja Menor")
        lbl_titulo.setStyleSheet("font-size: 20px; font-weight: bold;")

        btn_ref = QPushButton("Actualizar Lista")
        btn_ref.clicked.connect(self.cargar_datos)

        top.addWidget(lbl_titulo)
        top.addStretch()
        top.addWidget(btn_ref)
        layout.addLayout(top)

        # --- FORMULARIO NUEVO GASTO (CON ENCABEZADO PERSONALIZADO) ---
        # SOLUCIÓN: Usar un contenedor con borde en lugar de QGroupBox con título
        contenedor_form = QFrame()
        contenedor_form.setFrameShape(QFrame.Shape.StyledPanel)
        contenedor_form.setFrameShadow(QFrame.Shadow.Plain)
        contenedor_form.setStyleSheet("""
            QFrame {
                border: 1px solid #c0c0c0;
                border-radius: 6px;
                background-color: #f8f9fa;
            }
        """)

        # Layout vertical para el título + grid
        contenedor_layout = QVBoxLayout(contenedor_form)
        contenedor_layout.setContentsMargins(0, 0, 0, 0)
        contenedor_layout.setSpacing(0)

        # --- TÍTULO PERSONALIZADO (reemplaza el título del QGroupBox) ---
        lbl_subtitulo = QLabel("➕ Registrar nuevo Gasto")
        lbl_subtitulo.setStyleSheet("""
            font-weight: bold;
            font-size: 13px;
            color: #1565c0;
            padding: 10px 15px 5px 15px;
            background-color: transparent;
        """)
        contenedor_layout.addWidget(lbl_subtitulo)

        # --- GRID CON LOS CAMPOS ---
        grid_widget = QWidget()
        grid = QGridLayout(grid_widget)
        grid.setContentsMargins(15, 10, 15, 15)
        grid.setHorizontalSpacing(0)
        grid.setVerticalSpacing(10)

        # --- Widgets ---
        self.d_fecha = QDateEdit(QDate.currentDate())
        self.d_fecha.setCalendarPopup(True)
        self.d_fecha.setMinimumHeight(32)

        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(1, 100_000_000)
        self.sp_monto.setPrefix("$ ")
        self.sp_monto.setMinimumHeight(32)

        self.txt_comp = QLineEdit()
        self.txt_comp.setPlaceholderText("Nº Factura/Recibo (Opcional)")
        self.txt_comp.setMinimumHeight(32)

        self.cmb_categoria = QComboBox()
        self.cmb_categoria.setMinimumHeight(32)
        self.cmb_categoria.addItems([
            "Lavadero y Aseo",
            "Parqueadero / Peajes",
            "Mantenimiento Menor",
            "Papelería y Oficina",
            "Servicios e Internet",
            "Impuestos y Seguros",
            "Nómina / Comisiones",
            "Otros"
        ])

        self.txt_desc = QLineEdit()
        self.txt_desc.setPlaceholderText("Ej: Lavado del vehículo ABC-123")
        self.txt_desc.setMinimumHeight(32)

        btn_save = QPushButton("💾  Registrar Salida de Dinero")
        btn_save.setMinimumHeight(36)
        btn_save.setProperty("cssClass", "danger")
        btn_save.clicked.connect(self.guardar)

        # --- Colocar widgets en el grid ---
        # col 0 = Fecha/Categoria | col 1 = separador | col 2 = Monto/Desc | col 3 = separador | col 4 = Comp/Botón

        # Etiquetas fila 0
        grid.addWidget(QLabel("Fecha:"),        0, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(QLabel("Monto Pagado:"), 0, 2, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(QLabel("Comprobante:"),  0, 4, Qt.AlignmentFlag.AlignLeft)

        # Campos fila 1
        grid.addWidget(self.d_fecha,   1, 0)
        grid.addWidget(self.sp_monto,  1, 2)
        grid.addWidget(self.txt_comp,  1, 4)

        # Etiquetas fila 2
        grid.addWidget(QLabel("Categoría:"),   2, 0, Qt.AlignmentFlag.AlignLeft)
        grid.addWidget(QLabel("Descripción:"), 2, 2, Qt.AlignmentFlag.AlignLeft)

        # Campos fila 3
        grid.addWidget(self.cmb_categoria, 3, 0)
        grid.addWidget(self.txt_desc,      3, 2)
        grid.addWidget(btn_save,           3, 4)

        # Columnas separadoras de 20px
        grid.setColumnMinimumWidth(1, 20)
        grid.setColumnMinimumWidth(3, 20)

        # Stretch de columnas de contenido
        grid.setColumnStretch(0, 2)
        grid.setColumnStretch(2, 3)
        grid.setColumnStretch(4, 2)

        contenedor_layout.addWidget(grid_widget)
        layout.addWidget(contenedor_form)

        # --- TABLA DE HISTORIAL ---
        lbl_hist = QLabel("Historial de Gastos Recientes")
        lbl_hist.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(lbl_hist)

        self.tbl = QTableWidget()
        cols = ["ID", "Fecha", "Categoría", "Descripción", "Comprobante", "Monto"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setAlternatingRowColors(True)
        layout.addWidget(self.tbl)

    def cargar_datos(self):
        self.tbl.setRowCount(0)
        try:
            gastos = GastoService.listar_recientes()
            for i, g in enumerate(gastos):
                self.tbl.insertRow(i)
                monto = float(g.get('monto', 0))

                self.tbl.setItem(i, 0, QTableWidgetItem(str(g.get('id', ''))))
                self.tbl.setItem(i, 1, QTableWidgetItem(str(g.get('fecha', ''))))
                self.tbl.setItem(i, 2, QTableWidgetItem(str(g.get('categoria', ''))))
                self.tbl.setItem(i, 3, QTableWidgetItem(str(g.get('descripcion', ''))))
                self.tbl.setItem(i, 4, QTableWidgetItem(str(g.get('comprobante', ''))))

                it_monto = QTableWidgetItem(f"$ {monto:,.0f}")
                it_monto.setForeground(QBrush(QColor("#c62828")))
                font = it_monto.font()
                font.setBold(True)
                it_monto.setFont(font)
                self.tbl.setItem(i, 5, it_monto)

        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", str(e))

    def guardar(self):
        datos = {
            "fecha": self.d_fecha.date().toString("yyyy-MM-dd"),
            "categoria": self.cmb_categoria.currentText(),
            "monto": self.sp_monto.value(),
            "descripcion": self.txt_desc.text().strip(),
            "comprobante": self.txt_comp.text().strip()
        }

        if not datos["descripcion"]:
            return QMessageBox.warning(self, "Faltan datos", "Por favor ingrese una descripción del gasto.")

        try:
            GastoService.registrar(datos)
            QMessageBox.information(self, "Éxito", "Gasto registrado correctamente en caja.")

            self.txt_desc.clear()
            self.txt_comp.clear()
            self.sp_monto.setValue(1)

            self.cargar_datos()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))