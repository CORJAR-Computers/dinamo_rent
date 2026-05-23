"""Vehicle inspection service."""

from typing import List, Dict

from core.exceptions import ValidacionError
from core.logger import get_logger, get_audit_logger
from core.validators import requerir
from core.schemas import InspeccionCreate
from repositories.repositories_sa import InspeccionRepositorySA

log = get_logger(__name__)
audit = get_audit_logger()


class InspeccionService:

    @staticmethod
    def listar_por_renta(id_renta: int) -> List[Dict]:
        return InspeccionRepositorySA.obtener_por_renta(id_renta)

    @staticmethod
    def registrar(datos: dict) -> int:
        requerir(datos.get("id_renta"), "ID de Renta")
        requerir(datos.get("tipo"), "Tipo de Inspección")
        requerir(datos.get("kilometraje"), "Kilometraje")

        try:
            inspeccion_validada = InspeccionCreate(**datos)
        except Exception as e:
            raise ValidacionError(f"Datos de inspección inválidos: {str(e)}")

        id_inspeccion = InspeccionRepositorySA.insertar(inspeccion_validada)
        audit.info("Inspección (%s) registrada para la renta #%s", datos["tipo"], datos["id_renta"])
        return id_inspeccion
