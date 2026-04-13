"""
auto_repository_sa.py — Auto Repository with SQLAlchemy 2.0

Modern repository pattern using SQLAlchemy ORM and Pydantic validation.
Replaces the old auto_repository.py
"""
from typing import List, Optional, Dict
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import func

from core.database_sa import get_session
from core.models import Auto
from core.schemas import AutoCreate, AutoUpdate
from core.exceptions import RegistroNoEncontrado, DuplicadoError
from core.logger import get_logger

log = get_logger(__name__)


class AutoRepositorySA:

    @staticmethod
    def obtener_todos() -> List[Dict]:
        """Get all vehicles."""
        with get_session() as session:
            autos = session.query(Auto).all()
            return [AutoRepositorySA._to_dict(auto) for auto in autos]

    @staticmethod
    def obtener_disponibles() -> List[Dict]:
        """Get all available vehicles."""
        with get_session() as session:
            autos = session.query(Auto).filter(
                Auto.estado == 'Disponible'
            ).order_by(Auto.marca, Auto.modelo).all()
            return [AutoRepositorySA._to_dict(auto) for auto in autos]

    @staticmethod
    def obtener_por_placa(placa: str) -> Optional[Dict]:
        """Get vehicle by plate number."""
        with get_session() as session:
            auto = session.query(Auto).filter(
                Auto.placa == placa.upper()
            ).first()
            
            if not auto:
                return None
            
            return AutoRepositorySA._to_dict(auto)

    @staticmethod
    def existe(placa: str) -> bool:
        """Check if vehicle exists."""
        with get_session() as session:
            return session.query(Auto).filter(
                Auto.placa == placa.upper()
            ).first() is not None

    @staticmethod
    def insertar(datos: AutoCreate) -> str:
        """
        Create new vehicle.
        
        Returns:
            Plate number of created vehicle
        """
        with get_session() as session:
            # Check for duplicate
            if AutoRepositorySA.existe(datos.placa):
                raise DuplicadoError(f"El vehículo con placa '{datos.placa}' ya existe.")
            
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
            
            session.add(nuevo_auto)
            log.info("Vehículo creado: %s - %s %s", datos.placa, datos.marca, datos.modelo)
            return nuevo_auto.placa

    @staticmethod
    def actualizar(datos: AutoUpdate) -> None:
        """Update vehicle data."""
        with get_session() as session:
            auto = session.query(Auto).filter(
                Auto.placa == datos.placa.upper()
            ).first()
            
            if not auto:
                raise RegistroNoEncontrado(f"Vehículo con placa '{datos.placa}' no encontrado.")
            
            # Update fields
            update_fields = datos.model_dump(exclude_unset=True, exclude={'placa'})
            for field, value in update_fields.items():
                if hasattr(auto, field):
                    setattr(auto, field, value)
            
            log.info("Vehículo actualizado: %s", datos.placa)

    @staticmethod
    def cambiar_estado(placa: str, nuevo_estado: str, kilometraje: Optional[float] = None) -> None:
        """Change vehicle status and optionally update mileage."""
        with get_session() as session:
            auto = session.query(Auto).filter(
                Auto.placa == placa.upper()
            ).first()
            
            if not auto:
                raise RegistroNoEncontrado(f"Vehículo con placa '{placa}' no encontrado.")
            
            auto.estado = nuevo_estado
            if kilometraje is not None:
                auto.kilometraje = kilometraje
            
            log.info("Estado de %s cambiado a: %s (km: %s)", placa, nuevo_estado, kilometraje)

    @staticmethod
    def eliminar(placa: str) -> None:
        """Delete vehicle."""
        with get_session() as session:
            auto = session.query(Auto).filter(
                Auto.placa == placa.upper()
            ).first()
            
            if not auto:
                raise RegistroNoEncontrado(f"Vehículo con placa '{placa}' no encontrado.")
            
            session.delete(auto)
            log.info("Vehículo eliminado: %s", placa)

    @staticmethod
    def obtener_alertas_flota() -> List[Dict]:
        """Get vehicles with upcoming alerts (SOAT, Tecno, Aceite, etc.)."""
        with get_session() as session:
            from datetime import date, timedelta
            
            hoy = date.today()
            dias_alerta_soat = 15
            dias_alerta_tecnico = 15
            
            autos = session.query(Auto).filter(
                Auto.estado != 'Vendido',
                Auto.estado != 'Baja'
            ).all()
            
            alertas = []
            for auto in autos:
                # Check SOAT
                if auto.vencimiento_soat:
                    dias_restantes = (auto.vencimiento_soat - hoy).days
                    if dias_restantes <= dias_alerta_soat:
                        alertas.append({
                            'placa': auto.placa,
                            'tipo': 'SOAT',
                            'vencimiento': auto.vencimiento_soat,
                            'dias_restantes': dias_restantes,
                        })
                
                # Check Tecno-mecánica
                if auto.vencimiento_tecnico:
                    dias_restantes = (auto.vencimiento_tecnico - hoy).days
                    if dias_restantes <= dias_alerta_tecnico:
                        alertas.append({
                            'placa': auto.placa,
                            'tipo': 'Tecno-mecánica',
                            'vencimiento': auto.vencimiento_tecnico,
                            'dias_restantes': dias_restantes,
                        })
                
                # Check Aceite
                if auto.proximo_aceite and auto.kilometraje >= (auto.proximo_aceite - 500):
                    alertas.append({
                        'placa': auto.placa,
                        'tipo': 'Aceite',
                        'km_actual': auto.kilometraje,
                        'km_proximo': auto.proximo_aceite,
                    })
            
            return alertas

    @staticmethod
    def contar_por_estado() -> Dict[str, int]:
        """Count vehicles by status."""
        with get_session() as session:
            resultados = session.query(
                Auto.estado,
                func.count(Auto.placa)
            ).group_by(Auto.estado).all()
            
            return {estado: cantidad for estado, cantidad in resultados}

    @staticmethod
    def _to_dict(auto: Auto) -> Dict:
        """Convert SQLAlchemy model to dictionary."""
        return {
            'placa': auto.placa,
            'marca': auto.marca,
            'modelo': auto.modelo,
            'version': auto.version,
            'color': auto.color,
            'tipo': auto.tipo,
            'cilindraje': auto.cilindraje,
            'transmision': auto.transmision,
            'combustible': auto.combustible,
            'no_motor': auto.no_motor,
            'no_chasis': auto.no_chasis,
            'propietario': auto.propietario,
            'estado': auto.estado,
            'costo_fijo_mensual': float(auto.costo_fijo_mensual or 0),
            'kilometraje': auto.kilometraje or 0,
            'ubicacion': auto.ubicacion,
            'tipo_adquisicion': auto.tipo_adquisicion,
            'proximo_aceite': auto.proximo_aceite,
            'proximo_frenos': auto.proximo_frenos,
            'vencimiento_soat': auto.vencimiento_soat,
            'vencimiento_tecnico': auto.vencimiento_tecnico,
            'vencimiento_extintor': auto.vencimiento_extintor,
            'vencimiento_bateria': auto.vencimiento_bateria,
            'observaciones': auto.observaciones,
            'fecha_ingreso': auto.fecha_ingreso,
            'created_at': auto.created_at,
            'updated_at': auto.updated_at,
        }
