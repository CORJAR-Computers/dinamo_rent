"""
usuario_repository_sa.py — Usuario Repository with SQLAlchemy

This is an EXAMPLE of how repositories should look after migration to SQLAlchemy.
Shows best practices and the new pattern.

Compare with the old pattern in repositories/usuario_repository.py
"""
from typing import Optional, List
from datetime import datetime

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from core.database_sa import get_session
from core.models import Usuario
from core.schemas import UsuarioCreate, UsuarioUpdate
from core.exceptions import RegistroNoEncontrado, DuplicadoError
from core.logger import get_logger
from core.security import SecurityManager

log = get_logger(__name__)


class UsuarioRepositorySA:
    """
    Modern repository using SQLAlchemy 2.0 patterns.
    
    Features:
    - Type hints throughout
    - Pydantic schema validation
    - SQLAlchemy ORM
    - Context managers for sessions
    """

    @staticmethod
    def obtener_todos() -> List[dict]:
        """Get all users as dict list (backward compatible)."""
        with get_session() as session:
            usuarios = session.query(Usuario).all()
            return [
                {
                    'id': u.id,
                    'username': u.username,
                    'nombre': u.nombre,
                    'rol': u.rol,
                    'email': u.email,
                    'activo': u.activo,
                    'intentos_fallidos': u.intentos_fallidos,
                    'ultimo_acceso': u.ultimo_acceso,
                    'created_at': u.created_at,
                }
                for u in usuarios
            ]

    @staticmethod
    def obtener_por_username(username: str) -> Optional[dict]:
        """Get user by username."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(
                Usuario.username == username
            ).first()
            
            if not usuario:
                return None
            
            return {
                'id': usuario.id,
                'username': usuario.username,
                'password': usuario.password,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'email': usuario.email,
                'activo': usuario.activo,
            }

    @staticmethod
    def obtener_por_id(usuario_id: int) -> dict:
        """Get user by ID."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(
                Usuario.id == usuario_id
            ).first()
            
            if not usuario:
                raise RegistroNoEncontrado(f"Usuario #{usuario_id} no encontrado.")
            
            return {
                'id': usuario.id,
                'username': usuario.username,
                'nombre': usuario.nombre,
                'rol': usuario.rol,
                'email': usuario.email,
                'activo': usuario.activo,
            }

    @staticmethod
    def insertar(datos: UsuarioCreate) -> int:
        """
        Create new user with Pydantic validation.
        
        Args:
            datos: UsuarioCreate schema with validated data
            
        Returns:
            New user ID
        """
        with get_session() as session:
            # Check for duplicate username
            existing = session.query(Usuario).filter(
                Usuario.username == datos.username
            ).first()
            
            if existing:
                raise DuplicadoError(f"El usuario '{datos.username}' ya existe.")
            
            # Create new user
            nuevo_usuario = Usuario(
                username=datos.username.strip(),
                password=SecurityManager.hash_password(datos.password_raw),
                nombre=datos.nombre.strip() if datos.nombre else None,
                rol=datos.rol or 'Operador',
                email=datos.email.strip() if datos.email else None,
                activo=1 if datos.activo else 0,
            )
            
            session.add(nuevo_usuario)
            session.flush()  # Get ID without committing
            
            log.info("Usuario creado: %s (rol=%s)", datos.username, datos.rol)
            return nuevo_usuario.id

    @staticmethod
    def actualizar(datos: UsuarioUpdate) -> None:
        """Update user data."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(
                Usuario.username == datos.username
            ).first()
            
            if not usuario:
                raise RegistroNoEncontrado(f"Usuario '{datos.username}' no encontrado.")
            
            # Update fields if provided
            if datos.nombre is not None:
                usuario.nombre = datos.nombre.strip()
            if datos.rol is not None:
                usuario.rol = datos.rol
            if datos.email is not None:
                usuario.email = datos.email.strip()
            if datos.activo is not None:
                usuario.activo = 1 if datos.activo else 0
            if datos.password_raw:
                usuario.password = SecurityManager.hash_password(datos.password_raw)
            
            log.info("Usuario actualizado: %s", datos.username)

    @staticmethod
    def eliminar(username: str) -> None:
        """Delete user (soft or hard delete)."""
        with get_session() as session:
            usuario = session.query(Usuario).filter(
                Usuario.username == username
            ).first()
            
            if not usuario:
                raise RegistroNoEncontrado(f"Usuario '{username}' no encontrado.")
            
            if username == "admin":
                from core.exceptions import NegocioError
                raise NegocioError(mensaje_usuario="No se puede eliminar el Administrador Principal.")
            
            session.delete(usuario)
            log.info("Usuario eliminado: %s", username)

    @staticmethod
    def registrar_acceso(username: str) -> None:
        """Update last login timestamp."""
        with get_session() as session:
            session.query(Usuario).filter(
                Usuario.username == username
            ).update({
                'ultimo_acceso': datetime.utcnow(),
                'intentos_fallidos': 0
            })

    @staticmethod
    def incrementar_intentos_fallidos(username: str) -> None:
        """Increment failed login attempts."""
        with get_session() as session:
            session.query(Usuario).filter(
                Usuario.username == username
            ).update({
                'intentos_fallidos': Usuario.intentos_fallidos + 1
            })

    @staticmethod
    def buscar_por_rol(rol: str) -> List[dict]:
        """Get all users by role."""
        with get_session() as session:
            usuarios = session.query(Usuario).filter(
                Usuario.rol == rol,
                Usuario.activo == 1
            ).order_by(Usuario.username).all()
            
            return [
                {
                    'id': u.id,
                    'username': u.username,
                    'nombre': u.nombre,
                    'rol': u.rol,
                    'email': u.email,
                }
                for u in usuarios
            ]

    @staticmethod
    def contar_activos() -> int:
        """Count active users."""
        with get_session() as session:
            return session.query(Usuario).filter(
                Usuario.activo == 1
            ).count()


# ═══════════════════════════════════════════════════════════════════════════
# USAGE EXAMPLES
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    """Example usage demonstrating the new pattern."""
    
    # Example 1: Create user with Pydantic validation
    from core.schemas import UsuarioCreate
    
    nuevo_usuario_data = UsuarioCreate(
        username="test_user",
        password_raw="secure_password_123",
        nombre="Test User",
        rol="Operador",
        email="test@example.com"
    )
    
    try:
        user_id = UsuarioRepositorySA.insertar(nuevo_usuario_data)
        print(f"Usuario creado con ID: {user_id}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Example 2: Get user
    usuario = UsuarioRepositorySA.obtener_por_username("test_user")
    if usuario:
        print(f"Found user: {usuario['nombre']}")
    
    # Example 3: List all users
    todos = UsuarioRepositorySA.obtener_todos()
    print(f"Total users: {len(todos)}")
