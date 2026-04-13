"""
cliente_service.py — Servicio de Clientes

Extraido de services.py como parte de F1B (Reestructuración de Services).
"""
from typing import List, Dict

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import validar_documento, requerir
from core.schemas import ClienteCreate, ClienteUpdate
from repositories.repositories_sa import ClienteRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class ClienteService:

    @staticmethod
    def buscar(termino: str = "") -> List[Dict]:
        return ClienteRepositorySA.buscar(termino)

    @staticmethod
    def obtener(id_cliente: int) -> Dict:
        return ClienteRepositorySA.obtener_por_id(id_cliente)

    @staticmethod
    def guardar(datos: dict) -> None:
        no_doc = datos.get("no_doc", "")
        tipo_doc = datos.get("tipo_doc", "Cédula")
        if no_doc:
            validar_documento(no_doc, tipo_doc)

        requerir(datos.get("nombres"), "Nombres")

        try:
            cliente_validado = ClienteCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de cliente inválidos: {str(e)}")

        cliente_id = datos.get("id")
        if cliente_id:
            update_data = ClienteUpdate(id=cliente_id, **datos)
            ClienteRepositorySA.actualizar(update_data)
        else:
            ClienteRepositorySA.insertar(cliente_validado)

        audit.info("Cliente guardado: %s (%s)", datos.get("nombres"), datos.get("no_doc"))
