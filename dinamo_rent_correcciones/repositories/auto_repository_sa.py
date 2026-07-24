"""
auto_repository_sa.py — Repositorio de Vehículos

que eran referenciados por los servicios pero no existían.
     soporte de UnitOfWork en operaciones transaccionales.
"""

from typing import List, Dict, Optional

from sqlalchemy.orm import Session

from core.models import Auto
from core.schemas import AutoCreate, AutoUpdate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger
from core.unit_of_work import session_scope

log = get_logger(__name__)

class AutoRepositorySA:
    @staticmethod
    def obtener_todos(session: Session = None) -> List[Dict]:
        """Obtiene todos los vehículos registrados."""
        with session_scope(session) as s:
            autos = s.query(Auto).order_by(Auto.placa).all()
            return [AutoRepositorySA._to_dict(a) for a in autos]

    @staticmethod
    def obtener_disponibles(session: Session = None) -> List[Dict]:
        """Obtiene solo los vehículos con estado 'Disponible'."""
        with session_scope(session) as s:
            autos = s.query(Auto).filter(Auto.estado == "Disponible").order_by(Auto.placa).all()
            return [AutoRepositorySA._to_dict(a) for a in autos]

    @staticmethod
    def obtener_por_placa(placa: str, session: Session = None) -> Optional[Dict]:
        """Obtiene un vehículo por su placa. Retorna None si no existe."""
        with session_scope(session) as s:
            auto = s.query(Auto).filter(Auto.placa == placa.upper()).first()
            return AutoRepositorySA._to_dict(auto) if auto else None

    @staticmethod
    def existe(placa: str, session: Session = None) -> bool:
        """Verifica si un vehículo existe por su placa."""
        with session_scope(session) as s:
            return s.query(Auto).filter(Auto.placa == placa.upper()).first() is not None

    @staticmethod
    def insertar(datos: AutoCreate, session: Session = None) -> str:
        """Inserta un nuevo vehículo. Retorna la placa."""
        with session_scope(session) as s:
            nuevo_auto = Auto(
                placa=datos.placa.upper(),
                marca=datos.marca,
                modelo=datos.modelo,
                version=datos.version,
                color=datos.color,
                tipo=datos.tipo,
                cilindraje=datos.cilindraje,
                transmision=datos.transmision,
                combustible=datos.combustible,
                no_motor=datos.no_motor,
                no_chasis=datos.no_chasis,
                propietario=datos.propietario,
                estado=datos.estado,
                costo_fijo_mensual=datos.costo_fijo_mensual,
                kilometraje=datos.kilometraje,
                ubicacion=datos.ubicacion,
                tipo_adquisicion=datos.tipo_adquisicion,
                proximo_aceite=datos.proximo_aceite,
                proximo_frenos=datos.proximo_frenos,
                vencimiento_soat=datos.vencimiento_soat,
                vencimiento_tecnico=datos.vencimiento_tecnico,
                vencimiento_extintor=datos.vencimiento_extintor,
                vencimiento_bateria=datos.vencimiento_bateria,
                observaciones=datos.observaciones,
                fecha_ingreso=datos.fecha_ingreso,
            )
            s.add(nuevo_auto)
            s.flush()
            log.info("Auto creado: placa=%s", datos.placa)
            return datos.placa

    @staticmethod
    def actualizar(datos: AutoUpdate, session: Session = None) -> None:
        """
        Actualiza los campos de un vehículo existente.

        F1C: AutoUpdate ahora incluye placa como campo requerido
        para identificar el registro a actualizar.
        """
        with session_scope(session) as s:
            auto = s.query(Auto).filter(Auto.placa == datos.placa).first()
            if not auto:
                raise RegistroNoEncontrado(f"Vehículo {datos.placa} no encontrado.")

            update_fields = datos.model_dump(exclude_unset=True, exclude={"placa"})
            for campo, valor in update_fields.items():
                if hasattr(auto, campo):
                    setattr(auto, campo, valor)

            log.info("Auto actualizado: placa=%s", datos.placa)

    @staticmethod
    def cambiar_estado(
        placa: str, nuevo_estado: str, kilometraje=None, session: Session = None
    ) -> None:
        """Cambia el estado de un vehículo y opcionalmente su kilometraje.

        F1D: Ahora acepta parámetro `session` para UnitOfWork.
        Este método es parte de 3 operaciones transaccionales:
          - RentaService.crear() (Disponible → Rentado)
          - RentaService.cerrar() (Rentado → Disponible)
          - RentaService.cambiar_vehiculo() (2 cambios de estado)

        Args:
            placa: Placa del vehículo
            nuevo_estado: Nuevo estado a asignar
            kilometraje: Nuevo kilometraje (opcional)
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            auto = s.query(Auto).filter(Auto.placa == placa.upper()).first()
            if not auto:
                raise RegistroNoEncontrado(f"Vehículo {placa} no encontrado.")

            auto.estado = nuevo_estado
            if kilometraje is not None:
                auto.kilometraje = float(kilometraje)
            log.info("Auto %s: estado cambiado a '%s'", placa, nuevo_estado)

    @staticmethod
    def obtener_alertas_flota(session: Session = None) -> List[Dict]:
        """
        Obtiene alertas de la flota: aceite próximo, SOAT y tecno-mecánica por vencer.
        Retorna lista de dicts con tipo, placa, y detalles según el tipo de alerta.
        """
        from datetime import date

        with session_scope(session) as s:
            alertas = []
            hoy = date.today()
            limite_dias = 15

            autos = s.query(Auto).filter(Auto.estado.notin_(["Vendido", "Baja"])).all()

            for a in autos:
                # Alerta de aceite
                if a.proximo_aceite and a.proximo_aceite > 0:
                    if a.kilometraje >= (a.proximo_aceite - 500):
                        alertas.append(
                            {
                                "tipo": "Aceite",
                                "placa": a.placa,
                                "km_actual": int(a.kilometraje or 0),
                                "km_proximo": a.proximo_aceite,
                            }
                        )

                # Alerta de SOAT
                if a.vencimiento_soat:
                    dias = (a.vencimiento_soat - hoy).days
                    if -30 <= dias <= limite_dias:
                        alertas.append(
                            {
                                "tipo": "SOAT",
                                "placa": a.placa,
                                "dias_restantes": dias,
                                "vencimiento": str(a.vencimiento_soat),
                            }
                        )

                # Alerta de tecno-mecánica
                if a.vencimiento_tecnico:
                    dias = (a.vencimiento_tecnico - hoy).days
                    if -30 <= dias <= limite_dias:
                        alertas.append(
                            {
                                "tipo": "Tecno-mecánica",
                                "placa": a.placa,
                                "dias_restantes": dias,
                                "vencimiento": str(a.vencimiento_tecnico),
                            }
                        )

            return alertas

    @staticmethod
    def _to_dict(auto: Auto) -> Dict:
        return {
            "placa": auto.placa,
            "marca": auto.marca,
            "modelo": auto.modelo,
            "version": auto.version,
            "color": auto.color,
            "tipo": auto.tipo,
            "cilindraje": auto.cilindraje,
            "transmision": auto.transmision,
            "combustible": auto.combustible,
            "no_motor": auto.no_motor,
            "no_chasis": auto.no_chasis,
            "propietario": auto.propietario,
            "estado": auto.estado,
            "costo_fijo_mensual": float(auto.costo_fijo_mensual or 0),
            "kilometraje": float(auto.kilometraje or 0),
            "ubicacion": auto.ubicacion,
            "tipo_adquisicion": auto.tipo_adquisicion,
            "proximo_aceite": auto.proximo_aceite,
            "proximo_frenos": auto.proximo_frenos,
            "vencimiento_soat": auto.vencimiento_soat,
            "vencimiento_tecnico": auto.vencimiento_tecnico,
            "vencimiento_extintor": auto.vencimiento_extintor,
            "vencimiento_bateria": auto.vencimiento_bateria,
            "observaciones": auto.observaciones,
            "fecha_ingreso": auto.fecha_ingreso,
            "created_at": auto.created_at,
            "updated_at": auto.updated_at,
        }
