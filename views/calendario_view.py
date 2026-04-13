"""
views/calendario_view.py — Vista refactorizada para el Calendario de Disponibilidad.
"""
import calendar
from datetime import date, datetime
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                               QTableWidgetItem, QPushButton, QLabel, QHeaderView, QAbstractItemView, QMessageBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

# IMPORTACIONES A LA CAPA DE SERVICIOS
from services.services import AutoService, RentaService
from core.exceptions import DinamoBaseError

class CalendarioWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.fecha_actual = date.today()
        self.mes_vista = self.fecha_actual.month
        self.anio_vista = self.fecha_actual.year

        self._setup_ui()
        self.cargar_calendario()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Header Control
        h_ctrl = QHBoxLayout()
        btn_prev = QPushButton("◀ Anterior")
        btn_prev.clicked.connect(self.mes_anterior)

        self.lbl_mes = QLabel("MES AÑO")
        self.lbl_mes.setStyleSheet("font-size: 16px; font-weight: bold; text-transform: uppercase;")

        btn_next = QPushButton("Siguiente ▶")
        btn_next.clicked.connect(self.mes_siguiente)

        btn_act = QPushButton("Actualizar")
        btn_act.clicked.connect(self.cargar_calendario)

        h_ctrl.addWidget(btn_prev)
        h_ctrl.addStretch()
        h_ctrl.addWidget(self.lbl_mes)
        h_ctrl.addStretch()
        h_ctrl.addWidget(btn_next)
        h_ctrl.addWidget(btn_act)
        layout.addLayout(h_ctrl)

        # Leyenda
        h_ley = QHBoxLayout()
        for txt, col in [("Disponible", "transparent"), ("Rentado", "#ef5350"), ("Reservado", "#ffa726")]:
            lbl = QLabel(f"  {txt}  ")
            if col == "transparent":
                lbl.setStyleSheet("border: 1px solid #ccc; border-radius: 4px; padding: 2px;")
            else:
                lbl.setStyleSheet(f"background-color: {col}; border-radius: 4px; padding: 2px; color: white; font-weight: bold;")
            h_ley.addWidget(lbl)
        h_ley.addStretch()
        layout.addLayout(h_ley)

        # Tabla Calendario
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.tabla)

    def mes_anterior(self):
        if self.mes_vista == 1:
            self.mes_vista = 12
            self.anio_vista -= 1
        else:
            self.mes_vista -= 1
        self.cargar_calendario()

    def mes_siguiente(self):
        if self.mes_vista == 12:
            self.mes_vista = 1
            self.anio_vista += 1
        else:
            self.mes_vista += 1
        self.cargar_calendario()

    def cargar_calendario(self):
        # Nombres de meses en español
        meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                 "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        nombre_mes = f"{meses[self.mes_vista - 1]} {self.anio_vista}"
        self.lbl_mes.setText(nombre_mes)

        # Obtener la cantidad exacta de días del mes seleccionado
        dias_en_mes = calendar.monthrange(self.anio_vista, self.mes_vista)[1]

        # Configurar columnas
        self.tabla.setColumnCount(dias_en_mes + 1) # +1 para la columna del auto
        headers = ["VEHÍCULO"] + [str(i) for i in range(1, dias_en_mes + 1)]
        self.tabla.setHorizontalHeaderLabels(headers)
        self.tabla.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for c in range(1, dias_en_mes + 1):
            self.tabla.setColumnWidth(c, 30)

        # Obtener Datos desde la capa de servicios
        try:
            autos = AutoService.listar()
            rentas = RentaService.obtener_para_calendario(self.mes_vista, self.anio_vista)
        except DinamoBaseError as e:
            QMessageBox.warning(self, "Error", f"No se pudo cargar el calendario:\n{e}")
            return

        self.tabla.setRowCount(0)

        for i, auto in enumerate(autos):
            self.tabla.insertRow(i)
            placa = auto.get('placa', '')
            modelo = auto.get('modelo', '')

            item_auto = QTableWidgetItem(f"{placa}\n{modelo}")
            self.tabla.setItem(i, 0, item_auto)

            # Filtrar eventos correspondientes a este auto
            eventos_auto = [r for r in rentas if r.get('placa') == placa]

            for r in eventos_auto:
                try:
                    f_ini_str = str(r.get('fecha_recogida', ''))[:10]
                    f_fin_str = str(r.get('fecha_retorno', ''))[:10]
                    f_ini = datetime.strptime(f_ini_str, "%Y-%m-%d").date()
                    f_fin = datetime.strptime(f_fin_str, "%Y-%m-%d").date()

                    # Iterar los días del mes actual para pintar
                    for dia in range(1, dias_en_mes + 1):
                        fecha_actual = date(self.anio_vista, self.mes_vista, dia)

                        if f_ini <= fecha_actual <= f_fin:
                            item = QTableWidgetItem()
                            color = "#ef5350" if r.get('tipo') == 'Renta' else "#ffa726"
                            item.setBackground(QColor(color))
                            item.setToolTip(f"{r.get('tipo')}: {r.get('nombre_cliente')}")
                            self.tabla.setItem(i, dia, item)
                except ValueError:
                    # Ignorar si hay fechas corruptas en la BD
                    pass