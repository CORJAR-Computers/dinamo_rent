"""
dashboard_view.py — Panel principal / Dashboard

Solo construye la UI y llama a los servicios para obtener datos operativos.
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidgetItem, QHeaderView, QScrollArea, QAbstractItemView,
    QMessageBox, QComboBox, QPushButton
)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_PRIMARIO
from services.dashboard_service import DashboardService
from services.auto_service import AutoService
from views.base_widget import BaseWidget

_ESTILO_TARJETA = """
    QFrame { background-color: white; border-radius: 10px; border: 1px solid #e0e0e0; }
    QFrame:hover { border: 1px solid #b0bec5; }
"""

class _KpiCard(QFrame):
    def __init__(self, titulo: str, color: str, icono: str = "📊"):
        super().__init__()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: white; border-radius: 12px;
                border-left: 6px solid {color};
                border-right: 1px solid #e0e0e0;
                border-top: 1px solid #e0e0e0;
                border-bottom: 1px solid #e0e0e0;
            }}
        """)
        self.setFixedHeight(110)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 15, 20, 15)

        h = QHBoxLayout()
        lbl_t = QLabel(titulo.upper())
        lbl_t.setStyleSheet("color:#78909c;font-size:11px;font-weight:bold;letter-spacing:1px;border:none;")
        lbl_i = QLabel(icono)
        lbl_i.setStyleSheet("font-size:20px;border:none;background:transparent;")
        h.addWidget(lbl_t); h.addStretch(); h.addWidget(lbl_i)

        self.lbl_valor = QLabel("—")
        self.lbl_valor.setStyleSheet(
            f"color:{color};font-size:32px;font-weight:bold;border:none;"
        )
        self.lbl_valor.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        lay.addLayout(h)
        lay.addWidget(self.lbl_valor)

    def set_value(self, v: str):
        self.lbl_valor.setText(v)


class DashboardWidget(BaseWidget):
    """Panel general con KPIs operativos, alertas y rentas con filtros."""

    def __init__(self):
        super().__init__()
        self._todas_las_rentas = [] # Caché para los filtros

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background-color:#f4f6f8;")

        self._content = QFrame()
        self._content.setStyleSheet("background-color:#f4f6f8;")
        self._lay = QVBoxLayout(self._content)
        self._lay.setContentsMargins(25, 25, 25, 25)
        self._lay.setSpacing(20)

        scroll.setWidget(self._content)
        main_layout.addWidget(scroll)

        self._construir_ui()
        self.cargar_datos()

    def _construir_ui(self):
        # --- Encabezado ---
        header = QHBoxLayout()
        lbl = QLabel("Tablero de Operaciones")
        lbl.setStyleSheet("font-size:26px;font-weight:900;color:#1a237e;")

        btn_ref = QPushButton("🔄 Actualizar Tablero")
        btn_ref.setProperty("cssClass", "primary")
        btn_ref.setFixedSize(160, 35)
        btn_ref.clicked.connect(self.cargar_datos)

        lbl_fecha = QLabel(datetime.now().strftime("%d-%m-%Y"))
        lbl_fecha.setStyleSheet("font-size:14px;color:#546e7a;font-weight:bold; margin-left: 15px;")

        header.addWidget(lbl)
        header.addStretch()
        header.addWidget(btn_ref)
        header.addWidget(lbl_fecha)
        self._lay.addLayout(header)

        # --- KPIs (100% Operativos, sin finanzas) ---
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(15)
        self.card_disp    = _KpiCard("Disponibles",    "#2E7D32", "✅") # Verde
        self.card_activas = _KpiCard("Rentas Activas", "#1565C0", "🚗") # Azul
        self.card_taller  = _KpiCard("En Taller",      "#EF6C00", "🔧") # Naranja
        self.card_alertas = _KpiCard("Alertas",        "#C62828", "⚠️") # Rojo

        for c in (self.card_disp, self.card_activas, self.card_taller, self.card_alertas):
            kpi_row.addWidget(c)
        self._lay.addLayout(kpi_row)

        # --- Sección central (Split View) ---
        mid = QHBoxLayout(); mid.setSpacing(20)

        # 1. Alertas (Izquierda)
        fr_al = QFrame(); fr_al.setStyleSheet(_ESTILO_TARJETA)
        lay_al = QVBoxLayout(fr_al)
        lbl_al = QLabel("⚠️ Alertas de Flota y Vencimientos")
        lbl_al.setStyleSheet("font-size:15px;font-weight:bold;color:#37474f;border:none;")
        lay_al.addWidget(lbl_al)

        from PySide6.QtWidgets import QTableWidget
        self.tbl_alertas = QTableWidget()
        self._estilizar(self.tbl_alertas, ["Placa", "Alerta", "Fecha/Detalle", "Estado"])
        lay_al.addWidget(self.tbl_alertas)

        # 2. Rentas activas + Filtros (Derecha)
        fr_r = QFrame(); fr_r.setStyleSheet(_ESTILO_TARJETA)
        lay_r = QVBoxLayout(fr_r)

        header_rentas = QHBoxLayout()
        lbl_r = QLabel("📋 Rentas  (doble clic → cerrar)")
        lbl_r.setStyleSheet("font-size:15px;font-weight:bold;color:#37474f;border:none;")

        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems([
            "Todas las Activas",
            "Vencen Hoy",
            "Retrasadas (Vencidas)",
            "Entregas de Mañana"
        ])
        self.cmb_filtro.currentIndexChanged.connect(self.filtrar_tabla)

        header_rentas.addWidget(lbl_r)
        header_rentas.addStretch()
        header_rentas.addWidget(self.cmb_filtro)
        lay_r.addLayout(header_rentas)

        self.tbl_rentas = QTableWidget()
        self._estilizar(self.tbl_rentas, ["ID", "Placa", "Cliente", "Retorno", "Días"])
        self.tbl_rentas.setColumnHidden(0, True) # Ocultar ID
        self.tbl_rentas.cellDoubleClicked.connect(self._abrir_cierre)
        lay_r.addWidget(self.tbl_rentas)

        # Proporción: Alertas ocupa menos espacio que las Rentas (stretch 2 vs 3)
        mid.addWidget(fr_al, stretch=2)
        mid.addWidget(fr_r,  stretch=3)
        self._lay.addLayout(mid)
        self._lay.addStretch()

    def _estilizar(self, tabla, columnas):
        self.ajustar_tabla(tabla, columnas)
        tabla.setStyleSheet("""
            QTableWidget { border:none; gridline-color:#f0f0f0; }
            QTableWidget::item { padding:5px; color:#37474f; }
            QTableWidget::item:selected { background-color:#e3f2fd; color:#1565c0; }
        """)
        try:
            tabla.horizontalHeader().setStyleSheet("""
                QHeaderView::section {
                    background-color:#fafafa; padding:8px; border:none;
                    border-bottom:2px solid #e0e0e0; font-weight:bold; color:#546e7a;
                }
            """)
        except Exception:
            pass

    def cargar_datos(self):
        # 1. Cargar KPIs Operativos
        flota = self.ejecutar_seguro(AutoService.listar) or []
        disp = sum(1 for a in flota if a.get("estado") == "Disponible")
        taller = sum(1 for a in flota if a.get("estado") == "En Taller")

        rentas = self.ejecutar_seguro(DashboardService.obtener_activas) or []
        alertas = self.ejecutar_seguro(AutoService.obtener_alertas) or []

        self.card_disp.set_value(str(disp))
        self.card_activas.set_value(str(len(rentas)))
        self.card_taller.set_value(str(taller))
        self.card_alertas.set_value(str(len(alertas)))

        # 2. Cargar Tabla de Alertas
        self.tbl_alertas.setRowCount(0)
        for a in alertas:
            r = self.tbl_alertas.rowCount()
            self.tbl_alertas.insertRow(r)
            self.tbl_alertas.setItem(r, 0, QTableWidgetItem(a.get("placa", "")))
            self.tbl_alertas.setItem(r, 1, QTableWidgetItem(a.get("tipo", "")))
            self.tbl_alertas.setItem(r, 2, QTableWidgetItem(a.get("detalle", "")))

            est = a.get("estado", "")
            it = QTableWidgetItem(est)
            it.setFont(QFont("Arial", 8, QFont.Weight.Bold))
            critico = "VENCIDO" in est or "CRÍTICO" in est
            it.setForeground(QBrush(QColor("#c62828" if critico else "#ef6c00")))
            self.tbl_alertas.setItem(r, 3, it)

        # 3. Guardar Rentas en caché y aplicar el filtro
        self._todas_las_rentas = rentas
        self.filtrar_tabla()

    def filtrar_tabla(self):
        self.tbl_rentas.setRowCount(0)
        filtro = self.cmb_filtro.currentText()
        hoy = datetime.now().date()
        hoy_str = hoy.strftime("%Y-%m-%d")

        rentas_filtradas = []

        for r in self._todas_las_rentas:
            fecha_ret_str = r.get("fecha_retorno", "")[:10]

            if filtro == "Todas las Activas":
                rentas_filtradas.append(r)
            elif filtro == "Vencen Hoy" and fecha_ret_str == hoy_str:
                rentas_filtradas.append(r)
            elif filtro == "Retrasadas (Vencidas)":
                if fecha_ret_str and fecha_ret_str < hoy_str:
                    rentas_filtradas.append(r)
            elif filtro == "Entregas de Mañana":
                manana = QDate.currentDate().addDays(1).toString("yyyy-MM-dd")
                if fecha_ret_str == manana:
                    rentas_filtradas.append(r)

        # Dibujar la tabla de rentas
        for renta in rentas_filtradas:
            row = self.tbl_rentas.rowCount()
            self.tbl_rentas.insertRow(row)
            self.tbl_rentas.setItem(row, 0, QTableWidgetItem(str(renta.get("id"))))

            placa = QTableWidgetItem(renta.get("placa", ""))
            placa.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            self.tbl_rentas.setItem(row, 1, placa)

            self.tbl_rentas.setItem(row, 2, QTableWidgetItem(renta.get("nombre_cliente", "")))
            self.tbl_rentas.setItem(row, 3, QTableWidgetItem(renta.get("fecha_retorno", "")))

            try:
                fr = datetime.strptime(renta.get("fecha_retorno", "")[:10], "%Y-%m-%d").date()
                dias = (fr - hoy).days
                txt = f"{dias} días" if dias >= 0 else f"Atrasado {abs(dias)}d"
                it = QTableWidgetItem(txt)
                color = "red" if dias < 0 else ("orange" if dias == 0 else "green")
                it.setForeground(QBrush(QColor(color)))
                if dias <= 0:
                    it.setFont(QFont("Arial", 9, QFont.Weight.Bold))
                self.tbl_rentas.setItem(row, 4, it)
            except ValueError:
                self.tbl_rentas.setItem(row, 4, QTableWidgetItem("—"))

    def _abrir_cierre(self, row: int, _col: int):
        item = self.tbl_rentas.item(row, 0) # La columna 0 es el ID (oculto)
        if not item:
            return
        try:
            from views.cierre_renta_view import CierreRentaDialog
            dlg = CierreRentaDialog(self, int(item.text()))
            if dlg.exec():
                self.cargar_datos() # Refrescar todo tras cerrar la renta
        except Exception as e:
            self.mostrar_error(f"No se pudo abrir el cierre: {e}")