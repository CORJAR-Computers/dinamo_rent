"""Payment service with atomic transactions."""

from typing import List, Dict

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import PagoCreate
from core.unit_of_work import UnitOfWork
from repositories.repositories_sa import PagoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class PagoService:
    @staticmethod
    def listar_por_renta(id_renta: int) -> List[Dict]:
        return PagoRepositorySA.obtener_por_renta(id_renta)

    @staticmethod
    def registrar(datos: dict) -> int:
        """Register a payment and update rental balance atomically via UnitOfWork."""
        requerir(datos.get("id_renta"), "ID de Renta")
        requerir(datos.get("monto"), "Monto del Pago")
        requerir(datos.get("metodo_pago"), "Método de Pago")

        monto = float(datos["monto"])
        if monto <= 0:
            raise ValidacionError("El monto del pago debe ser mayor a cero.")

        try:
            pago_validado = PagoCreate(
                id_renta=int(datos["id_renta"]),
                monto=monto,
                metodo_pago=datos["metodo_pago"],
                concepto=datos.get("concepto", "Abono"),
                observaciones=datos.get("observaciones"),
                usuario=datos.get("usuario"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de pago inválidos: {str(e)}")

        id_renta = int(datos["id_renta"])
        with UnitOfWork() as uow:
            id_pago = PagoRepositorySA.insertar(pago_validado, session=uow.session)
            PagoRepositorySA.actualizar_abono_renta(id_renta, session=uow.session)

        audit.info(
            "Pago de $%s registrado para la renta #%s (%s)",
            monto,
            datos["id_renta"],
            datos["metodo_pago"],
        )
        return id_pago
