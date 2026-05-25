from views.components import ModernMessageBox
"""
views/pagos_view.py — Vista para el historial y registro de pagos de caja.

Mejoras UI/UX:
  - Sin estilos inline — todo por QSS (cssClass)
  - BUG FIX: Font bold corregido (self.font().setBold(True) no funciona en PySide6)
  - Colores desde config.py
  - Filas alternas en tabla
  - Labels financieros con cssClass
  - Sugerir saldo pendiente en el monto
"""
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QGroupBox, QAbstractItemView,
    QWidget,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QFont
from views.base_dialog import BaseDialog

from core.config import COLOR_EXITO
from services.pago_service import PagoService
from core.exceptions import DinamoBaseError
from views.styles import btn_default, btn_primary, lbl_section, lbl_subtitle, group_box, input_field, input_combo, input_spinbox, status_active, status_inactive, dialog_background


class PagosDialog(BaseDialog):
    """Dialogo de Estado de Cuenta y Pagos de una Renta."""

    def __init__(self, parent=None, id_renta=None, total_renta=0.0, cliente=""):
        super().__init__(parent)
        self.id_renta = id_renta
        self.total_renta = float(total_renta)
        self.cliente = cliente

        self.setWindowTitle(f"Estado de Cuenta - Renta #{id_renta}")
        self.setMinimumSize(650, 600)
        self._setup_ui()
        self._init_overlay("Cargando pagos...")
        QTimer.singleShot(0, self._deferred_load)

    def _deferred_load(self):
        self._deferred_call(self.cargar_pagos)

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        from views.layouts.form_helpers import build_dialog_header
        root.addWidget(build_dialog_header("💰", "Estado de Cuenta", f"Cliente: {self.cliente} — Renta #{self.id_renta}"))

        from views.styles import dialog_body_style
        body = QWidget()
        body.setObjectName("dlg_body")
        dialog_body_style(body)
        body_lay = QVBoxLayout(body)
        body_lay.setSpacing(14)
        body_lay.setContentsMargins(20, 16, 20, 14)

        # ── Resumen financiero ──
        gb_resumen = QGroupBox("Resumen Financiero")
        group_box(gb_resumen)
        lay_resumen = QHBoxLayout(gb_resumen)

        self.lbl_total = QLabel(f"Total Renta:\n$ {self.total_renta:,.0f}")
        lbl_section(self.lbl_total)

        self.lbl_abonado = QLabel("Abonado:\n$ 0")
        status_active(self.lbl_abonado)

        self.lbl_saldo = QLabel("Saldo Pendiente:\n$ 0")
        status_inactive(self.lbl_saldo)

        lay_resumen.addWidget(self.lbl_total)
        lay_resumen.addWidget(self.lbl_abonado)
        lay_resumen.addWidget(self.lbl_saldo)
        body_lay.addWidget(gb_resumen)

        # ── Formulario nuevo pago ──
        gb_nuevo = QGroupBox("Registrar Nuevo Pago")
        group_box(gb_nuevo)
        form_pago = QFormLayout(gb_nuevo)

        self.sp_monto = QDoubleSpinBox()
        self.sp_monto.setRange(1, 100_000_000)
        self.sp_monto.setPrefix("$ ")
        input_spinbox(self.sp_monto)

        self.cmb_metodo = QComboBox()
        self.cmb_metodo.addItems([
            "Efectivo",
            "Tarjeta de Credito",
            "Tarjeta de Debito",
            "Transferencia / Nequi",
        ])

        self.cmb_concepto = QComboBox()
        input_combo(self.cmb_concepto)
        self.cmb_concepto.addItems([
            "Abono / Anticipo",
            "Pago Final",
            "Garantia",
            "Cobro por Danos",
            "Cobro por Retraso",
        ])

        self.txt_obs = QLineEdit()
        self.txt_obs.setPlaceholderText(
            "Referencia de transaccion, recibo manual, etc."
        )
        input_field(self.txt_obs)

        btn_registrar = QPushButton("Registrar Recibo")
        btn_primary(btn_registrar)
        btn_registrar.clicked.connect(self._registrar_pago)

        form_pago.addRow("Monto a Pagar:", self.sp_monto)
        form_pago.addRow("Metodo de Pago:", self.cmb_metodo)
        form_pago.addRow("Concepto:", self.cmb_concepto)
        form_pago.addRow("Observaciones:", self.txt_obs)
        form_pago.addRow("", btn_registrar)
        body_lay.addWidget(gb_nuevo)

        # ── Historial ──
        lbl_hist = QLabel("Historial de Recibos")
        lbl_section(lbl_hist)
        body_lay.addWidget(lbl_hist)

        self.tbl = QTableWidget()
        self.tbl.setAlternatingRowColors(True)
        cols = ["Fecha", "Monto", "Metodo", "Concepto", "Observacion"]
        self.tbl.setColumnCount(len(cols))
        self.tbl.setHorizontalHeaderLabels(cols)
        self.tbl.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tbl.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        body_lay.addWidget(self.tbl)

        body_lay.addStretch()

        # Separador
        from PySide6.QtWidgets import QFrame
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("QFrame { background: #cbd5e1; max-height: 1px; border: none; }")
        body_lay.addWidget(sep)

        # Boton cerrar
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        btn_cerrar = QPushButton("Cerrar Ventana")
        btn_default(btn_cerrar)
        btn_cerrar.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cerrar)
        body_lay.addLayout(btn_layout)

        root.addWidget(body)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_pagos(self):
        self.tbl.setRowCount(0)
        total_abonado = 0.0

        try:
            pagos = PagoService.listar_por_renta(self.id_renta)

            for i, p in enumerate(pagos):
                self.tbl.insertRow(i)
                monto = float(p.get("monto", 0))
                total_abonado += monto

                self.tbl.setItem(
                    i, 0, QTableWidgetItem(str(p.get("fecha", ""))[:16])
                )

                # Monto en verde y negrita (BUG FIX: QFont value-type)
                it_monto = QTableWidgetItem(f"$ {monto:,.0f}")
                it_monto.setForeground(QBrush(QColor(COLOR_EXITO)))
                fnt = QFont(it_monto.font())
                fnt.setBold(True)
                it_monto.setFont(fnt)
                self.tbl.setItem(i, 1, it_monto)

                self.tbl.setItem(
                    i, 2, QTableWidgetItem(str(p.get("metodo_pago", "")))
                )
                self.tbl.setItem(
                    i, 3, QTableWidgetItem(str(p.get("concepto", "")))
                )
                self.tbl.setItem(
                    i, 4, QTableWidgetItem(str(p.get("observaciones", "")))
                )

            # Actualizar resumen financiero
            self.lbl_abonado.setText(f"Abonado:\n$ {total_abonado:,.0f}")

            saldo = self.total_renta - total_abonado
            if saldo > 0:
                self.lbl_saldo.setText(f"Saldo Pendiente:\n$ {saldo:,.0f}")
                status_inactive(self.lbl_saldo)
            else:
                self.lbl_saldo.setText("Saldo Pendiente:\n$ 0 - PAZ Y SALVO")
                status_active(self.lbl_saldo)

            # Forzar repintado para que QSS tome el cambio de propiedad
            self.lbl_saldo.style().unpolish(self.lbl_saldo)
            self.lbl_saldo.style().polish(self.lbl_saldo)

            # Sugerir el saldo pendiente
            self.sp_monto.setValue(saldo if saldo > 0 else 0)

        except DinamoBaseError as e:
            ModernMessageBox.warning(self, "Error", str(e))

    # ── Registrar pago ─────────────────────────────────────────

    def _registrar_pago(self):
        if self.sp_monto.value() <= 0:
            ModernMessageBox.warning(
                self, "Validacion", "El monto debe ser mayor a cero"
            )
            return

        datos = {
            "id_renta": self.id_renta,
            "monto": self.sp_monto.value(),
            "metodo_pago": self.cmb_metodo.currentText(),
            "concepto": self.cmb_concepto.currentText(),
            "observaciones": self.txt_obs.text().strip(),
        }

        try:
            PagoService.registrar(datos)
            from views.components.toast_notification import ToastNotification
            ToastNotification(self.window(), "Pago registrado correctamente en caja.", "success")
            self.txt_obs.clear()
            self.cargar_pagos()

            # Notificar al widget padre para refrescar
            if hasattr(self.parent(), "cargar_rentas"):
                self.parent().cargar_rentas()

        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", str(e))
