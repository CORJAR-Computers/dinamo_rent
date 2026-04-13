"""
auto_service.py — Servicio de Vehículos

Extraido de services.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict
import datetime

from core.config import DIAS_ALERTA_SOAT, DIAS_ALERTA_TECNICO, KM_ALERTA_ACEITE_PREV
from core.exceptions import NegocioError, ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import validar_placa
from core.schemas import AutoCreate, AutoUpdate
from repositories.repositories_sa import AutoRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class AutoService:

    @staticmethod
    def listar() -> List[Dict]:
        return AutoRepositorySA.obtener_todos()

    @staticmethod
    def listar_disponibles() -> List[Dict]:
        return AutoRepositorySA.obtener_disponibles()

    @staticmethod
    def obtener(placa: str) -> Dict:
        placa = validar_placa(placa)
        auto = AutoRepositorySA.obtener_por_placa(placa)
        if not auto:
            raise NegocioError(f"Vehículo {placa} no encontrado.")
        return auto

    @staticmethod
    def guardar(datos: dict) -> None:
        placa = validar_placa(datos.get("placa", ""))
        datos["placa"] = placa

        try:
            auto_validado = AutoCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de vehículo inválidos: {str(e)}")

        if AutoRepositorySA.existe(placa):
            update_data = AutoUpdate(placa=placa, **datos)
            AutoRepositorySA.actualizar(update_data)
            audit.info("Auto actualizado: %s por usuario del sistema", placa)
        else:
            AutoRepositorySA.insertar(auto_validado)
            audit.info("Auto creado: %s", placa)

    @staticmethod
    def obtener_alertas() -> List[Dict]:
        alertas: List[Dict] = []
        hoy = datetime.date.today()

        for alerta in AutoRepositorySA.obtener_alertas_flota():
            tipo = alerta.get('tipo')

            if tipo == 'Aceite':
                km_act = alerta.get('km_actual', 0)
                km_prox = alerta.get('km_proximo', 0)
                estado = "CRÍTICO" if km_act >= km_prox else "Pronto"
                alertas.append({
                    "placa": alerta['placa'],
                    "tipo": "Aceite",
                    "detalle": f"{km_act:,.0f}/{km_prox:,.0f} km",
                    "estado": estado,
                })
            elif tipo in ['SOAT', 'Tecno-mecánica']:
                dias = alerta.get('dias_restantes', 0)
                if dias < 0:
                    estado = "VENCIDO"
                else:
                    estado = f"{dias} días"

                doc_tipo = tipo.replace('-mecánica', '').replace('Tecno', 'Tecno')
                alertas.append({
                    "placa": alerta['placa'],
                    "tipo": doc_tipo,
                    "detalle": str(alerta.get('vencimiento', '')),
                    "estado": estado,
                })

        return alertas
