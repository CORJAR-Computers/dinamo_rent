"""
database_sa.py — SQLAlchemy Database Layer for Dinamo Rent ERP

This module provides a modern SQLAlchemy 2.0 database layer with:
- Session management with context managers
- Connection pooling
- Support for both MySQL and SQLite
- Backward compatibility with existing code

Usage:
    from core.database_sa import get_session, SessionLocal
    from core.models import Base, Usuario, Auto
    
    # Get a session
    with get_session() as session:
        users = session.query(Usuario).all()
"""
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, DeclarativeBase
from sqlalchemy.pool import StaticPool, QueuePool

from core.config import DB_ENGINE, DB_MYSQL, DB_PATH
from core.models import Base
from core.logger import get_logger

log = get_logger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

def _get_database_url() -> str:
    """Generate database URL from configuration."""
    if DB_ENGINE == "mysql":
        cfg = DB_MYSQL
        password_part = f":{cfg['password']}" if cfg['password'] else ""
        return (
            f"mysql+pymysql://{cfg['user']}{password_part}"
            f"@{cfg['host']}:{cfg['port']}/{cfg['database']}"
            f"?charset=utf8mb4"
        )
    else:
        return f"sqlite:///{DB_PATH}"


def _create_engine_instance():
    """Create SQLAlchemy engine with appropriate configuration."""
    url = _get_database_url()
    
    if DB_ENGINE == "mysql":
        # MySQL with connection pooling
        engine = create_engine(
            url,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections every hour
            echo=False,
        )
    else:
        # SQLite with foreign keys enabled
        engine = create_engine(
            url,
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
            echo=False,
        )
        
        # Enable foreign keys for SQLite
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()
    
    return engine


# Create the engine
engine = _create_engine_instance()

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


# ═══════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

def get_db_session() -> Session:
    """
    Get a new database session.
    Remember to close it when done!
    
    Usage:
        session = get_db_session()
        try:
            # do work
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    """
    return SessionLocal()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Automatically commits on success, rollbacks on error.
    
    Usage:
        with get_session() as session:
            users = session.query(Usuario).all()
            # session.commit() is automatic
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════
# DATABASE INITIALIZATION
# ═══════════════════════════════════════════════════════════════════════════

def init_db(drop: bool = False) -> None:
    """
    Initialize database tables.
    
    Args:
        drop: If True, drops all tables first (DANGEROUS!)
    """
    if drop:
        log.warning("DROPPING ALL TABLES!")
        Base.metadata.drop_all(bind=engine)
    
    Base.metadata.create_all(bind=engine)
    log.info("Database tables created successfully")


def check_connection() -> tuple[bool, str]:
    """
    Test database connection.

    Returns:
        Tuple of (success: bool, message: str)
    """
    from sqlalchemy import text
    
    try:
        with get_session() as session:
            if DB_ENGINE == "mysql":
                result = session.execute(
                    text("SELECT VERSION() as version")
                )
                version = result.scalar()
                return True, f"MySQL {version} - Connection successful"
            else:
                result = session.execute(
                    text("SELECT sqlite_version()")
                )
                version = result.scalar()
                return True, f"SQLite {version} - Connection successful"
    except Exception as e:
        return False, f"Connection failed: {str(e)}"


# ═══════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY (Bridge to old code)
# ═══════════════════════════════════════════════════════════════════════════

def get_session_legacy() -> dict:
    """
    Legacy compatibility function.
    Returns a dict-based row compatible with old repository code.
    
    This allows gradual migration from old to new system.
    """
    from sqlalchemy import text
    
    session = SessionLocal()
    
    # Create a wrapper that returns dict-based results
    class LegacySession:
        def __init__(self, sa_session):
            self._session = sa_session
        
        def execute(self, sql, params=None):
            result = self._session.execute(text(sql), params or {})
            # Convert to list of dicts for compatibility
            if result.returns_rows:
                columns = result.keys()
                return [dict(zip(columns, row)) for row in result.fetchall()]
            return []
        
        def commit(self):
            self._session.commit()
        
        def rollback(self):
            self._session.rollback()
        
        def close(self):
            self._session.close()
        
        def __enter__(self):
            return self
        
        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_type:
                self.rollback()
            else:
                self.commit()
            self.close()
    
    return LegacySession(session)


# ═══════════════════════════════════════════════════════════════════════════
# INITIALIZATION ON IMPORT
# ═══════════════════════════════════════════════════════════════════════════

# Auto-initialize database on import (optional, can be disabled)
try:
    # Uncomment to auto-create tables on import
    # init_db()
    pass
except Exception as e:
    log.error(f"Failed to initialize database: {e}")
