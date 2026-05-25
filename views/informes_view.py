from views.components import ModernMessageBox
"""
views/informes_view.py — Informes financieros y operativos (Acceso Restringido)

Muestra balance mensual cruzando Caja Menor, Taller y Pagos. Exporta a Excel.

Mejoras UI/UX:
  - Sin estilos inline — todo por QSS (cssClass)
  - Sin emojis en tabs/labels
  - Font bold corregido (QFont value-type)
  - Usa pd importado en vez de __import__("pandas")
  - Tabs heredan estilo global (sin override inline)
  - Celdas de moneda con alineacion y formato consistente
"""
import os

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QTabWidget, QPushButton, QWidget,
    QFileDialog, QAbstractItemView,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QBrush, QFont

from core.config import COLOR_EXITO, COLOR_PELIGRO, COLOR_ALERTA
from services.financial_service import FinancialService
from services.informe_service import InformeService
from views.base_widget import BaseWidget
from views.styles import btn_success, lbl_section, table_widget, view_background, tab_widget_pane_style, tab_bar_style

# ── Paleta coherente con el sistema Dinamo Pro ────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"

class InformesWidget(BaseWidget):
    """Panel de Informes Financieros Gerenciales."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.setStyleSheet(f"QWidget {{ background: {_BG}; }} QLabel {{ color: {_TEXT}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        from views.layouts.form_helpers import create_banner
        banner = create_banner("📊", "Informes Financieros Gerenciales", "Balance consolidado y Rentabilidad (ROI)", self.cargar_datos)
        main_layout.addWidget(banner)

        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(14)
        main_layout.addWidget(content, stretch=1)

        top = QHBoxLayout()
        top.addStretch()
        btn_excel = QPushButton("Exportar a Excel")
        btn_success(btn_excel)
        btn_excel.clicked.connect(self._exportar)
        top.addWidget(btn_excel)

        c_lay.addLayout(top)

        # ── Tabs ──
        self.tabs = QTabWidget()
        tab_widget_pane_style(self.tabs)
        tab_bar_style(self.tabs.tabBar())
        view_background(self)

        # --- TAB 1: Balance Consolidado ---
        tab_bal = QWidget()
        lay_bal = QVBoxLayout(tab_bal)

        lbl_info = QLabel(
            "Resumen de Utilidad Neta (Ingresos de Pagos vs Egresos Totales)"
        )
        lbl_section(lbl_info)
        lay_bal.addWidget(lbl_info)

        self.tbl_bal = QTableWidget()
        self.tbl_bal.setAlternatingRowColors(True)
        table_widget(self.tbl_bal)
        self.ajustar_tabla(self.tbl_bal, [
            "Mes (Ano-Mes)", "Ingresos (Rentas)", "Egresos (Taller)",
            "Gastos (Caja Menor)", "Utilidad Neta",
        ])
        self.tbl_bal.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay_bal.addWidget(self.tbl_bal)

        # --- TAB 2: ROI por Vehiculo ---
        tab_roi = QWidget()
        lay_roi = QVBoxLayout(tab_roi)

        lbl_roi = QLabel("Analisis de rentabilidad por vehiculo de la flota")
        lbl_section(lbl_roi)
        lay_roi.addWidget(lbl_roi)

        self.tbl_roi = QTableWidget()
        self.tbl_roi.setAlternatingRowColors(True)
        table_widget(self.tbl_roi)
        self.ajustar_tabla(self.tbl_roi, [
            "Placa", "Vehiculo", "Ingresos Totales",
            "Gastos Mtto.", "Costos Fijos Acum.", "Utilidad Total", "Punto Equilibrio",
        ])
        self.tbl_roi.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        lay_roi.addWidget(self.tbl_roi)

        self.tabs.addTab(tab_bal, "Balance Mensual Consolidado")
        self.tabs.addTab(tab_roi, "Rentabilidad por Vehiculo (ROI)")
        c_lay.addWidget(self.tabs)

        self._init_loading_overlay()
        QTimer.singleShot(0, self._deferred_load)

    # ── Carga de datos ─────────────────────────────────────────

    def cargar_datos(self):
        self._cargar_balance()
        self._cargar_roi()

    def _cargar_balance(self):
        self.tbl_bal.setRowCount(0)
        balance = self.ejecutar_seguro(InformeService.balance_mensual_real, session_id=self._session_id) or []
        for r in balance:
            row = self.tbl_bal.rowCount()
            self.tbl_bal.insertRow(row)

            it_mes = QTableWidgetItem(r["mes"])
            fnt = QFont(it_mes.font())
            fnt.setBold(True)
            it_mes.setFont(fnt)
            self.tbl_bal.setItem(row, 0, it_mes)

            self._celda_moneda(row, 1, r["ingresos"],   COLOR_EXITO,   self.tbl_bal)
            self._celda_moneda(row, 2, r["taller"],     COLOR_PELIGRO, self.tbl_bal)
            self._celda_moneda(row, 3, r["caja_menor"], COLOR_ALERTA,  self.tbl_bal)

            util = r["utilidad"]
            color = COLOR_EXITO if util >= 0 else COLOR_PELIGRO
            self._celda_moneda(row, 4, util, color, self.tbl_bal, bold=True, font_size=11)

    def _cargar_roi(self):
        self.tbl_roi.setRowCount(0)
        roi = self.ejecutar_seguro(FinancialService.roi_flota) or []
        for r in roi:
            row = self.tbl_roi.rowCount()
            self.tbl_roi.insertRow(row)
            self.tbl_roi.setItem(row, 0, QTableWidgetItem(r.get("placa", "")))
            self.tbl_roi.setItem(row, 1, QTableWidgetItem(r.get("vehiculo", "")))
            self._celda_moneda(row, 2, r.get("ingresos", 0),      "#333333", self.tbl_roi)
            self._celda_moneda(row, 3, r.get("mantenimiento", 0),  "#333333", self.tbl_roi)
            self._celda_moneda(row, 4, r.get("costos_fijos", 0),   "#333333", self.tbl_roi)

            util = r.get("utilidad", 0)
            color = COLOR_EXITO if util >= 0 else COLOR_PELIGRO
            self._celda_moneda(row, 5, util, color, self.tbl_roi, bold=True, font_size=9)

            eq = r.get("equilibrio", 0)
            txt = f"{eq:.1f} dias/mes" if eq > 0 else "N/A"
            it_e = QTableWidgetItem(txt)
            if eq > 20:
                it_e.setForeground(QBrush(QColor(COLOR_PELIGRO)))
            elif eq > 0:
                it_e.setForeground(QBrush(QColor("#1565c0")))
            self.tbl_roi.setItem(row, 6, it_e)

    def _celda_moneda(self, row, col, valor, color, tabla, bold=False, font_size=10):
        """Crea una celda de moneda con formato y color."""
        it = QTableWidgetItem(f"$ {valor:,.0f}")
        it.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        it.setForeground(QBrush(QColor(color)))
        if bold:
            fnt = QFont(it.font())
            fnt.setBold(True)
            if font_size != 10:
                fnt.setPointSize(font_size)
            it.setFont(fnt)
        tabla.setItem(row, col, it)

    # ── Exportar a Excel ───────────────────────────────────────

    def _exportar(self):
        try:
            import pandas as pd
        except ImportError:
            ModernMessageBox.warning(
                self, "Libreria faltante",
                "Para exportar instale pandas:\n\npip install pandas openpyxl",
            )
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar Informe Gerencial",
            "Informe_Financiero_Dinamo.xlsx",
            "Excel (*.xlsx)",
        )
        if not archivo:
            return

        try:
            balance = InformeService.balance_mensual_real(session_id=self._session_id)
            roi = FinancialService.roi_flota()

            df_bal = pd.DataFrame(balance).rename(columns={
                "mes": "Mes",
                "ingresos": "Ingresos (Rentas)",
                "taller": "Egresos (Taller)",
                "caja_menor": "Gastos (Caja Menor)",
                "utilidad": "Utilidad Neta",
            })
            df_roi = pd.DataFrame(roi).rename(columns={
                "placa": "Placa",
                "vehiculo": "Vehiculo",
                "ingresos": "Ingresos Totales",
                "mantenimiento": "Mantenimiento",
                "costos_fijos": "Costos Fijos Acum.",
                "utilidad": "Utilidad Total",
                "equilibrio": "Punto Equilibrio (Dias)",
            })

            with pd.ExcelWriter(archivo, engine="openpyxl") as writer:
                df_bal.to_excel(writer, sheet_name="Balance Consolidado", index=False)
                df_roi.to_excel(writer, sheet_name="Rentabilidad Flota", index=False)

            self.mostrar_exito(f"Informe exportado correctamente en:\n{archivo}")
            try:
                os.startfile(archivo)
            except Exception:
                pass
        except Exception as e:
            self.mostrar_error(f"No se pudo exportar:\n{e}")
