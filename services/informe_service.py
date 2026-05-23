"""Management reports service with RBAC protection."""

from typing import List

from core.logger import get_logger, get_audit_logger
from core.schemas import BalanceMensualItemResponse
from core.rbac import require_role
from core.config import ROLES_CON_INFORMES
from repositories.repositories_sa import InformeRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class InformeService:

    @staticmethod
    @require_role(*ROLES_CON_INFORMES)
    def balance_mensual_real(session_id: str = None) -> List[BalanceMensualItemResponse]:
        """Monthly consolidated balance with income, workshop, and petty cash."""
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
