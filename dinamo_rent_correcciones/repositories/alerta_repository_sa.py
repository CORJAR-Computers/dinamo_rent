"""
alerta_repository_sa.py — Repositorio de Alertas y Notificaciones

"""

from typing import List, Dict

from sqlalchemy import and_

from core.database_sa import get_session
from core.models import Renta, Cliente, Auto
from core.logger import get_logger

log = get_logger(__name__)

class AlertaRepositorySA:
    @staticmethod
    def obtener_rentas_por_vencer() -> List[Dict]:
        from datetime import date, timedelta

        hoy = date.today()
        tres_dias = hoy + timedelta(days=3)

        with get_session() as session:
            rentas = (
                session.query(Renta, Cliente)
                .join(Cliente, Renta.id_cliente == Cliente.id)
                .filter(
                    and_(
                        Renta.estado == "Activo",
                        Renta.fecha_retorno <= tres_dias,
                        Renta.fecha_retorno >= hoy,
                    )
                )
                .all()
            )

            return [
                {
                    "id": r.id,
                    "placa": r.placa,
                    "nombre_completo": c.nombre_completo if c else r.nombre_cliente,
                    "celular": c.celular if c else None,
                    "fecha_retorno": r.fecha_retorno,
                    "hora_retorno": r.hora_retorno,
                }
                for r, c in rentas
            ]

    @staticmethod
    def obtener_documentos_por_vencer() -> List[Dict]:
        from datetime import date, timedelta

        hoy = date.today()
        quince_dias = hoy + timedelta(days=15)

        with get_session() as session:
            autos = (
                session.query(Auto)
                .filter(
                    and_(
                        Auto.estado.notin_(["Vendido", "Baja"]),
                        and_(
                            Auto.vencimiento_soat <= quince_dias,
                            Auto.vencimiento_soat >= hoy,
                        ),
                    )
                )
                .all()
            )

            return [
                {
                    "placa": a.placa,
                    "marca": a.marca,
                    "modelo": a.modelo,
                    "vencimiento_soat": a.vencimiento_soat,
                    "vencimiento_tecnico": a.vencimiento_tecnico,
                }
                for a in autos
            ]

    @staticmethod
    def obtener_mantenimientos_proximos() -> List[Dict]:
        with get_session() as session:
            autos = (
                session.query(Auto)
                .filter(
                    and_(
                        Auto.proximo_aceite.isnot(None),
                        Auto.kilometraje >= (Auto.proximo_aceite - 500),
                    )
                )
                .all()
            )

            return [
                {
                    "placa": a.placa,
                    "kilometraje": a.kilometraje,
                    "proximo_aceite": a.proximo_aceite,
                }
                for a in autos
            ]
