"""
inspeccion_repository_sa.py — Repositorio de Inspecciones

"""

from typing import List, Dict

from core.database_sa import get_session
from core.models import Inspeccion
from core.schemas import InspeccionCreate
from core.logger import get_logger

log = get_logger(__name__)


class InspeccionRepositorySA:
    @staticmethod
    def obtener_por_renta(id_renta: int) -> List[Dict]:
        with get_session() as session:
            inspecciones = (
                session.query(Inspeccion)
                .filter(Inspeccion.id_renta == id_renta)
                .order_by(Inspeccion.fecha)
                .all()
            )

            return [InspeccionRepositorySA._to_dict(i) for i in inspecciones]

    @staticmethod
    def insertar(datos: InspeccionCreate) -> int:
        with get_session() as session:
            nueva_inspeccion = Inspeccion(
                id_renta=datos.id_renta,
                tipo=datos.tipo,
                kilometraje=datos.kilometraje,
                nivel_gasolina=datos.nivel_gasolina,
                limpieza=datos.limpieza,
                tiene_repuesto=1 if datos.tiene_repuesto else 0,
                tiene_gato_cruceta=1 if datos.tiene_gato_cruceta else 0,
                tiene_kit_carretera=1 if datos.tiene_kit_carretera else 0,
                tiene_documentos=1 if datos.tiene_documentos else 0,
                danos_carroceria=datos.danos_carroceria,
                observaciones=datos.observaciones,
            )

            session.add(nueva_inspeccion)
            session.flush()
            log.info("Inspeccion (%s) registrada para renta #%s", datos.tipo, datos.id_renta)
            return nueva_inspeccion.id

    @staticmethod
    def _to_dict(insp: Inspeccion) -> Dict:
        return {
            "id": insp.id,
            "id_renta": insp.id_renta,
            "tipo": insp.tipo,
            "fecha": insp.fecha,
            "kilometraje": insp.kilometraje,
            "nivel_gasolina": insp.nivel_gasolina,
            "limpieza": insp.limpieza,
            "tiene_repuesto": bool(insp.tiene_repuesto),
            "tiene_gato_cruceta": bool(insp.tiene_gato_cruceta),
            "tiene_kit_carretera": bool(insp.tiene_kit_carretera),
            "tiene_documentos": bool(insp.tiene_documentos),
            "danos_carroceria": insp.danos_carroceria,
            "observaciones": insp.observaciones,
        }
