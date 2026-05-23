"""
test_exceptions.py — Unit tests for core/exceptions.py

Covers all 20 exception classes:
  DinamoBaseError, DatabaseError, RegistroNoEncontrado, DuplicadoError,
  ValidacionError, CampoRequerido, FechaInvalida, PlacaInvalida, RangoInvalido,
  NegocioError, VehiculoNoDisponible, RentaYaCerrada, ClienteEnListaNegra,
  SeguridadError, CredencialesInvalidas, SesionExpirada, PermisoInsuficiente,
  CuentaBloqueadaError, RateLimitExceededError, InputSanitizationError

Strategy:
  - Test inheritance hierarchy for each exception
  - Test default mensaje_usuario for each class
  - Test custom __init__ for CampoRequerido, RangoInvalido, VehiculoNoDisponible
  - Test __str__ behavior (detalle vs mensaje_usuario)
  - Test mensaje_usuario override via constructor
  - Test catch-by-parent polymorphism
  - Test module exports

Run: pytest tests/test_exceptions.py -v
"""

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# DinamoBaseError
# ═══════════════════════════════════════════════════════════════════════════════

class TestDinamoBaseError:
    """Base exception class."""

    def test_hereda_exception(self):
        """DinamoBaseError inherits from Exception."""
        from core.exceptions import DinamoBaseError
        assert issubclass(DinamoBaseError, Exception)

    def test_mensaje_usuario_default(self):
        """Default mensaje_usuario."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError()
        assert err.mensaje_usuario == "Ocurrió un error inesperado."

    def test_con_detalle(self):
        """Constructor accepts detalle."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError(detalle="Algo salió mal")
        assert err.detalle == "Algo salió mal"

    def test_str_usa_detalle(self):
        """__str__ returns detalle when present."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError(detalle="Error específico")
        assert str(err) == "Error específico"

    def test_str_sin_detalle_usa_mensaje_usuario(self):
        """__str__ falls back to mensaje_usuario when detalle is empty."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError()
        assert str(err) == "Ocurrió un error inesperado."

    def test_mensaje_usuario_override(self):
        """Constructor can override mensaje_usuario."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError(mensaje_usuario="Mensaje personalizado")
        assert err.mensaje_usuario == "Mensaje personalizado"
        assert str(err) == "Mensaje personalizado"

    def test_detalle_y_mensaje_personalizado(self):
        """Both detalle and mensaje_usuario can be set."""
        from core.exceptions import DinamoBaseError
        err = DinamoBaseError(detalle="Detalle técnico",
                              mensaje_usuario="Mensaje usuario")
        assert err.detalle == "Detalle técnico"
        assert err.mensaje_usuario == "Mensaje usuario"
        assert str(err) == "Detalle técnico"

    def test_raise_y_catch(self):
        """DinamoBaseError can be raised and caught."""
        from core.exceptions import DinamoBaseError
        with pytest.raises(DinamoBaseError):
            raise DinamoBaseError(detalle="test")

    def test_raise_y_catch_como_exception(self):
        """DinamoBaseError can be caught as Exception (polymorphism)."""
        from core.exceptions import DinamoBaseError
        with pytest.raises(Exception):
            raise DinamoBaseError(detalle="test")


# ═══════════════════════════════════════════════════════════════════════════════
# Database errors
# ═══════════════════════════════════════════════════════════════════════════════

class TestDatabaseError:
    """DatabaseError and subclasses."""

    def test_database_error_hereda(self):
        """DatabaseError inherits from DinamoBaseError."""
        from core.exceptions import DatabaseError, DinamoBaseError
        assert issubclass(DatabaseError, DinamoBaseError)

    def test_database_error_mensaje_usuario(self):
        """DatabaseError default mensaje_usuario."""
        from core.exceptions import DatabaseError
        err = DatabaseError()
        assert err.mensaje_usuario == "Error al acceder a la base de datos."

    def test_database_error_catch_como_base(self):
        """DatabaseError can be caught as DinamoBaseError."""
        from core.exceptions import DatabaseError, DinamoBaseError
        with pytest.raises(DinamoBaseError):
            raise DatabaseError()

    # ── RegistroNoEncontrado ──

    def test_registro_no_encontrado_hereda(self):
        """RegistroNoEncontrado inherits from DatabaseError."""
        from core.exceptions import RegistroNoEncontrado, DatabaseError
        assert issubclass(RegistroNoEncontrado, DatabaseError)

    def test_registro_no_encontrado_mensaje_usuario(self):
        """RegistroNoEncontrado default mensaje_usuario."""
        from core.exceptions import RegistroNoEncontrado
        err = RegistroNoEncontrado()
        assert err.mensaje_usuario == "El registro solicitado no existe."

    def test_registro_no_encontrado_catch_como_database(self):
        """RegistroNoEncontrado caught as DatabaseError."""
        from core.exceptions import RegistroNoEncontrado, DatabaseError
        with pytest.raises(DatabaseError):
            raise RegistroNoEncontrado()

    # ── DuplicadoError ──

    def test_duplicado_error_hereda(self):
        """DuplicadoError inherits from DatabaseError."""
        from core.exceptions import DuplicadoError, DatabaseError
        assert issubclass(DuplicadoError, DatabaseError)

    def test_duplicado_error_mensaje_usuario(self):
        """DuplicadoError default mensaje_usuario."""
        from core.exceptions import DuplicadoError
        err = DuplicadoError()
        assert err.mensaje_usuario == "Ya existe un registro con esos datos."


# ═══════════════════════════════════════════════════════════════════════════════
# Validation errors
# ═══════════════════════════════════════════════════════════════════════════════

class TestValidacionError:
    """ValidacionError and subclasses."""

    def test_validacion_hereda(self):
        """ValidacionError inherits from DinamoBaseError."""
        from core.exceptions import ValidacionError, DinamoBaseError
        assert issubclass(ValidacionError, DinamoBaseError)

    def test_validacion_mensaje_usuario(self):
        """ValidacionError default mensaje_usuario."""
        from core.exceptions import ValidacionError
        err = ValidacionError()
        assert err.mensaje_usuario == "Los datos ingresados no son válidos."

    # ── CampoRequerido ──

    def test_campo_requerido_hereda(self):
        """CampoRequerido inherits from ValidacionError."""
        from core.exceptions import CampoRequerido, ValidacionError
        assert issubclass(CampoRequerido, ValidacionError)

    def test_campo_requerido_con_campo(self):
        """CampoRequerido formats message with field name."""
        from core.exceptions import CampoRequerido
        err = CampoRequerido("email")
        assert "email" in str(err)
        assert "email" in err.mensaje_usuario
        assert err.detalle == "El campo 'email' es obligatorio."

    def test_campo_requerido_mensaje_usuario(self):
        """CampoRequerido mensaje_usuario includes field name."""
        from core.exceptions import CampoRequerido
        err = CampoRequerido("username")
        assert err.mensaje_usuario == "El campo 'username' es obligatorio."

    # ── FechaInvalida ──

    def test_fecha_invalida_hereda(self):
        """FechaInvalida inherits from ValidacionError."""
        from core.exceptions import FechaInvalida, ValidacionError
        assert issubclass(FechaInvalida, ValidacionError)

    def test_fecha_invalida_mensaje_usuario(self):
        """FechaInvalida default mensaje_usuario."""
        from core.exceptions import FechaInvalida
        err = FechaInvalida()
        assert err.mensaje_usuario == "La fecha ingresada no es válida."

    # ── PlacaInvalida ──

    def test_placa_invalida_hereda(self):
        """PlacaInvalida inherits from ValidacionError."""
        from core.exceptions import PlacaInvalida, ValidacionError
        assert issubclass(PlacaInvalida, ValidacionError)

    def test_placa_invalida_mensaje_usuario(self):
        """PlacaInvalida default mensaje_usuario."""
        from core.exceptions import PlacaInvalida
        err = PlacaInvalida()
        assert err.mensaje_usuario == "La placa ingresada no tiene un formato válido."

    # ── RangoInvalido ──

    def test_rango_invalido_hereda(self):
        """RangoInvalido inherits from ValidacionError."""
        from core.exceptions import RangoInvalido, ValidacionError
        assert issubclass(RangoInvalido, ValidacionError)

    def test_rango_invalido_formato(self):
        """RangoInvalido formats message with campo, minimo, maximo."""
        from core.exceptions import RangoInvalido
        err = RangoInvalido("edad", 18, 99)
        assert "edad" in str(err)
        assert "18" in str(err)
        assert "99" in str(err)
        assert err.detalle == "'edad' debe estar entre 18 y 99."

    def test_rango_invalido_con_float(self):
        """RangoInvalido works with float values."""
        from core.exceptions import RangoInvalido
        err = RangoInvalido("porcentaje", 0.0, 100.0)
        assert "0.0" in str(err)
        assert "100.0" in str(err)

    def test_rango_invalido_catch_como_validacion(self):
        """RangoInvalido caught as ValidacionError."""
        from core.exceptions import RangoInvalido, ValidacionError
        with pytest.raises(ValidacionError):
            raise RangoInvalido("edad", 0, 100)


# ═══════════════════════════════════════════════════════════════════════════════
# Business errors
# ═══════════════════════════════════════════════════════════════════════════════

class TestNegocioError:
    """NegocioError and subclasses."""

    def test_negocio_hereda(self):
        """NegocioError inherits from DinamoBaseError."""
        from core.exceptions import NegocioError, DinamoBaseError
        assert issubclass(NegocioError, DinamoBaseError)

    def test_negocio_mensaje_usuario(self):
        """NegocioError default mensaje_usuario."""
        from core.exceptions import NegocioError
        err = NegocioError()
        assert err.mensaje_usuario == "La operación no puede realizarse."

    # ── VehiculoNoDisponible ──

    def test_vehiculo_no_disponible_hereda(self):
        """VehiculoNoDisponible inherits from NegocioError."""
        from core.exceptions import VehiculoNoDisponible, NegocioError
        assert issubclass(VehiculoNoDisponible, NegocioError)

    def test_vehiculo_no_disponible_con_placa(self):
        """VehiculoNoDisponible formats message with placa."""
        from core.exceptions import VehiculoNoDisponible
        err = VehiculoNoDisponible("ABC123")
        assert "ABC123" in str(err)
        assert "ABC123" in err.mensaje_usuario

    def test_vehiculo_no_disponible_detalle_tecnico(self):
        """VehiculoNoDisponible detalle is technical message."""
        from core.exceptions import VehiculoNoDisponible
        err = VehiculoNoDisponible("XYZ789")
        assert err.detalle == "El vehículo XYZ789 no está disponible para renta."

    def test_vehiculo_no_disponible_mensaje_usuario(self):
        """VehiculoNoDisponible mensaje_usuario is user-friendly."""
        from core.exceptions import VehiculoNoDisponible
        err = VehiculoNoDisponible("DEF456")
        assert err.mensaje_usuario == "El vehículo DEF456 no está disponible en este momento."

    # ── RentaYaCerrada ──

    def test_renta_ya_cerrada_hereda(self):
        """RentaYaCerrada inherits from NegocioError."""
        from core.exceptions import RentaYaCerrada, NegocioError
        assert issubclass(RentaYaCerrada, NegocioError)

    def test_renta_ya_cerrada_mensaje_usuario(self):
        """RentaYaCerrada default mensaje_usuario."""
        from core.exceptions import RentaYaCerrada
        err = RentaYaCerrada()
        assert err.mensaje_usuario == "Esta renta ya fue finalizada y no puede modificarse."

    # ── ClienteEnListaNegra ──

    def test_cliente_en_lista_negra_hereda(self):
        """ClienteEnListaNegra inherits from NegocioError."""
        from core.exceptions import ClienteEnListaNegra, NegocioError
        assert issubclass(ClienteEnListaNegra, NegocioError)

    def test_cliente_en_lista_negra_mensaje_usuario(self):
        """ClienteEnListaNegra default mensaje_usuario."""
        from core.exceptions import ClienteEnListaNegra
        err = ClienteEnListaNegra()
        assert err.mensaje_usuario == "Este cliente está en lista negra y no puede rentar."


# ═══════════════════════════════════════════════════════════════════════════════
# Security errors
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeguridadError:
    """SeguridadError and subclasses."""

    def test_seguridad_hereda(self):
        """SeguridadError inherits from DinamoBaseError."""
        from core.exceptions import SeguridadError, DinamoBaseError
        assert issubclass(SeguridadError, DinamoBaseError)

    def test_seguridad_mensaje_usuario(self):
        """SeguridadError default mensaje_usuario."""
        from core.exceptions import SeguridadError
        err = SeguridadError()
        assert err.mensaje_usuario == "Acceso denegado."

    # ── CredencialesInvalidas ──

    def test_credenciales_invalidas_hereda(self):
        """CredencialesInvalidas inherits from SeguridadError."""
        from core.exceptions import CredencialesInvalidas, SeguridadError
        assert issubclass(CredencialesInvalidas, SeguridadError)

    def test_credenciales_invalidas_mensaje_usuario(self):
        """CredencialesInvalidas default mensaje_usuario."""
        from core.exceptions import CredencialesInvalidas
        err = CredencialesInvalidas()
        assert err.mensaje_usuario == "Usuario o contraseña incorrectos."

    def test_credenciales_invalidas_con_detalle(self):
        """CredencialesInvalidas accepts custom detalle."""
        from core.exceptions import CredencialesInvalidas
        err = CredencialesInvalidas(detalle="Login failed for user admin")
        assert err.detalle == "Login failed for user admin"
        assert err.mensaje_usuario == "Usuario o contraseña incorrectos."

    # ── SesionExpirada ──

    def test_sesion_expirada_hereda(self):
        """SesionExpirada inherits from SeguridadError."""
        from core.exceptions import SesionExpirada, SeguridadError
        assert issubclass(SesionExpirada, SeguridadError)

    def test_sesion_expirada_mensaje_usuario(self):
        """SesionExpirada default mensaje_usuario."""
        from core.exceptions import SesionExpirada
        err = SesionExpirada()
        assert err.mensaje_usuario == "Tu sesión ha expirado. Por favor inicia sesión nuevamente."

    # ── PermisoInsuficiente ──

    def test_permiso_insuficiente_hereda(self):
        """PermisoInsuficiente inherits from SeguridadError."""
        from core.exceptions import PermisoInsuficiente, SeguridadError
        assert issubclass(PermisoInsuficiente, SeguridadError)

    def test_permiso_insuficiente_mensaje_usuario(self):
        """PermisoInsuficiente default mensaje_usuario."""
        from core.exceptions import PermisoInsuficiente
        err = PermisoInsuficiente()
        assert err.mensaje_usuario == "No tienes permisos para realizar esta acción."

    # ── CuentaBloqueadaError ──

    def test_cuenta_bloqueada_hereda(self):
        """CuentaBloqueadaError inherits from SeguridadError."""
        from core.exceptions import CuentaBloqueadaError, SeguridadError
        assert issubclass(CuentaBloqueadaError, SeguridadError)

    def test_cuenta_bloqueada_mensaje_usuario(self):
        """CuentaBloqueadaError default mensaje_usuario."""
        from core.exceptions import CuentaBloqueadaError
        err = CuentaBloqueadaError()
        assert err.mensaje_usuario == "Tu cuenta ha sido bloqueada por múltiples intentos fallidos. Contacta al administrador."

    # ── RateLimitExceededError ──

    def test_rate_limit_exceeded_hereda(self):
        """RateLimitExceededError inherits from SeguridadError."""
        from core.exceptions import RateLimitExceededError, SeguridadError
        assert issubclass(RateLimitExceededError, SeguridadError)

    def test_rate_limit_exceeded_mensaje_usuario(self):
        """RateLimitExceededError default mensaje_usuario."""
        from core.exceptions import RateLimitExceededError
        err = RateLimitExceededError()
        assert err.mensaje_usuario == "Demasiados intentos de inicio de sesión. Por favor espera antes de intentar nuevamente."

    # ── InputSanitizationError ──

    def test_input_sanitization_hereda(self):
        """InputSanitizationError inherits from SeguridadError."""
        from core.exceptions import InputSanitizationError, SeguridadError
        assert issubclass(InputSanitizationError, SeguridadError)

    def test_input_sanitization_mensaje_usuario(self):
        """InputSanitizationError default mensaje_usuario."""
        from core.exceptions import InputSanitizationError
        err = InputSanitizationError()
        assert err.mensaje_usuario == "Los datos contienen caracteres no permitidos."


# ═══════════════════════════════════════════════════════════════════════════════
# Polymorphism — catch by parent type
# ═══════════════════════════════════════════════════════════════════════════════

class TestPolymorphism:
    """All exceptions can be caught by their parent types."""

    @pytest.mark.parametrize("exception_class,detalle", [
        ("DatabaseError", None),
        ("RegistroNoEncontrado", None),
        ("DuplicadoError", None),
        ("ValidacionError", None),
        ("CampoRequerido", "email"),
        ("FechaInvalida", None),
        ("PlacaInvalida", None),
        ("RangoInvalido", "edad,0,100"),
        ("NegocioError", None),
        ("VehiculoNoDisponible", "ABC123"),
        ("RentaYaCerrada", None),
        ("ClienteEnListaNegra", None),
        ("SeguridadError", None),
        ("CredencialesInvalidas", None),
        ("SesionExpirada", None),
        ("PermisoInsuficiente", None),
        ("CuentaBloqueadaError", None),
        ("RateLimitExceededError", None),
        ("InputSanitizationError", None),
    ])
    def test_catch_como_dinamo_base_error(self, exception_class, detalle):
        """Every exception can be caught as DinamoBaseError."""
        from core import exceptions
        cls = getattr(exceptions, exception_class)
        with pytest.raises(exceptions.DinamoBaseError):
            if detalle is not None and exception_class in ("CampoRequerido",):
                raise cls(detalle)
            elif detalle is not None and exception_class == "RangoInvalido":
                campo, minimo, maximo = detalle.split(",")
                raise cls(campo, int(minimo), int(maximo))
            elif detalle is not None:
                raise cls(detalle)
            else:
                raise cls()

    def test_todas_las_excepciones_son_exception(self):
        """All custom exceptions are subclasses of Exception."""
        from core import exceptions
        exception_names = [
            name for name in dir(exceptions)
            if name.endswith(("Error", "Invalida", "Invalido", "Expirada",
                              "Insuficiente", "NoDisponible", "Cerrada",
                              "ListaNegra", "Invalidas", "Bloqueada"))
            and isinstance(getattr(exceptions, name), type)
            and issubclass(getattr(exceptions, name), Exception)
        ]
        for name in exception_names:
            cls = getattr(exceptions, name)
            assert issubclass(cls, Exception), f"{name} is not an Exception subclass"


# ═══════════════════════════════════════════════════════════════════════════════
# Raise and catch integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestRaiseYCatch:
    """Exceptions can be raised and caught in practice."""

    def test_raise_campo_requerido(self):
        """CampoRequerido raised and caught."""
        from core.exceptions import CampoRequerido
        with pytest.raises(CampoRequerido) as excinfo:
            raise CampoRequerido("nombre")
        assert "nombre" in str(excinfo.value)

    def test_raise_rango_invalido(self):
        """RangoInvalido raised and caught."""
        from core.exceptions import RangoInvalido
        with pytest.raises(RangoInvalido) as excinfo:
            raise RangoInvalido("edad", 0, 150)
        assert "edad" in str(excinfo.value)

    def test_raise_vehiculo_no_disponible(self):
        """VehiculoNoDisponible raised and caught."""
        from core.exceptions import VehiculoNoDisponible
        with pytest.raises(VehiculoNoDisponible) as excinfo:
            raise VehiculoNoDisponible("ABC123")
        assert "ABC123" in str(excinfo.value)

    def test_raise_con_detalle_personalizado(self):
        """Any exception can be raised with custom detalle."""
        from core.exceptions import SesionExpirada
        with pytest.raises(SesionExpirada) as excinfo:
            raise SesionExpirada(detalle="Token expired at 12:00")
        assert "Token expired" in str(excinfo.value)

    def test_mensaje_usuario_se_mantiene_con_detalle(self):
        """mensaje_usuario is preserved even when detalle is provided."""
        from core.exceptions import PermisoInsuficiente
        err = PermisoInsuficiente(detalle="Falta permiso ADMIN")
        assert err.mensaje_usuario == "No tienes permisos para realizar esta acción."


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:
    """All exceptions are importable from core.exceptions."""

    def test_todas_las_excepciones_importables(self):
        """All exception classes are importable."""
        from core.exceptions import (
            DinamoBaseError,
            DatabaseError, RegistroNoEncontrado, DuplicadoError,
            ValidacionError, CampoRequerido, FechaInvalida, PlacaInvalida,
            RangoInvalido,
            NegocioError, VehiculoNoDisponible, RentaYaCerrada,
            ClienteEnListaNegra,
            SeguridadError, CredencialesInvalidas, SesionExpirada,
            PermisoInsuficiente, CuentaBloqueadaError, RateLimitExceededError,
            InputSanitizationError,
        )
        assert DinamoBaseError is not None
        assert InputSanitizationError is not None
