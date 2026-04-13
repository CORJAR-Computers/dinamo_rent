"""
informes_view.py — Informes financieros y operativos (Acceso Restringido)

Muestra balance mensual cruzando Caja Menor, Taller y Pagos. Exporta a Excel.
"""
import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidgetItem, QHeaderView,
    QLabel, QTabWidget, QPushButton, QWidget, QFileDialog, QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont

from services.financial_service import FinancialService
from services.services_extra import InformeService
from views.base_widget import BaseWidget

try:
    import pandas as pd
    _PANDAS = True
except ImportError:
    _PANDAS = False


class InformesWidget(BaseWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Header
        top = QHBoxLayout()
        lbl = QLabel("Informes Financieros Gerenciales")
        lbl.setStyleSheet("font-size:22px; font-weight:900; color:#1a237e;")

        btn_excel = QPushButton("📗 Exportar a Excel")
        btn_excel.setStyleSheet(
            "background-color:#2e7d32; color:white; font-weight:bold; padding:8px 15px; border-radius: 5px;"
        )
        btn_excel.clicked.connect(self._exportar)

        btn_act = QPushButton("🔄 Actualizar")
        btn_act.setProperty("cssClass", "primary")
        btn_act.setFixedSize(120, 35)
        btn_act.clicked.connect(self.cargar_datos)

        top.addWidget(lbl); top.addStretch()
        top.addWidget(btn_excel); top.addSpacing(10); top.addWidget(btn_act)
        layout.addLayout(top)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border:1px solid #ccc; background:white; border-radius: 5px; }
            QTabBar::tab { background:#e0e0e0; padding:10px 20px; font-weight:bold; font-size: 13px; }
            QTabBar::tab:selected { background:#004aad; color:white; }
        """)

        from PySide6.QtWidgets import QTableWidget

        # --- TAB 1: BALANCE CONSOLIDADO ---
        tab_bal = QWidget()
        lay_bal = QVBoxLayout(tab_bal)
        lay_bal.setContentsMargins(15, 15, 15, 15)

        lbl_info = QLabel("Resumen de Utilidad Neta (Ingresos de Pagos vs Egresos Totales)")
        lbl_info.setStyleSheet("color: #546e7a; font-weight: bold; margin-bottom: 10px;")
        lay_bal.addWidget(lbl_info)

        self.tbl_bal = QTableWidget()
        self.ajustar_tabla(self.tbl_bal, [
            "Mes (Año-Mes)", "💰 Ingresos (Rentas)", "🔧 Egresos (Taller)",
            "💸 Gastos (Caja Menor)", "📈 Utilidad Neta"
        ])
        self.tbl_bal.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_bal.setAlternatingRowColors(True)
        lay_bal.addWidget(self.tbl_bal)

        # --- TAB 2: ROI POR VEHÍCULO ---
        tab_roi = QWidget()
        lay_roi = QVBoxLayout(tab_roi)
        lay_roi.setContentsMargins(15, 15, 15, 15)
        self.tbl_roi = QTableWidget()
        self.ajustar_tabla(self.tbl_roi, [
            "Placa", "Vehículo", "Ingresos Totales",
            "Gastos Mtto.", "Costos Fijos Acum.", "Utilidad Total", "Punto Equilibrio"
        ])
        self.tbl_roi.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tbl_roi.setAlternatingRowColors(True)
        lay_roi.addWidget(self.tbl_roi)

        self.tabs.addTab(tab_bal, "📊 Balance Mensual Consolidado")
        self.tabs.addTab(tab_roi, "🚗 Rentabilidad por Vehículo (ROI)")
        layout.addWidget(self.tabs)

        self.cargar_datos()

    def cargar_datos(self):
        # 1. Cargar Balance Mensual (El nuevo motor financiero)
        self.tbl_bal.setRowCount(0)
        balance = self.ejecutar_seguro(InformeService.balance_mensual_real) or []
        for r in balance:
            row = self.tbl_bal.rowCount()
            self.tbl_bal.insertRow(row)

            it_mes = QTableWidgetItem(r["mes"])
            it_mes.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tbl_bal.setItem(row, 0, it_mes)

            self._celda_moneda(row, 1, r["ingresos"],   "#2e7d32", self.tbl_bal) # Verde
            self._celda_moneda(row, 2, r["taller"],     "#c62828", self.tbl_bal) # Rojo
            self._celda_moneda(row, 3, r["caja_menor"], "#ef6c00", self.tbl_bal) # Naranja

            util = r["utilidad"]
            it_u = QTableWidgetItem(f"$ {util:,.0f}")
            it_u.setFont(QFont("Arial", 11, QFont.Weight.Bold))
            it_u.setForeground(QBrush(QColor("#2e7d32" if util >= 0 else "#c62828")))
            self.tbl_bal.setItem(row, 4, it_u)

        # 2. Cargar ROI por Vehículo (Mantenemos la función original intacta)
        self.tbl_roi.setRowCount(0)
        roi = self.ejecutar_seguro(FinancialService.roi_flota) or []
        for r in roi:
            row = self.tbl_roi.rowCount()
            self.tbl_roi.insertRow(row)
            self.tbl_roi.setItem(row, 0, QTableWidgetItem(r.get("placa", "")))
            self.tbl_roi.setItem(row, 1, QTableWidgetItem(r.get("vehiculo", "")))
            self._celda_moneda(row, 2, r.get("ingresos", 0),     "black", self.tbl_roi)
            self._celda_moneda(row, 3, r.get("mantenimiento", 0),"black", self.tbl_roi)
            self._celda_moneda(row, 4, r.get("costos_fijos", 0), "black", self.tbl_roi)

            util = r.get("utilidad", 0)
            it_u = QTableWidgetItem(f"$ {util:,.0f}")
            it_u.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            it_u.setForeground(QBrush(QColor("green" if util >= 0 else "red")))
            self.tbl_roi.setItem(row, 5, it_u)

            eq  = r.get("equilibrio", 0)
            txt = f"{eq:.1f} días/mes" if eq > 0 else "N/A"
            it_e = QTableWidgetItem(txt)
            if eq > 20:
                it_e.setForeground(QBrush(QColor("red")))
            elif eq > 0:
                it_e.setForeground(QBrush(QColor("blue")))
            self.tbl_roi.setItem(row, 6, it_e)

    def _celda_moneda(self, row, col, valor, color, tabla):
        it = QTableWidgetItem(f"$ {valor:,.0f}")
        it.setForeground(QBrush(QColor(color)))
        tabla.setItem(row, col, it)

    def _exportar(self):
        if not _PANDAS:
            QMessageBox.warning(
                self, "Librería faltante",
                "Para exportar instale pandas:\n\npip install pandas openpyxl"
            )
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Informe Gerencial", "Informe_Financiero_Dinamo.xlsx", "Excel (*.xlsx)"
        )
        if not archivo:
            return

        try:
            # Traer los datos limpios para Excel
            balance = InformeService.balance_mensual_real()
            roi     = FinancialService.roi_flota()

            df_bal = (
                __import__("pandas").DataFrame(balance)
                .rename(columns={
                    "mes": "Mes",
                    "ingresos": "Ingresos (Rentas)",
                    "taller": "Egresos (Taller)",
                    "caja_menor": "Gastos (Caja Menor)",
                    "utilidad": "Utilidad Neta",
                })
            )
            df_roi = (
                __import__("pandas").DataFrame(roi)
                .rename(columns={
                    "placa": "Placa", "vehiculo": "Vehículo",
                    "ingresos": "Ingresos Totales", "mantenimiento": "Mantenimiento",
                    "costos_fijos": "Costos Fijos Acum.", "utilidad": "Utilidad Total",
                    "equilibrio": "Punto Equilibrio (Días)",
                })
            )

            # Exportar con múltiples pestañas
            with __import__("pandas").ExcelWriter(archivo, engine="openpyxl") as writer:
                df_bal.to_excel(writer, sheet_name="Balance Consolidado", index=False)
                df_roi.to_excel(writer, sheet_name="Rentabilidad Flota",  index=False)

            self.mostrar_exito(f"Informe exportado correctamente en:\n{archivo}")
            try:
                os.startfile(archivo)
            except Exception:
                pass
        except Exception as e:
            self.mostrar_error(f"No se pudo exportar:\n{e}")