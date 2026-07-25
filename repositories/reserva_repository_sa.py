"""
reserva_repository_sa.py — Repositorio de Reservas

"""

from typing import List, Dict

from core.database_sa import get_session
from core.models import Reserva
from core.schemas import ReservaCreate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger

log = get_logger(__name__)


class ReservaRepositorySA:
    @staticmethod
    def obtener_todas() -> List[Dict]:
        with get_session() as session:
            reservas = session.query(Reserva).order_by(Reserva.fecha_recogida).all()
            return [ReservaRepositorySA._to_dict(r) for r in reservas]

    @staticmethod
    def insertar(datos: ReservaCreate) -> int:
        with get_session() as session:
            nueva_reserva = Reserva(
                id_cliente=datos.id_cliente,
                nombre_cliente=datos.nombre_cliente,
                nacionalidad=datos.nacionalidad,
                categoria_vehiculo=datos.categoria_vehiculo,
                placa_asignada=datos.placa_asignada.upper() if datos.placa_asignada else None,
                fecha_recogida=datos.fecha_recogida,
                hora_recogida=datos.hora_recogida,
                ubicacion_recogida=datos.ubicacion_recogida,
                fecha_retorno=datos.fecha_retorno,
                hora_retorno=datos.hora_retorno,
                ubicacion_retorno=datos.ubicacion_retorno,
                dias_calculados=datos.dias_calculados,
                horas_extras=datos.horas_extras,
                valor_dia=datos.valor_dia,
                valor_hora_adic=datos.valor_hora_adic,
                abono=datos.abono,
                total=datos.total,
                observaciones=datos.observaciones,
                estado=datos.estado,
            )

            session.add(nueva_reserva)
            session.flush()
            log.info("Reserva creada: id=%s, cliente=%s", nueva_reserva.id, datos.nombre_cliente)
            return nueva_reserva.id

    @staticmethod
    def cancelar(id_reserva: int) -> None:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            reserva.estado = "Cancelada"
            log.info("Reserva #%s cancelada", id_reserva)

    @staticmethod
    def obtener_contacto_cliente(id_reserva: int) -> Dict:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            return {
                "nombre_cliente": reserva.nombre_cliente,
                "nacionalidad": reserva.nacionalidad,
            }

    @staticmethod
    def obtener_por_id(id_reserva: int) -> Dict:
        with get_session() as session:
            reserva = session.query(Reserva).filter(Reserva.id == id_reserva).first()

            if not reserva:
                raise RegistroNoEncontrado(f"Reserva #{id_reserva} no encontrada.")

            return ReservaRepositorySA._to_dict(reserva)

    @staticmethod
    def _to_dict(reserva: Reserva) -> Dict:
        return {
            "id": reserva.id,
            "id_cliente": reserva.id_cliente,
            "nombre_cliente": reserva.nombre_cliente,
            "nacionalidad": reserva.nacionalidad,
            "categoria_vehiculo": reserva.categoria_vehiculo,
            "placa_asignada": reserva.placa_asignada,
            "fecha_recogida": reserva.fecha_recogida,
            "hora_recogida": reserva.hora_recogida,
            "ubicacion_recogida": reserva.ubicacion_recogida,
            "fecha_retorno": reserva.fecha_retorno,
            "hora_retorno": reserva.hora_retorno,
            "ubicacion_retorno": reserva.ubicacion_retorno,
            "dias_calculados": reserva.dias_calculados,
            "horas_extras": reserva.horas_extras,
            "valor_dia": float(reserva.valor_dia or 0),
            "valor_hora_adic": float(reserva.valor_hora_adic or 0),
            "abono": float(reserva.abono or 0),
            "total": float(reserva.total or 0),
            "observaciones": reserva.observaciones,
            "estado": reserva.estado,
            "created_at": reserva.created_at,
            "updated_at": reserva.updated_at,
        }
