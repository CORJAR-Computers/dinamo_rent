"""
pago_repository_sa.py — Repositorio de Pagos

F1D: Métodos insertar() y actualizar_abono_renta() ahora aceptan
     parámetro `session` para soporte de UnitOfWork.
"""

from typing import List, Dict

from sqlalchemy import func
from sqlalchemy.orm import Session

from core.models import Pago, Renta
from core.schemas import PagoCreate
from core.logger import get_logger
from core.unit_of_work import session_scope

log = get_logger(__name__)

class PagoRepositorySA:
    @staticmethod
    def obtener_por_renta(id_renta: int, session: Session = None) -> List[Dict]:
        with session_scope(session) as s:
            pagos = (
                s.query(Pago).filter(Pago.id_renta == id_renta).order_by(Pago.fecha.desc()).all()
            )

            return [PagoRepositorySA._to_dict(p) for p in pagos]

    @staticmethod
    def insertar(datos: PagoCreate, session: Session = None) -> int:
        """Registra un nuevo pago. Retorna el ID.

        F1D: Ahora acepta `session` para UnitOfWork.
        Este método es parte de la operación transaccional:
          - PagoService.registrar() (insertar pago + actualizar abono)

        Args:
            datos: Datos validados del pago (Pydantic PagoCreate)
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            nuevo_pago = Pago(
                id_renta=datos.id_renta,
                monto=datos.monto,
                metodo_pago=datos.metodo_pago,
                concepto=datos.concepto,
                observaciones=datos.observaciones,
                usuario=datos.usuario,
            )

            s.add(nuevo_pago)
            s.flush()
            log.info("Pago registrado: $%s para renta #%s", datos.monto, datos.id_renta)
            return nuevo_pago.id

    @staticmethod
    def actualizar_abono_renta(id_renta: int, session: Session = None) -> None:
        """Recalcula y actualiza el total abonado y saldo pendiente de una renta.

        F1D: Ahora acepta `session` para UnitOfWork.
        Este método es parte de la operación transaccional:
          - PagoService.registrar() (insertar pago + actualizar abono)

        Args:
            id_renta: ID de la renta a actualizar
            session: Sesión de UnitOfWork (opcional)
        """
        with session_scope(session) as s:
            total_abonado = (
                s.query(func.coalesce(func.sum(Pago.monto), 0))
                .filter(Pago.id_renta == id_renta)
                .scalar()
            )

            renta = s.query(Renta).filter(Renta.id == id_renta).first()
            if renta:
                renta.abono = total_abonado
                renta.saldo_pendiente = max(0, float(renta.total or 0) - float(total_abonado))

    @staticmethod
    def _to_dict(pago: Pago) -> Dict:
        return {
            "id": pago.id,
            "id_renta": pago.id_renta,
            "fecha": pago.fecha,
            "monto": float(pago.monto or 0),
            "metodo_pago": pago.metodo_pago,
            "concepto": pago.concepto,
            "observaciones": pago.observaciones,
            "usuario": pago.usuario,
            "updated_at": pago.updated_at,
        }
