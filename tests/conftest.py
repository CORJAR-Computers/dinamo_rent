import os
import sys
import pytest
from pathlib import Path

# Add project root to sys.path so modules can be imported
sys.path.insert(0, str(Path(__file__).parent.parent))

# Set env vars for testing database (SQLite in memory)
os.environ["DINAMO_DB_ENGINE"] = "sqlite"

from core import config
# Override DB_PATH to use an in-memory database
config.DB_PATH = ":memory:"

from core.database_sa import engine, Base, SessionLocal, init_db

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """Create all tables in the in-memory database for testing."""
    init_db()
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Returns a new session for a test and rolls back changes after the test."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()
