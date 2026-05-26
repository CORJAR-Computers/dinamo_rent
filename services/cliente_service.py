"""Client service."""

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
            datos_upd = {k: v for k, v in datos.items() if k != "id"}
            update_data = ClienteUpdate(id=cliente_id, **datos_upd)
            ClienteRepositorySA.actualizar(update_data)
        else:
            ClienteRepositorySA.insertar(cliente_validado)

        audit.info("Cliente guardado: %s (%s)", datos.get("nombres"), datos.get("no_doc"))

    @staticmethod
    def obtener_opciones_geograficas() -> dict:
        from core.config import PAISES_DEFECTO

        paises_db = ClienteRepositorySA.obtener_valores_unicos("pais")
        regiones_db = ClienteRepositorySA.obtener_valores_unicos("estado_region")
        ciudades_db = ClienteRepositorySA.obtener_valores_unicos("ciudad")

        paises_combinados = sorted(list(set(PAISES_DEFECTO + paises_db)))

        return {"paises": paises_combinados, "regiones": regiones_db, "ciudades": ciudades_db}

    @staticmethod
    def obtener_regiones_por_pais(pais: str) -> List[str]:
        return ClienteRepositorySA.obtener_regiones_por_pais(pais)

    @staticmethod
    def obtener_ciudades_por_region(pais: str, region: str) -> List[str]:
        return ClienteRepositorySA.obtener_ciudades_por_region(pais, region)
