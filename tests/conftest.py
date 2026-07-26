import os
import sys
import pytest
from pathlib import Path

# ── sys.path ─────────────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

# ── Qt: forzar modo offscreen ANTES de importar PySide6 ─────────────────────
# Permite correr tests de UI sin display físico ni xvfb.
# Producción usa Firebird; CI usa SQLite sólo para las pruebas.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false")
os.environ.setdefault("DINAMO_DB_ENGINE", "sqlite")

from core import config  # noqa: E402

config.DB_PATH = ":memory:"

from core.database_sa import get_engine, SessionLocal, init_db  # noqa: E402


# ── QApplication singleton ────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def qapp():
    """QApplication singleton compartida por toda la sesión de tests."""
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # No llamar app.quit() — puede romper otros tests que aún corren


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Crea todas las tablas en la BD en memoria para la sesión de tests."""
    init_db()
    yield
    from core.models import Base

    Base.metadata.drop_all(bind=get_engine())


@pytest.fixture
def db_session():
    """Retorna una sesión nueva y hace rollback al finalizar el test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
