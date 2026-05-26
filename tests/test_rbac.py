"""
test_rbac.py — Unit tests for core/rbac.py

Covers:
  _extract_session_id:  Extract session_id from kwargs
  _validate_session:    Validate session and return user data
  require_role:         Decorator that restricts access by role
  require_active_session: Decorator that checks active session
  PermissionChecker:    Programmatic role verification (check_role,
                        can_access_informes, can_manage_users, get_user_role)

Run: pytest tests/test_rbac.py -v
"""

import pytest

from core.rbac import (
    _extract_session_id,
    _validate_session,
    require_role,
    require_active_session,
    PermissionChecker,
)
from core.security import SessionManager
from core.exceptions import PermisoInsuficiente


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(autouse=True)
def reset_session_manager():
    """Clear SessionManager state before each test."""
    SessionManager._sessions.clear()
    yield


@pytest.fixture
def admin_session():
    """Create and return a valid session_id for an Administrador user."""
    return SessionManager.create(
        user_id=1,
        username="admin",
        role="Administrador",
        nombre="Admin Principal",
    )


@pytest.fixture
def supervisor_session():
    """Create and return a valid session_id for a Supervisor user."""
    return SessionManager.create(
        user_id=2,
        username="supervisor",
        role="Supervisor",
        nombre="Supervisor Principal",
    )


@pytest.fixture
def operador_session():
    """Create and return a valid session_id for an Operador user."""
    return SessionManager.create(
        user_id=3,
        username="operador",
        role="Operador",
        nombre="Operador Regular",
    )


# Helper: a sample function decorated with require_role or require_active_session


@require_role("Administrador", "Supervisor")
def _func_protegida(session_id: str = None, **kwargs):
    """Sample function that requires Admin or Supervisor role."""
    return kwargs.get("resultado", "OK")


@require_role("Administrador")
def _func_solo_admin(session_id: str = None, **kwargs):
    """Sample function that only Administrador can access."""
    return "SOLO_ADMIN_OK"


@require_active_session
def _func_sesion_activa(session_id: str = None, **kwargs):
    """Sample function that only requires an active session."""
    return "SESION_ACTIVA_OK"


# ═══════════════════════════════════════════════════════════════════════════════
# _extract_session_id
# ═══════════════════════════════════════════════════════════════════════════════


class TestExtractSessionId:
    def test_extrae_de_session_id_kwarg(self):
        """Extracts session_id from kwargs['session_id']."""
        result = _extract_session_id((), {"session_id": "abc123"})
        assert result == "abc123"

    def test_extrae_de_sid_kwarg(self):
        """Extracts session_id from kwargs['sid']."""
        result = _extract_session_id((), {"sid": "xyz789"})
        assert result == "xyz789"

    def test_session_id_priority_over_sid(self):
        """session_id takes priority over sid if both are present."""
        result = _extract_session_id((), {"session_id": "primary", "sid": "secondary"})
        assert result == "primary"

    def test_pop_session_id_from_kwargs(self):
        """session_id is removed from kwargs after extraction."""
        kwargs = {"session_id": "to_remove", "data": "keep_me"}
        _extract_session_id((), kwargs)
        assert "session_id" not in kwargs
        assert kwargs == {"data": "keep_me"}

    def test_pop_sid_from_kwargs(self):
        """sid is removed from kwargs after extraction."""
        kwargs = {"sid": "to_remove", "data": "keep_me"}
        _extract_session_id((), kwargs)
        assert "sid" not in kwargs
        assert kwargs == {"data": "keep_me"}

    def test_sin_session_id_retorna_none(self):
        """No session_id in kwargs returns None."""
        result = _extract_session_id((), {"other": "value"})
        assert result is None

    def test_kwargs_vacio_retorna_none(self):
        """Empty kwargs returns None."""
        result = _extract_session_id((), {})
        assert result is None

    def test_args_ignorados(self):
        """Positional args are ignored (only kwargs are searched)."""
        result = _extract_session_id(("pos_arg_1", "pos_arg_2"), {})
        assert result is None

    def test_session_id_none_valor(self):
        """session_id=None in kwargs returns None."""
        result = _extract_session_id((), {"session_id": None})
        assert result is None

    def test_sid_none_valor(self):
        """sid=None in kwargs returns None."""
        result = _extract_session_id((), {"sid": None})
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# _validate_session
# ═══════════════════════════════════════════════════════════════════════════════


class TestValidateSession:
    def test_sesion_valida_retorna_datos(self, admin_session):
        """Valid session returns user data dict."""
        data = _validate_session(admin_session)
        assert data is not None
        assert data["username"] == "admin"
        assert data["role"] == "Administrador"
        assert data["nombre"] == "Admin Principal"

    def test_session_id_none_lanza_error(self):
        """None session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="sesión|sesión"):
            _validate_session(None)

    def test_session_id_vacio_lanza_error(self):
        """Empty string session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="sesión|sesión"):
            _validate_session("")

    def test_session_id_invalida_lanza_error(self):
        """Invalid session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="inválida|expirada"):
            _validate_session("token_inexistente_12345")

    def test_mensaje_usuario_para_sin_sesion(self):
        """Error message includes guidance to login when no session provided."""
        with pytest.raises(PermisoInsuficiente) as excinfo:
            _validate_session(None)
        assert "iniciar sesión" in str(excinfo.value.mensaje_usuario).lower()

    def test_mensaje_usuario_para_sesion_expirada(self):
        """Error message includes guidance to login again for expired session."""
        with pytest.raises(PermisoInsuficiente) as excinfo:
            _validate_session("fake_token")
        assert "sesión" in str(excinfo.value.mensaje_usuario).lower()
        assert "nuevamente" in str(excinfo.value.mensaje_usuario).lower()

    def test_datos_completos(self, admin_session):
        """Returned data includes all expected fields."""
        data = _validate_session(admin_session)
        expected_keys = {"user_id", "username", "role", "nombre", "last_activity"}
        assert expected_keys.issubset(data.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# require_role decorator
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequireRole:
    def test_admin_puede_acceder(self, admin_session):
        """Administrador can access function requiring Admin/Supervisor."""
        result = _func_protegida(session_id=admin_session)
        assert result == "OK"

    def test_supervisor_puede_acceder(self, supervisor_session):
        """Supervisor can access function requiring Admin/Supervisor."""
        result = _func_protegida(session_id=supervisor_session)
        assert result == "OK"

    def test_operador_no_puede_acceder(self, operador_session):
        """Operador cannot access function requiring Admin/Supervisor."""
        with pytest.raises(PermisoInsuficiente, match="permisos|no tiene permisos"):
            _func_protegida(session_id=operador_session)

    def test_solo_admin_excluye_supervisor(self, supervisor_session):
        """Supervisor cannot access function requiring only Administrador."""
        with pytest.raises(PermisoInsuficiente, match="permisos"):
            _func_solo_admin(session_id=supervisor_session)

    def test_solo_admin_excluye_operador(self, operador_session):
        """Operador cannot access function requiring Administrador."""
        with pytest.raises(PermisoInsuficiente):
            _func_solo_admin(session_id=operador_session)

    def test_solo_admin_admin_puede(self, admin_session):
        """Administrador can access function requiring Administrador."""
        result = _func_solo_admin(session_id=admin_session)
        assert result == "SOLO_ADMIN_OK"

    def test_sin_session_id_lanza_error(self):
        """Function call without session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente):
            _func_protegida()

    def test_session_id_invalida_lanza_error(self):
        """Invalid session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="inválida|expirada"):
            _func_protegida(session_id="fake_token_abc")

    def test_resultado_personalizado_via_kwargs(self, admin_session):
        """Extra kwargs (besides session_id) pass through the decorator."""
        result = _func_protegida(session_id=admin_session, resultado="EXTRA_OK")
        assert result == "EXTRA_OK"

    def test_sid_alias_funciona(self, admin_session):
        """Using sid= instead of session_id= also works."""
        result = _func_protegida(sid=admin_session)
        assert result == "OK"

    def test_role_none_lanza_error(self):
        """User with None role fails permission check."""
        sid = SessionManager.create(4, "norole", None, "Sin Rol")
        with pytest.raises(PermisoInsuficiente, match="permisos|None"):
            _func_protegida(session_id=sid)

    def test_supervisor_excluido_de_rol_unico(self, admin_session, operador_session):
        """Only Administrador can access require_role('Administrador')."""
        with pytest.raises(PermisoInsuficiente):
            _func_solo_admin(session_id=operador_session)
        result = _func_solo_admin(session_id=admin_session)
        assert result == "SOLO_ADMIN_OK"

    def test_kwargs_extra_pasan_limpias(self, admin_session):
        """Extra kwargs (besides session_id) pass through to the decorated function."""

        def _check_kwargs(session_id=None, **kw):
            return kw

        decorated = require_role("Administrador")(_check_kwargs)
        result = decorated(session_id=admin_session, extra1="a", extra2="b")
        assert result == {"extra1": "a", "extra2": "b"}


# ═══════════════════════════════════════════════════════════════════════════════
# require_active_session decorator
# ═══════════════════════════════════════════════════════════════════════════════


class TestRequireActiveSession:
    def test_admin_con_sesion_activa_accede(self, admin_session):
        """Administrador with active session can access."""
        result = _func_sesion_activa(session_id=admin_session)
        assert result == "SESION_ACTIVA_OK"

    def test_operador_con_sesion_activa_accede(self, operador_session):
        """Operador with active session can access (no role check)."""
        result = _func_sesion_activa(session_id=operador_session)
        assert result == "SESION_ACTIVA_OK"

    def test_sin_session_id_lanza_error(self):
        """No session_id raises PermisoInsuficiente (no active session)."""
        with pytest.raises(PermisoInsuficiente, match="sesión|sesión"):
            _func_sesion_activa()

    def test_session_invalida_lanza_error(self):
        """Invalid session_id raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="inválida|expirada"):
            _func_sesion_activa(session_id="fake_token_here")

    def test_sid_alias_funciona(self, admin_session):
        """Using sid= instead of session_id= works."""
        result = _func_sesion_activa(sid=admin_session)
        assert result == "SESION_ACTIVA_OK"

    def test_cualquier_rol_accede(self):
        """Any role (even custom) can access with active session."""
        sid = SessionManager.create(5, "invitado", "Invitado", "Usuario Invitado")
        result = _func_sesion_activa(session_id=sid)
        assert result == "SESION_ACTIVA_OK"

    def test_kwargs_extra_pasan_limpias(self, admin_session):
        """Extra kwargs pass through the decorator."""
        result = _func_sesion_activa(session_id=admin_session, extra="data")
        assert result == "SESION_ACTIVA_OK"


# ═══════════════════════════════════════════════════════════════════════════════
# PermissionChecker.check_role
# ═══════════════════════════════════════════════════════════════════════════════


class TestPermissionCheckerCheckRole:
    def test_admin_rol_permitido(self, admin_session):
        """Administrador passes check_role with matching roles."""
        data = PermissionChecker.check_role(admin_session, "Administrador", "Supervisor")
        assert data["username"] == "admin"
        assert data["role"] == "Administrador"

    def test_supervisor_rol_permitido(self, supervisor_session):
        """Supervisor passes check_role with matching roles."""
        data = PermissionChecker.check_role(supervisor_session, "Administrador", "Supervisor")
        assert data["username"] == "supervisor"

    def test_rol_no_permitido_lanza_error(self, operador_session):
        """Operador without required role raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente):
            PermissionChecker.check_role(operador_session, "Administrador", "Supervisor")

    def test_rol_permitido_sin_roles(self, admin_session):
        """check_role with no required_roles passes for any valid session."""
        data = PermissionChecker.check_role(admin_session)
        assert data is not None

    def test_session_invalida_lanza_error(self):
        """Invalid session raises PermisoInsuficiente."""
        with pytest.raises(PermisoInsuficiente, match="inválida|expirada"):
            PermissionChecker.check_role("fake_token", "Administrador")

    def test_session_none_lanza_error(self):
        """None session raises exception."""
        with pytest.raises(PermisoInsuficiente, match="inválida|expirada"):
            PermissionChecker.check_role(None, "Administrador")

    def test_devuelve_datos_completos(self, admin_session):
        """Returns full session data dict."""
        data = PermissionChecker.check_role(admin_session, "Administrador")
        assert data["user_id"] == 1
        assert data["nombre"] == "Admin Principal"


# ═══════════════════════════════════════════════════════════════════════════════
# PermissionChecker.can_access_informes
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanAccessInformes:
    def test_admin_puede(self, admin_session):
        """Administrador can access reports."""
        assert PermissionChecker.can_access_informes(admin_session) is True

    def test_supervisor_puede(self, supervisor_session):
        """Supervisor can access reports (ROLES_CON_INFORMES includes Supervisor)."""
        assert PermissionChecker.can_access_informes(supervisor_session) is True

    def test_operador_no_puede(self, operador_session):
        """Operador cannot access reports."""
        assert PermissionChecker.can_access_informes(operador_session) is False

    def test_sesion_invalida_retorna_false(self):
        """Invalid session returns False (no exception)."""
        assert PermissionChecker.can_access_informes("fake_token") is False

    def test_sesion_none_retorna_false(self):
        """None session returns False."""
        assert PermissionChecker.can_access_informes(None) is False

    def test_sin_rol_retorna_false(self):
        """User with no role should not access reports."""
        sid = SessionManager.create(6, "norole", None, "Sin Rol")
        assert PermissionChecker.can_access_informes(sid) is False


# ═══════════════════════════════════════════════════════════════════════════════
# PermissionChecker.can_manage_users
# ═══════════════════════════════════════════════════════════════════════════════


class TestCanManageUsers:
    def test_admin_puede(self, admin_session):
        """Administrador can manage users."""
        assert PermissionChecker.can_manage_users(admin_session) is True

    def test_supervisor_no_puede(self, supervisor_session):
        """Supervisor cannot manage users (only Administrador)."""
        assert PermissionChecker.can_manage_users(supervisor_session) is False

    def test_operador_no_puede(self, operador_session):
        """Operador cannot manage users."""
        assert PermissionChecker.can_manage_users(operador_session) is False

    def test_sesion_invalida_retorna_false(self):
        """Invalid session returns False."""
        assert PermissionChecker.can_manage_users("fake_token") is False

    def test_sesion_none_retorna_false(self):
        """None session returns False."""
        assert PermissionChecker.can_manage_users(None) is False


# ═══════════════════════════════════════════════════════════════════════════════
# PermissionChecker.get_user_role
# ═══════════════════════════════════════════════════════════════════════════════


class TestGetUserRole:
    def test_admin_retorna_rol(self, admin_session):
        """Returns 'Administrador' for admin session."""
        role = PermissionChecker.get_user_role(admin_session)
        assert role == "Administrador"

    def test_operador_retorna_rol(self, operador_session):
        """Returns 'Operador' for operador session."""
        role = PermissionChecker.get_user_role(operador_session)
        assert role == "Operador"

    def test_session_invalida_retorna_none(self):
        """Invalid session returns None (no exception)."""
        role = PermissionChecker.get_user_role("fake_token")
        assert role is None

    def test_session_none_retorna_none(self):
        """None session returns None."""
        role = PermissionChecker.get_user_role(None)
        assert role is None

    def test_usuario_sin_rol_retorna_none(self):
        """User with role=None returns None."""
        sid = SessionManager.create(7, "norole", None, "Sin Rol")
        role = PermissionChecker.get_user_role(sid)
        assert role is None

    def test_rol_despues_de_destroy(self, admin_session):
        """After session is destroyed, get_user_role returns None."""
        SessionManager.destroy(admin_session)
        role = PermissionChecker.get_user_role(admin_session)
        assert role is None

    def test_session_expirada_captura_excepcion(self, admin_session):
        """Expired session triggers SesionExpirada in SessionManager.get();
        get_user_role catches it via except Exception and returns None (lines 199-200)."""
        # Set last_activity to epoch 0 so time.time() - 0 > SESSION_TIMEOUT
        SessionManager._sessions[admin_session]["last_activity"] = 0
        role = PermissionChecker.get_user_role(admin_session)
        assert role is None
