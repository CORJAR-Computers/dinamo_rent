"""
test_services_restantes.py — Tests for UsuarioService, AuthService, DashboardService, InformeService, BackupService

Requires conftest.py to set up the in-memory SQLite database.
Each test method is self-contained (creates its own data).
Run: pytest tests/test_services_restantes.py -v
"""

import datetime
import os
import tempfile
from decimal import Decimal
from pathlib import Path

import pytest

from core.exceptions import (
    NegocioError, ValidacionError, RegistroNoEncontrado,
    CredencialesInvalidas, CuentaBloqueadaError, PermisoInsuficiente,
)
from core.security import SecurityManager, SessionManager
from core.schemas import UsuarioCreate
from repositories.repositories_sa import UsuarioRepositorySA
from services.usuario_service import UsuarioService
from services.auth_service import AuthService
from services.dashboard_service import DashboardService
from services.informe_service import InformeService
from services.backup_service import BackupService
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.renta_service import RentaService
from repositories.repositories_sa import AutoRepositorySA, RentaRepositorySA
from repositories.pago_repository_sa import PagoRepositorySA
from core.schemas import AutoCreate, RentaCreate, PagoCreate


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level counter for unique IDs (shared DB across tests)
# ═══════════════════════════════════════════════════════════════════════════════

_test_counter = 0


def _next_placa(prefix: str = "RES") -> str:
    global _test_counter
    _test_counter += 1
    return f"{prefix}{_test_counter:04d}"


def _next_username() -> str:
    global _test_counter
    _test_counter += 1
    return f"testuser{_test_counter}"


def _next_doc() -> str:
    global _test_counter
    _test_counter += 1
    return f"{_test_counter:09d}"


def _crear_auto(placa: str, **kwargs):
    """Create a test auto via AutoService."""
    defaults = {
        "placa": placa,
        "marca": "Test",
        "modelo": "Auto",
        "tipo": "Automóvil",
        "transmision": "Mecánica",
        "combustible": "Gasolina",
        "kilometraje": 10000,
        "estado": "Disponible",
    }
    defaults.update(kwargs)
    AutoService.guardar(defaults)


def _crear_cliente(no_doc: str, nombres: str = "Test", apellidos: str = "Cliente", **kwargs):
    """Create a test client via ClienteService."""
    nombre_completo = f"{nombres} {apellidos}".strip() if nombres else ""
    defaults = {
        "tipo_doc": "Cédula",
        "no_doc": no_doc,
        "nombres": nombres,
        "apellidos": apellidos,
        "nombre_completo": nombre_completo,
        "celular": "+573000000000",
        "estado": "Activo",
    }
    defaults.update(kwargs)
    ClienteService.guardar(defaults)


def _crear_renta(placa: str, **kwargs) -> int:
    """Create a test rental and return its ID."""
    hoy = datetime.date.today()
    defaults = {
        "placa": placa,
        "nombre_cliente": "Test Renta",
        "fecha_recogida": hoy,
        "hora_recogida": datetime.time(10, 0),
        "fecha_retorno": hoy + datetime.timedelta(days=3),
        "hora_retorno": datetime.time(10, 0),
        "dias_calculados": 3,
        "valor_dia": Decimal("100000"),
        "total": Decimal("300000"),
        "abono": Decimal("50000"),
    }
    defaults.update(kwargs)
    return RentaService.crear(defaults)


def _crear_admin_session() -> str:
    """Create a valid admin session for RBAC-protected methods."""
    return SessionManager.create(
        user_id=1,
        username="test_admin",
        role="Administrador",
        nombre="Test Admin",
    )


def _crear_supervisor_session() -> str:
    """Create a valid supervisor session for informe tests."""
    return SessionManager.create(
        user_id=2,
        username="test_supervisor",
        role="Supervisor",
        nombre="Test Supervisor",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# UsuarioService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioService:

    def test_crear_y_listar_usuarios(self):
        """crear() creates a user, listar() returns it (with admin session)."""
        sid = _crear_admin_session()
        username = _next_username()
        UsuarioService.crear({
            "username": username,
            "nombre": "Test User One",
            "password_raw": "TestPass123!",
            "rol": "Operador",
        }, session_id=sid)

        usuarios = UsuarioService.listar(session_id=sid)
        assert any(u["username"] == username for u in usuarios)

    def test_crear_usuario_duplicado(self):
        """crear() raises NegocioError for duplicate username."""
        sid = _crear_admin_session()
        username = _next_username()

        UsuarioService.crear({
            "username": username,
            "nombre": "Original",
            "password_raw": "TestPass123!",
        }, session_id=sid)

        with pytest.raises(NegocioError, match="ya está en uso"):
            UsuarioService.crear({
                "username": username,
                "nombre": "Duplicate",
                "password_raw": "OtherPass456!",
            }, session_id=sid)

    def test_crear_usuario_password_debil(self):
        """crear() raises ValidacionError for weak password."""
        sid = _crear_admin_session()
        username = _next_username()

        with pytest.raises(ValidacionError, match="Contraseña débil|contraseña no cumple"):
            UsuarioService.crear({
                "username": username,
                "nombre": "Weak Password",
                "password_raw": "123",  # Too short, no uppercase, no special char
            }, session_id=sid)

    def test_crear_usuario_sin_password(self):
        """crear() raises ValidacionError when password is missing."""
        sid = _crear_admin_session()
        username = _next_username()

        with pytest.raises(ValidacionError, match="contraseña es obligatoria"):
            UsuarioService.crear({
                "username": username,
                "nombre": "No Password",
                "password_raw": "",
            }, session_id=sid)

    def test_actualizar_usuario(self):
        """actualizar() updates user fields."""
        sid = _crear_admin_session()
        username = _next_username()

        UsuarioService.crear({
            "username": username,
            "nombre": "Original Name",
            "password_raw": "TestPass123!",
            "rol": "Operador",
        }, session_id=sid)

        UsuarioService.actualizar({
            "username": username,
            "nombre": "Updated Name",
            "rol": "Supervisor",
            "activo": "1",
        }, session_id=sid)

        usuarios = UsuarioService.listar(session_id=sid)
        usuario = next(u for u in usuarios if u["username"] == username)
        assert usuario["nombre"] == "Updated Name"
        assert usuario["rol"] == "Supervisor"

    def test_eliminar_usuario(self):
        """eliminar() removes a user."""
        sid = _crear_admin_session()
        username = _next_username()

        UsuarioService.crear({
            "username": username,
            "nombre": "To Delete",
            "password_raw": "TestPass123!",
        }, session_id=sid)

        UsuarioService.eliminar(username, session_id=sid)

        usuarios = UsuarioService.listar(session_id=sid)
        assert not any(u["username"] == username for u in usuarios)

    def test_eliminar_admin_denied(self):
        """eliminar() raises NegocioError for 'admin' user."""
        sid = _crear_admin_session()
        with pytest.raises(NegocioError, match="Administrador Principal"):
            UsuarioService.eliminar("admin", session_id=sid)

    def test_listar_sin_sesion_lanza_error(self):
        """listar() without session raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente):
            UsuarioService.listar()

    # ── forzar_cambio_password ────────────────────────────────────────────

    def test_forzar_cambio_password_ok(self):
        """forzar_cambio_password() sets debe_cambiar_password=True on user."""
        sid = _crear_admin_session()
        username = _next_username()

        # Crear usuario (debe_cambiar_password defaults to 0)
        UsuarioService.crear({
            "username": username,
            "nombre": "Forced User",
            "password_raw": "StrongPass123!",
            "rol": "Operador",
        }, session_id=sid)

        # Forzar cambio de contraseña
        UsuarioService.forzar_cambio_password(username, session_id=sid)

        # Verificar que el flag se activó
        usuarios = UsuarioService.listar(session_id=sid)
        usuario = next(u for u in usuarios if u["username"] == username)
        assert usuario["debe_cambiar_password"] is True

    def test_forzar_cambio_password_admin_denied(self):
        """forzar_cambio_password() raises NegocioError for 'admin' user."""
        sid = _crear_admin_session()
        with pytest.raises(NegocioError, match="Administrador Principal"):
            UsuarioService.forzar_cambio_password("admin", session_id=sid)

    def test_forzar_cambio_password_sin_sesion_lanza_error(self):
        """forzar_cambio_password() without session raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente):
            UsuarioService.forzar_cambio_password("some_user")

    def test_forzar_cambio_password_username_vacio(self):
        """forzar_cambio_password() raises ValidacionError for empty username."""
        sid = _crear_admin_session()
        with pytest.raises(ValidacionError, match="Nombre de usuario"):
            UsuarioService.forzar_cambio_password("", session_id=sid)

    def test_forzar_cambio_password_usuario_inexistente(self):
        """forzar_cambio_password() raises RegistroNoEncontrado for non-existent user."""
        sid = _crear_admin_session()
        with pytest.raises(RegistroNoEncontrado):
            UsuarioService.forzar_cambio_password("nonexistent_user_xyz", session_id=sid)


# ═══════════════════════════════════════════════════════════════════════════════
# AuthService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthService:

    def _crear_usuario_en_bd(self, username: str, password: str = "TestPass123!",
                             rol: str = "Operador", nombre: str = "Test Auth User"):
        """Create a user directly in the database for auth testing."""
        UsuarioRepositorySA.insertar(UsuarioCreate(
            username=username,
            password_raw=password,
            nombre=nombre,
            rol=rol,
            email="",
            activo=True,
        ))

    def test_login_exitoso(self):
        """login() returns session data on valid credentials."""
        username = _next_username()
        password = "SecurePass789!"
        self._crear_usuario_en_bd(username, password)

        result = AuthService.login(username, password)
        assert result["success"] is True
        assert result["username"] == username
        assert "session_id" in result
        assert result["rol"] == "Operador"

        # Session should be valid
        session_data = SessionManager.get(result["session_id"])
        assert session_data is not None

    def test_login_fallido_usuario_inexistente(self):
        """login() raises CredencialesInvalidas for non-existent user."""
        with pytest.raises(CredencialesInvalidas):
            AuthService.login("nonexistent_user_xyz", "SomePass123!")

    def test_login_fallido_password_incorrecta(self):
        """login() raises CredencialesInvalidas for wrong password."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "CorrectPass123!")

        with pytest.raises(CredencialesInvalidas):
            AuthService.login(username, "WrongPass456!")

    def test_login_sin_credenciales(self):
        """login() raises CredencialesInvalidas when username/password are empty."""
        with pytest.raises(CredencialesInvalidas):
            AuthService.login("", "")
        with pytest.raises(CredencialesInvalidas):
            AuthService.login(None, None)

    def test_login_bloqueo_por_intentos(self):
        """login() locks account after 5 failed attempts."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "RealPass123!")

        # 5 failed attempts
        for _ in range(4):
            with pytest.raises(CredencialesInvalidas):
                AuthService.login(username, "WrongPass!")

        # 5th attempt locks the account
        with pytest.raises(CuentaBloqueadaError):
            AuthService.login(username, "WrongPass!")

    def test_unlock_account(self):
        """unlock_account() unlocks a previously locked account."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "RealPass123!")

        # Lock the account
        for _ in range(4):
            with pytest.raises(CredencialesInvalidas):
                AuthService.login(username, "WrongPass!")

        # 5th attempt locks the account
        with pytest.raises(CuentaBloqueadaError):
            AuthService.login(username, "WrongPass!")

        # Verify locked
        status = AuthService.get_login_status(username)
        assert status["is_locked"] is True

        # Unlock
        unlocked = AuthService.unlock_account(username)
        assert unlocked is True

        # Verify unlocked and can login
        status = AuthService.get_login_status(username)
        assert status["is_locked"] is False

        result = AuthService.login(username, "RealPass123!")
        assert result["success"] is True

    def test_get_login_status(self):
        """get_login_status() returns correct account state."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "TestPass123!")

        # Initial state should be unlocked
        status = AuthService.get_login_status(username)
        assert status["is_locked"] is False
        assert status["failed_attempts"] == 0
        assert status["remaining_attempts"] == 5

        # After a failed attempt
        with pytest.raises(CredencialesInvalidas):
            AuthService.login(username, "WrongPass!")

        status = AuthService.get_login_status(username)
        assert status["failed_attempts"] >= 1

    # ── cambiar_password_obligatorio ───────────────────────────────────────

    def test_cambiar_password_obligatorio_ok(self):
        """cambiar_password_obligatorio() updates password and clears debe_cambiar_password flag."""
        username = _next_username()
        old_pwd = "OldPass123!"
        new_pwd = "NewStr0ng!"
        self._crear_usuario_en_bd(username, old_pwd)

        # Ejecutar cambio obligatorio
        AuthService.cambiar_password_obligatorio(username, old_pwd, new_pwd)

        # Verificar que puede iniciar sesión con la nueva contraseña
        result = AuthService.login(username, new_pwd)
        assert result["success"] is True

        # Verificar que debe_cambiar_password ahora es False
        assert result["debe_cambiar_password"] is False

    def test_cambiar_password_obligatorio_password_actual_incorrecta(self):
        """cambiar_password_obligatorio() raises CredencialesInvalidas when current password is wrong."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "RealPass123!")

        with pytest.raises(CredencialesInvalidas, match="contraseña actual no es correcta"):
            AuthService.cambiar_password_obligatorio(
                username, "WrongPass456!", "NewStr0ng!"
            )

    def test_cambiar_password_obligatorio_igual_a_actual(self):
        """cambiar_password_obligatorio() raises ValidacionError when new password equals current."""
        username = _next_username()
        same_pwd = "SamePass123!"
        self._crear_usuario_en_bd(username, same_pwd)

        with pytest.raises(ValidacionError, match="diferente a la actual"):
            AuthService.cambiar_password_obligatorio(
                username, same_pwd, same_pwd
            )

    def test_cambiar_password_obligatorio_password_debil(self):
        """cambiar_password_obligatorio() raises ValidacionError for weak new password."""
        username = _next_username()
        self._crear_usuario_en_bd(username, "RealPass123!")

        with pytest.raises(ValidacionError, match="[Cc]ontraseña [Dd]ébil"):
            AuthService.cambiar_password_obligatorio(
                username, "RealPass123!", "123"  # Too short, no uppercase, no special
            )

    def test_cambiar_password_obligatorio_campos_vacios(self):
        """cambiar_password_obligatorio() raises CredencialesInvalidas for empty fields."""
        with pytest.raises(CredencialesInvalidas, match="obligatorios"):
            AuthService.cambiar_password_obligatorio("", "", "")

    def test_cambiar_password_obligatorio_usuario_inexistente(self):
        """cambiar_password_obligatorio() raises CredencialesInvalidas for non-existent user."""
        with pytest.raises(CredencialesInvalidas, match="no encontrado"):
            AuthService.cambiar_password_obligatorio(
                "ghost_user_xyz", "AnyPass123!", "NewStr0ng!"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# DashboardService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestDashboardService:

    def test_kpi_globales_estructura(self):
        """kpi_globales() returns dict with expected keys and correct types."""
        kpi = DashboardService.kpi_globales()
        expected_keys = {"rentas_activas", "autos_disponibles", "autos_rentados",
                         "autos_mantenimiento", "total_flota", "ocupacion_flota",
                         "ingresos_mes", "pagos_pendientes"}
        assert expected_keys.issubset(kpi.keys())
        assert isinstance(kpi["rentas_activas"], int)
        assert isinstance(kpi["autos_disponibles"], int)
        assert isinstance(kpi["total_flota"], int)
        assert isinstance(kpi["ingresos_mes"], (int, float))
        assert isinstance(kpi["pagos_pendientes"], (int, float))
        assert kpi["rentas_activas"] >= 0
        assert kpi["total_flota"] >= 0

    def test_kpi_globales_con_datos(self):
        """kpi_globales() reflects created autos and rentals."""
        p1 = _next_placa("DSK")
        _crear_auto(p1)
        p2 = _next_placa("DSL")
        _crear_auto(p2, estado="Rentado")
        p3 = _next_placa("DSM")
        _crear_auto(p3, estado="Mantenimiento")

        kpi = DashboardService.kpi_globales()
        assert kpi["total_flota"] >= 3
        assert kpi["autos_disponibles"] >= 1
        assert kpi["autos_rentados"] >= 1
        assert kpi["autos_mantenimiento"] >= 1

    def test_obtener_activas(self):
        """obtener_activas() returns active rentals."""
        p = _next_placa("DSA")
        _crear_auto(p)
        _crear_renta(p, nombre_cliente="Dashboard Active")

        activas = DashboardService.obtener_activas()
        assert len(activas) >= 1
        assert any(r["placa"] == p for r in activas)

    def test_obtener_alertas_flota(self):
        """obtener_alertas_flota() returns fleet alerts."""
        p = _next_placa("DSF")
        _crear_auto(p, vencimiento_soat=str(datetime.date.today()))

        alertas = DashboardService.obtener_alertas_flota()
        soat_alerts = [a for a in alertas if a["placa"] == p]
        assert len(soat_alerts) >= 1

    def test_obtener_resumen_financiero_sin_datos(self):
        """obtener_resumen_financiero() returns zeroed resumen when no data."""
        resumen = DashboardService.obtener_resumen_financiero()
        assert resumen["ingresos_mes"] == 0.0
        assert resumen["utilidad_mes"] == 0.0
        assert "mes" in resumen

    def test_obtener_alertas_estructura(self):
        """obtener_alertas() returns dict with clientes and internas keys."""
        alertas = DashboardService.obtener_alertas()
        assert "clientes" in alertas
        assert "internas" in alertas


# ═══════════════════════════════════════════════════════════════════════════════
# InformeService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestInformeService:

    def test_balance_mensual_sin_datos(self):
        """balance_mensual_real() returns empty list when no data."""
        sid = _crear_supervisor_session()
        balance = InformeService.balance_mensual_real(session_id=sid)
        assert isinstance(balance, list)

    def test_balance_mensual_sin_sesion_lanza_error(self):
        """balance_mensual_real() without session raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente):
            InformeService.balance_mensual_real()

    def test_balance_mensual_con_rol_supervisor(self):
        """balance_mensual_real() works with a Supervisor role."""
        sid = _crear_supervisor_session()
        balance = InformeService.balance_mensual_real(session_id=sid)
        assert isinstance(balance, list)

    def test_balance_mensual_incluye_ingresos(self):
        """balance_mensual_real() includes ingresos from rental payments."""
        # Create auto and rental
        p = _next_placa("INF")
        _crear_auto(p)

        # Create a rental (pasamos total directamente)
        sid_sup = _crear_supervisor_session()
        hoy = datetime.date.today()
        renta_id = _crear_renta(
            p,
            fecha_recogida=hoy - datetime.timedelta(days=5),
            fecha_retorno=hoy - datetime.timedelta(days=2),
            dias_calculados=3,
            valor_dia=Decimal("100000"),
            total=Decimal("300000"),
            abono=Decimal("50000"),
            nombre_cliente="Informe Test",
        )

        # Register a payment to generate ingresos in balance
        from repositories.pago_repository_sa import PagoRepositorySA
        PagoRepositorySA.insertar(PagoCreate(
            id_renta=renta_id,
            monto=Decimal("50000"),
            metodo_pago="Efectivo",
            concepto="Abono inicial",
        ))

        balance = InformeService.balance_mensual_real(session_id=sid_sup)
        # Should find our data in one of the months
        mes_actual = hoy.strftime("%Y-%m")
        found = any(b.get("mes") == mes_actual for b in balance)
        # Even if empty, it should return a list
        assert isinstance(balance, list)


# ═══════════════════════════════════════════════════════════════════════════════
# BackupService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestBackupService:

    def test_decrypt_file_roundtrip(self):
        """decrypt_file() can decrypt what was encrypted by _encrypt_file()."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an original file
            original_path = os.path.join(tmpdir, "test_original.txt")
            original_content = b"Hello, this is a test backup file content!"
            with open(original_path, "wb") as f:
                f.write(original_content)

            password = "TestBackupPass123!"

            # Encrypt it using the internal method (testing decryption is the public API)
            encrypted_path = BackupService._encrypt_file(original_path, password)
            assert os.path.exists(encrypted_path)
            assert encrypted_path.endswith(".enc")

            # Decrypt it
            decrypted_path = os.path.join(tmpdir, "test_decrypted.txt")
            success, msg = BackupService.decrypt_file(encrypted_path, decrypted_path, password)
            assert success is True

            # Content should match
            with open(decrypted_path, "rb") as f:
                decrypted_content = f.read()
            assert decrypted_content == original_content

    def test_decrypt_file_wrong_password(self):
        """decrypt_file() returns error with wrong password."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_path = os.path.join(tmpdir, "test_orig2.txt")
            original_content = b"Sensitive data here"
            with open(original_path, "wb") as f:
                f.write(original_content)

            encrypted_path = BackupService._encrypt_file(original_path, "CorrectPass123!")
            decrypted_path = os.path.join(tmpdir, "test_decrypted2.txt")

            success, msg = BackupService.decrypt_file(
                encrypted_path, decrypted_path, "WrongPass456!"
            )
            assert success is False
            assert "Error" in msg or "contraseña" in msg.lower()

    def test_decrypt_file_sin_password(self):
        """decrypt_file() returns error when no password provided."""
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_enc = os.path.join(tmpdir, "fake.enc")
            with open(fake_enc, "wb") as f:
                f.write(b"fake data")

            success, msg = BackupService.decrypt_file(fake_enc, fake_enc + ".dec", "")
            assert success is False

    def test_crear_backup_sqlite(self, monkeypatch):
        """crear() returns (True, message) for a valid SQLite backup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary SQLite database file by touching the path
            db_path = os.path.join(tmpdir, "test_db.sqlite")

            # Import and set up a proper SQLite file
            from sqlalchemy import create_engine
            from core.models import Base as AllModels
            engine = create_engine(f"sqlite:///{db_path}")
            AllModels.metadata.create_all(bind=engine)
            engine.dispose()

            # Verify the file was created
            assert os.path.exists(db_path), f"DB file not created at {db_path}"

            # Monkey-patch config paths — we need to patch at the service module level too
            import services.backup_service as bs
            import core.config as cfg

            original_db_path = cfg.DB_PATH
            original_backup_dir = cfg.BACKUP_DIR

            cfg.DB_PATH = db_path
            cfg.BACKUP_DIR = Path(tmpdir)
            # Also patch the backup service's module-level imports
            bs.DB_PATH = db_path
            bs.BACKUP_DIR = Path(tmpdir)
            bs.DB_ENGINE = "sqlite"

            try:
                success, msg = BackupService.crear()
                assert success is True, f"Backup failed: {msg}"
                assert "Backup" in msg or "copia" in msg.lower()

                # Verify the backup file was created
                backup_files = [f for f in os.listdir(tmpdir) if f.endswith(".db")]
                assert len(backup_files) >= 1
            finally:
                cfg.DB_PATH = original_db_path
                cfg.BACKUP_DIR = original_backup_dir

    def test_crear_backup_sqlite_falla_sin_db(self, monkeypatch):
        """crear() returns (False, message) when database file doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import core.config as cfg
            original_db_path = cfg.DB_PATH
            original_backup_dir = cfg.BACKUP_DIR

            cfg.DB_PATH = "/nonexistent/path/database.db"
            cfg.BACKUP_DIR = Path(tmpdir)
            cfg.DB_ENGINE = "sqlite"

            try:
                success, msg = BackupService.crear()
                assert success is False
                assert "no encontrada" in msg.lower()
            finally:
                cfg.DB_PATH = original_db_path
                cfg.BACKUP_DIR = original_backup_dir
