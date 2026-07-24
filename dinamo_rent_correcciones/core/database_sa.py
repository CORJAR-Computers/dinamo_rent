"""
SQLAlchemy database layer with auto-migrations. Dual MySQL/SQLite support.

Engine and session factory are lazily initialized (deferred until first use)
to speed up module import time by ~300-500ms.

Mejoras aplicadas:
  - SEC-04: get_session() ahora solo hace commit si hay cambios pendientes
  - CODE-09: pool_size y max_overflow leídos desde config.py
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session as SASession
from sqlalchemy.pool import StaticPool, QueuePool

from core.config import (
    DB_ENGINE,
    DB_MYSQL,
    DB_PATH,
    DB_POOL_SIZE,
    DB_POOL_MAX_OVERFLOW,
    DB_POOL_PRE_PING,
)
from core.logger import get_logger

log = get_logger(__name__)


# ── Lazy singleton holders ──────────────────────────────────────────────────

_engine = None
_SessionMaker = None


def _get_database_url() -> str:
    if DB_ENGINE == "mysql":
        cfg = DB_MYSQL
        password_part = f":{cfg['password']}" if cfg["password"] else ""
        return (
            f"mysql+pymysql://{cfg['user']}{password_part}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
            f"?charset=utf8mb4"
        )
    return f"sqlite:///{DB_PATH}"


def _create_engine_instance():
    url = _get_database_url()

    if DB_ENGINE == "mysql":
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_POOL_MAX_OVERFLOW,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=DB_POOL_PRE_PING,
            echo=False,
        )
    else:
        engine = create_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


def get_engine():
    """Lazy engine initializer — engine is created on first call."""
    global _engine
    if _engine is None:
        _engine = _create_engine_instance()
    return _engine


class _LazySessionMaker:
    """Lazy sessionmaker wrapper — defers initialization until first call."""

    def __init__(self):
        self._maker = None

    def __call__(self):
        if self._maker is None:
            from sqlalchemy.orm import sessionmaker

            self._maker = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=get_engine(),
                expire_on_commit=False,
            )
        return self._maker()


# Module-level session factory (backward compatible — works as callable)
SessionLocal = _LazySessionMaker()


@contextmanager
def get_session() -> Generator[SASession, None, None]:
    """Context manager de sesión SQLAlchemy.

    SEC-04: Solo hace commit si hay cambios pendientes en la sesión
    (session.dirty, session.new, o session.deleted no vacíos). Esto evita
    commits vacíos innecesarios y posibles inconsistencias.
    """
    session = SessionLocal()
    try:
        yield session
        # Solo cometer si hay cambios pendientes
        if session.dirty or session.new or session.deleted:
            session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ── Migrations ──────────────────────────────────────────────────────────────

_MIGRATIONS_F1A = [
    (
        "clientes.updated_at",
        "ALTER TABLE clientes ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    (
        "reservas.updated_at",
        "ALTER TABLE reservas ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    (
        "mantenimiento_vehiculos.updated_at",
        "ALTER TABLE mantenimiento_vehiculos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    (
        "comparendos.updated_at",
        "ALTER TABLE comparendos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    (
        "pagos.updated_at",
        "ALTER TABLE pagos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    (
        "gastos.updated_at",
        "ALTER TABLE gastos ADD COLUMN updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP",
    ),
    ("gastos.placa", "ALTER TABLE gastos ADD COLUMN placa VARCHAR(20) NULL"),
]

_MIGRATIONS_INDEXES = [
    ("ix_gastos_placa", "CREATE INDEX ix_gastos_placa ON gastos (placa)"),
]


def _apply_migrations() -> None:
    eng = get_engine()
    applied = 0
    skipped = 0

    for desc, sql in _MIGRATIONS_F1A:
        try:
            with eng.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            applied += 1
            log.info(f"Migracion aplicada: {desc}")
        except Exception as e:
            err_msg = str(e).lower()
            if "duplicate column" in err_msg:
                skipped += 1
                log.debug(f"Migracion omitida (ya existe): {desc}")
            else:
                log.warning(f"Migracion fallida: {desc} — {e}")

    for desc, sql in _MIGRATIONS_INDEXES:
        try:
            with eng.connect() as conn:
                conn.execute(text(sql))
                conn.commit()
            applied += 1
            log.info(f"Indice creado: {desc}")
        except Exception as e:
            err_msg = str(e).lower()
            if "duplicate" in err_msg or "already exists" in err_msg:
                skipped += 1
                log.debug(f"Indice omitido (ya existe): {desc}")
            else:
                log.warning(f"Indice fallido: {desc} — {e}")

    if applied > 0:
        log.info(f"Migraciones: {applied} aplicada(s), {skipped} omitida(s)")
    elif skipped > 0:
        log.info(f"Migraciones: esquema sincronizado ({skipped} verificaciones OK)")
    else:
        log.info("Migraciones: sin cambios necesarios")


def init_db(drop: bool = False) -> None:
    """Initialize database — imports models lazily."""
    from core.models import Base

    eng = get_engine()

    if drop:
        log.warning("DROPPING ALL TABLES!")
        Base.metadata.drop_all(bind=eng)

    Base.metadata.create_all(bind=eng)
    log.info("Database tables created successfully")
    _apply_migrations()


def check_connection() -> tuple[bool, str]:
    try:
        with get_session() as session:
            if DB_ENGINE == "mysql":
                result = session.execute(text("SELECT VERSION() as version"))
                version = result.scalar()
                return True, f"MySQL {version} - Connection successful"
            else:
                result = session.execute(text("SELECT sqlite_version()"))
                version = result.scalar()
                return True, f"SQLite {version} - Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


def reset_database_connection() -> None:
    """Disposes the current engine and resets deferred singletons to allow reconnection."""
    global _engine, _SessionMaker
    if _engine is not None:
        try:
            _engine.dispose()
            log.info("Active database engine disposed successfully")
        except Exception as e:
            log.warning(f"Error disposing database engine: {e}")
    _engine = None
    _SessionMaker = None
    log.info("Database connection singletons reset successfully")
