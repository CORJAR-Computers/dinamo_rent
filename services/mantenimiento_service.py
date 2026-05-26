"""Vehicle maintenance service with atomic transactions."""

import datetime
from typing import List, Dict
from datetime import datetime as dt_datetime

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import validar_placa
from core.schemas import MantenimientoCreate
from core.unit_of_work import UnitOfWork
from repositories.repositories_sa import MantenimientoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class MantenimientoService:
    @staticmethod
    def listar_historial(limite: int = 50) -> List[Dict]:
        return MantenimientoRepositorySA.obtener_historial(limite)

    @staticmethod
    def listar_autos() -> List[Dict]:
        return MantenimientoRepositorySA.obtener_autos_con_km()

    @staticmethod
    def registrar(datos: dict) -> None:
        """Register maintenance and update vehicle atomically via UnitOfWork."""
        placa = validar_placa(datos.get("placa", ""))
        if not datos.get("tipo"):
            raise ValidacionError(mensaje_usuario="Seleccione el tipo de servicio.")

        mant_data = {
            "placa": placa,
            "pieza_varias_tipo": datos["tipo"],
            "pieza_varias_fecha": datos.get("fecha"),
            "pieza_varias_desc": datos.get("desc"),
            "pieza_varias_obs": datos.get("obs"),
            "cost_varios": float(datos.get("costo", 0)),
            "km_proximo_cambio_aceite": int(datos.get("prox_km", 0))
            if datos["tipo"] == "Cambio Aceite"
            else 0,
            "total_mantenimiento": float(datos.get("costo", 0)),
        }

        try:
            mant_validado = MantenimientoCreate(**mant_data)
        except Exception as e:
            raise ValidacionError(f"Datos de mantenimiento inválidos: {str(e)}")

        campos_auto: dict = {"kilometraje": datos.get("km_actual", 0)}

        tipo = datos["tipo"]
        if tipo == "Cambio Aceite":
            campos_auto["proximo_aceite"] = int(datos.get("prox_km", 0))
        elif tipo == "Frenos":
            campos_auto["proximo_frenos"] = int(datos.get("prox_km", 0))
        elif tipo == "Tecno-Mecánica":
            try:
                fecha_base = dt_datetime.strptime(str(datos.get("fecha"))[:10], "%Y-%m-%d")
                campos_auto["vencimiento_tecnico"] = (
                    fecha_base + datetime.timedelta(days=365)
                ).date()
            except (ValueError, TypeError):
                pass

        accion = datos.get("accion_estado", "mantener")
        if accion == "mantenimiento":
            campos_auto["estado"] = "Mantenimiento"
        elif accion == "disponible":
            campos_auto["estado"] = "Disponible"

        with UnitOfWork() as uow:
            MantenimientoRepositorySA.insertar(mant_validado, session=uow.session)
            MantenimientoRepositorySA.actualizar_auto(placa, campos_auto, session=uow.session)

        audit.info(
            "Mantenimiento registrado: placa=%s, tipo=%s, costo=%s", placa, tipo, datos.get("costo")
        )
