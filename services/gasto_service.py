"""
gasto_service.py — Servicio de Gastos y Caja Menor

Extraido de services_extra.py como parte de F1B (Reestructuración de Services).
F1A: Ahora soporta vincular gastos a vehículos vía campo placa.
"""
from typing import List, Dict

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir, validar_placa
from core.schemas import GastoCreate
from repositories.repositories_sa import GastoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class GastoService:

    @staticmethod
    def listar_recientes() -> List[Dict]:
        return GastoRepositorySA.obtener_todos(200)

    @staticmethod
    def listar_por_placa(placa: str) -> List[Dict]:
        """Obtiene todos los gastos vinculados a un vehículo."""
        placa = validar_placa(placa)
        return GastoRepositorySA.obtener_por_placa(placa)

    @staticmethod
    def registrar(datos: dict) -> int:
        requerir(datos.get("fecha"), "Fecha del Gasto")
        requerir(datos.get("categoria"), "Categoría")
        requerir(datos.get("descripcion"), "Descripción")
        requerir(datos.get("monto"), "Monto")

        monto = float(datos["monto"])
        if monto <= 0:
            raise ValidacionError("El monto del gasto debe ser mayor a cero.")

        # Validar placa si viene (es opcional)
        placa_gasto = datos.get("placa")
        if placa_gasto:
            placa_gasto = validar_placa(placa_gasto)

        try:
            gasto_validado = GastoCreate(
                placa=placa_gasto,
                fecha=datos["fecha"],
                categoria=datos["categoria"],
                descripcion=datos["descripcion"],
                monto=monto,
                comprobante=datos.get("comprobante"),
                usuario=datos.get("usuario", "Sistema"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de gasto inválidos: {str(e)}")

        id_gasto = GastoRepositorySA.insertar(gasto_validado)
        audit.info("Gasto de $%s registrado en categoría '%s' placa=%s",
                   monto, datos["categoria"], placa_gasto or 'N/A')

        return id_gasto
