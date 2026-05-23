"""
comparendo_repository_sa.py — Repositorio de Comparendos / Multas

F1C: Extraído de repositories_sa.py. Sin cambios funcionales.
"""
from typing import List, Dict


from core.database_sa import get_session
from core.models import Comparendo, Renta
from core.schemas import ComparendoCreate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger

log = get_logger(__name__)


class ComparendoRepositorySA:

    @staticmethod
    def obtener_todos() -> List[Dict]:
        with get_session() as session:
            comparendos = session.query(Comparendo).order_by(Comparendo.fecha_infraccion.desc()).all()
            return [ComparendoRepositorySA._to_dict(c) for c in comparendos]

    @staticmethod
    def insertar(datos: ComparendoCreate) -> int:
        with get_session() as session:
            nuevo_comparendo = Comparendo(
                placa=datos.placa.upper(),
                fecha_infraccion=datos.fecha_infraccion,
                hora_infraccion=datos.hora_infraccion,
                monto=datos.monto,
                id_renta=datos.id_renta,
                id_cliente=datos.id_cliente,
                estado=datos.estado,
                observaciones=datos.observaciones,
            )

            session.add(nuevo_comparendo)
            session.flush()
            log.info("Comparendo registrado para placa %s", datos.placa)
            return nuevo_comparendo.id

    @staticmethod
    def actualizar_estado(id_comparendo: int, estado: str) -> None:
        with get_session() as session:
            comparendo = session.query(Comparendo).filter(Comparendo.id == id_comparendo).first()

            if not comparendo:
                raise RegistroNoEncontrado(f"Comparendo #{id_comparendo} no encontrado.")

            comparendo.estado = estado

    @staticmethod
    def buscar_historial_rentas_placa(placa: str) -> List[Dict]:
        with get_session() as session:
            rentas = session.query(Renta).filter(
                Renta.placa == placa.upper()
            ).order_by(Renta.fecha_recogida.desc()).all()

            return [{
                'id': r.id,
                'id_cliente': r.id_cliente,
                'fecha_recogida': r.fecha_recogida,
                'hora_recogida': r.hora_recogida,
                'fecha_retorno': r.fecha_retorno,
                'hora_retorno': r.hora_retorno,
            } for r in rentas]

    @staticmethod
    def _to_dict(comp: Comparendo) -> Dict:
        return {
            'id': comp.id,
            'placa': comp.placa,
            'fecha_infraccion': comp.fecha_infraccion,
            'hora_infraccion': comp.hora_infraccion,
            'monto': float(comp.monto or 0),
            'id_renta': comp.id_renta,
            'id_cliente': comp.id_cliente,
            'estado': comp.estado,
            'observaciones': comp.observaciones,
            'created_at': comp.created_at,
            'updated_at': comp.updated_at,
        }
