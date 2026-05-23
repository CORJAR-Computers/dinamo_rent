"""
informe_repository_sa.py — Repositorio de Informes Gerenciales

F1C: Extraído de repositories_sa.py. Sin cambios funcionales.
Incluye los métodos F1B para ROI de Flota.
"""
from typing import List, Dict

from sqlalchemy import func, text

from core.database_sa import get_session
from core.models import MantenimientoVehiculo, Gasto, Renta
from core.logger import get_logger

log = get_logger(__name__)


class InformeRepositorySA:

    @staticmethod
    def obtener_balance_consolidado() -> List[Dict]:
        from core.config import DB_ENGINE
        with get_session() as session:
            date_func = "DATE_FORMAT(fecha, '%%Y-%%m')" if DB_ENGINE == "mysql" else "strftime('%%Y-%%m', fecha)"
            sql = text(f"""
                SELECT
                    {date_func} as mes,
                    SUM(ingreso) as ingresos,
                    SUM(taller) as egresos_taller,
                    SUM(caja) as gastos_caja
                FROM (
                    SELECT fecha, monto as ingreso, 0 as taller, 0 as caja
                    FROM pagos

                    UNION ALL

                    SELECT pieza_varias_fecha as fecha, 0 as ingreso, total_mantenimiento as taller, 0 as caja
                    FROM mantenimiento_vehiculos

                    UNION ALL

                    SELECT fecha, 0 as ingreso, 0 as taller, monto as caja
                    FROM gastos
                ) t
                WHERE fecha IS NOT NULL
                GROUP BY mes
                ORDER BY mes DESC
            """)

            result = session.execute(sql)
            return [dict(row._mapping) for row in result]

    # ── F1B: Métodos para ROI de Flota ─────────────────────────────────────

    @staticmethod
    def obtener_ingresos_por_vehiculo() -> Dict[str, float]:
        """
        Retorna un diccionario {placa: total_ingresos} con los ingresos
        de todas las rentas finalizadas agrupados por vehículo.
        """
        with get_session() as session:
            resultados = session.query(
                Renta.placa,
                func.coalesce(func.sum(Renta.total), 0).label('total_ingresos')
            ).filter(
                Renta.estado == 'Finalizado',
                Renta.placa.isnot(None),
            ).group_by(Renta.placa).all()

            return {str(r.placa).upper(): float(r.total_ingresos or 0) for r in resultados}

    @staticmethod
    def obtener_mantenimiento_por_vehiculo() -> Dict[str, float]:
        """
        Retorna un diccionario {placa: total_mantenimiento} con los costos
        de mantenimiento agrupados por vehículo.
        """
        with get_session() as session:
            resultados = session.query(
                MantenimientoVehiculo.placa,
                func.coalesce(func.sum(MantenimientoVehiculo.total_mantenimiento), 0).label('total_manto')
            ).filter(
                MantenimientoVehiculo.placa.isnot(None),
            ).group_by(MantenimientoVehiculo.placa).all()

            return {str(r.placa).upper(): float(r.total_manto or 0) for r in resultados}

    @staticmethod
    def obtener_gastos_por_vehiculo() -> Dict[str, float]:
        """
        Retorna un diccionario {placa: total_gastos} con los gastos
        vinculados a vehículos agrupados por placa.
        """
        with get_session() as session:
            resultados = session.query(
                Gasto.placa,
                func.coalesce(func.sum(Gasto.monto), 0).label('total_gastos')
            ).filter(
                Gasto.placa.isnot(None),
            ).group_by(Gasto.placa).all()

            return {str(r.placa).upper(): float(r.total_gastos or 0) for r in resultados}
