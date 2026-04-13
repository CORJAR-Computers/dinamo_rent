"""
reserva_service.py — Servicio de Reservas

Extraido de services_extra.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict
from decimal import Decimal

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.schemas import ReservaCreate
from repositories.repositories_sa import ReservaRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class ReservaService:

    @staticmethod
    def listar() -> List[Dict]:
        return ReservaRepositorySA.obtener_todas()

    @staticmethod
    def crear(datos: dict) -> int:
        """Crea una reserva validando que el cliente esté seleccionado."""
        if not datos.get("id_cliente"):
            raise ValidacionError(
                detalle="id_cliente requerido",
                mensaje_usuario="Debe seleccionar un cliente para la reserva.",
            )
        if not datos.get("categoria_vehiculo") and not datos.get("placa_asignada"):
            raise ValidacionError(
                detalle="Sin vehículo/categoría",
                mensaje_usuario="Seleccione un vehículo o categoría válida.",
            )

        # Calcular total si no viene
        if not datos.get("total"):
            dias = int(datos.get("dias_calculados", 1))
            horas = int(datos.get("horas_extras", 0))
            val_dia = float(datos.get("valor_dia", 0))
            val_hora = float(datos.get("valor_hora_adic", 0))
            datos["total"] = dias * val_dia + horas * val_hora

        datos.setdefault("estado", "Confirmada")
        datos.setdefault("ubicacion_recogida", "Oficina")
        datos.setdefault("ubicacion_retorno", "Oficina")

        # Validar con Pydantic
        try:
            reserva_validada = ReservaCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de reserva inválidos: {str(e)}")

        id_reserva = ReservaRepositorySA.insertar(reserva_validada)
        audit.info("Reserva creada: id=%s, cliente=%s", id_reserva, datos.get("nombre_cliente"))
        return id_reserva

    @staticmethod
    def cancelar(id_reserva: int) -> None:
        ReservaRepositorySA.cancelar(id_reserva)
        audit.info("Reserva #%s cancelada", id_reserva)

    @staticmethod
    def obtener_contacto(id_reserva: int) -> Dict:
        return ReservaRepositorySA.obtener_contacto_cliente(id_reserva)

    @staticmethod
    def obtener_para_pdf(id_reserva: int) -> Dict:
        return ReservaRepositorySA.obtener_por_id(id_reserva)
