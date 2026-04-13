"""
cliente_repository_sa.py — Cliente Repository with SQLAlchemy 2.0
"""
from typing import List, Optional, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from core.database_sa import get_session
from core.models import Cliente
from core.schemas import ClienteCreate, ClienteUpdate
from core.exceptions import RegistroNoEncontrado, DuplicadoError
from core.logger import get_logger

log = get_logger(__name__)


class ClienteRepositorySA:

    @staticmethod
    def obtener_todos() -> List[Dict]:
        with get_session() as session:
            clientes = session.query(Cliente).order_by(Cliente.nombre_completo).all()
            return [ClienteRepositorySA._to_dict(c) for c in clientes]

    @staticmethod
    def obtener_por_id(cliente_id: int) -> Optional[Dict]:
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.id == cliente_id).first()
            return ClienteRepositorySA._to_dict(cliente) if cliente else None

    @staticmethod
    def buscar(termino: str = "") -> List[Dict]:
        with get_session() as session:
            query = session.query(Cliente)
            
            if termino:
                termino_busqueda = f"%{termino}%"
                query = query.filter(
                    or_(
                        Cliente.nombre_completo.ilike(termino_busqueda),
                        Cliente.no_doc.ilike(termino_busqueda),
                        Cliente.celular.ilike(termino_busqueda),
                        Cliente.email.ilike(termino_busqueda),
                    )
                )
            
            clientes = query.order_by(Cliente.nombre_completo).all()
            return [ClienteRepositorySA._to_dict(c) for c in clientes]

    @staticmethod
    def obtener_por_documento(no_doc: str) -> Optional[Dict]:
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.no_doc == no_doc).first()
            return ClienteRepositorySA._to_dict(cliente) if cliente else None

    @staticmethod
    def insertar(datos: ClienteCreate) -> int:
        with get_session() as session:
            # Check for duplicate document
            if datos.no_doc:
                existing = session.query(Cliente).filter(Cliente.no_doc == datos.no_doc).first()
                if existing:
                    raise DuplicadoError(f"Cliente con documento '{datos.no_doc}' ya existe.")
            
            nuevo_cliente = Cliente(
                tipo_doc=datos.tipo_doc,
                no_doc=datos.no_doc,
                nombres=datos.nombres,
                apellidos=datos.apellidos,
                nombre_completo=datos.nombre_completo or f"{datos.nombres or ''} {datos.apellidos or ''}".strip(),
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
            log.info("Cliente creado: %s (%s)", nuevo_cliente.nombre_completo, datos.no_doc)
            return nuevo_cliente.id

    @staticmethod
    def actualizar(datos: ClienteUpdate) -> None:
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.id == datos.id).first()
            
            if not cliente:
                raise RegistroNoEncontrado(f"Cliente #{datos.id} no encontrado.")
            
            update_fields = datos.model_dump(exclude_unset=True, exclude={'id'})
            for field, value in update_fields.items():
                if hasattr(cliente, field):
                    setattr(cliente, field, value)
            
            # Update nombre_completo if nombres/apellidos changed
            if datos.nombres or datos.apellidos:
                cliente.nombre_completo = f"{cliente.nombres or ''} {cliente.apellidos or ''}".strip()
            
            log.info("Cliente actualizado: %s", cliente.nombre_completo)

    @staticmethod
    def eliminar(cliente_id: int) -> None:
        with get_session() as session:
            cliente = session.query(Cliente).filter(Cliente.id == cliente_id).first()
            
            if not cliente:
                raise RegistroNoEncontrado(f"Cliente #{cliente_id} no encontrado.")
            
            session.delete(cliente)
            log.info("Cliente eliminado: %s", cliente.nombre_completo)

    @staticmethod
    def contar_por_estado() -> Dict[str, int]:
        with get_session() as session:
            resultados = session.query(Cliente.estado, func.count(Cliente.id)).group_by(Cliente.estado).all()
            return {estado: cantidad for estado, cantidad in resultados}

    @staticmethod
    def _to_dict(cliente: Cliente) -> Dict:
        return {
            'id': cliente.id,
            'tipo_doc': cliente.tipo_doc,
            'no_doc': cliente.no_doc,
            'nombres': cliente.nombres,
            'apellidos': cliente.apellidos,
            'nombre_completo': cliente.nombre_completo,
            'celular': cliente.celular,
            'celular2': cliente.celular2,
            'email': cliente.email,
            'ciudad': cliente.ciudad,
            'estado_region': cliente.estado_region,
            'pais': cliente.pais,
            'nacionalidad': cliente.nacionalidad,
            'dir_residencia': cliente.dir_residencia,
            'dir_temporal': cliente.dir_temporal,
            'hotel': cliente.hotel,
            'habitacion': cliente.habitacion,
            'no_licencia': cliente.no_licencia,
            'tipo_licencia': cliente.tipo_licencia,
            'vencimiento_licencia': cliente.vencimiento_licencia,
            'estado': cliente.estado,
            'created_at': cliente.created_at,
        }
