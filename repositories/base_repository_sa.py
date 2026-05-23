"""
base_repository_sa.py — Base Repository for SQLAlchemy

F1C: Clase base compartida por todos los repositorios.
F1D: Agregado session_scope helper para soporte de UnitOfWork.

Centraliza imports comunes y provee el contexto de sesión.
Todos los repositorios usan session_scope(session) para soportar
tanto operaciones independientes como transaccionales.
"""


from core.database_sa import get_session
from core.logger import get_logger

log = get_logger(__name__)


class BaseRepositorySA:
    """
    Clase base para todos los repositorios SQLAlchemy.

    Provee:
      - Acceso a get_session() vía herencia
      - Acceso a session_scope() para soporte de UnitOfWork
      - Métodos utilitarios comunes
      - Patrón consistente de _to_dict

    Todos los repositorios heredan de esta clase y usan @staticmethod
    para mantener compatibilidad con el código existente.
    """

    # Subclases deben definir esto
    model_class = None

    @staticmethod
    def _session():
        """Retorna un context manager de sesión SQLAlchemy."""
        return get_session()
