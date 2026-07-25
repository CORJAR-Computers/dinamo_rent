"""Dashboard KPIs and data service."""

from typing import Dict, List
from datetime import date

from core.logger import get_logger
from core.schemas import (
    KpiGlobalesResponse,
    ResumenFinancieroResponse,
    AlertasResponse,
)
from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
    AlertaRepositorySA,
)

log = get_logger(__name__)


class DashboardService:
    @staticmethod
    def kpi_y_financiero() -> Dict:
        """Obtiene KPIs de flota + resumen financiero del mes en una sola pasada."""
        from sqlalchemy import text
        from core.database_sa import get_session
        from core.config import DB_ENGINE

        # ── Flota y rentas ────────────────────────────────────────────
        autos = AutoRepositorySA.obtener_todos()
        rentas_activas = RentaRepositorySA.obtener_activas()

        disponibles = sum(1 for a in autos if a.get("estado") == "Disponible")
        rentados = sum(1 for a in autos if a.get("estado") == "Rentado")
        en_mantenimiento = sum(1 for a in autos if a.get("estado") == "Mantenimiento")
        total_flota = len(autos)
        activos_flota = sum(1 for a in autos if a.get("estado") not in ["Vendido", "Baja"])
        ocupacion = round((rentados / activos_flota) * 100, 1) if activos_flota > 0 else 0.0

        # ── Financiero del mes actual: una sola query con filtro WHERE ──
        mes_actual = date.today().strftime("%Y-%m")

        if DB_ENGINE == "mysql":
            date_expr_fecha = "DATE_FORMAT(fecha, '%Y-%m')"
            date_expr_pieza = "DATE_FORMAT(pieza_varias_fecha, '%Y-%m')"
        elif DB_ENGINE == "firebird":
            date_expr_fecha = "EXTRACT(YEAR FROM fecha) || '-' || LPAD(EXTRACT(MONTH FROM fecha), 2, '0')"
            date_expr_pieza = "EXTRACT(YEAR FROM pieza_varias_fecha) || '-' || LPAD(EXTRACT(MONTH FROM pieza_varias_fecha), 2, '0')"
        else:
            date_expr_fecha = "strftime('%Y-%m', fecha)"
            date_expr_pieza = "strftime('%Y-%m', pieza_varias_fecha)"

        sql_mes = text(f"""
            SELECT
                COALESCE(SUM(ingreso), 0) as ingresos,
                COALESCE(SUM(taller), 0) as egresos_taller,
                COALESCE(SUM(caja),   0) as gastos_caja
            FROM (
                SELECT fecha, monto        as ingreso, 0                    as taller, 0     as caja
                FROM pagos
                WHERE {date_expr_fecha} = :mes

                UNION ALL

                SELECT pieza_varias_fecha as fecha,
                       0 as ingreso, total_mantenimiento as taller, 0 as caja
                FROM mantenimiento_vehiculos
                WHERE {date_expr_pieza} = :mes

                UNION ALL

                SELECT fecha, 0 as ingreso, 0 as taller, monto as caja
                FROM gastos
                WHERE {date_expr_fecha} = :mes
            ) t
            WHERE fecha IS NOT NULL
        """)

        with get_session() as session:
            row = session.execute(sql_mes, {"mes": mes_actual}).fetchone()

        ingresos = float(row[0] or 0) if row else 0.0
        egresos_taller = float(row[1] or 0) if row else 0.0
        gastos_caja = float(row[2] or 0) if row else 0.0

        return {
            # KPIs de flota
            "rentas_activas": len(rentas_activas),
            "autos_disponibles": disponibles,
            "autos_rentados": rentados,
            "autos_mantenimiento": en_mantenimiento,
            "total_flota": total_flota,
            "ocupacion_flota": ocupacion,
            # Financiero mes actual
            "ingresos_mes": ingresos,
            "egresos_taller_mes": egresos_taller,
            "gastos_caja_mes": gastos_caja,
            "utilidad_mes": ingresos - egresos_taller - gastos_caja,
        }

    @staticmethod
    def kpi_globales() -> KpiGlobalesResponse:
        """Delegado a kpi_y_financiero para compatibilidad con código existente."""
        return DashboardService.kpi_y_financiero()

    @staticmethod
    def obtener_activas() -> List[Dict]:
        return RentaRepositorySA.obtener_activas()

    @staticmethod
    def obtener_activas_filtradas(filtro: str) -> List[Dict]:
        return RentaRepositorySA.obtener_activas_filtradas(filtro)

    @staticmethod
    def obtener_alertas() -> AlertasResponse:
        from services.alerta_service import AlertaService
        return AlertaService.obtener_todas_las_alertas()

    @staticmethod
    def obtener_rentas_por_vencer() -> List[Dict]:
        return AlertaRepositorySA.obtener_rentas_por_vencer()

    @staticmethod
    def obtener_documentos_por_vencer() -> List[Dict]:
        return AlertaRepositorySA.obtener_documentos_por_vencer()

    @staticmethod
    def obtener_alertas_flota() -> List[Dict]:
        return AutoRepositorySA.obtener_alertas_flota()

    @staticmethod
    def obtener_resumen_financiero() -> ResumenFinancieroResponse:
        """Compatibilidad: extrae solo el resumen financiero del resultado unificado."""
        data = DashboardService.kpi_y_financiero()
        return {
            "mes": date.today().strftime("%Y-%m"),
            "ingresos_mes": data["ingresos_mes"],
            "egresos_taller_mes": data["egresos_taller_mes"],
            "gastos_caja_mes": data["gastos_caja_mes"],
            "utilidad_mes": data["utilidad_mes"],
        }
