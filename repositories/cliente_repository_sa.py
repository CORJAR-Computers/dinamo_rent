"""
cliente_repository_sa.py — Repositorio de Clientes

F1C: Extraído y completado para separación de responsabilidades.
"""

from typing import List, Dict

from sqlalchemy import or_

from core.database_sa import get_session
from core.models import Cliente
from core.schemas import ClienteCreate, ClienteUpdate
from core.exceptions import RegistroNoEncontrado
from core.logger import get_logger

log = get_logger(__name__)


class ClienteRepositorySA:
    @staticmethod
    def buscar(termino: str = "") -> List[Dict]:
        """Busca clientes por nombre, documento, celular o email."""
        with get_session() as session:
            query = session.query(Cliente)
            if termino:
                like = f"%{termino}%"
                query = query.filter(
                    or_(
                        Cliente.nombre_completo.like(like),
                        Cliente.no_doc.like(like),
                        Cliente.celular.like(like),
                        Cliente.email.like(like),
                    )
                )
            clientes = query.order_by(Cliente.nombre_completo).all()
            return [ClienteRepositorySA._to_dict(c) for c in clientes]

    @staticmethod
    def obtener_por_id(id_cliente: int) -> Dict:
        """Obtiene un cliente por su ID."""
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.id == id_cliente).first()
            if not cliente:
                raise RegistroNoEncontrado(f"Cliente #{id_cliente} no encontrado.")
            return ClienteRepositorySA._to_dict(cliente)

    @staticmethod
    def obtener_valores_unicos(campo: str) -> List[str]:
        """Obtiene una lista de valores únicos para un campo específico (ej. pais, ciudad)."""
        if not hasattr(Cliente, campo):
            return []

        with get_session() as session:
            columna = getattr(Cliente, campo)
            resultados = (
                session.query(columna)
                .filter(columna.isnot(None), columna != "")
                .distinct()
                .order_by(columna)
                .all()
            )
            return [r[0] for r in resultados]

    @staticmethod
    def obtener_regiones_por_pais(pais: str) -> List[str]:
        with get_session() as session:
            resultados = (
                session.query(Cliente.estado_region)
                .filter(
                    Cliente.pais == pais,
                    Cliente.estado_region.isnot(None),
                    Cliente.estado_region != "",
                )
                .distinct()
                .order_by(Cliente.estado_region)
                .all()
            )
            return [r[0] for r in resultados]

    @staticmethod
    def obtener_ciudades_por_region(pais: str, region: str) -> List[str]:
        with get_session() as session:
            resultados = (
                session.query(Cliente.ciudad)
                .filter(
                    Cliente.pais == pais,
                    Cliente.estado_region == region,
                    Cliente.ciudad.isnot(None),
                    Cliente.ciudad != "",
                )
                .distinct()
                .order_by(Cliente.ciudad)
                .all()
            )
            return [r[0] for r in resultados]

    @staticmethod
    def insertar(datos: ClienteCreate) -> int:
        """Inserta un nuevo cliente. Retorna el ID."""
        with get_session() as session:
            nuevo_cliente = Cliente(
                tipo_doc=datos.tipo_doc,
                no_doc=datos.no_doc,
                nombres=datos.nombres,
                apellidos=datos.apellidos,
                nombre_completo=datos.nombre_completo,
                celular=datos.celular,
                celular2=datos.celular2,
                email=datos.email,
                ciudad=datos.ciudad,
                estado_region=datos.estado_region,
                pais=datos.pais,
                nacionalidad=datos.nacionalidad,
                dir_residencia=datos.dir_residencia,
                dir_temporal=datos.dir_temporal,
                hotel=datos.hotel,
                habitacion=datos.habitacion,
                no_licencia=datos.no_licencia,
                tipo_licencia=datos.tipo_licencia,
                vencimiento_licencia=datos.vencimiento_licencia,
                estado=datos.estado,
            )
            session.add(nuevo_cliente)
            session.flush()
            log.info("Cliente creado: id=%s, nombre=%s", nuevo_cliente.id, datos.nombre_completo)
            return nuevo_cliente.id

    @staticmethod
    def actualizar(datos: ClienteUpdate) -> None:
        """
        Actualiza los campos de un cliente existente.

        F1C: ClienteUpdate ahora incluye id como campo requerido
        para identificar el registro a actualizar.
        """
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.id == datos.id).first()
            if not cliente:
                raise RegistroNoEncontrado(f"Cliente #{datos.id} no encontrado.")

            update_fields = datos.model_dump(exclude_unset=True, exclude={"id"})
            for campo, valor in update_fields.items():
                if hasattr(cliente, campo):
                    setattr(cliente, campo, valor)

            log.info("Cliente actualizado: id=%s", datos.id)

    @staticmethod
    def _to_dict(cliente: Cliente) -> Dict:
        return {
            "id": cliente.id,
            "tipo_doc": cliente.tipo_doc,
            "no_doc": cliente.no_doc,
            "nombres": cliente.nombres,
            "apellidos": cliente.apellidos,
            "nombre_completo": cliente.nombre_completo,
            "celular": cliente.celular,
            "celular2": cliente.celular2,
            "email": cliente.email,
            "ciudad": cliente.ciudad,
            "estado_region": cliente.estado_region,
            "pais": cliente.pais,
            "nacionalidad": cliente.nacionalidad,
            "dir_residencia": cliente.dir_residencia,
            "dir_temporal": cliente.dir_temporal,
            "hotel": cliente.hotel,
            "habitacion": cliente.habitacion,
            "no_licencia": cliente.no_licencia,
            "tipo_licencia": cliente.tipo_licencia,
            "vencimiento_licencia": cliente.vencimiento_licencia,
            "estado": cliente.estado,
            "created_at": cliente.created_at,
            "updated_at": cliente.updated_at,
        }
