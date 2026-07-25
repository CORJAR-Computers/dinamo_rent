"""
gasto_repository_sa.py — Repositorio de Gastos / Caja Menor

"""

from typing import List, Dict

from core.database_sa import get_session
from core.models import Gasto
from core.schemas import GastoCreate
from core.logger import get_logger

log = get_logger(__name__)


class GastoRepositorySA:
    @staticmethod
    def obtener_todos(limite: int = 200) -> List[Dict]:
        with get_session() as session:
            gastos = session.query(Gasto).order_by(Gasto.fecha.desc()).limit(limite).all()
            return [GastoRepositorySA._to_dict(g) for g in gastos]

    @staticmethod
    def obtener_por_placa(placa: str) -> List[Dict]:
        """Obtiene todos los gastos vinculados a un vehiculo."""
        with get_session() as session:
            gastos = (
                session.query(Gasto)
                .filter(Gasto.placa == placa.upper())
                .order_by(Gasto.fecha.desc())
                .all()
            )
            return [GastoRepositorySA._to_dict(g) for g in gastos]

    @staticmethod
    def insertar(datos: GastoCreate) -> int:
        with get_session() as session:
            nuevo_gasto = Gasto(
                placa=datos.placa.upper() if datos.placa else None,
                fecha=datos.fecha,
                categoria=datos.categoria,
                descripcion=datos.descripcion,
                monto=datos.monto,
                comprobante=datos.comprobante,
                usuario=datos.usuario,
            )

            session.add(nuevo_gasto)
            session.flush()
            log.info(
                "Gasto registrado: $%s en '%s' placa=%s",
                datos.monto,
                datos.categoria,
                datos.placa or "N/A",
            )
            return nuevo_gasto.id

    @staticmethod
    def _to_dict(gasto: Gasto) -> Dict:
        return {
            "id": gasto.id,
            "placa": gasto.placa,
            "fecha": gasto.fecha,
            "categoria": gasto.categoria,
            "descripcion": gasto.descripcion,
            "monto": float(gasto.monto or 0),
            "comprobante": gasto.comprobante,
            "usuario": gasto.usuario,
            "created_at": gasto.created_at,
            "updated_at": gasto.updated_at,
        }
