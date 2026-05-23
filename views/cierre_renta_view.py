from views.components import ModernMessageBox
"""
views/cierre_renta_view.py — Dialogo para procesar la devolucion de una renta
BUG FIX: metodos inconsistentes corregidos. Estilos via views.styles.py.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QDateEdit, QTimeEdit,
    QDoubleSpinBox, QComboBox, QPushButton, QGroupBox, QFrame,
)
from PySide6.QtCore import QDate, QTime

from core.config import NIVEL_TANQUE
from core.exceptions import DinamoBaseError
from services.renta_service import RentaService
from core.logger import get_logger
from views.styles import (
    btn_success, btn_danger, btn_warning, lbl_subtitle, lbl_section, frame_summary,
    group_box, input_date, input_time, input_spinbox, input_field, input_combo, dialog_title,
    dialog_background,
)

log = get_logger(__name__)


class CierreRentaDialog(QDialog):
    def __init__(self, parent=None, id_renta: int | None = None):
        super().__init__(parent)
        title = "Procesar Devolucion"
        if id_renta:
            title += f" — Renta #{id_renta}"
        self.setWindowTitle(title)
        self.setMinimumSize(600, 700)
        dialog_background(self)
        self.id_renta = id_renta
        self._renta = {}

        layout = QVBoxLayout(self)
        self.lbl_info = QLabel("Cargando...")
        dialog_title(self.lbl_info)
        layout.addWidget(self.lbl_info)

        gb_dev = QGroupBox("Datos de Devolucion")
        group_box(gb_dev)
        f_dev = QFormLayout()
        self.date_retorno = QDateEdit(QDate.currentDate())
        self.date_retorno.setCalendarPopup(True)
        input_date(self.date_retorno)
        self.date_retorno.dateChanged.connect(self._recalcular)

        self.time_retorno = QTimeEdit(QTime.currentTime())
        input_time(self.time_retorno)
        self.time_retorno.timeChanged.connect(self._recalcular)

        self.txt_km_final = QLineEdit()
        self.txt_km_final.setPlaceholderText("Ej: 50500")
        input_field(self.txt_km_final)

        self.cmb_tanque = QComboBox()
        self.cmb_tanque.addItems(NIVEL_TANQUE)
        input_combo(self.cmb_tanque)
        f_dev.addRow("Fecha Real:", self.date_retorno); f_dev.addRow("Hora Real:", self.time_retorno)
        f_dev.addRow("Kilometraje Final:", self.txt_km_final); f_dev.addRow("Nivel Gasolina:", self.cmb_tanque)
        gb_dev.setLayout(f_dev); layout.addWidget(gb_dev)

        gb_cos = QGroupBox("Costos Adicionales")
        group_box(gb_cos)
        f_cos = QFormLayout()
        self.sp_dias_extra = QDoubleSpinBox(); self.sp_dias_extra.setReadOnly(True); self.sp_dias_extra.setSuffix(" dias"); input_spinbox(self.sp_dias_extra)
        self.sp_mora = QDoubleSpinBox(); self.sp_mora.setRange(0, 1e7); self.sp_mora.setPrefix("$ "); self.sp_mora.setEnabled(False); input_spinbox(self.sp_mora)
        self.sp_otros = QDoubleSpinBox(); self.sp_otros.setRange(0, 1e7); self.sp_otros.setPrefix("$ "); self.sp_otros.valueChanged.connect(self._recalcular); input_spinbox(self.sp_otros)
        self.txt_obs = QLineEdit(); self.txt_obs.setPlaceholderText("Danos, gasolina, etc."); input_field(self.txt_obs)
        f_cos.addRow("Tiempo Extra:", self.sp_dias_extra); f_cos.addRow("Costo Tiempo Extra:", self.sp_mora)
        f_cos.addRow("Otros (Danos/Gasolina):", self.sp_otros); f_cos.addRow("Observacion:", self.txt_obs)
        gb_cos.setLayout(f_cos); layout.addWidget(gb_cos)

        frame_tot = QFrame()
        frame_summary(frame_tot)
        lay_tot = QVBoxLayout(frame_tot)
        self.lbl_pactado = QLabel("Pactado: $0"); lbl_section(self.lbl_pactado)
        self.lbl_total = QLabel("TOTAL A PAGAR: $0"); lbl_subtitle(self.lbl_total)
        self.lbl_detalle = QLabel("")
        lay_tot.addWidget(self.lbl_pactado); lay_tot.addWidget(self.lbl_total); lay_tot.addWidget(self.lbl_detalle)
        layout.addWidget(frame_tot)

        btn_layout = QHBoxLayout()
        btn_inspeccion = QPushButton("Inspeccion (Check-in)"); btn_warning(btn_inspeccion)
        btn_inspeccion.clicked.connect(self._abrir_inspeccion)
        btn_cerrar = QPushButton("Finalizar Renta"); btn_success(btn_cerrar)
        btn_cerrar.clicked.connect(self._guardar)
        btn_cancel = QPushButton("Cancelar"); btn_danger(btn_cancel)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_inspeccion); btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel); btn_layout.addWidget(btn_cerrar)
        layout.addLayout(btn_layout)

        self._cargar_datos()

    def _cargar_datos(self):
        if self.id_renta is None:
            ModernMessageBox.error(self, "Error", "ID de Renta no especificado.")
            log.error("CierreRentaDialog llamado sin id_renta.")
            self.reject()
            return
        try:
            self._renta = RentaService.obtener(self.id_renta)
            info = (f"<b>Cliente:</b> {self._renta.get('nombre_cliente', '')}<br>"
                    f"<b>Vehiculo:</b> {self._renta.get('placa', '')}<br>"
                    f"<b>Fecha Pactada:</b> {self._renta.get('fecha_retorno', '')} {self._renta.get('hora_retorno', '')}")
            self.lbl_info.setText(info)
            self.lbl_pactado.setText(f"Valor Pactado Inicial: ${float(self._renta.get('total', 0)):,.0f}")
            self._recalcular()
        except DinamoBaseError as e:
            ModernMessageBox.warning(self, "Error", e.mensaje_usuario); self.reject()
        except Exception as e:
            log.error("Error cargando renta #%s: %s", self.id_renta, e, exc_info=True)
            ModernMessageBox.error(self, "Error", str(e)); self.reject()

    def _abrir_inspeccion(self):
        if self.id_renta is None:
            ModernMessageBox.warning(self, "Atención", "No hay una renta seleccionada.")
            return
        try:
            from views.rentas_view import InspeccionDialog
            dlg = InspeccionDialog(self, self.id_renta)
            dlg.cmb_tipo.setCurrentText("Recepcion (Check-in)")
            if self.txt_km_final.text().strip():
                try:
                    dlg.spin_km.setValue(float(self.txt_km_final.text().replace(',', '').strip()))
                except ValueError:
                    pass
            dlg.exec()
        except Exception as e:
            ModernMessageBox.error(self, "Error", f"No se pudo abrir inspeccion:\n{e}")

    def _recalcular(self):
        if not self._renta: return
        fecha_str = str(self._renta.get("fecha_retorno", ""))[:10]
        if not fecha_str: return
        try:
            fp = QDate.fromString(fecha_str, "yyyy-MM-dd")
            fr = self.date_retorno.date()
            dias_retraso = max(0, fp.daysTo(fr))
            mora = dias_retraso * float(self._renta.get("valor_dia", 0))
            self.sp_dias_extra.setValue(dias_retraso); self.sp_mora.setValue(mora)
            total_base = float(self._renta.get("total", 0))
            otros = self.sp_otros.value()
            gran_total = total_base + mora + otros
            self.lbl_total.setText(f"TOTAL A PAGAR: ${gran_total:,.0f}")
            self.lbl_detalle.setText(f"(${mora:,.0f} mora + ${otros:,.0f} extras)")
        except (ValueError, TypeError): pass

    def _guardar(self):
        if self.id_renta is None:
            ModernMessageBox.warning(self, "Atención", "No hay una renta seleccionada para cerrar.")
            return
        km_text = self.txt_km_final.text().strip()
        if not km_text:
            ModernMessageBox.warning(self, "Dato faltante", "Ingrese el Kilometraje Final")
            self.txt_km_final.setFocus()
            return
        try:
            km_final_float = float(km_text.replace(',', '').replace(' ', ''))
        except ValueError:
            ModernMessageBox.warning(self, "Dato inválido", "Ingrese un Kilometraje Final válido")
            self.txt_km_final.setFocus()
            return
        datos_cierre = {
            "fecha_devolucion_real": self.date_retorno.date().toString("yyyy-MM-dd"),
            "hora_devolucion_real": self.time_retorno.time().toString("HH:mm"),
            "km_final": km_text,
            "km_final_float": km_final_float,
            "tanque_final": self.cmb_tanque.currentText(),
            "nota_cierre": f" | Cierre: {self.txt_obs.text()}",
            "otros_cobros": self.sp_otros.value(),
        }
        try:
            RentaService.cerrar(self.id_renta, datos_cierre)
            ModernMessageBox.success(self, "Exito", "Renta finalizada correctamente.\nEl vehiculo esta Disponible.")
            self.accept()
        except DinamoBaseError as e:
            ModernMessageBox.error(self, "Error", e.mensaje_usuario)
        except Exception as e:
            log.error("Error cerrando renta #%s: %s", self.id_renta, e, exc_info=True)
            ModernMessageBox.error(self, "Error", str(e))
