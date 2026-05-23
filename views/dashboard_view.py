"""
dashboard_view.py — Panel principal / Dashboard (Tema: Dinamo Pro)
"""
from datetime import datetime

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QTableWidgetItem, QComboBox, QTableWidget, QWidget,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QBrush, QFont

from services.dashboard_service import DashboardService
from services.auto_service import AutoService
from views.base_widget import BaseWidget
import views.styles as styles
from core.config import (
    COLOR_EXITO, COLOR_PRIMARIO, COLOR_ALERTA, COLOR_PELIGRO
)

# ── Paleta coherente con clientes_view ────────────────────────────────
_NAV   = "#1a3558"
_BLUE  = "#2563eb"
_BG    = "#f1f5f9"
_SURF  = "#ffffff"
_BORD  = "#cbd5e1"
_TEXT  = "#1e293b"
_MUTED = "#64748b"

_DASH_STYLE = f"""
QWidget {{
    font-family: 'Segoe UI', sans-serif;
}}
QFrame[dashcard="true"] {{
    background: {_SURF};
    border: 1px solid {_BORD};
    border-radius: 10px;
}}
QLabel {{
    color: {_TEXT};
}}
QComboBox {{
    border: 1px solid {_BORD};
    border-radius: 6px;
    padding: 5px 10px;
    background: {_SURF};
    color: {_TEXT};
    font-size: 9pt;
    min-height: 28px;
}}
QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}
QComboBox:focus {{
    border-color: {_BLUE};
}}
"""


class _KpiCard(QFrame):
    """Tarjeta KPI con banda de gradiente superior y valor prominente."""

    def __init__(self, titulo: str, icono: str, color: str, color_end: str = ""):
        super().__init__()
        self.setProperty("dashcard", "true")
        color_end = color_end or color
        self.setMinimumHeight(110)
        self.setMaximumHeight(130)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Banda superior con gradiente de color ──
        banner = QWidget()
        banner.setFixedHeight(6)
        banner.setStyleSheet(f"""
            background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                stop:0 {color}, stop:1 {color_end});
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
        """)
        root.addWidget(banner)

        # ── Cuerpo del card ──
        body = QWidget()
        body.setStyleSheet("QWidget { background: transparent; }")
        body_lay = QHBoxLayout(body)
        body_lay.setContentsMargins(18, 12, 18, 14)
        body_lay.setSpacing(12)

        # Columna izquierda: texto
        left = QVBoxLayout()
        left.setSpacing(4)

        lbl_titulo = QLabel(titulo.upper())
        lbl_titulo.setStyleSheet(
            f"QLabel {{ font-size:8.5pt; font-weight:700; color:{_MUTED}; letter-spacing:0.8px; }}"
        )

        self.lbl_valor = QLabel("—")
        self.lbl_valor.setStyleSheet(
            f"QLabel {{ color:{color}; font-size:30pt; font-weight:700; letter-spacing:-1px; }}"
        )

        left.addWidget(lbl_titulo)
        left.addWidget(self.lbl_valor)
        left.addStretch()
        body_lay.addLayout(left, stretch=1)

        # Icono decorativo derecho
        lbl_ico = QLabel(icono)
        lbl_ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ico.setFixedSize(44, 44)
        lbl_ico.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 {color}22, stop:1 {color}44);
                border-radius: 22px;
                font-size: 20px;
            }}
        """)
        body_lay.addWidget(lbl_ico)

        root.addWidget(body)

    def set_value(self, v: str):
        self.lbl_valor.setText(v)


def _section_header(texto: str, icono: str = "") -> QWidget:
    """Encabezado de sección con línea de acento izquierda y gradiente."""
    w = QWidget()
    w.setStyleSheet("QWidget { background: transparent; }")
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 8)
    lay.setSpacing(8)

    # Barra de acento
    bar = QFrame()
    bar.setFixedWidth(4)
    bar.setFixedHeight(20)
    bar.setStyleSheet(f"""
        background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
            stop:0 {_BLUE}, stop:1 {_NAV});
        border-radius: 2px;
    """)
    lay.addWidget(bar)

    if icono:
        lbl_i = QLabel(icono)
        lbl_i.setStyleSheet(f"QLabel {{ font-size:14px; color:{_BLUE}; background:transparent; }}")
        lay.addWidget(lbl_i)

    lbl = QLabel(texto)
    lbl.setStyleSheet(
        f"QLabel {{ font-size:11pt; font-weight:700; color:{_NAV}; background:transparent; letter-spacing:0.2px; }}"
    )
    lay.addWidget(lbl)
    lay.addStretch()
    return w


def _apply_table_style(tbl: QTableWidget):
    """Aplica estilo refinado coherente con la paleta Dinamo Pro."""
    styles.table_widget(tbl)
    tbl.setStyleSheet(tbl.styleSheet() + f"""
        QTableWidget {{
            background: {_SURF};
            border: 1px solid {_BORD};
            border-radius: 6px;
            gridline-color: #e2e8f0;
        }}
        QHeaderView::section {{
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                stop:0 {_NAV}, stop:1 #1e3f6e);
            color: #ffffff;
            font-size: 9pt;
            font-weight: 700;
            padding: 7px 10px;
            border: none;
            letter-spacing: 0.3px;
        }}
        QTableWidget::item {{
            padding: 5px 8px;
        }}
        QTableWidget::item:alternate {{
            background: #f8fafc;
        }}
    """)


class DashboardWidget(BaseWidget):
    """Panel general con KPIs, alertas y rentas — Dinamo Pro."""

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self._todas_las_rentas = []
        self.setStyleSheet(_DASH_STYLE)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        self.setLayout(main_layout)

        self._construir_ui()
        self.cargar_datos()

    def _construir_ui(self):
        # ── Banner superior ──────────────────────────────────────────────
        from views.layouts.form_helpers import create_banner
        banner = create_banner("📊", "Tablero de Operaciones", "Resumen en tiempo real de la flota", self.cargar_datos)
        self.layout().addWidget(banner)

        # ── Área de contenido ────────────────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"QWidget {{ background: {_BG}; }}")
        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(22, 18, 22, 18)
        c_lay.setSpacing(16)
        self.layout().addWidget(content, stretch=1)

        # ── KPIs ─────────────────────────────────────────────────────────
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(14)
        self.card_disp    = _KpiCard("Disponibles",     "🟢", COLOR_EXITO,   "#22c55e")
        self.card_activas = _KpiCard("Rentas Activas",  "🚗", COLOR_PRIMARIO, _BLUE)
        self.card_taller  = _KpiCard("En Taller",       "🔧", COLOR_ALERTA,  "#f59e0b")
        self.card_alertas = _KpiCard("Alertas Críticas","⚠️", COLOR_PELIGRO, "#ef4444")
        for c in (self.card_disp, self.card_activas, self.card_taller, self.card_alertas):
            kpi_row.addWidget(c)
        c_lay.addLayout(kpi_row)

        # ── Sección media (Alertas + Rentas) ─────────────────────────────
        mid = QHBoxLayout()
        mid.setSpacing(14)

        # -- Panel Alertas --
        fr_al = QFrame()
        fr_al.setProperty("dashcard", "true")
        lay_al = QVBoxLayout(fr_al)
        lay_al.setContentsMargins(18, 16, 18, 16)
        lay_al.setSpacing(10)
        lay_al.addWidget(_section_header("Alertas de Flota y Vencimientos", "🔔"))

        self.tbl_alertas = QTableWidget()
        self.ajustar_tabla(self.tbl_alertas, ["Placa", "Alerta", "Detalle", "Estado"])
        _apply_table_style(self.tbl_alertas)
        lay_al.addWidget(self.tbl_alertas)

        # -- Panel Rentas --
        fr_r = QFrame()
        fr_r.setProperty("dashcard", "true")
        lay_r = QVBoxLayout(fr_r)
        lay_r.setContentsMargins(18, 16, 18, 16)
        lay_r.setSpacing(10)

        hdr_r = QHBoxLayout()
        hdr_r.setSpacing(10)
        hdr_r.addWidget(_section_header("Rentas Activas", "📋"))
        hdr_r.addStretch()

        self.cmb_filtro = QComboBox()
        self.cmb_filtro.addItems([
            "Todas las Activas", "Vencen Hoy",
            "Retrasadas (Vencidas)", "Entregas de Mañana",
        ])
        self.cmb_filtro.currentIndexChanged.connect(self.filtrar_tabla)
        hdr_r.addWidget(self.cmb_filtro)
        lay_r.addLayout(hdr_r)

        self.tbl_rentas = QTableWidget()
        self.ajustar_tabla(self.tbl_rentas, ["ID", "Placa", "Cliente", "Retorno", "Días"])
        _apply_table_style(self.tbl_rentas)
        self.tbl_rentas.setColumnHidden(0, True)
        self.tbl_rentas.cellDoubleClicked.connect(self._abrir_cierre)
        lay_r.addWidget(self.tbl_rentas)

        mid.addWidget(fr_al, stretch=2)
        mid.addWidget(fr_r,  stretch=3)
        c_lay.addLayout(mid, stretch=1)

    def cargar_datos(self):
        # Obtener KPIs del dashboard
        kpis = self.ejecutar_seguro(DashboardService.kpi_globales) or {}

        # Obtener alertas
        alertas = self.ejecutar_seguro(AutoService.obtener_alertas) or []

        # Actualizar tarjetas KPI
        self.card_disp.set_value(str(kpis.get("autos_disponibles", 0)))
        self.card_activas.set_value(str(kpis.get("rentas_activas", 0)))
        self.card_taller.set_value(str(kpis.get("autos_mantenimiento", 0)))
        self.card_alertas.set_value(str(len(alertas)))

        self.tbl_alertas.setRowCount(0)
        for a in alertas:
            r = self.tbl_alertas.rowCount()
            self.tbl_alertas.insertRow(r)
            self.tbl_alertas.setItem(r, 0, QTableWidgetItem(a.get("placa", "")))
            self.tbl_alertas.setItem(r, 1, QTableWidgetItem(a.get("tipo", "")))
            self.tbl_alertas.setItem(r, 2, QTableWidgetItem(a.get("detalle", "")))

            est = a.get("estado", "")
            it = QTableWidgetItem(est)
            it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            critico = "VENCIDO" in est or "CRÍTICO" in est
            it.setForeground(QBrush(QColor(COLOR_PELIGRO if critico else COLOR_ALERTA)))
            self.tbl_alertas.setItem(r, 3, it)

        self.filtrar_tabla()

    def filtrar_tabla(self):
        self.tbl_rentas.setRowCount(0)
        filtro = self.cmb_filtro.currentText()
        hoy = datetime.now().date()

        rentas_filtradas = self.ejecutar_seguro(DashboardService.obtener_activas_filtradas, filtro) or []

        for renta in rentas_filtradas:
            row = self.tbl_rentas.rowCount()
            self.tbl_rentas.insertRow(row)
            self.tbl_rentas.setItem(row, 0, QTableWidgetItem(str(renta.get("id"))))

            placa = QTableWidgetItem(renta.get("placa", ""))
            placa.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.tbl_rentas.setItem(row, 1, placa)

            self.tbl_rentas.setItem(row, 2, QTableWidgetItem(renta.get("nombre_cliente", "")))
            fecha_ret = renta.get("fecha_retorno")
            self.tbl_rentas.setItem(row, 3, QTableWidgetItem(fecha_ret.strftime("%Y-%m-%d") if fecha_ret else ""))

            try:
                if isinstance(fecha_ret, str):
                    fr = datetime.strptime(fecha_ret[:10], "%Y-%m-%d").date()
                else:
                    fr = fecha_ret
                dias = (fr - hoy).days if fr else 0
                txt = f"{dias} días" if dias > 0 else ("Hoy" if dias == 0 else f"Atrasado {abs(dias)}d")
                it = QTableWidgetItem(txt)
                color = COLOR_PELIGRO if dias < 0 else (COLOR_ALERTA if dias == 0 else COLOR_EXITO)
                it.setForeground(QBrush(QColor(color)))
                if dias <= 0: it.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
                self.tbl_rentas.setItem(row, 4, it)
            except (ValueError, TypeError):
                self.tbl_rentas.setItem(row, 4, QTableWidgetItem("—"))

    def _abrir_cierre(self, row: int, _col: int):
        item = self.tbl_rentas.item(row, 0)
        if not item: return
        try:
            from views.cierre_renta_view import CierreRentaDialog
            dlg = CierreRentaDialog(self, int(item.text()))
            if dlg.exec(): self.cargar_datos()
        except Exception as e:
            self.mostrar_error(f"No se pudo abrir el cierre: {e}")
