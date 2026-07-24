"""
mantenimiento_repository_sa.py — Repositorio de Mantenimiento de Vehículos

F1D: Métodos insertar() y actualizar_auto() ahora aceptan parámetro
     `session` para soporte de UnitOfWork.
"""

from typing import List, Dict

from sqlalchemy.orm import Session

from core.models import Auto, MantenimientoVehiculo
from core.schemas import MantenimientoCreate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger
from core.unit_of_work import session_scope

log = get_logger(__name__)

class MantenimientoRepositorySA:
    @staticmethod
    def obtener_historial(limite: int = 50, session: Session = None) -> List[Dict]:
        with session_scope(session) as s:
            mantenimientos = (
                s.query(MantenimientoVehiculo)
                .order_by(MantenimientoVehiculo.created_at.desc())
                .limit(limite)
                .all()
            )

            return [MantenimientoRepositorySA._to_dict(m) for m in mantenimientos]

    @staticmethod
    def obtener_autos_con_km(session: Session = None) -> List[Dict]:
        with session_scope(session) as s:
            autos = s.query(Auto).filter(Auto.estado.notin_(["Vendido", "Baja"])).all()

            return [
                {
                    "placa": a.placa,
                    "marca": a.marca,
                    "modelo": a.modelo,
                    "kilometraje": a.kilometraje,
                    "estado": a.estado,
                }
                for a in autos
            ]

    @staticmethod
    def insertar(datos: MantenimientoCreate, session: Session = None) -> int:
        """Inserta un registro de mantenimiento. Retorna el ID.

        F1D: Ahora acepta `session` para UnitOfWork.
        Este método es parte de la operación transaccional:
          - MantenimientoService.registrar() (insertar + actualizar auto)

        Args:
            datos: Datos validados del mantenimiento (Pydantic MantenimientoCreate)
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            nuevo_mant = MantenimientoVehiculo(
                placa=datos.placa.upper(),
                pieza_varias_tipo=datos.pieza_varias_tipo,
                pieza_varias_fecha=datos.pieza_varias_fecha,
                pieza_varias_desc=datos.pieza_varias_desc,
                pieza_varias_obs=datos.pieza_varias_obs,
                cost_varios=datos.cost_varios,
                km_proximo_cambio_aceite=datos.km_proximo_cambio_aceite,
                total_mantenimiento=datos.total_mantenimiento,
            )

            s.add(nuevo_mant)
            s.flush()
            log.info(
                "Mantenimiento registrado: placa=%s, tipo=%s", datos.placa, datos.pieza_varias_tipo
            )
            return nuevo_mant.id

    @staticmethod
    def actualizar_auto(placa: str, campos: Dict, session: Session = None) -> None:
        """Actualiza campos del vehículo después de un mantenimiento.

        F1D: Ahora acepta `session` para UnitOfWork.
        Este método es parte de la operación transaccional:
          - MantenimientoService.registrar() (insertar + actualizar auto)

        Args:
            placa: Placa del vehículo
            campos: Diccionario de campos a actualizar
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            auto = s.query(Auto).filter(Auto.placa == placa.upper()).first()

            if not auto:
                raise RegistroNoEncontrado(f"Vehiculo {placa} no encontrado.")

            for campo, valor in campos.items():
                if hasattr(auto, campo):
                    setattr(auto, campo, valor)

    @staticmethod
    def _to_dict(mant: MantenimientoVehiculo) -> Dict:
        return {
            "id": mant.id,
            "placa": mant.placa,
            "pieza_varias_tipo": mant.pieza_varias_tipo,
            "pieza_varias_fecha": mant.pieza_varias_fecha,
            "pieza_varias_desc": mant.pieza_varias_desc,
            "pieza_varias_obs": mant.pieza_varias_obs,
            "cost_varios": float(mant.cost_varios or 0),
            "km_proximo_cambio_aceite": mant.km_proximo_cambio_aceite,
            "total_mantenimiento": float(mant.total_mantenimiento or 0),
            "created_at": mant.created_at,
            "updated_at": mant.updated_at,
        }
