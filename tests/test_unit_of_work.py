"""
test_unit_of_work.py — Unit tests for core/unit_of_work.py

Covers:
  UnitOfWork:        __enter__, __exit__ (commit/rollback/close),
                     manual commit(), manual rollback(), error handling
  session_scope:     With and without session, commit/rollback, flush

Strategy:
  - Uses an isolated in-memory SQLite engine per test (monkeypatched)
  - Patches both core.database_sa.SessionLocal AND core.unit_of_work.SessionLocal
    to ensure UnitOfWork uses the patched sessionmaker regardless of import order
  - Does NOT depend on the conftest.py global DB to avoid side effects
  - Tests operations on real SQLAlchemy models (Usuario, Auto)

Run: pytest tests/test_unit_of_work.py -v
"""

import pytest
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.models import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Helper: create a minimal isolated in-memory engine + sessionmaker
# ═══════════════════════════════════════════════════════════════════════════════

def _make_memory_engine():
    """Create an in-memory SQLite engine with foreign keys enabled."""
    eng = create_engine(
        "sqlite://",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
        echo=False,
    )

    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return eng


def _make_sessionmaker(eng=None):
    """Create a sessionmaker bound to the given engine (or a fresh one)."""
    if eng is None:
        eng = _make_memory_engine()
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=eng,
        expire_on_commit=False,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Fixture: patch SessionLocal in both database_sa AND unit_of_work
# ═══════════════════════════════════════════════════════════════════════════════
#
# unit_of_work.py imports SessionLocal at module load time:
#     from core.database_sa import SessionLocal, get_session
#
# This creates a local reference `unit_of_work.SessionLocal` that is NOT affected
# by subsequent monkeypatches on `core.database_sa.SessionLocal`. To ensure
# UnitOfWork uses the patched sessionmaker, we must patch both locations.
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def test_db(monkeypatch):
    """Create an isolated in-memory DB with tables, patch both SessionLocal refs."""
    # Import the module first so the attribute exists for monkeypatch
    import core.unit_of_work as uow_module

    eng = _make_memory_engine()
    Base.metadata.create_all(bind=eng)
    maker = _make_sessionmaker(eng)

    # Patch at the source (for get_session and direct imports)
    monkeypatch.setattr("core.database_sa.SessionLocal", maker)
    # Patch the already-imported reference in unit_of_work
    monkeypatch.setattr(uow_module, "SessionLocal", maker)
    return maker


# ═══════════════════════════════════════════════════════════════════════════════
# UnitOfWork
# ═══════════════════════════════════════════════════════════════════════════════

class TestUnitOfWorkEnterExit:
    """UnitOfWork context manager entry and exit behaviour."""

    def test_enter_crea_sesion(self, test_db):
        """__enter__ creates a session and returns self."""
        from core.unit_of_work import UnitOfWork

        with UnitOfWork() as uow:
            assert uow.session is not None
            assert uow.session.is_active

    def test_commit_en_exito_persiste_datos(self, test_db):
        """__exit__ without exception commits the transaction."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        with UnitOfWork() as uow:
            user = Usuario(
                username="uow_commit",
                password="a",
                nombre="Commit Test",
                rol="Operador",
                email="commit@test.com",
            )
            uow.session.add(user)

        # Verify data persisted
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="uow_commit").first()
            assert found is not None
            assert found.nombre == "Commit Test"

    def test_rollback_en_excepcion(self, test_db):
        """__exit__ with exception rollbacks the transaction."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        with pytest.raises(RuntimeError, match="uow_fail"):
            with UnitOfWork() as uow:
                user = Usuario(
                    username="uow_rollback",
                    password="b",
                    nombre="Rollback Test",
                    rol="Operador",
                    email="rb@test.com",
                )
                uow.session.add(user)
                raise RuntimeError("uow_fail")

        # Verify data was rolled back
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="uow_rollback").first()
            assert found is None

    def test_session_cerrada_al_salir(self, test_db):
        """Session is not in a transaction after __exit__ (close called)."""
        from core.unit_of_work import UnitOfWork

        with UnitOfWork() as uow:
            session = uow.session

        # After __exit__ calls session.close(), the session should have
        # no active transaction. In SA 2.x, is_active may still be True
        # (autobegin), but in_transaction() reliably returns False after close.
        assert not session.in_transaction()

    def test_multiple_operaciones_misma_sesion(self, test_db):
        """Multiple adds within one UoW share the same session and commit atomically."""
        from core.unit_of_work import UnitOfWork
        from core.models import Auto

        with UnitOfWork() as uow:
            auto1 = Auto(
                placa="UOW001",
                marca="Mazda",
                modelo="3",
                estado="Disponible",
                tipo="Automóvil",
                transmision="Automática",
                combustible="Gasolina",
            )
            auto2 = Auto(
                placa="UOW002",
                marca="Mazda",
                modelo="CX-30",
                estado="Disponible",
                tipo="Automóvil",
                transmision="Automática",
                combustible="Gasolina",
            )
            uow.session.add(auto1)
            uow.session.add(auto2)

        # Both should persist
        maker = test_db
        with maker() as s:
            count = s.query(Auto).filter(
                Auto.placa.in_(["UOW001", "UOW002"])
            ).count()
            assert count == 2

    def test_rollback_manual(self, test_db):
        """Manual rollback() reverts changes within the UoW."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        with UnitOfWork() as uow:
            user = Usuario(
                username="uow_manual_rb",
                password="c",
                nombre="Manual Rollback",
                rol="Operador",
                email="mrb@test.com",
            )
            uow.session.add(user)
            uow.session.flush()

            # Manually rollback
            uow.rollback()

        # Data should NOT have persisted
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="uow_manual_rb").first()
            assert found is None

    def test_commit_manual_luego_exit_normal(self, test_db):
        """Manual commit() then normal exit persists everything once."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        with UnitOfWork() as uow:
            user = Usuario(
                username="uow_manual_cmt",
                password="d",
                nombre="Manual Commit",
                rol="Operador",
                email="mcmt@test.com",
            )
            uow.session.add(user)
            uow.commit()  # manual commit

            # Add another user after manual commit
            user2 = Usuario(
                username="uow_manual_cmt2",
                password="e",
                nombre="Manual Commit 2",
                rol="Operador",
                email="mcmt2@test.com",
            )
            uow.session.add(user2)
            # exit will commit user2

        # Both should persist
        maker = test_db
        with maker() as s:
            assert s.query(Usuario).filter_by(username="uow_manual_cmt").first() is not None
            assert s.query(Usuario).filter_by(username="uow_manual_cmt2").first() is not None

    def test_flush_obtiene_id_generado(self, test_db):
        """flush() within UoW obtains auto-generated IDs before commit."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        with UnitOfWork() as uow:
            user = Usuario(
                username="uow_flush_id",
                password="f",
                nombre="Flush ID",
                rol="Operador",
                email="flush@test.com",
            )
            uow.session.add(user)
            uow.session.flush()

            # After flush, the ID should be populated
            assert user.id is not None
            assert isinstance(user.id, int)

    def test_sin_operaciones_no_falla(self, test_db):
        """UoW with no operations exits cleanly."""
        from core.unit_of_work import UnitOfWork

        with UnitOfWork() as uow:
            pass  # no operations

        # Should not raise
        assert True


class TestUnitOfWorkErrorHandling:
    """UnitOfWork edge case and error handling paths."""

    def test_error_en_commit_maneja_rollback(self, test_db):
        """If session.commit() raises, UnitOfWork rollbacks and the error propagates."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        def failing_commit(*args, **kwargs):
            raise RuntimeError("commit_failed")

        with pytest.raises(RuntimeError, match="commit_failed"):
            with UnitOfWork() as uow:
                user = Usuario(
                    username="uow_commit_fail",
                    password="g",
                    nombre="Commit Fail",
                    rol="Operador",
                    email="cfail@test.com",
                )
                uow.session.add(user)
                # Patch commit to fail — exit will try commit, catch error, rollback, then re-raise
                uow.session.commit = failing_commit

        # Data should NOT have persisted (rollback was attempted)
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="uow_commit_fail").first()
            assert found is None

    def test_error_en_commit_y_rollback_propaga_excepcion(self, test_db):
        """If both commit and rollback fail, the original commit error propagates."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        def failing_call(*args, **kwargs):
            raise RuntimeError("everything_fails")

        with pytest.raises(RuntimeError, match="everything_fails"):
            with UnitOfWork() as uow:
                user = Usuario(
                    username="uow_double_fail",
                    password="h",
                    nombre="Double Fail",
                    rol="Operador",
                    email="dfail@test.com",
                )
                uow.session.add(user)
                # Patch both commit and rollback to fail
                uow.session.commit = failing_call
                uow.session.rollback = failing_call

    def test_uow_reusa_si_se_llama_dos_veces(self, test_db):
        """Two separate UoW blocks use different sessions."""
        from core.unit_of_work import UnitOfWork
        from core.models import Usuario

        sessions = []

        with UnitOfWork() as uow:
            sessions.append(uow.session)
            user = Usuario(
                username="uow_reuse_1",
                password="i",
                nombre="Reuse 1",
                rol="Operador",
                email="r1@test.com",
            )
            uow.session.add(user)

        with UnitOfWork() as uow:
            sessions.append(uow.session)
            user = Usuario(
                username="uow_reuse_2",
                password="j",
                nombre="Reuse 2",
                rol="Operador",
                email="r2@test.com",
            )
            uow.session.add(user)

        # Different session instances
        assert sessions[0] is not sessions[1]

        # Both sets of data persisted independently
        maker = test_db
        with maker() as s:
            assert s.query(Usuario).filter_by(username="uow_reuse_1").first() is not None
            assert s.query(Usuario).filter_by(username="uow_reuse_2").first() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# session_scope
# ═══════════════════════════════════════════════════════════════════════════════

class TestSessionScopeSinSession:
    """session_scope() without a session parameter delegates to get_session()."""

    def test_commit_en_exito(self, test_db, monkeypatch):
        """Without session, scope creates own session and commits on success."""
        # Patch get_session in unit_of_work namespace too
        from core.database_sa import get_session as real_get_session
        monkeypatch.setattr("core.unit_of_work.get_session", real_get_session)

        from core.unit_of_work import session_scope
        from core.models import Usuario

        with session_scope() as s:
            user = Usuario(
                username="scope_auto",
                password="k",
                nombre="Scope Auto",
                rol="Operador",
                email="auto@test.com",
            )
            s.add(user)

        # Data should persist
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="scope_auto").first()
            assert found is not None

    def test_rollback_en_excepcion(self, test_db, monkeypatch):
        """Without session, scope rollbacks on exception."""
        from core.database_sa import get_session as real_get_session
        monkeypatch.setattr("core.unit_of_work.get_session", real_get_session)

        from core.unit_of_work import session_scope
        from core.models import Usuario

        with pytest.raises(ValueError, match="scope_fail"):
            with session_scope() as s:
                user = Usuario(
                    username="scope_rollback",
                    password="l",
                    nombre="Scope Rollback",
                    rol="Operador",
                    email="sr@test.com",
                )
                s.add(user)
                raise ValueError("scope_fail")

        # Data should NOT persist
        maker = test_db
        with maker() as s:
            found = s.query(Usuario).filter_by(username="scope_rollback").first()
            assert found is None

    def test_flush_obtiene_id(self, test_db, monkeypatch):
        """Without session, flush gets auto-generated ID within scope."""
        from core.database_sa import get_session as real_get_session
        monkeypatch.setattr("core.unit_of_work.get_session", real_get_session)

        from core.unit_of_work import session_scope
        from core.models import Usuario

        with session_scope() as s:
            user = Usuario(
                username="scope_flush",
                password="m",
                nombre="Scope Flush",
                rol="Operador",
                email="sflush@test.com",
            )
            s.add(user)
            s.flush()
            assert user.id is not None

    def test_funciona_con_db_global(self):
        """session_scope works with the conftest's shared in-memory DB (no crash)."""
        # No monkeypatch — uses conftest's SessionLocal (in-memory SQLite)
        from core.unit_of_work import session_scope

        with session_scope() as s:
            result = s.execute(text("SELECT 1 AS val"))
            assert result.scalar() == 1


class TestSessionScopeConSession:
    """session_scope(session=...) when passed from UnitOfWork."""

    def test_usa_sesion_existente(self, test_db):
        """With session, scope yields it without managing lifecycle."""
        from core.unit_of_work import UnitOfWork, session_scope
        from core.models import Usuario

        with UnitOfWork() as uow:
            with session_scope(uow.session) as s:
                user = Usuario(
                    username="scope_with_uow",
                    password="n",
                    nombre="Scope With UoW",
                    rol="Operador",
                    email="swuow@test.com",
                )
                s.add(user)
                # session_scope should yield uow.session
                assert s is uow.session

            # Still inside UnitOfWork — data should NOT be committed yet
            # (UoW manages the lifecycle, session_scope doesn't commit)
            maker = test_db
            with maker() as check_s:
                found = check_s.query(Usuario).filter_by(username="scope_with_uow").first()
                assert found is None  # Not yet committed

        # After UoW exits → committed
        maker = test_db
        with maker() as check_s:
            found = check_s.query(Usuario).filter_by(username="scope_with_uow").first()
            assert found is not None

    def test_no_commit_ni_rollback(self, test_db):
        """With session, scope does NOT commit or rollback (UoW manages)."""
        from core.unit_of_work import UnitOfWork, session_scope
        from core.models import Usuario

        with UnitOfWork() as uow:
            with session_scope(uow.session) as s:
                user = Usuario(
                    username="scope_no_commit",
                    password="o",
                    nombre="Scope No Commit",
                    rol="Operador",
                    email="snc@test.com",
                )
                s.add(user)

            # session_scope should NOT have committed
            maker = test_db
            with maker() as check_s:
                found = check_s.query(Usuario).filter_by(username="scope_no_commit").first()
                assert found is None  # Not committed yet — good!

    def test_flush_funciona_con_uow(self, test_db):
        """flush() works inside session_scope with UoW session, obtaining IDs."""
        from core.unit_of_work import UnitOfWork, session_scope
        from core.models import Usuario

        with UnitOfWork() as uow:
            with session_scope(uow.session) as s:
                user = Usuario(
                    username="scope_uow_flush",
                    password="p",
                    nombre="Scope UoW Flush",
                    rol="Operador",
                    email="suflush@test.com",
                )
                s.add(user)
                s.flush()
                assert user.id is not None
                assert isinstance(user.id, int)

    def test_excepcion_en_scope_con_uow_hace_rollback(self, test_db):
        """Exception inside session_scope with UoW → UoW rollbacks."""
        from core.unit_of_work import UnitOfWork, session_scope
        from core.models import Usuario

        with pytest.raises(RuntimeError, match="scope_uow_fail"):
            with UnitOfWork() as uow:
                with session_scope(uow.session) as s:
                    user = Usuario(
                        username="scope_uow_fail",
                        password="q",
                        nombre="Scope UoW Fail",
                        rol="Operador",
                        email="sufail@test.com",
                    )
                    s.add(user)
                    raise RuntimeError("scope_uow_fail")

        # Data should NOT persist
        maker = test_db
        with maker() as check_s:
            found = check_s.query(Usuario).filter_by(username="scope_uow_fail").first()
            assert found is None

    def test_varias_llamadas_a_scope_misma_uow(self, test_db):
        """Multiple session_scope calls within same UoW use the same session."""
        from core.unit_of_work import UnitOfWork, session_scope
        from core.models import Usuario, Auto

        with UnitOfWork() as uow:
            with session_scope(uow.session) as s1:
                user = Usuario(
                    username="multi_scope",
                    password="r",
                    nombre="Multi Scope",
                    rol="Operador",
                    email="ms@test.com",
                )
                s1.add(user)

            with session_scope(uow.session) as s2:
                auto = Auto(
                    placa="MULTI01",
                    marca="Nissan",
                    modelo="Versa",
                    estado="Disponible",
                    tipo="Automóvil",
                    transmision="Automática",
                    combustible="Gasolina",
                )
                s2.add(auto)

            # Both objects share the same session
            assert s1 is s2

        # Both should persist atomically
        maker = test_db
        with maker() as check_s:
            assert check_s.query(Usuario).filter_by(username="multi_scope").first() is not None
            assert check_s.query(Auto).filter_by(placa="MULTI01").first() is not None


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level exports
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """UnitOfWork and session_scope are importable."""

    def test_unit_of_work_importable(self):
        """UnitOfWork class is importable from core.unit_of_work."""
        from core.unit_of_work import UnitOfWork
        assert UnitOfWork is not None
        assert callable(UnitOfWork)

    def test_session_scope_importable(self):
        """session_scope function is importable from core.unit_of_work."""
        from core.unit_of_work import session_scope
        assert session_scope is not None
        assert callable(session_scope)
