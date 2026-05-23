"""
unit_of_work.py — Patrón Unit of Work para transacciones atómicas

F1D: Implementación del patrón UnitOfWork para garantizar integridad
de datos en operaciones que afectan múltiples tablas.

PROBLEMA que resuelve:
  Las 5 operaciones críticas del sistema (crear renta, cerrar renta,
  cambio de vehículo, registrar mantenimiento, registrar pago) realizan
  múltiples escrituras en tablas diferentes usando sesiones separadas.
  Si la segunda escritura falla, la primera ya está commiteada → datos
  inconsistentes.

SOLUCIÓN:
  UnitOfWork provee UNA sesión compartida. Todas las operaciones dentro
  del bloque `with UnitOfWork() as uow:` usan la misma transacción.
  Si algo falla → rollback total. Si todo OK → commit atómico.

Uso en Servicios:
    with UnitOfWork() as uow:
        RentaRepositorySA.insertar(datos, session=uow.session)
        AutoRepositorySA.cambiar_estado(placa, "Rentado", session=uow.session)
        # auto-commit al salir del with, auto-rollback si hay excepción

Uso en Repositorios:
    @staticmethod
    def insertar(datos, session=None):
        with session_scope(session) as s:
            nueva = Renta(...)
            s.add(nueva)
            s.flush()
            return nueva.id
"""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy.orm import Session

from core.database_sa import SessionLocal, get_session
from core.logger import get_logger

log = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# UNIT OF WORK
# ═══════════════════════════════════════════════════════════════════════════

class UnitOfWork:
    """
    Context manager para operaciones transaccionales.

    Provee una sesión SQLAlchemy que se comparte entre múltiples
    llamadas a repositorios. Commit automático al salir sin errores,
    rollback automático si ocurre cualquier excepción.

    Ejemplo:
        with UnitOfWork() as uow:
            renta_id = RentaRepositorySA.insertar(datos, session=uow.session)
            AutoRepositorySA.cambiar_estado(placa, "Rentado", session=uow.session)
            # Si cambiar_estado falla → insertar también se revierte
            # Si todo OK → commit atómico de ambas operaciones
    """

    def __init__(self):
        self.session: Optional[Session] = None

    def __enter__(self) -> 'UnitOfWork':
        self.session = SessionLocal()
        log.debug("UnitOfWork: sesión creada (id=%s)", id(self.session))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                log.warning(
                    "UnitOfWork: rollback por excepción (%s: %s)",
                    exc_type.__name__ if exc_type else '', exc_val
                )
                self.session.rollback()
            else:
                self.session.commit()
                log.debug("UnitOfWork: commit exitoso")
        except Exception as e:
            # Si el commit falla, intentar rollback
            log.error("UnitOfWork: error en commit/rollback: %s", e)
            try:
                self.session.rollback()
            except Exception:
                pass
            raise
        finally:
            self.session.close()
            log.debug("UnitOfWork: sesión cerrada")

    def commit(self):
        """Commit manual (útil para operaciones por pasos)."""
        self.session.commit()

    def rollback(self):
        """Rollback manual (útil para validaciones en multi-paso)."""
        self.session.rollback()


# ═══════════════════════════════════════════════════════════════════════════
# SESSION SCOPE HELPER
# ═══════════════════════════════════════════════════════════════════════════

@contextmanager
def session_scope(session: Optional[Session] = None) -> Generator[Session, None, None]:
    """
    Context manager que provee una sesión SQLAlchemy.

    Si se pasa una sesión (desde UnitOfWork), la usa directamente sin
    gestionar commit/rollback (el UnitOfWork se encarga).

    Si no se pasa sesión, crea una nueva con get_session() que se
    auto-commitea/rollback al salir del bloque (comportamiento original).

    Uso en repositorios:
        @staticmethod
        def insertar(datos, session=None):
            with session_scope(session) as s:
                nueva = Modelo(...)
                s.add(nueva)
                s.flush()  # Flush para obtener IDs autogenerados
                return nueva.id

    Este patrón garantiza:
    - Backward compatibility: llamadas sin session funcionan igual que antes
    - Transacciones: llamadas con session de UnitOfWork comparten transacción
    - flush() vs commit(): flush envía SQL sin commit, permitiendo IDs
    """
    if session is not None:
        # Sesión proporcionada por UnitOfWork → no gestionar ciclo de vida
        yield session
    else:
        # Sin sesión → crear propia (comportamiento original)
        with get_session() as s:
            yield s
