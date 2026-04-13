"""
clientes_view.py — Directorio de clientes

La búsqueda y persistencia van por ClienteService.
"""
from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QPushButton, QLabel,
    QLineEdit, QDialog, QFormLayout, QComboBox, QMessageBox,
    QTabWidget, QDateEdit, QWidget
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush

from core.config import TIPOS_DOC, ESTADOS_CLIENTE, COLOR_PRIMARIO
from core.exceptions import DinamoBaseError
from services.services import ClienteService
from views.base_widget import BaseWidget


class ClienteFormDialog(QDialog):
    """Formulario de creación/edición de cliente."""

    def __init__(self, parent=None, datos: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Ficha de Cliente")
        self.setFixedSize(700, 600)
        self._datos = datos or {}

        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        tab1 = QWidget(); self._construir_tab_personal(tab1)
        tab2 = QWidget(); self._construir_tab_licencia(tab2)
        self.tabs.addTab(tab1, "Datos Personales")
        self.tabs.addTab(tab2, "Licencia / Ubicación / Estado")
        layout.addWidget(self.tabs)

        btn_row = QHBoxLayout()
        btn_cancel = QPushButton("Cancelar"); btn_cancel.clicked.connect(self.reject)
        btn_save   = QPushButton("Guardar Ficha")
        btn_save.setStyleSheet(
            f"background-color:{COLOR_PRIMARIO};color:white;padding:10px;font-weight:bold;"
        )
        btn_save.clicked.connect(self._guardar)
        btn_row.addStretch(); btn_row.addWidget(btn_cancel); btn_row.addWidget(btn_save)
        layout.addLayout(btn_row)

        if datos:
            self._cargar()

    def _construir_tab_personal(self, tab):
        lay = QFormLayout(tab); lay.setSpacing(10)
        self.cmb_tipo_doc   = QComboBox(); self.cmb_tipo_doc.addItems(TIPOS_DOC)
        self.txt_no_doc     = QLineEdit(); self.txt_no_doc.setPlaceholderText("Número único")
        self.txt_nombres    = QLineEdit()
        self.txt_apellidos  = QLineEdit()
        self.txt_nacion     = QLineEdit()
        self.txt_pais       = QLineEdit(); self.txt_pais.setText("Colombia")
        self.txt_estado_reg = QLineEdit()
        self.txt_ciudad     = QLineEdit()
        self.txt_celular    = QLineEdit()
        self.txt_celular2   = QLineEdit()
        self.txt_email      = QLineEdit()
        for label, widget in [
            ("Tipo Doc:",         self.cmb_tipo_doc),
            ("No. Documento (*):",self.txt_no_doc),
            ("Nombres (*):",      self.txt_nombres),
            ("Apellidos:",        self.txt_apellidos),
            ("Nacionalidad:",     self.txt_nacion),
            ("País Origen:",      self.txt_pais),
            ("Estado/Región:",    self.txt_estado_reg),
            ("Ciudad Origen:",    self.txt_ciudad),
            ("Celular Principal:",self.txt_celular),
            ("Celular Secundario:",self.txt_celular2),
            ("Email:",            self.txt_email),
        ]:
            lay.addRow(label, widget)

    def _construir_tab_licencia(self, tab):
        lay = QFormLayout(tab)
        self.txt_licencia     = QLineEdit()
        self.txt_tipo_lic     = QLineEdit(); self.txt_tipo_lic.setPlaceholderText("Ej: B1, C1, Internacional")
        self.date_venc_lic    = QDateEdit(QDate.currentDate().addYears(1))
        self.date_venc_lic.setCalendarPopup(True)
        self.txt_dir_res      = QLineEdit()
        self.txt_dir_temp     = QLineEdit(); self.txt_dir_temp.setPlaceholderText("Si es turista")
        self.txt_hotel        = QLineEdit()
        self.txt_habitacion   = QLineEdit()
        self.cmb_estado       = QComboBox(); self.cmb_estado.addItems(ESTADOS_CLIENTE)
        for label, widget in [
            ("No. Licencia:",         self.txt_licencia),
            ("Categoría/Tipo:",       self.txt_tipo_lic),
            ("Vencimiento Licencia:", self.date_venc_lic),
            ("Dir. Residencia:",      self.txt_dir_res),
            ("Dir. Temporal:",        self.txt_dir_temp),
            ("Hotel / Hospedaje:",    self.txt_hotel),
            ("No. Habitación:",       self.txt_habitacion),
            ("Estado Cliente:",       self.cmb_estado),
        ]:
            lay.addRow(label, widget)

    def _cargar(self):
        d = self._datos
        self.cmb_tipo_doc.setCurrentText(str(d.get("tipo_doc", "Cédula")))
        self.txt_no_doc.setText(str(d.get("no_doc", "")))
        self.txt_nombres.setText(str(d.get("nombres", "")))
        self.txt_apellidos.setText(str(d.get("apellidos", "")))
        self.txt_nacion.setText(str(d.get("nacionalidad", "")))
        self.txt_pais.setText(str(d.get("pais", "Colombia")))
        self.txt_estado_reg.setText(str(d.get("estado_region", "")))
        self.txt_ciudad.setText(str(d.get("ciudad", "")))
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
                from datetime import datetime
                self.date_venc_lic.setDate(
                    datetime.strptime(str(venc)[:10], "%Y-%m-%d").date()
                )
            except ValueError:
                pass

    def _guardar(self):
        if not self.txt_no_doc.text().strip() or not self.txt_nombres.text().strip():
            QMessageBox.warning(self, "Error", "Documento y Nombres son obligatorios")
            return

        datos = {
            "tipo_doc":           self.cmb_tipo_doc.currentText(),
            "no_doc":             self.txt_no_doc.text().strip(),
            "nombres":            self.txt_nombres.text().strip(),
            "apellidos":          self.txt_apellidos.text().strip(),
            "celular":            self.txt_celular.text().strip(),
            "celular2":           self.txt_celular2.text().strip(),
            "email":              self.txt_email.text().strip(),
            "pais":               self.txt_pais.text().strip(),
            "estado_region":      self.txt_estado_reg.text().strip(),
            "ciudad":             self.txt_ciudad.text().strip(),
            "nacionalidad":       self.txt_nacion.text().strip(),
            "dir_residencia":     self.txt_dir_res.text().strip(),
            "dir_temporal":       self.txt_dir_temp.text().strip(),
            "hotel":              self.txt_hotel.text().strip(),
            "habitacion":         self.txt_habitacion.text().strip(),
            "no_licencia":        self.txt_licencia.text().strip(),
            "tipo_licencia":      self.txt_tipo_lic.text().strip(),
            "vencimiento_licencia": self.date_venc_lic.date().toString("yyyy-MM-dd"),
            "estado":             self.cmb_estado.currentText(),
        }

        try:
            ClienteService.guardar(datos)
            self.accept()
        except DinamoBaseError as e:
            QMessageBox.critical(self, "Error", e.mensaje_usuario)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))


class ClientesWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        lbl = QLabel("Directorio de Clientes")
        lbl.setStyleSheet("font-size:20px;font-weight:bold;")
        self.txt_buscar = QLineEdit()
        self.txt_buscar.setPlaceholderText("🔍 Buscar por nombre o cédula…")
        self.txt_buscar.textChanged.connect(self._filtrar)
        self.txt_buscar.setFixedWidth(250)
        btn_nuevo   = QPushButton(" + Nuevo Cliente")
        btn_nuevo.setStyleSheet("background-color:green;color:white;font-weight:bold;padding:8px;")
        btn_nuevo.clicked.connect(self._nuevo)
        btn_ref     = QPushButton("Recargar"); btn_ref.clicked.connect(self.cargar_datos)
        top.addWidget(lbl); top.addStretch()
        top.addWidget(self.txt_buscar); top.addWidget(btn_ref); top.addWidget(btn_nuevo)
        layout.addLayout(top)

        from PySide6.QtWidgets import QTableWidget
        self.tabla = QTableWidget()
        self.ajustar_tabla(
            self.tabla,
            ["Documento", "Nombre Completo", "Celular", "Nacionalidad", "Estado", "Licencia"]
        )
        self.tabla.cellDoubleClicked.connect(self._editar)
        layout.addWidget(self.tabla)

        self._lista: list[dict] = []
        self.cargar_datos()

    def cargar_datos(self):
        self.tabla.setRowCount(0)
        self._lista = self.ejecutar_seguro(ClienteService.buscar) or []
        for i, cli in enumerate(self._lista):
            self.tabla.insertRow(i)
            items = [
                QTableWidgetItem(str(cli.get("no_doc", ""))),
                QTableWidgetItem(str(cli.get("nombre_completo", ""))),
                QTableWidgetItem(str(cli.get("celular", ""))),
                QTableWidgetItem(str(cli.get("nacionalidad", ""))),
                QTableWidgetItem(str(cli.get("estado", ""))),
                QTableWidgetItem(str(cli.get("no_licencia", ""))),
            ]
            estado = str(cli.get("estado", ""))
            color_map = {"Activo": "green", "Lista Negra": "red", "VIP": "purple"}
            if estado in color_map:
                items[4].setForeground(QBrush(QColor(color_map[estado])))
            for j, it in enumerate(items):
                it.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.tabla.setItem(i, j, it)

    def _filtrar(self):
        txt = self.txt_buscar.text().lower()
        for i in range(self.tabla.rowCount()):
            doc = self.tabla.item(i, 0)
            nom = self.tabla.item(i, 1)
            vis = (doc and txt in doc.text().lower()) or (nom and txt in nom.text().lower())
            self.tabla.setRowHidden(i, not vis)

    def _nuevo(self):
        if ClienteFormDialog(self).exec():
            self.cargar_datos()
            self.mostrar_exito("Cliente registrado correctamente")

    def _editar(self, row: int, _col: int):
        if row >= len(self._lista):
            return
        datos = self.ejecutar_seguro(ClienteService.obtener, self._lista[row]["id"])
        if datos and ClienteFormDialog(self, datos).exec():
            self.cargar_datos()
