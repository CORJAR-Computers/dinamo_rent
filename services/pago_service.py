"""
pago_service.py — Servicio de Pagos y Caja

Extraido de services_extra.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import PagoCreate
from repositories.repositories_sa import PagoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class PagoService:

    @staticmethod
    def listar_por_renta(id_renta: int) -> List[Dict]:
        return PagoRepositorySA.obtener_por_renta(id_renta)

    @staticmethod
    def registrar(datos: dict) -> int:
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

        # 1. Registrar el recibo
        id_pago = PagoRepositorySA.insertar(pago_validado)

        # 2. Sincronizar el total abonado en la tabla principal de rentas
        PagoRepositorySA.actualizar_abono_renta(int(datos["id_renta"]))

        audit.info("Pago de $%s registrado para la renta #%s (%s)", monto, datos["id_renta"], datos["metodo_pago"])
        return id_pago
