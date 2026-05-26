"""Rental service with atomic transactions."""

from typing import List, Dict

from core.exceptions import (
    VehiculoNoDisponible,
    RentaYaCerrada,
    ClienteEnListaNegra,
    ValidacionError,
    NegocioError,
)
from core.logger import get_logger, get_audit_logger
from core.validators import validar_placa
from core.schemas import RentaCreate, RentaCierre, RentaDetalleResponse
from core.unit_of_work import UnitOfWork
from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
)
from services.financial_service import FinancialService

log = get_logger(__name__)
audit = get_audit_logger()


class RentaService:
    @staticmethod
    def crear(datos: dict) -> int:
        """Create a rental and mark vehicle as rented (atomic)."""
        placa = validar_placa(datos.get("placa", ""))
        auto = AutoRepositorySA.obtener_por_placa(placa)

        if not auto:
            raise NegocioError(f"Vehículo {placa} no encontrado.")

        if auto.get("estado", "").upper() != "DISPONIBLE":
            raise VehiculoNoDisponible(placa)

        if datos.get("estado_cliente") == "Lista Negra":
            raise ClienteEnListaNegra()

        if not datos.get("total"):
            datos["total"] = FinancialService.calcular_total_renta(datos)

        datos["placa"] = placa

        try:
            renta_validada = RentaCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de renta inválidos: {str(e)}")

        with UnitOfWork() as uow:
            id_renta = RentaRepositorySA.insertar(renta_validada, session=uow.session)
            AutoRepositorySA.cambiar_estado(placa, "Rentado", session=uow.session)

        audit.info(
            "Renta creada: id=%s, placa=%s, cliente=%s",
            id_renta,
            placa,
            datos.get("nombre_cliente"),
        )
        return id_renta

    @staticmethod
    def cerrar(id_renta: int, datos_cierre: dict) -> float:
        """Close a rental and mark vehicle as available (atomic)."""
        renta = RentaRepositorySA.obtener_por_id(id_renta)

        if renta.get("estado") == "Finalizado":
            raise RentaYaCerrada()

        gran_total = FinancialService.calcular_total_cierre(renta, datos_cierre)
        datos_cierre["total"] = gran_total

        # Parse km_final to float for updating auto's kilometraje
        km_final_str = datos_cierre.get("km_final", "")
        km_final_float = None
        if km_final_str:
            try:
                km_final_float = float(km_final_str.replace(",", ""))
            except ValueError:
                km_final_float = None
        datos_cierre["km_final_float"] = km_final_float

        try:
            cierre_validado = RentaCierre(**datos_cierre)
        except Exception as e:
            raise ValidacionError(f"Datos de cierre inválidos: {str(e)}")

        with UnitOfWork() as uow:
            RentaRepositorySA.cerrar_renta(id_renta, cierre_validado, session=uow.session)
            AutoRepositorySA.cambiar_estado(
                renta["placa"],
                "Disponible",
                kilometraje=km_final_float,
                session=uow.session,
            )

        audit.info(
            "Renta cerrada: id=%s, total=%.0f, placa=%s", id_renta, gran_total, renta["placa"]
        )
        return gran_total

    @staticmethod
    def obtener(id_renta: int) -> Dict:
        return RentaRepositorySA.obtener_por_id(id_renta)

    @staticmethod
    def obtener_activas() -> List[Dict]:
        return RentaRepositorySA.obtener_activas()

    @staticmethod
    def extender(
        id_renta: int,
        nueva_fecha: str,
        nueva_hora: str,
        nuevos_dias: int,
        nuevo_total: float,
        nuevo_saldo: float,
    ) -> None:
        RentaRepositorySA.extender(
            id_renta, nueva_fecha, nueva_hora, nuevos_dias, nuevo_total, nuevo_saldo
        )
        audit.info("Renta %s extendida hasta %s", id_renta, nueva_fecha)

    @staticmethod
    def cambiar_vehiculo(
        id_renta: int,
        placa_actual: str,
        km_actual: float,
        estado_actual: str,
        placa_nueva: str,
        motivo: str,
    ) -> None:
        """Swap vehicle on an active rental (atomic: 3 operations)."""
        nota = f"\n[CAMBIO VEHÍCULO: de {placa_actual} a {placa_nueva}. Motivo: {motivo}]"

        with UnitOfWork() as uow:
            AutoRepositorySA.cambiar_estado(
                placa_actual, estado_actual, km_actual, session=uow.session
            )
            AutoRepositorySA.cambiar_estado(placa_nueva, "Rentado", session=uow.session)
            RentaRepositorySA.actualizar_placa(id_renta, placa_nueva, nota, session=uow.session)

        audit.info("Cambio de vehículo renta %s: %s -> %s", id_renta, placa_actual, placa_nueva)

    @staticmethod
    def obtener_datos_documento(id_renta: int) -> RentaDetalleResponse:
        return RentaRepositorySA.obtener_datos_documento(id_renta)

    @staticmethod
    def obtener_para_calendario(mes: int, anio: int) -> List[RentaDetalleResponse]:
        return RentaRepositorySA.obtener_para_calendario(mes, anio)
