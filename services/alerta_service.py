"""Alert and notification service."""

from core.logger import get_logger, get_audit_logger
from repositories.repositories_sa import AlertaRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class AlertaService:
    @staticmethod
    def obtener_todas_las_alertas() -> dict:
        alertas = {"clientes": [], "internas": []}

        rentas = AlertaRepositorySA.obtener_rentas_por_vencer()
        for r in rentas:
            mensaje = (
                f"Hola {r['nombre_completo']}, te saludamos de Dinamo Rent a Car. "
                f"Te recordamos que la renta del vehículo {r['placa']} finaliza "
                f"el {r['fecha_retorno']} a las {str(r['hora_retorno'])[:5]}. "
                "¡Por favor confírmanos tu hora de entrega para esperarte!"
            )

            alertas["clientes"].append(
                {
                    "titulo": f"Renta por vencer - {r['placa']}",
                    "cliente": r["nombre_completo"],
                    "celular": r["celular"],
                    "fecha": f"{r['fecha_retorno']} {str(r['hora_retorno'])[:5]}",
                    "mensaje_whatsapp": mensaje,
                }
            )

        docs = AlertaRepositorySA.obtener_documentos_por_vencer()
        for d in docs:
            texto = f"El vehículo {d['placa']} ({d['marca']}) tiene documentos próximos a vencer:\n"
            if d.get("vencimiento_soat"):
                texto += f"  SOAT: {d['vencimiento_soat']}\n"
            if d.get("vencimiento_tecnico"):
                texto += f"  Tecno-mecánica: {d['vencimiento_tecnico']}"

            alertas["internas"].append(
                {
                    "titulo": f"Documentos por Vencer - {d['placa']}",
                    "nivel": "Crítico",
                    "descripcion": texto,
                }
            )

        mantenimientos = AlertaRepositorySA.obtener_mantenimientos_proximos()
        for m in mantenimientos:
            faltan = m["proximo_aceite"] - m["kilometraje"]
            alertas["internas"].append(
                {
                    "titulo": f"Cambio de Aceite - {m['placa']}",
                    "nivel": "Advertencia",
                    "descripcion": f"Faltan {faltan:,.0f} km para el próximo cambio de aceite. (Actual: {m['kilometraje']})",
                }
            )

        return alertas
