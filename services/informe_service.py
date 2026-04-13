"""
informe_service.py — Servicio de Informes Gerenciales

Extraido de services_extra.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict

from core.logger import get_logger, get_audit_logger
from repositories.repositories_sa import InformeRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class InformeService:

    @staticmethod
    def balance_mensual_real() -> List[Dict]:
        """
        Balance consolidado mensual con ingresos, taller y caja menor.
        Usa la query SQL consolidada del repositorio.
        """
        resultados = InformeRepositorySA.obtener_balance_consolidado()

        balance_procesado = []
        for r in resultados:
            ingresos = float(r.get('ingresos') or 0)
            taller = float(r.get('egresos_taller') or 0)
            caja = float(r.get('gastos_caja') or 0)

            utilidad = ingresos - (taller + caja)

            balance_procesado.append({
                "mes": r.get('mes', 'Desconocido'),
                "ingresos": ingresos,
                "taller": taller,
                "caja_menor": caja,
                "utilidad": utilidad
            })

        return balance_procesado
