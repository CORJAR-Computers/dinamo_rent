"""
cierre_renta_view.py — Diálogo para procesar la devolución de una renta

Calcula cargos de mora y libera el vehículo mediante RentaService.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDateEdit, QTimeEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QGroupBox, QFrame, QMessageBox
)
from PySide6.QtCore import QDate, QTime

from core.config import NIVEL_TANQUE, COLOR_PRIMARIO
from core.exceptions import DinamoBaseError
from services.services import RentaService
from core.logger import get_logger

log = get_logger(__name__)


class CierreRentaDialog(QDialog):
    """Procesa la devolución de un vehículo rentado."""

    def __init__(self, parent=None, id_renta: int | None = None):
        super().__init__(parent)
        self.setWindowTitle(f"Procesar Devolución — Renta #{id_renta}")
        self.setFixedSize(600, 700)
        self.id_renta   = id_renta
        self._renta     = {}

        layout = QVBoxLayout(self)

        # Info original
        self.lbl_info = QLabel("Cargando…")
        self.lbl_info.setStyleSheet(
            "background-color:#f0f0f0;padding:10px;border-radius:5px;"
        )
        layout.addWidget(self.lbl_info)

        # Devolución
        gb_dev = QGroupBox("Datos de Devolución")
        f_dev  = QFormLayout()
        self.date_retorno = QDateEdit(QDate.currentDate())
        self.date_retorno.setCalendarPopup(True)
        self.date_retorno.dateChanged.connect(self._recalcular)
        self.time_retorno = QTimeEdit(QTime.currentTime())
        self.time_retorno.timeChanged.connect(self._recalcular)
        self.txt_km_final = QLineEdit()
        self.txt_km_final.setPlaceholderText("Ej: 50500")
        self.cmb_tanque = QComboBox()
        self.cmb_tanque.addItems(NIVEL_TANQUE)
        f_dev.addRow("Fecha Real:",       self.date_retorno)
        f_dev.addRow("Hora Real:",        self.time_retorno)
        f_dev.addRow("Kilometraje Final:",self.txt_km_final)
        f_dev.addRow("Nivel Gasolina:",   self.cmb_tanque)
        gb_dev.setLayout(f_dev); layout.addWidget(gb_dev)

        # Costos adicionales
        gb_cos = QGroupBox("Costos Adicionales")
        f_cos  = QFormLayout()
        self.sp_dias_extra  = QDoubleSpinBox(); self.sp_dias_extra.setReadOnly(True); self.sp_dias_extra.setSuffix(" días")
        self.sp_mora        = QDoubleSpinBox(); self.sp_mora.setRange(0, 1e7); self.sp_mora.setPrefix("$ "); self.sp_mora.setEnabled(False)
        self.sp_otros       = QDoubleSpinBox(); self.sp_otros.setRange(0, 1e7); self.sp_otros.setPrefix("$ ")
        self.sp_otros.valueChanged.connect(self._recalcular)
        self.txt_obs        = QLineEdit(); self.txt_obs.setPlaceholderText("Daños, gasolina, etc.")
        f_cos.addRow("Tiempo Extra:",           self.sp_dias_extra)
        f_cos.addRow("Costo Tiempo Extra:",     self.sp_mora)
        f_cos.addRow("Otros (Daños/Gasolina):", self.sp_otros)
        f_cos.addRow("Observación:",            self.txt_obs)
        gb_cos.setLayout(f_cos); layout.addWidget(gb_cos)

        # Resumen
        frame_tot = QFrame()
        frame_tot.setStyleSheet("background-color:#e3f2fd;border-radius:8px;")
        lay_tot = QVBoxLayout(frame_tot)
        self.lbl_pactado = QLabel("Pactado: $0")
        self.lbl_total   = QLabel("TOTAL A PAGAR: $0")
        self.lbl_total.setStyleSheet(
            f"font-size:18px;font-weight:bold;color:{COLOR_PRIMARIO};"
        )
        self.lbl_detalle = QLabel("")
        lay_tot.addWidget(self.lbl_pactado)
        lay_tot.addWidget(self.lbl_total)
        lay_tot.addWidget(self.lbl_detalle)
        layout.addWidget(frame_tot)

        # BOTONES
        btn_layout = QHBoxLayout()

        # --- NUEVO BOTÓN DE INSPECCIÓN ---
        btn_inspeccion = QPushButton("📋 Inspección (Check-in)")
        btn_inspeccion.setProperty("cssClass", "warning")  # Usando tu CSS global
        btn_inspeccion.clicked.connect(self.abrir_inspeccion)

        btn_cerrar = QPushButton("Finalizar Renta")
        btn_cerrar.setProperty("cssClass", "success")
        btn_cerrar.clicked.connect(self.guardar_cierre)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.setProperty("cssClass", "danger")
        btn_cancel.clicked.connect(self.reject)

        btn_layout.addWidget(btn_inspeccion)  # Añadido a la izquierda
        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)

        self.cargar_datos()

    # ── lógica ───────────────────────────────────────────────────────────────

    def _cargar_datos(self):
        try:
            self._renta = RentaService.obtener_activas()  # Fallback: buscamos por id
            # Obtener directamente del repositorio para el diálogo
            from repositories.renta_repository import RentaRepository
            self._renta = RentaRepository.obtener_por_id(self.id_renta)
            info = (
                f"<b>Cliente:</b> {self._renta.get('nombre_cliente','')}<br>"
                f"<b>Vehículo:</b> {self._renta.get('placa','')}<br>"
                f"<b>Fecha Pactada:</b> {self._renta.get('fecha_retorno','')} "
                f"{self._renta.get('hora_retorno','')}"
            )
            self.lbl_info.setText(info)
            self.lbl_pactado.setText(
                f"Valor Pactado Inicial: ${float(self._renta.get('total', 0)):,.0f}"
            )
            self._recalcular()
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", e.mensaje_usuario)
            self.reject()
        except Exception as e:
            log.error("Error cargando renta #%s: %s", self.id_renta, e, exc_info=True)
            QMessageBox.critical(self, "Error", str(e))
            self.reject()

    def abrir_inspeccion(self):
        try:
            # Importación local para evitar errores de referencia circular
            from views.rentas_view import InspeccionDialog

            dlg = InspeccionDialog(self, self.id_renta)
            # Magia: pre-seleccionamos que es recepción
            dlg.cmb_tipo.setCurrentText("Recepción (Check-in)")

            # Si el usuario ya digitó un KM final en esta ventana, lo pasamos al diálogo
            if self.txt_km_final.text().isdigit():
                dlg.spin_km.setValue(float(self.txt_km_final.text()))

            dlg.exec()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo abrir el módulo de inspección: {e}")

    def _recalcular(self):
        if not self._renta:
            return
        fecha_str = str(self._renta.get("fecha_retorno", ""))[:10]
        if not fecha_str:
            return
        try:
            fp = QDate.fromString(fecha_str, "yyyy-MM-dd")
            fr = self.date_retorno.date()
            dias_retraso = max(0, fp.daysTo(fr))
            valor_dia    = float(self._renta.get("valor_dia", 0))
            mora         = dias_retraso * valor_dia
            self.sp_dias_extra.setValue(dias_retraso)
            self.sp_mora.setValue(mora)
            total_base = float(self._renta.get("total", 0))
            otros      = self.sp_otros.value()
            gran_total = total_base + mora + otros
            self.lbl_total.setText(f"TOTAL A PAGAR: ${gran_total:,.0f}")
            self.lbl_detalle.setText(
                f"(${mora:,.0f} mora  +  ${otros:,.0f} extras)"
            )
        except (ValueError, TypeError):
            pass

    def _guardar(self):
        if not self.txt_km_final.text().strip():
            QMessageBox.warning(self, "Dato faltante", "Ingrese el Kilometraje Final")
            return

        mora   = self.sp_mora.value()
        otros  = self.sp_otros.value()
        total  = float(self._renta.get("total", 0)) + mora + otros

        datos_cierre = {
            "fecha_devolucion_real": self.date_retorno.date().toString("yyyy-MM-dd"),
            "hora_devolucion_real":  self.time_retorno.time().toString("HH:mm"),
            "km_final":              self.txt_km_final.text().strip(),
            "km_final_float":        float(self.txt_km_final.text().strip() or 0),
            "tanque_final":          self.cmb_tanque.currentText(),
            "nota_cierre":           f" | Cierre: {self.txt_obs.text()}",
            "otros_cobros":          otros,
        }

        try:
            RentaService.cerrar(self.id_renta, datos_cierre)
            QMessageBox.information(
                self, "Éxito",
                "Renta finalizada correctamente.\nEl vehículo está Disponible."
            )
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", e.mensaje_usuario)
        except Exception as e:
            log.error("Error cerrando renta #%s: %s", self.id_renta, e, exc_info=True)
            QMessageBox.critical(self, "Error", str(e))
