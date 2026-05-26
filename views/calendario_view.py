from views.components import ModernMessageBox

"""
views/calendario_view.py — Calendario de Disponibilidad

Colores: Azul claro=Disponible, Verde=Rentado, Amarillo=Reservado
Herencia: BaseWidget. Estilos via QSS class-based.
"""
import calendar
from datetime import date, datetime

from PySide6.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QAbstractItemView,
    QWidget,
    QFrame,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont

from core.exceptions import DinamoBaseError
from services.auto_service import AutoService
from services.renta_service import RentaService
from services.dashboard_service import DashboardService
from views.base_widget import BaseWidget

_NAV = "#1a3558"
_BLUE = "#2563eb"
_BG = "#f1f5f9"
_SURF = "#ffffff"
_BORD = "#cbd5e1"
_TEXT = "#1e293b"
_MUTED = "#64748b"


class CalendarioWidget(BaseWidget):
    """Panel de Calendario de Disponibilidad de Flota — Dinamo Pro."""

    _MESES = [
        "Enero",
        "Febrero",
        "Marzo",
        "Abril",
        "Mayo",
        "Junio",
        "Julio",
        "Agosto",
        "Septiembre",
        "Octubre",
        "Noviembre",
        "Diciembre",
    ]

    def __init__(self, session_id: str = None):
        super().__init__(session_id=session_id)
        self.fecha_actual = date.today()
        self.mes_vista = self.fecha_actual.month
        self.anio_vista = self.fecha_actual.year
        self._setup_ui()
        self._init_loading_overlay("Cargando calendario...")
        QTimer.singleShot(0, lambda: self._deferred_call(self.cargar_calendario))

    def _setup_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Banner superior con gradiente ────────────────────────────────
        banner = QWidget()
        banner.setFixedHeight(64)
        banner.setProperty("class", "banner")
        b_lay = QHBoxLayout(banner)
        b_lay.setContentsMargins(22, 0, 22, 0)
        b_lay.setSpacing(14)

        ico = QLabel("📅")
        ico.setFixedSize(40, 40)
        ico.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ico.setProperty("class", "banner-icon")
        b_lay.addWidget(ico)

        t_col = QVBoxLayout()
        t_col.setSpacing(1)
        t_col.addStretch()
        lbl_t = QLabel("Calendario de Disponibilidad")
        lbl_t.setProperty("class", "banner-title")
        lbl_s = QLabel("Vista mensual de la flota")
        lbl_s.setProperty("class", "banner-subtitle")
        t_col.addWidget(lbl_t)
        t_col.addWidget(lbl_s)
        t_col.addStretch()
        b_lay.addLayout(t_col)
        b_lay.addStretch()
        root.addWidget(banner)

        # ── Área de contenido ────────────────────────────────────────────
        content = QWidget()

        c_lay = QVBoxLayout(content)
        c_lay.setContentsMargins(20, 16, 20, 16)
        c_lay.setSpacing(12)
        root.addWidget(content, stretch=1)

        # ── Barra de navegación de mes ───────────────────────────────────
        nav_card = QFrame()
        nav_card.setProperty("class", "card")
        nav_lay = QHBoxLayout(nav_card)
        nav_lay.setContentsMargins(14, 10, 14, 10)
        nav_lay.setSpacing(12)

        btn_prev = QPushButton("◀  Anterior")
        btn_next = QPushButton("Siguiente  ▶")
        btn_act = QPushButton("↻  Actualizar")
        for b in (btn_prev, btn_next, btn_act):
            b.setProperty("class", "ghost")
        btn_prev.clicked.connect(self.mes_anterior)
        btn_next.clicked.connect(self.mes_siguiente)
        btn_act.clicked.connect(self.cargar_calendario)

        # Etiqueta del mes — centrada y destacada
        self.lbl_mes = QLabel("MES AÑO")
        self.lbl_mes.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mes.setStyleSheet(
            "QLabel { font-size: 13pt; font-weight: 700; letter-spacing: 0.3px; }"
        )

        nav_lay.addWidget(btn_prev)
        nav_lay.addStretch()
        nav_lay.addWidget(self.lbl_mes)
        nav_lay.addStretch()
        nav_lay.addWidget(btn_next)
        nav_lay.addWidget(btn_act)
        c_lay.addWidget(nav_card)

        # ── Leyenda de colores ───────────────────────────────────────────
        ley_lay = QHBoxLayout()
        ley_lay.setSpacing(10)

        for texto, emoji, legend_class in (
            ("Disponible", "🔵", "legend-available"),
            ("Rentado", "🟢", "legend-rented"),
            ("Reservado", "🟡", "legend-reserved"),
            ("En Taller", "🟠", "legend-warning"),
        ):
            pill = QLabel(f" {emoji}  {texto} ")
            pill.setProperty("class", legend_class)
            ley_lay.addWidget(pill)

        # Leyenda de fin de semana
        pill_fe = QLabel(" 🗓  Fin de semana (negrita) ")
        pill_fe.setProperty("class", "badge")
        ley_lay.addWidget(pill_fe)
        ley_lay.addStretch()
        c_lay.addLayout(ley_lay)

        # ── Tabla del Calendario ─────────────────────────────────────────
        self.tabla = QTableWidget()
        self.tabla.verticalHeader().setVisible(False)
        self.tabla.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.setAlternatingRowColors(False)
        self.tabla.horizontalHeader().setMinimumSectionSize(30)
        self.tabla.setShowGrid(True)
        self.tabla.verticalHeader().setDefaultSectionSize(42)
        c_lay.addWidget(self.tabla)

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
        self.lbl_mes.setText(f"{self._MESES[self.mes_vista - 1]}  {self.anio_vista}")

        dias_en_mes = calendar.monthrange(self.anio_vista, self.mes_vista)[1]
        self.tabla.setColumnCount(dias_en_mes + 1)
        headers = ["VEHÍCULO"] + [str(d) for d in range(1, dias_en_mes + 1)]
        self.tabla.setHorizontalHeaderLabels(headers)
        self.tabla.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents
        )
        for c in range(1, dias_en_mes + 1):
            self.tabla.setColumnWidth(c, 44)

        autos = self._obtener_autos()
        rentas = self._obtener_rentas_calendario()
        if autos is None:
            return

        self.tabla.setRowCount(0)
        color_disp = QColor("#dbeafe")  # Azul claro
        color_rent = QColor("#dcfce7")  # Verde claro
        color_resv = QColor("#fef08a")  # Amarillo pastel
        color_tall = QColor("#ffedd5")  # Naranja claro

        # Color de resaltado para el día actual
        hoy = date.today()

        for i, auto in enumerate(autos):
            self.tabla.insertRow(i)
            placa = auto.get("placa", "")
            modelo = auto.get("modelo", "")
            marca = auto.get("marca", "")

            item_auto = QTableWidgetItem(f"{placa}\n{marca} {modelo}")
            item_auto.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            fnt = QFont("Segoe UI", 9)
            fnt.setBold(True)
            item_auto.setFont(fnt)
            item_auto.setForeground(QColor(_NAV))
            self.tabla.setItem(i, 0, item_auto)

            eventos_auto = [r for r in rentas if r.get("placa") == placa]

            for dia in range(1, dias_en_mes + 1):
                fecha_dia = date(self.anio_vista, self.mes_vista, dia)
                item = QTableWidgetItem()
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

                estado_dia = self._estado_dia(fecha_dia, eventos_auto, auto)
                if estado_dia == "rentado":
                    item.setBackground(color_rent)
                elif estado_dia == "reservado":
                    item.setBackground(color_resv)
                elif estado_dia == "taller":
                    item.setBackground(color_tall)
                else:
                    item.setBackground(color_disp)

                # Marcar el día actual con un punto sobre el color de estado
                if fecha_dia == hoy:
                    item.setText("●")
                    item.setForeground(QColor("#0f172a"))  # Punto oscuro para buen contraste

                dia_semana = calendar.weekday(self.anio_vista, self.mes_vista, dia)
                if dia_semana >= 5:
                    fnt_we = QFont(item.font())
                    fnt_we.setBold(True)
                    item.setFont(fnt_we)

                self.tabla.setItem(i, dia, item)

            self.tabla.setRowHeight(i, 42)

    def _estado_dia(self, fecha_dia: date, eventos: list[dict], auto: dict) -> str:
        for ev in eventos:
            try:
                f_ini_str = str(ev.get("fecha_recogida", ""))[:10]
                f_fin_str = str(ev.get("fecha_retorno", ""))[:10]
                if not f_ini_str or not f_fin_str:
                    continue
                f_ini = datetime.strptime(f_ini_str, "%Y-%m-%d").date()
                f_fin = datetime.strptime(f_fin_str, "%Y-%m-%d").date()

                if f_ini <= fecha_dia <= f_fin:
                    tipo = ev.get("tipo", "").lower()
                    if "renta" in tipo:
                        return "rentado"
                    elif "reserva" in tipo:
                        return "reservado"
                    else:
                        return "rentado"
            except ValueError:
                continue

        # Si no hay evento, verificar si el auto está en Mantenimiento.
        # Asumimos que bloquea desde hoy hacia el futuro.
        if auto.get("estado") == "Mantenimiento":
            if fecha_dia >= date.today():
                return "taller"

        return "disponible"

    def _obtener_autos(self) -> list[dict] | None:
        try:
            return AutoService.listar()
        except DinamoBaseError as e:
            ModernMessageBox.warning(
                self, "Error", f"No se pudo obtener la flota:\n{e.mensaje_usuario}"
            )
            return None
        except Exception as e:
            ModernMessageBox.warning(self, "Error", f"No se pudo obtener la flota:\n{e}")
            return None

    def _obtener_rentas_calendario(self) -> list[dict]:
        try:
            resultado = RentaService.obtener_para_calendario(self.mes_vista, self.anio_vista)
            return resultado if resultado else []
        except AttributeError:
            pass
        except DinamoBaseError:
            pass
        except Exception:
            pass

        try:
            resultado = DashboardService.obtener_activas()
            return resultado if resultado else []
        except AttributeError:
            pass
        except Exception:
            pass

        try:
            resultado = RentaService.obtener_activas()
            return resultado if resultado else []
        except AttributeError:
            pass
        except Exception:
            pass

        return []
