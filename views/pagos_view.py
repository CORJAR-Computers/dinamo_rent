"""
views/pagos_view.py — Vista para el historial y registro de pagos de caja.
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QGroupBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush

from services.services_extra import PagoService
from core.exceptions import DinamoBaseError


class PagosDialog(QDialog):
    def __init__(self, parent=None, id_renta=None, total_renta=0.0, cliente=""):
        super().__init__(parent)
        self.id_renta = id_renta
        self.total_renta = float(total_renta)
        self.cliente = cliente

        self.setWindowTitle(f"Estado de Cuenta y Pagos - Renta #{id_renta}")
        self.setFixedSize(650, 600)
        self._setup_ui()
        self.cargar_pagos()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # --- 1. CABECERA RESUMEN FINANCIERO ---
        gb_resumen = QGroupBox(f"Cliente: {self.cliente}")
        lay_resumen = QHBoxLayout(gb_resumen)

        self.lbl_total = QLabel(f"Total Renta:\n$ {self.total_renta:,.0f}")
        self.lbl_total.setStyleSheet("font-size: 14px; font-weight: bold; color: #424242;")

        self.lbl_abonado = QLabel("Abonado:\n$ 0")
        self.lbl_abonado.setStyleSheet("font-size: 14px; font-weight: bold; color: #2e7d32;")  # Verde

        self.lbl_saldo = QLabel("Saldo Pendiente:\n$ 0")
        self.lbl_saldo.setStyleSheet("font-size: 15px; font-weight: bold; color: #c62828;")  # Rojo

        lay_resumen.addWidget(self.lbl_total)
        lay_resumen.addWidget(self.lbl_abonado)
        lay_resumen.addWidget(self.lbl_saldo)
        layout.addWidget(gb_resumen)

        # --- 2. FORMULARIO NUEVO PAGO ---
        gb_nuevo = QGroupBox("Registrar Nuevo Pago")
        form_pago = QFormLayout(gb_nuevo)

        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(1, 100000000)
        self.sp_monto.setPrefix("$ ")

        self.cmb_metodo = QComboBox()
        self.cmb_metodo.addItems(["Efectivo", "Tarjeta de Crédito", "Tarjeta de Débito", "Transferencia / Nequi"])

        self.cmb_concepto = QComboBox()
        self.cmb_concepto.addItems(
            ["Abono / Anticipo", "Pago Final", "Garantía", "Cobro por Daños", "Cobro por Retraso"])

        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText("Referencia de transacción, recibo manual, etc.")

        btn_registrar = QPushButton("Registrar Recibo")
        btn_registrar.setProperty("cssClass", "primary")
        btn_registrar.clicked.connect(self.registrar_pago)

        form_pago.addRow("Monto a Pagar:", self.sp_monto)
        form_pago.addRow("Método de Pago:", self.cmb_metodo)
        form_pago.addRow("Concepto:", self.cmb_concepto)
        form_pago.addRow("Observaciones:", self.txt_obs)
        form_pago.addRow("", btn_registrar)
        layout.addWidget(gb_nuevo)

        # --- 3. TABLA DE HISTORIAL ---
        lbl_hist = QLabel("Historial de Recibos")
        lbl_hist.setStyleSheet("font-weight: bold; margin-top: 10px;")
        layout.addWidget(lbl_hist)

        self.tbl = QTableWidget()
        cols = ["Fecha", "Monto", "Método", "Concepto", "Observación"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        layout.addWidget(self.tbl)

        # Botón cerrar
        btn_cerrar = QPushButton("Cerrar Ventana")
        btn_cerrar.clicked.connect(self.accept)
        layout.addWidget(btn_cerrar, alignment=Qt.AlignmentFlag.AlignRight)

    def cargar_pagos(self):
        self.tbl.setRowCount(0)
        total_abonado = 0.0

        try:
            pagos = PagoService.listar_por_renta(self.id_renta)

            for i, p in enumerate(pagos):
                self.tbl.insertRow(i)
                monto = float(p.get('monto', 0))
                total_abonado += monto

                self.tbl.setItem(i, 0, QTableWidgetItem(str(p.get('fecha', ''))[:16]))

                it_monto = QTableWidgetItem(f"$ {monto:,.0f}")
                it_monto.setForeground(QBrush(QColor("green")))
                it_monto.setFont(self.font())
                it_monto.font().setBold(True)
                self.tbl.setItem(i, 1, it_monto)

                self.tbl.setItem(i, 2, QTableWidgetItem(str(p.get('metodo_pago', ''))))
                self.tbl.setItem(i, 3, QTableWidgetItem(str(p.get('concepto', ''))))
                self.tbl.setItem(i, 4, QTableWidgetItem(str(p.get('observaciones', ''))))

            # Actualizar las etiquetas financieras
            self.lbl_abonado.setText(f"Abonado:\n$ {total_abonado:,.0f}")

            saldo = self.total_renta - total_abonado
            color_saldo = "#c62828" if saldo > 0 else "#2e7d32"  # Rojo si debe, Verde si está a paz y salvo
            self.lbl_saldo.setText(f"Saldo Pendiente:\n$ {saldo:,.0f}")
            self.lbl_saldo.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {color_saldo};")

            # Sugerir el pago del saldo restante en el formulario
            if saldo > 0:
                self.sp_monto.setValue(saldo)
            else:
                self.sp_monto.setValue(0)

        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", str(e))

    def registrar_pago(self):
        datos = {
            "id_renta": self.id_renta,
            "monto": self.sp_monto.value(),
            "metodo_pago": self.cmb_metodo.currentText(),
            "concepto": self.cmb_concepto.currentText(),
            "observaciones": self.txt_obs.text().strip()
        }

        try:
            PagoService.registrar(datos)
            QMessageBox.information(self, "Éxito", "Pago registrado correctamente en caja.")
            self.txt_obs.clear()
            self.cargar_pagos()  # Refrescar la tabla y los totales

            # Si la ventana padre (RentasWidget) tiene método actualizar, la llamamos
            if hasattr(self.parent(), 'cargar_rentas'):
                self.parent().cargar_rentas()

        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", str(e))