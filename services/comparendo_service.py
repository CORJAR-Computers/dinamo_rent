"""Traffic ticket / fine service."""

from typing import List, Dict
from datetime import datetime as dt_datetime

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import ComparendoCreate, ComparendoRegistroResponse
from repositories.repositories_sa import ComparendoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class ComparendoService:

    @staticmethod
    def listar() -> List[Dict]:
        return ComparendoRepositorySA.obtener_todos()

    @staticmethod
    def registrar(datos: dict) -> ComparendoRegistroResponse:
        """Register a ticket and auto-link it to a client/rental if possible."""
        placa = requerir(datos.get("placa"), "Placa del Vehículo")
        fecha_str = requerir(datos.get("fecha"), "Fecha de Infracción")
        hora_str = requerir(datos.get("hora"), "Hora de Infracción")

        try:
            infraccion_dt = dt_datetime.strptime(f"{fecha_str} {hora_str}", "%Y-%m-%d %H:%M")
        except ValueError as e:
            raise ValidacionError(f"Fecha/hora inválida: {str(e)}")

        rentas = ComparendoRepositorySA.buscar_historial_rentas_placa(placa)

        cliente_encontrado = None
        renta_encontrada = None

        for r in rentas:
            try:
                f_rec_str = str(r['fecha_recogida'])[:10]
                h_rec_str = str(r['hora_recogida'])[:5] if r['hora_recogida'] else "00:00"
                f_ret_str = str(r['fecha_retorno'])[:10]
                h_ret_str = str(r['hora_retorno'])[:5] if r['hora_retorno'] else "00:00"

                inicio_dt = dt_datetime.strptime(f"{f_rec_str} {h_rec_str}", "%Y-%m-%d %H:%M")
                fin_dt = dt_datetime.strptime(f"{f_ret_str} {h_ret_str}", "%Y-%m-%d %H:%M")

                if inicio_dt <= infraccion_dt <= fin_dt:
                    cliente_encontrado = r['id_cliente']
                    renta_encontrada = r['id']
                    break
            except Exception as e:
                log.warning(f"Error parseando fechas de renta {r['id']}: {e}")
                continue

        datos["id_cliente"] = cliente_encontrado
        datos["id_renta"] = renta_encontrada

        try:
            comparendo_validado = ComparendoCreate(
                placa=placa,
                fecha_infraccion=dt_datetime.strptime(fecha_str, "%Y-%m-%d").date(),
                hora_infraccion=dt_datetime.strptime(hora_str, "%H:%M").time(),
                monto=float(datos.get("monto", 0)),
                id_renta=renta_encontrada,
                id_cliente=cliente_encontrado,
                estado=datos.get("estado", "Pendiente"),
                observaciones=datos.get("observaciones"),
            )
        except Exception as e:
            raise ValidacionError(f"Datos de comparendo inválidos: {str(e)}")

        id_nuevo = ComparendoRepositorySA.insertar(comparendo_validado)
        audit.info("Comparendo registrado para placa %s. Renta vinculada: %s", placa, renta_encontrada)

        return {
            "id_comparendo": id_nuevo,
            "vinculado": cliente_encontrado is not None,
            "id_renta": renta_encontrada,
            "id_cliente": cliente_encontrado
        }

    @staticmethod
    def cambiar_estado(id_comparendo: int, estado: str) -> None:
        ComparendoRepositorySA.actualizar_estado(id_comparendo, estado)
