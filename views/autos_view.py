"""
autos_view.py — Gestión de flota (vista)

Solo maneja la UI. Toda la lógica va a AutoService.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QLineEdit, QDialog, QFormLayout,
    QComboBox, QDateEdit, QDoubleSpinBox, QGroupBox, QPlainTextEdit,
    QAbstractItemView, QGridLayout, QScrollArea, QWidget, QMessageBox
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush

from core.config import (
    TIPOS_AUTO, TIPOS_TRANSMISION, TIPOS_COMBUSTIBLE,
    ESTADOS_AUTO, TIPOS_ADQUISICION, COLOR_PRIMARIO,
)
from core.exceptions import DinamoBaseError
from services.services import AutoService
from views.base_widget import BaseWidget


class _UpperLineEdit(QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.textChanged.connect(lambda t: self.setText(t.upper()) if not t.isupper() else None)


class DialogoAuto(QDialog):
    """Diálogo para crear o editar un vehículo."""

    def __init__(self, parent=None, placa_editar: str | None = None):
        super().__init__(parent)
        self.setWindowTitle("Gestión de Vehículo")
        self.setFixedSize(900, 650)
        self.placa_editar = placa_editar
        self._log = __import__("core.logger", fromlist=["get_logger"]).get_logger(__name__)

        layout = QVBoxLayout(self)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.form_layout = QVBoxLayout(content)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self._construir_form()

        btn_save = QPushButton("GUARDAR VEHÍCULO")
        btn_save.setStyleSheet(
            f"background-color:{COLOR_PRIMARIO};color:white;font-weight:bold;padding:12px;"
        )
        btn_save.clicked.connect(self._guardar)
        fila = QHBoxLayout()
        fila.addStretch()
        fila.addWidget(btn_save)
        layout.addLayout(fila)

        if placa_editar:
            self._cargar(placa_editar)

    # ── construcción del formulario ──────────────────────────────────────────

    def _construir_form(self):
        # Básico
        gb = QGroupBox("Información Básica")
        g = QGridLayout()
        self.txt_placa       = _UpperLineEdit()
        self.txt_marca       = _UpperLineEdit()
        self.txt_modelo      = _UpperLineEdit()
        self.txt_version     = _UpperLineEdit()
        self.txt_color       = _UpperLineEdit()
        self.cmb_tipo        = QComboBox(); self.cmb_tipo.addItems(TIPOS_AUTO)
        if self.placa_editar:
            self.txt_placa.setReadOnly(True)
        g.addWidget(QLabel("Placa (*):"),   0, 0); g.addWidget(self.txt_placa,   0, 1)
        g.addWidget(QLabel("Marca:"),       0, 2); g.addWidget(self.txt_marca,   0, 3)
        g.addWidget(QLabel("Modelo:"),      1, 0); g.addWidget(self.txt_modelo,  1, 1)
        g.addWidget(QLabel("Versión:"),     1, 2); g.addWidget(self.txt_version, 1, 3)
        g.addWidget(QLabel("Color:"),       2, 0); g.addWidget(self.txt_color,   2, 1)
        g.addWidget(QLabel("Tipo:"),        2, 2); g.addWidget(self.cmb_tipo,    2, 3)
        gb.setLayout(g); self.form_layout.addWidget(gb)

        # Técnico
        gb2 = QGroupBox("Datos Técnicos")
        g2 = QGridLayout()
        self.txt_cilindraje   = _UpperLineEdit()
        self.cmb_transmision  = QComboBox(); self.cmb_transmision.addItems(TIPOS_TRANSMISION)
        self.cmb_combustible  = QComboBox(); self.cmb_combustible.addItems(TIPOS_COMBUSTIBLE)
        self.txt_motor        = _UpperLineEdit()
        self.txt_chasis       = _UpperLineEdit()
        self.sp_km            = QDoubleSpinBox(); self.sp_km.setRange(0, 1e7)
        g2.addWidget(QLabel("Cilindraje:"),    0, 0); g2.addWidget(self.txt_cilindraje,  0, 1)
        g2.addWidget(QLabel("Transmisión:"),   0, 2); g2.addWidget(self.cmb_transmision, 0, 3)
        g2.addWidget(QLabel("Combustible:"),   1, 0); g2.addWidget(self.cmb_combustible, 1, 1)
        g2.addWidget(QLabel("Kilometraje:"),   1, 2); g2.addWidget(self.sp_km,           1, 3)
        g2.addWidget(QLabel("No. Motor:"),     2, 0); g2.addWidget(self.txt_motor,       2, 1)
        g2.addWidget(QLabel("No. Chasis:"),    2, 2); g2.addWidget(self.txt_chasis,      2, 3)
        gb2.setLayout(g2); self.form_layout.addWidget(gb2)

        # Administrativo
        gb3 = QGroupBox("Administrativo y Financiero")
        g3 = QGridLayout()
        self.txt_propietario = _UpperLineEdit()
        self.sp_costo        = QDoubleSpinBox(); self.sp_costo.setRange(0, 1e9); self.sp_costo.setPrefix("$ ")
        self.cmb_estado      = QComboBox(); self.cmb_estado.addItems(ESTADOS_AUTO)
        self.cmb_adq         = QComboBox(); self.cmb_adq.addItems(TIPOS_ADQUISICION)
        self.txt_ubicacion   = _UpperLineEdit()
        self.d_ingreso       = QDateEdit(QDate.currentDate())
        self.d_ingreso.setCalendarPopup(True); self.d_ingreso.setDisplayFormat("yyyy-MM-dd")
        g3.addWidget(QLabel("Propietario:"),         0, 0); g3.addWidget(self.txt_propietario, 0, 1)
        g3.addWidget(QLabel("Costo Fijo Mensual:"),  0, 2); g3.addWidget(self.sp_costo,        0, 3)
        g3.addWidget(QLabel("Estado:"),              1, 0); g3.addWidget(self.cmb_estado,      1, 1)
        g3.addWidget(QLabel("Tipo Adquisición:"),    1, 2); g3.addWidget(self.cmb_adq,         1, 3)
        g3.addWidget(QLabel("Ubicación Actual:"),    2, 0); g3.addWidget(self.txt_ubicacion,   2, 1)
        g3.addWidget(QLabel("Fecha Ingreso Flota:"), 2, 2); g3.addWidget(self.d_ingreso,       2, 3)
        gb3.setLayout(g3); self.form_layout.addWidget(gb3)

        # Vencimientos
        gb4 = QGroupBox("Vencimientos")
        g4 = QGridLayout()
        def _date_widget():
            w = QDateEdit(QDate.currentDate().addYears(1))
            w.setCalendarPopup(True); w.setDisplayFormat("yyyy-MM-dd")
            return w
        self.d_soat    = _date_widget()
        self.d_tecno   = _date_widget()
        self.d_extintor= _date_widget()
        self.d_bateria = _date_widget()
        g4.addWidget(QLabel("SOAT:"),              0, 0); g4.addWidget(self.d_soat,     0, 1)
        g4.addWidget(QLabel("Tecnicomecánica:"),   0, 2); g4.addWidget(self.d_tecno,    0, 3)
        g4.addWidget(QLabel("Extintor:"),          1, 0); g4.addWidget(self.d_extintor, 1, 1)
        g4.addWidget(QLabel("Garantía Batería:"),  1, 2); g4.addWidget(self.d_bateria,  1, 3)
        gb4.setLayout(g4); self.form_layout.addWidget(gb4)

        # Observaciones
        self.form_layout.addWidget(QLabel("Observaciones:"))
        self.txt_obs = QPlainTextEdit(); self.txt_obs.setMaximumHeight(60)
        self.form_layout.addWidget(self.txt_obs)

    # ── datos ────────────────────────────────────────────────────────────────

    def _cargar(self, placa: str):
        try:
            d = AutoService.obtener(placa)
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", e.mensaje_usuario)
            return

        self.txt_placa.setText(d.get("placa", ""))
        self.txt_marca.setText(d.get("marca", ""))
        self.txt_modelo.setText(d.get("modelo", ""))
        self.txt_version.setText(d.get("version", ""))
        self.txt_color.setText(d.get("color", ""))
        self.cmb_tipo.setCurrentText(d.get("tipo", "Automóvil"))
        self.txt_cilindraje.setText(d.get("cilindraje", ""))
        self.cmb_transmision.setCurrentText(d.get("transmision", "Automática"))
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
            (self.d_soat, "vencimiento_soat"), (self.d_tecno, "vencimiento_tecnico"),
            (self.d_extintor, "vencimiento_extintor"), (self.d_bateria, "vencimiento_bateria"),
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
            QMessageBox.warning(self, "Error", "La placa es obligatoria")
            return

        datos = {
            "placa":               self.txt_placa.text().strip(),
            "marca":               self.txt_marca.text().strip(),
            "modelo":              self.txt_modelo.text().strip(),
            "version":             self.txt_version.text().strip(),
            "color":               self.txt_color.text().strip(),
            "tipo":                self.cmb_tipo.currentText(),
            "cilindraje":          self.txt_cilindraje.text().strip(),
            "transmision":         self.cmb_transmision.currentText(),
            "combustible":         self.cmb_combustible.currentText(),
            "no_motor":            self.txt_motor.text().strip(),
            "no_chasis":           self.txt_chasis.text().strip(),
            "propietario":         self.txt_propietario.text().strip(),
            "estado":              self.cmb_estado.currentText(),
            "costo_fijo_mensual":  self.sp_costo.value(),
            "kilometraje":         self.sp_km.value(),
            "ubicacion":           self.txt_ubicacion.text().strip(),
            "vencimiento_soat":    self.d_soat.date().toString("yyyy-MM-dd"),
            "vencimiento_tecnico": self.d_tecno.date().toString("yyyy-MM-dd"),
            "vencimiento_extintor":self.d_extintor.date().toString("yyyy-MM-dd"),
            "vencimiento_bateria": self.d_bateria.date().toString("yyyy-MM-dd"),
            "observaciones":       self.txt_obs.toPlainText(),
            "tipo_adquisicion":    self.cmb_adq.currentText(),
            "fecha_ingreso":       self.d_ingreso.date().toString("yyyy-MM-dd"),
        }

        try:
            AutoService.guardar(datos)
            QMessageBox.information(self, "Éxito", "Vehículo guardado correctamente")
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", e.mensaje_usuario)


class AutosWidget(BaseWidget):
    """Panel principal de gestión de flota."""

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        top.addWidget(QLabel("Gestión de Flota", styleSheet="font-size:18px;font-weight:bold"))
        btn_nuevo = QPushButton("+ Nuevo Vehículo")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_act = QPushButton("Actualizar")
        btn_act.clicked.connect(self.cargar_datos)
        top.addStretch()
        top.addWidget(btn_nuevo)
        top.addWidget(btn_act)
        layout.addLayout(top)

        self.tabla = QTableWidget()
        self.ajustar_tabla(
            self.tabla,
            ["Placa", "Marca/Modelo", "Color", "Estado", "KM", "Ubicación", "Ingreso", ""]
        )
        self.tabla.setColumnWidth(7, 50)
        layout.addWidget(self.tabla)

        self.cargar_datos()

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        autos = self.ejecutar_seguro(AutoService.listar) or []
        for r in autos:
            i = self.tabla.rowCount()
            self.tabla.insertRow(i)
            self.tabla.setItem(i, 0, QTableWidgetItem(r.get("placa", "")))
            self.tabla.setItem(i, 1, QTableWidgetItem(f"{r.get('marca','')} {r.get('modelo','')}"))
            self.tabla.setItem(i, 2, QTableWidgetItem(r.get("color", "")))

            st = QTableWidgetItem(r.get("estado", ""))
            if r.get("estado") == "Disponible":
                st.setForeground(QBrush(QColor("green")))
            elif r.get("estado") == "Rentado":
                st.setForeground(QBrush(QColor("blue")))
            self.tabla.setItem(i, 3, st)

            self.tabla.setItem(i, 4, QTableWidgetItem(f"{r.get('kilometraje', 0):,.0f}"))
            self.tabla.setItem(i, 5, QTableWidgetItem(r.get("ubicacion", "")))
            self.tabla.setItem(i, 6, QTableWidgetItem(r.get("fecha_ingreso", "")))

            btn = QPushButton("✏️")
            btn.setFixedWidth(40)
            btn.clicked.connect(lambda _, p=r.get("placa"): self._editar(p))
            self.tabla.setCellWidget(i, 7, btn)

    def _nuevo(self):
        if DialogoAuto(self).exec():
            self.cargar_datos()

    def _editar(self, placa: str):
        if DialogoAuto(self, placa).exec():
            self.cargar_datos()
