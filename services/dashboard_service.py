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
    InformeRepositorySA,
    AlertaRepositorySA,
)

log = get_logger(__name__)


class DashboardService:
    @staticmethod
    def kpi_globales() -> KpiGlobalesResponse:
        autos = AutoRepositorySA.obtener_todos()
        rentas_activas = RentaRepositorySA.obtener_activas()

        disponibles = sum(1 for a in autos if a.get("estado") == "Disponible")
        rentados = sum(1 for a in autos if a.get("estado") == "Rentado")
        en_mantenimiento = sum(1 for a in autos if a.get("estado") == "Mantenimiento")
        total_flota = len(autos)

        ocupacion = 0.0
        if total_flota > 0:
            activos = sum(1 for a in autos if a.get("estado") not in ["Vendido", "Baja"])
            ocupacion = round((rentados / activos) * 100, 1) if activos > 0 else 0.0

        mes_actual = date.today().strftime("%Y-%m")
        balance = InformeRepositorySA.obtener_balance_consolidado()
        ingresos_mes = 0.0
        for b in balance:
            if str(b.get("mes", "")) == mes_actual:
                ingresos_mes = float(b.get("ingresos", 0) or 0)
                break

        pagos_pendientes = sum(float(r.get("saldo_pendiente", 0) or 0) for r in rentas_activas)

        return {
            "rentas_activas": len(rentas_activas),
            "autos_disponibles": disponibles,
            "autos_rentados": rentados,
            "autos_mantenimiento": en_mantenimiento,
            "total_flota": total_flota,
            "ocupacion_flota": ocupacion,
            "ingresos_mes": ingresos_mes,
            "pagos_pendientes": pagos_pendientes,
        }

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
        mes_actual = date.today().strftime("%Y-%m")
        balance = InformeRepositorySA.obtener_balance_consolidado()

        for b in balance:
            if str(b.get("mes", "")) == mes_actual:
                ingresos = float(b.get("ingresos", 0) or 0)
                taller = float(b.get("egresos_taller", 0) or 0)
                caja = float(b.get("gastos_caja", 0) or 0)
                return {
                    "mes": mes_actual,
                    "ingresos_mes": ingresos,
                    "egresos_taller_mes": taller,
                    "gastos_caja_mes": caja,
                    "utilidad_mes": ingresos - taller - caja,
                }

        return {
            "mes": mes_actual,
            "ingresos_mes": 0.0,
            "egresos_taller_mes": 0.0,
            "gastos_caja_mes": 0.0,
            "utilidad_mes": 0.0,
        }
