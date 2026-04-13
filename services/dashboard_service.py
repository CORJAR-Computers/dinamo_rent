"""
dashboard_service.py — Servicio de Dashboard y KPIs

NUEVO en F1B: Extraído de RentaService.kpi_globales() para separar responsabilidades.
Proporciona métricas agregadas para el panel principal del sistema.
"""
from typing import Dict
from datetime import date

from core.logger import get_logger
from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
    InformeRepositorySA,
)

log = get_logger(__name__)


class DashboardService:

    @staticmethod
    def kpi_globales() -> Dict:
        """
        Retorna los KPIs principales para el dashboard.

        Incluye:
          - rentas_activas: Cantidad de rentas en estado Activo
          - autos_disponibles: Cantidad de autos disponibles
          - autos_rentados: Cantidad de autos rentados
          - autos_mantenimiento: Cantidad de autos en mantenimiento
          - ocupacion_flota: Porcentaje de la flota rentada
          - ingresos_mes: Total de ingresos del mes actual
          - pagos_pendientes: Total de saldo pendiente en rentas activas
        """
        # Obtener datos de repositorios existentes
        autos = AutoRepositorySA.obtener_todos()
        rentas_activas = RentaRepositorySA.obtener_activas()

        # Contar estados de autos
        disponibles = sum(1 for a in autos if a.get('estado') == 'Disponible')
        rentados = sum(1 for a in autos if a.get('estado') == 'Rentado')
        en_mantenimiento = sum(1 for a in autos if a.get('estado') == 'Mantenimiento')
        total_flota = len(autos)

        # Ocupación de flota
        ocupacion = 0.0
        if total_flota > 0:
            # Excluir vendidos y baja del cálculo
            activos = sum(1 for a in autos if a.get('estado') not in ['Vendido', 'Baja'])
            ocupacion = round((rentados / activos) * 100, 1) if activos > 0 else 0.0

        # Ingresos del mes actual
        mes_actual = date.today().strftime("%Y-%m")
        balance = InformeRepositorySA.obtener_balance_consolidado()
        ingresos_mes = 0.0
        for b in balance:
            if str(b.get('mes', '')) == mes_actual:
                ingresos_mes = float(b.get('ingresos', 0) or 0)
                break

        # Saldo pendiente total
        pagos_pendientes = sum(
            float(r.get('saldo_pendiente', 0) or 0)
            for r in rentas_activas
        )

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
