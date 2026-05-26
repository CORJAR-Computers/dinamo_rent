"""
test_schemas.py — Unit tests for core/schemas.py

Covers all Pydantic v2 schemas (approximately 49):
  BaseSchema, Usuario*, Auto*, Cliente*, Renta*, Reserva*,
  Mantenimiento*, Comparendo*, Pago*, Gasto*, Inspeccion*,
  Login*, and composite response schemas.

Strategy:
  - Test required fields trigger ValidationError when missing
  - Test valid data passes validation
  - Test default values are applied
  - Test optional fields can be omitted
  - Test field constraints (min_length, max_length, pattern, ge, gt, regex)
  - Test custom validators (ClienteBase.generar_nombre)
  - Test ConfigDict (from_attributes, str_strip_whitespace)
  - Test response schemas with from_attributes=True

Run: pytest tests/test_schemas.py -v
"""

from datetime import date, time, datetime
from decimal import Decimal

import pytest
from pydantic import ValidationError


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _assert_validation_error(schema_class, data, match=None):
    """Assert that creating schema_class with data raises ValidationError."""
    with pytest.raises(ValidationError) as excinfo:
        schema_class(**data)
    if match:
        assert match in str(excinfo.value)


def _assert_valid(schema_class, data):
    """Assert that data is valid for schema_class and return the instance."""
    return schema_class(**data)


# ═══════════════════════════════════════════════════════════════════════════════
# BaseSchema
# ═══════════════════════════════════════════════════════════════════════════════


class TestBaseSchema:
    """BaseSchema common configuration."""

    def test_base_schema_importable(self):
        from core.schemas import BaseSchema

        assert BaseSchema is not None

    def test_strip_whitespace(self):
        """str_strip_whitespace=True strips leading/trailing spaces."""
        from core.schemas import UsuarioBase

        u = UsuarioBase(username="  test_user  ")
        assert u.username == "test_user"


# ═══════════════════════════════════════════════════════════════════════════════
# USUARIO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestUsuarioSchemas:
    """UsuarioBase, UsuarioCreate, UsuarioUpdate, UsuarioResponse."""

    def test_usuariobase_requiere_username(self):
        """Username is required."""
        from core.schemas import UsuarioBase

        _assert_validation_error(UsuarioBase, {}, "username")

    def test_usuariobase_username_min_length(self):
        """Username must be at least 3 chars."""
        from core.schemas import UsuarioBase

        _assert_validation_error(UsuarioBase, {"username": "ab"}, "username")

    def test_usuariobase_username_max_length(self):
        """Username must be at most 50 chars."""
        from core.schemas import UsuarioBase

        _assert_validation_error(UsuarioBase, {"username": "a" * 51}, "username")

    def test_usuariobase_username_pattern(self):
        """Username only allows alphanumeric and underscore."""
        from core.schemas import UsuarioBase

        _assert_validation_error(UsuarioBase, {"username": "user name!"}, "username")

    def test_usuariobase_username_valid(self):
        """Valid username passes."""
        from core.schemas import UsuarioBase

        u = _assert_valid(UsuarioBase, {"username": "admin_user"})
        assert u.username == "admin_user"

    def test_usuariobase_defaults(self):
        """Default activo=True when not provided."""
        from core.schemas import UsuarioBase

        u = _assert_valid(UsuarioBase, {"username": "admin"})
        assert u.activo is True

    def test_usuariobase_optional_fields(self):
        """Optional fields can be omitted."""
        from core.schemas import UsuarioBase

        u = _assert_valid(UsuarioBase, {"username": "admin"})
        assert u.nombre is None
        assert u.rol is None
        assert u.email is None

    def test_usuariobase_con_todos(self):
        """All fields provided."""
        from core.schemas import UsuarioBase

        u = _assert_valid(
            UsuarioBase,
            {
                "username": "jdoe",
                "nombre": "John Doe",
                "rol": "Operador",
                "email": "john@test.com",
            },
        )
        assert u.nombre == "John Doe"
        assert u.rol == "Operador"
        assert u.email == "john@test.com"

    # ── UsuarioCreate ──

    def test_usuariocreate_requiere_password_raw(self):
        """UsuarioCreate requires password_raw."""
        from core.schemas import UsuarioCreate

        _assert_validation_error(UsuarioCreate, {"username": "admin"}, "password_raw")

    def test_usuariocreate_password_min_length(self):
        """password_raw must be >= 6 chars."""
        from core.schemas import UsuarioCreate

        _assert_validation_error(
            UsuarioCreate, {"username": "admin", "password_raw": "Ab1!"}, "password_raw"
        )

    def test_usuariocreate_password_max_length(self):
        """password_raw must be <= 100 chars."""
        from core.schemas import UsuarioCreate

        _assert_validation_error(
            UsuarioCreate, {"username": "admin", "password_raw": "A" * 101}, "password_raw"
        )

    def test_usuariocreate_valid(self):
        """Valid UsuarioCreate."""
        from core.schemas import UsuarioCreate

        u = _assert_valid(UsuarioCreate, {"username": "new_user", "password_raw": "SecurePass1!"})
        assert u.password_raw == "SecurePass1!"

    # ── UsuarioUpdate ──

    def test_usuarioupdate_requiere_username(self):
        """UsuarioUpdate requires username."""
        from core.schemas import UsuarioUpdate

        _assert_validation_error(UsuarioUpdate, {}, "username")

    def test_usuarioupdate_optional_fields(self):
        """UsuarioUpdate optional fields can be omitted."""
        from core.schemas import UsuarioUpdate

        u = _assert_valid(UsuarioUpdate, {"username": "admin"})
        assert u.nombre is None
        assert u.rol is None
        assert u.activo is None
        assert u.password_raw is None

    def test_usuarioupdate_valid(self):
        """Valid UsuarioUpdate with all fields."""
        from core.schemas import UsuarioUpdate

        u = _assert_valid(
            UsuarioUpdate,
            {
                "username": "admin",
                "nombre": "Admin",
                "rol": "Administrador",
                "activo": False,
            },
        )
        assert u.nombre == "Admin"
        assert u.activo is False

    # ── UsuarioResponse ──

    def test_usuarioresponse_from_attributes(self):
        """UsuarioResponse can be built from an ORM-like dict."""
        from core.schemas import UsuarioResponse

        now = datetime(2026, 5, 1, 12, 0, 0)
        u = UsuarioResponse.model_validate(
            {
                "id": 1,
                "username": "admin",
                "nombre": "Admin",
                "rol": "Administrador",
                "email": "admin@test.com",
                "activo": True,
                "ultimo_acceso": None,
                "created_at": now,
                "updated_at": now,
            }
        )
        assert u.id == 1
        assert u.username == "admin"
        assert u.created_at == now

    def test_usuarioresponse_sin_id_falla(self):
        """UsuarioResponse requires id."""
        from core.schemas import UsuarioResponse

        now = datetime.now()
        _assert_validation_error(
            UsuarioResponse,
            {
                "username": "admin",
                "created_at": now,
                "updated_at": now,
            },
            "id",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# AUTO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoSchemas:
    """AutoBase, AutoCreate, AutoUpdate, AutoResponse."""

    def test_autobase_requiere_placa(self):
        """Placa is required."""
        from core.schemas import AutoBase

        _assert_validation_error(AutoBase, {}, "placa")

    def test_autobase_placa_pattern(self):
        """Placa only allows uppercase letters and numbers."""
        from core.schemas import AutoBase

        _assert_validation_error(AutoBase, {"placa": "abc-123"}, "placa")

    def test_autobase_placa_min_length(self):
        """Placa must be >= 6 chars."""
        from core.schemas import AutoBase

        _assert_validation_error(AutoBase, {"placa": "ABC12"}, "placa")

    def test_autobase_valid(self):
        """Valid AutoBase with only placa."""
        from core.schemas import AutoBase

        a = _assert_valid(AutoBase, {"placa": "ABC123"})
        assert a.placa == "ABC123"

    def test_autobase_defaults(self):
        """AutoBase defaults are applied."""
        from core.schemas import AutoBase

        a = _assert_valid(AutoBase, {"placa": "XYZ789"})
        assert a.estado == "Disponible"
        assert a.kilometraje == 0.0
        assert a.costo_fijo_mensual == Decimal("0.00")
        assert a.fecha_ingreso == date.today()

    def test_autobase_optional_fields(self):
        """AutoBase optional fields can be omitted."""
        from core.schemas import AutoBase

        a = _assert_valid(AutoBase, {"placa": "DEF456"})
        assert a.marca is None
        assert a.modelo is None
        assert a.color is None

    def test_autobase_kilometraje_no_negativo(self):
        """Kilometraje must be >= 0."""
        from core.schemas import AutoBase

        _assert_validation_error(AutoBase, {"placa": "ABC123", "kilometraje": -1}, "kilometraje")

    def test_autobase_full(self):
        """AutoBase with all fields."""
        from core.schemas import AutoBase

        a = _assert_valid(
            AutoBase,
            {
                "placa": "ABC123",
                "marca": "Toyota",
                "modelo": "Corolla",
                "color": "Blanco",
                "tipo": "Automóvil",
                "transmision": "Automática",
                "combustible": "Gasolina",
                "estado": "Disponible",
                "kilometraje": 15000.5,
            },
        )
        assert a.marca == "Toyota"
        assert a.kilometraje == 15000.5

    # ── AutoCreate ──

    def test_autocreate_hereda_autobase(self):
        """AutoCreate has same fields as AutoBase (pass-through)."""
        from core.schemas import AutoCreate

        a = _assert_valid(AutoCreate, {"placa": "LMN456"})
        assert a.placa == "LMN456"

    # ── AutoUpdate ──

    def test_autoupdate_requires_placa(self):
        """AutoUpdate requires placa."""
        from core.schemas import AutoUpdate

        _assert_validation_error(AutoUpdate, {}, "placa")

    def test_autoupdate_optional_fields(self):
        """AutoUpdate fields are optional."""
        from core.schemas import AutoUpdate

        a = _assert_valid(AutoUpdate, {"placa": "ABC123"})
        assert a.marca is None
        assert a.estado is None
        assert a.kilometraje is None

    def test_autoupdate_valid(self):
        """AutoUpdate with partial fields."""
        from core.schemas import AutoUpdate

        a = _assert_valid(
            AutoUpdate,
            {
                "placa": "ABC123",
                "marca": "Mazda",
                "kilometraje": 20000.0,
            },
        )
        assert a.marca == "Mazda"
        assert a.kilometraje == 20000.0

    # ── AutoResponse ──

    def test_autoresponse_from_attributes(self):
        """AutoResponse from ORM dict."""
        from core.schemas import AutoResponse

        now = datetime.now()
        a = AutoResponse.model_validate(
            {
                "placa": "ABC123",
                "marca": "Toyota",
                "created_at": now,
                "updated_at": now,
            }
        )
        assert a.placa == "ABC123"
        assert a.marca == "Toyota"


# ═══════════════════════════════════════════════════════════════════════════════
# CLIENTE schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestClienteSchemas:
    """ClienteBase, ClienteCreate, ClienteUpdate, ClienteResponse."""

    def test_clientebase_requiere_nombre_completo(self):
        """nombre_completo defaults to '' when not provided."""
        from core.schemas import ClienteBase

        c = _assert_valid(ClienteBase, {})
        assert c.nombre_completo == ""

    def test_clientebase_defaults(self):
        """ClienteBase defaults: estado=Activo, nombre_completo=''."""
        from core.schemas import ClienteBase

        c = _assert_valid(ClienteBase, {"nombre_completo": "Juan Pérez"})
        assert c.estado == "Activo"
        assert c.nombre_completo == "Juan Pérez"

    def test_clientebase_optional_fields(self):
        """Optional fields can be omitted."""
        from core.schemas import ClienteBase

        c = _assert_valid(ClienteBase, {"nombre_completo": "Ana"})
        assert c.tipo_doc is None
        assert c.no_doc is None
        assert c.celular is None

    def test_clientebase_validador_genera_nombre_desde_nombres(self):
        """generar_nombre_completo model_validator builds nombre_completo from nombres+apellidos."""
        from core.schemas import ClienteBase

        c = _assert_valid(
            ClienteBase,
            {
                "nombres": "Carlos",
                "apellidos": "López",
            },
        )
        assert c.nombre_completo == "Carlos López"

    def test_clientebase_validador_no_sobrescribe_si_provisto(self):
        """generar_nombre does NOT override explicit nombre_completo."""
        from core.schemas import ClienteBase

        c = _assert_valid(
            ClienteBase,
            {
                "nombre_completo": "Explicit Name",
                "nombres": "Carlos",
                "apellidos": "López",
            },
        )
        assert c.nombre_completo == "Explicit Name"

    def test_clientebase_full(self):
        """ClienteBase with all fields."""
        from core.schemas import ClienteBase

        c = _assert_valid(
            ClienteBase,
            {
                "tipo_doc": "Cédula",
                "no_doc": "12345678",
                "nombres": "María",
                "apellidos": "García",
                "nombre_completo": "María García",
                "celular": "3001234567",
                "email": "maria@test.com",
                "ciudad": "Bogotá",
                "pais": "Colombia",
                "estado": "VIP",
            },
        )
        assert c.no_doc == "12345678"
        assert c.estado == "VIP"

    # ── ClienteCreate ──

    def test_clientecreate_hereda_clientebase(self):
        """ClienteCreate passes through."""
        from core.schemas import ClienteCreate

        c = _assert_valid(ClienteCreate, {"nombre_completo": "Test"})
        assert c.nombre_completo == "Test"

    # ── ClienteUpdate ──

    def test_clienteupdate_requiere_id(self):
        """ClienteUpdate requires id."""
        from core.schemas import ClienteUpdate

        _assert_validation_error(ClienteUpdate, {}, "id")

    def test_clienteupdate_id_gt_0(self):
        """ClienteUpdate id must be > 0."""
        from core.schemas import ClienteUpdate

        _assert_validation_error(ClienteUpdate, {"id": 0}, "id")

    def test_clienteupdate_optional_fields(self):
        """ClienteUpdate fields are optional."""
        from core.schemas import ClienteUpdate

        c = _assert_valid(ClienteUpdate, {"id": 5})
        assert c.nombre_completo is None
        assert c.estado is None

    # ── ClienteResponse ──

    def test_clienteresponse_from_attributes(self):
        """ClienteResponse from ORM dict."""
        from core.schemas import ClienteResponse

        now = datetime.now()
        c = ClienteResponse.model_validate(
            {
                "id": 1,
                "nombre_completo": "Juan",
                "created_at": now,
                "updated_at": now,
            }
        )
        assert c.id == 1
        assert c.nombre_completo == "Juan"


# ═══════════════════════════════════════════════════════════════════════════════
# RENTA schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestRentaSchemas:
    """RentaBase, RentaCreate, RentaCierre, RentaUpdate, RentaResponse."""

    def test_rentabase_requiere_campos(self):
        """RentaBase requires placa, fecha_recogida, hora_recogida, fecha_retorno, hora_retorno."""
        from core.schemas import RentaBase

        _assert_validation_error(RentaBase, {}, "placa")

    def test_rentabase_minimal(self):
        """RentaBase with only required fields."""
        from core.schemas import RentaBase

        r = _assert_valid(
            RentaBase,
            {
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
            },
        )
        assert r.placa == "ABC123"
        assert r.estado == "Activo"

    def test_rentabase_defaults(self):
        """RentaBase default values."""
        from core.schemas import RentaBase

        r = _assert_valid(
            RentaBase,
            {
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
            },
        )
        assert r.estado == "Activo"
        assert r.valor_dia == Decimal("0.00")
        assert r.subtotal == Decimal("0.00")
        assert r.total == Decimal("0.00")
        assert r.descuento == Decimal("0.00")
        assert r.ubicacion_recogida == "Oficina"
        assert r.ubicacion_retorno == "Oficina"
        assert r.tanque_salida == "Lleno"

    def test_rentabase_valor_dia_no_negativo(self):
        """valor_dia must be >= 0."""
        from core.schemas import RentaBase

        _assert_validation_error(
            RentaBase,
            {
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
                "valor_dia": Decimal("-1"),
            },
            "valor_dia",
        )

    # ── RentaCreate ──

    def test_rentacreate_hereda(self):
        """RentaCreate passes through."""
        from core.schemas import RentaCreate

        r = _assert_valid(
            RentaCreate,
            {
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
            },
        )
        assert r.placa == "ABC123"

    # ── RentaCierre ──

    def test_rentacierre_requiere_campos(self):
        """RentaCierre requires fecha_devolucion_real, hora_devolucion_real."""
        from core.schemas import RentaCierre

        _assert_validation_error(RentaCierre, {}, "fecha_devolucion_real")

    def test_rentacierre_minimal(self):
        """RentaCierre with only required fields."""
        from core.schemas import RentaCierre

        c = _assert_valid(
            RentaCierre,
            {
                "fecha_devolucion_real": date(2026, 5, 5),
                "hora_devolucion_real": time(17, 30),
            },
        )
        assert c.nota_cierre == ""

    def test_rentacierre_con_todo(self):
        """RentaCierre with all fields."""
        from core.schemas import RentaCierre

        c = _assert_valid(
            RentaCierre,
            {
                "fecha_devolucion_real": date(2026, 5, 5),
                "hora_devolucion_real": time(17, 30),
                "km_final": "15600",
                "tanque_final": "Lleno",
                "nota_cierre": "Cliente devolvió en buen estado",
                "otros_cobros": Decimal("50000.00"),
            },
        )
        assert c.km_final == "15600"
        assert c.nota_cierre == "Cliente devolvió en buen estado"

    # ── RentaUpdate ──

    def test_rentaupdate_todo_opcional(self):
        """RentaUpdate all fields optional."""
        from core.schemas import RentaUpdate

        r = _assert_valid(RentaUpdate, {})
        assert r.saldo_pendiente is None

    def test_rentaupdate_valid(self):
        """RentaUpdate with some fields."""
        from core.schemas import RentaUpdate

        r = _assert_valid(
            RentaUpdate,
            {
                "dias_calculados": 5,
                "total": Decimal("500000.00"),
                "observaciones": "Extensión aprobada",
            },
        )
        assert r.dias_calculados == 5
        assert r.total == Decimal("500000.00")

    # ── RentaResponse ──

    def test_rentaresponse_from_attributes(self):
        """RentaResponse from ORM dict."""
        from core.schemas import RentaResponse

        now = datetime.now()
        r = RentaResponse.model_validate(
            {
                "id": 1,
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
                "created_at": now,
            }
        )
        assert r.id == 1
        assert r.placa == "ABC123"


# ═══════════════════════════════════════════════════════════════════════════════
# RESERVA schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestReservaSchemas:
    """ReservaBase, ReservaCreate, ReservaUpdate, ReservaResponse."""

    def test_reservabase_requiere_campos(self):
        """ReservaBase requires fecha_recogida, hora_recogida, fecha_retorno, hora_retorno."""
        from core.schemas import ReservaBase

        _assert_validation_error(ReservaBase, {}, "fecha_recogida")

    def test_reservabase_minimal(self):
        """ReservaBase with only required fields."""
        from core.schemas import ReservaBase

        r = _assert_valid(
            ReservaBase,
            {
                "fecha_recogida": date(2026, 6, 1),
                "hora_recogida": time(9, 0),
                "fecha_retorno": date(2026, 6, 5),
                "hora_retorno": time(17, 0),
            },
        )
        assert r.estado == "Confirmada"

    def test_reservabase_defaults(self):
        """ReservaBase default values."""
        from core.schemas import ReservaBase

        r = _assert_valid(
            ReservaBase,
            {
                "fecha_recogida": date(2026, 6, 1),
                "hora_recogida": time(9, 0),
                "fecha_retorno": date(2026, 6, 5),
                "hora_retorno": time(17, 0),
            },
        )
        assert r.estado == "Confirmada"
        assert r.valor_dia == Decimal("0.00")
        assert r.total == Decimal("0.00")
        assert r.ubicacion_recogida == "Oficina"

    # ── ReservaUpdate ──

    def test_reservaupdate_todo_opcional(self):
        """ReservaUpdate all fields optional."""
        from core.schemas import ReservaUpdate

        r = _assert_valid(ReservaUpdate, {})
        assert r.estado is None

    def test_reservaupdate_valid(self):
        """ReservaUpdate with partial fields."""
        from core.schemas import ReservaUpdate

        r = _assert_valid(
            ReservaUpdate,
            {
                "estado": "Cancelada",
                "observaciones": "Cliente canceló",
            },
        )
        assert r.estado == "Cancelada"

    # ── ReservaResponse ──

    def test_reservaresponse_from_attributes(self):
        """ReservaResponse from ORM dict."""
        from core.schemas import ReservaResponse

        now = datetime.now()
        r = ReservaResponse.model_validate(
            {
                "id": 1,
                "fecha_recogida": date(2026, 6, 1),
                "hora_recogida": time(9, 0),
                "fecha_retorno": date(2026, 6, 5),
                "hora_retorno": time(17, 0),
                "created_at": now,
                "updated_at": now,
            }
        )
        assert r.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# MANTENIMIENTO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestMantenimientoSchemas:
    """MantenimientoBase, MantenimientoCreate, MantenimientoResponse."""

    def test_mantenimientobase_requiere_placa(self):
        """MantenimientoBase requires placa."""
        from core.schemas import MantenimientoBase

        _assert_validation_error(MantenimientoBase, {}, "placa")

    def test_mantenimientobase_minimal(self):
        """MantenimientoBase with only placa."""
        from core.schemas import MantenimientoBase

        m = _assert_valid(MantenimientoBase, {"placa": "ABC123"})
        assert m.cost_varios == Decimal("0.00")
        assert m.total_mantenimiento == Decimal("0.00")

    def test_mantenimientobase_full(self):
        """MantenimientoBase with all fields."""
        from core.schemas import MantenimientoBase

        m = _assert_valid(
            MantenimientoBase,
            {
                "placa": "ABC123",
                "pieza_varias_tipo": "Cambio Aceite",
                "cost_varios": Decimal("150000.00"),
                "total_mantenimiento": Decimal("250000.00"),
            },
        )
        assert m.total_mantenimiento == Decimal("250000.00")

    # ── MantenimientoResponse ──

    def test_mantenimientoresponse_from_attributes(self):
        """MantenimientoResponse from ORM dict."""
        from core.schemas import MantenimientoResponse

        now = datetime.now()
        m = MantenimientoResponse.model_validate(
            {
                "id": 1,
                "placa": "ABC123",
                "created_at": now,
                "updated_at": now,
            }
        )
        assert m.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# COMPARENDO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestComparendoSchemas:
    """ComparendoBase, ComparendoCreate, ComparendoUpdate, ComparendoResponse."""

    def test_comparendobase_requiere_campos(self):
        """ComparendoBase requires placa, fecha_infraccion, hora_infraccion, monto."""
        from core.schemas import ComparendoBase

        _assert_validation_error(ComparendoBase, {}, "placa")

    def test_comparendobase_minimal(self):
        """ComparendoBase with only required fields."""
        from core.schemas import ComparendoBase

        c = _assert_valid(
            ComparendoBase,
            {
                "placa": "ABC123",
                "fecha_infraccion": date(2026, 3, 15),
                "hora_infraccion": time(14, 30),
                "monto": Decimal("500000.00"),
            },
        )
        assert c.estado == "Pendiente"

    def test_comparendobase_monto_gt_0(self):
        """Monto must be >= 0."""
        from core.schemas import ComparendoBase

        _assert_validation_error(
            ComparendoBase,
            {
                "placa": "ABC123",
                "fecha_infraccion": date(2026, 3, 15),
                "hora_infraccion": time(14, 30),
                "monto": Decimal("-100"),
            },
            "monto",
        )

    # ── ComparendoUpdate ──

    def test_comparendoupdate_todo_opcional(self):
        """ComparendoUpdate all fields optional."""
        from core.schemas import ComparendoUpdate

        u = _assert_valid(ComparendoUpdate, {})
        assert u.estado is None
        assert u.observaciones is None

    # ── ComparendoResponse ──

    def test_comparendoresponse_from_attributes(self):
        """ComparendoResponse from ORM dict."""
        from core.schemas import ComparendoResponse

        now = datetime.now()
        c = ComparendoResponse.model_validate(
            {
                "id": 1,
                "placa": "ABC123",
                "fecha_infraccion": date(2026, 3, 15),
                "hora_infraccion": time(14, 30),
                "monto": Decimal("500000.00"),
                "created_at": now,
                "updated_at": now,
            }
        )
        assert c.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# PAGO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagoSchemas:
    """PagoBase, PagoCreate, PagoResponse."""

    def test_pagobase_requiere_campos(self):
        """PagoBase requires id_renta, monto, metodo_pago, concepto."""
        from core.schemas import PagoBase

        _assert_validation_error(PagoBase, {}, "id_renta")

    def test_pagobase_minimal(self):
        """PagoBase with only required fields."""
        from core.schemas import PagoBase

        p = _assert_valid(
            PagoBase,
            {
                "id_renta": 1,
                "monto": Decimal("100000.00"),
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
            },
        )
        assert p.id_renta == 1

    def test_pagobase_monto_gt_0(self):
        """Monto must be > 0."""
        from core.schemas import PagoBase

        _assert_validation_error(
            PagoBase,
            {
                "id_renta": 1,
                "monto": Decimal("-1"),
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
            },
            "monto",
        )

    def test_pagobase_id_renta_gt_0(self):
        """id_renta must be > 0."""
        from core.schemas import PagoBase

        _assert_validation_error(
            PagoBase,
            {
                "id_renta": 0,
                "monto": Decimal("100000.00"),
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
            },
            "id_renta",
        )

    # ── PagoResponse ──

    def test_pagoresponse_from_attributes(self):
        """PagoResponse from ORM dict."""
        from core.schemas import PagoResponse

        now = datetime.now()
        p = PagoResponse.model_validate(
            {
                "id": 1,
                "id_renta": 5,
                "monto": Decimal("100000.00"),
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
                "fecha": now,
                "updated_at": now,
            }
        )
        assert p.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# GASTO schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestGastoSchemas:
    """GastoBase, GastoCreate, GastoResponse."""

    def test_gastobase_requiere_campos(self):
        """GastoBase requires fecha, categoria, descripcion, monto."""
        from core.schemas import GastoBase

        _assert_validation_error(GastoBase, {}, "fecha")

    def test_gastobase_minimal(self):
        """GastoBase with only required fields."""
        from core.schemas import GastoBase

        g = _assert_valid(
            GastoBase,
            {
                "fecha": date(2026, 4, 1),
                "categoria": "Combustible",
                "descripcion": "Gasolina",
                "monto": Decimal("100000.00"),
            },
        )
        assert g.usuario == "Sistema"

    def test_gastobase_monto_gt_0(self):
        """Monto must be > 0."""
        from core.schemas import GastoBase

        _assert_validation_error(
            GastoBase,
            {
                "fecha": date(2026, 4, 1),
                "categoria": "Combustible",
                "descripcion": "Gasolina",
                "monto": Decimal("-1"),
            },
            "monto",
        )

    def test_gastobase_con_placa(self):
        """GastoBase with optional placa."""
        from core.schemas import GastoBase

        g = _assert_valid(
            GastoBase,
            {
                "placa": "ABC123",
                "fecha": date(2026, 4, 1),
                "categoria": "Mantenimiento",
                "descripcion": "Cambio aceite",
                "monto": Decimal("150000.00"),
            },
        )
        assert g.placa == "ABC123"

    # ── GastoResponse ──

    def test_gastoresponse_from_attributes(self):
        """GastoResponse from ORM dict."""
        from core.schemas import GastoResponse

        now = datetime.now()
        g = GastoResponse.model_validate(
            {
                "id": 1,
                "fecha": date(2026, 4, 1),
                "categoria": "Combustible",
                "descripcion": "Gasolina",
                "monto": Decimal("100000.00"),
                "created_at": now,
                "updated_at": now,
            }
        )
        assert g.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# INSPECCION schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestInspeccionSchemas:
    """InspeccionBase, InspeccionCreate, InspeccionResponse."""

    def test_inspeccionbase_requiere_campos(self):
        """InspeccionBase requires id_renta, tipo, kilometraje, nivel_gasolina."""
        from core.schemas import InspeccionBase

        _assert_validation_error(InspeccionBase, {}, "id_renta")

    def test_inspeccionbase_minimal(self):
        """InspeccionBase with only required fields."""
        from core.schemas import InspeccionBase

        i = _assert_valid(
            InspeccionBase,
            {
                "id_renta": 1,
                "tipo": "Salida",
                "kilometraje": 5000.0,
                "nivel_gasolina": "Lleno",
            },
        )
        assert i.limpieza == "Limpio"
        assert i.tiene_repuesto is True
        assert i.tiene_documentos is True

    def test_inspeccionbase_kilometraje_no_negativo(self):
        """Kilometraje must be >= 0."""
        from core.schemas import InspeccionBase

        _assert_validation_error(
            InspeccionBase,
            {
                "id_renta": 1,
                "tipo": "Salida",
                "kilometraje": -1,
                "nivel_gasolina": "Lleno",
            },
            "kilometraje",
        )

    # ── InspeccionResponse ──

    def test_inspeccionresponse_from_attributes(self):
        """InspeccionResponse from ORM dict."""
        from core.schemas import InspeccionResponse

        now = datetime.now()
        i = InspeccionResponse.model_validate(
            {
                "id": 1,
                "id_renta": 5,
                "tipo": "Salida",
                "kilometraje": 1000.0,
                "nivel_gasolina": "Medio",
                "fecha": now,
            }
        )
        assert i.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# LOGIN schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestLoginSchemas:
    """LoginRequest, LoginResponse."""

    def test_loginrequest_requiere_campos(self):
        """LoginRequest requires username and password."""
        from core.schemas import LoginRequest

        _assert_validation_error(LoginRequest, {}, "username")

    def test_loginrequest_min_length(self):
        """Username min_length=3."""
        from core.schemas import LoginRequest

        _assert_validation_error(
            LoginRequest,
            {
                "username": "ab",
                "password": "pass123",
            },
            "username",
        )

    def test_loginrequest_valid(self):
        """Valid LoginRequest."""
        from core.schemas import LoginRequest

        result = _assert_valid(
            LoginRequest,
            {
                "username": "admin",
                "password": "s3cr3t",
            },
        )
        assert result.username == "admin"
        assert result.password == "s3cr3t"

    def test_loginresponse_valid(self):
        """Valid LoginResponse."""
        from core.schemas import LoginResponse

        result = _assert_valid(
            LoginResponse,
            {
                "success": True,
                "session_id": "abc123",
                "username": "admin",
                "nombre": "Admin",
                "rol": "Administrador",
            },
        )
        assert result.success is True
        assert result.rol == "Administrador"


# ═══════════════════════════════════════════════════════════════════════════════
# COMPOSITE / RESPONSE schemas
# ═══════════════════════════════════════════════════════════════════════════════


class TestRentaDetalleResponse:
    """RentaDetalleResponse — extended Renta with auto/cliente fields."""

    def test_minimal(self):
        """RentaDetalleResponse with required fields."""
        from core.schemas import RentaDetalleResponse

        now = datetime.now()
        r = _assert_valid(
            RentaDetalleResponse,
            {
                "id": 1,
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
                "created_at": now,
            },
        )
        assert r.id == 1
        assert r.auto_marca is None
        assert r.cliente_celular is None

    def test_con_auto_cliente(self):
        """RentaDetalleResponse with auto and cliente data."""
        from core.schemas import RentaDetalleResponse

        now = datetime.now()
        r = _assert_valid(
            RentaDetalleResponse,
            {
                "id": 1,
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
                "created_at": now,
                "auto_marca": "Toyota",
                "auto_modelo": "Corolla",
                "cliente_celular": "3001234567",
                "cliente_email": "cliente@test.com",
            },
        )
        assert r.auto_marca == "Toyota"
        assert r.cliente_celular == "3001234567"

    def test_con_cierre(self):
        """RentaDetalleResponse with closure fields."""
        from core.schemas import RentaDetalleResponse

        now = datetime.now()
        r = _assert_valid(
            RentaDetalleResponse,
            {
                "id": 1,
                "placa": "ABC123",
                "fecha_recogida": date(2026, 5, 1),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date(2026, 5, 5),
                "hora_retorno": time(18, 0),
                "created_at": now,
                "fecha_devolucion_real": date(2026, 5, 5),
                "hora_devolucion_real": time(17, 0),
                "km_final": "15600",
                "tanque_final": "Lleno",
            },
        )
        assert r.fecha_devolucion_real == date(2026, 5, 5)
        assert r.km_final == "15600"


class TestKpiGlobalesResponse:
    """KpiGlobalesResponse — dashboard KPIs."""

    def test_defaults(self):
        """All fields default to 0."""
        from core.schemas import KpiGlobalesResponse

        k = _assert_valid(KpiGlobalesResponse, {})
        assert k.rentas_activas == 0
        assert k.autos_disponibles == 0
        assert k.ocupacion_flota == 0.0
        assert k.ingresos_mes == 0.0

    def test_con_valores(self):
        """KpiGlobalesResponse with values."""
        from core.schemas import KpiGlobalesResponse

        k = _assert_valid(
            KpiGlobalesResponse,
            {
                "rentas_activas": 5,
                "autos_disponibles": 12,
                "total_flota": 20,
                "ocupacion_flota": 65.5,
                "ingresos_mes": 15000000.0,
            },
        )
        assert k.rentas_activas == 5
        assert k.ocupacion_flota == 65.5


class TestResumenFinancieroResponse:
    """ResumenFinancieroResponse — monthly financial summary."""

    def test_defaults(self):
        """All fields default to 0."""
        from core.schemas import ResumenFinancieroResponse

        r = _assert_valid(ResumenFinancieroResponse, {"mes": "2026-05"})
        assert r.mes == "2026-05"
        assert r.ingresos_mes == 0.0
        assert r.utilidad_mes == 0.0

    def test_con_valores(self):
        """ResumenFinancieroResponse with values."""
        from core.schemas import ResumenFinancieroResponse

        r = _assert_valid(
            ResumenFinancieroResponse,
            {
                "mes": "2026-05",
                "ingresos_mes": 50000000.0,
                "egresos_taller_mes": 5000000.0,
                "gastos_caja_mes": 2000000.0,
                "utilidad_mes": 43000000.0,
            },
        )
        assert r.utilidad_mes == 43000000.0


class TestRoiVehiculoResponse:
    """RoiVehiculoResponse — vehicle ROI."""

    def test_minimal(self):
        """RoiVehiculoResponse with only placa and vehiculo."""
        from core.schemas import RoiVehiculoResponse

        r = _assert_valid(
            RoiVehiculoResponse,
            {
                "placa": "ABC123",
                "vehiculo": "Toyota Corolla",
            },
        )
        assert r.ingresos == 0.0
        assert r.roi_pct == 0.0

    def test_con_valores(self):
        """RoiVehiculoResponse with financial data."""
        from core.schemas import RoiVehiculoResponse

        r = _assert_valid(
            RoiVehiculoResponse,
            {
                "placa": "ABC123",
                "vehiculo": "Toyota Corolla",
                "ingresos": 15000000.0,
                "mantenimiento": 2000000.0,
                "gastos": 1000000.0,
                "costos_fijos": 3000000.0,
                "utilidad": 9000000.0,
                "roi_pct": 60.0,
                "equilibrio_dias": 180.0,
            },
        )
        assert r.roi_pct == 60.0
        assert r.utilidad == 9000000.0


class TestBalanceMensualItemResponse:
    """BalanceMensualItemResponse — monthly balance item."""

    def test_minimal(self):
        """BalanceMensualItemResponse with only mes."""
        from core.schemas import BalanceMensualItemResponse

        b = _assert_valid(BalanceMensualItemResponse, {"mes": "2026-05"})
        assert b.ingresos == 0.0


class TestAlertaClienteResponse:
    """AlertaClienteResponse — client alert."""

    def test_requiere_campos(self):
        """AlertaClienteResponse requires titulo, cliente, fecha, mensaje_whatsapp."""
        from core.schemas import AlertaClienteResponse

        _assert_validation_error(AlertaClienteResponse, {}, "titulo")

    def test_minimal(self):
        """AlertaClienteResponse with required fields."""
        from core.schemas import AlertaClienteResponse

        a = _assert_valid(
            AlertaClienteResponse,
            {
                "titulo": "Vencimiento",
                "cliente": "Juan Pérez",
                "fecha": "2026-05-10",
                "mensaje_whatsapp": "Hola Juan, su renta vence...",
            },
        )
        assert a.titulo == "Vencimiento"
        assert a.celular is None


class TestAlertaInternaResponse:
    """AlertaInternaResponse — internal alert."""

    def test_minimal(self):
        """AlertaInternaResponse with required fields."""
        from core.schemas import AlertaInternaResponse

        a = _assert_valid(
            AlertaInternaResponse,
            {
                "titulo": "Vencimiento SOAT",
                "descripcion": "El SOAT del vehículo ABC123 vence en 5 días",
            },
        )
        assert a.nivel == "Advertencia"


class TestAlertasResponse:
    """AlertasResponse — consolidated alerts."""

    def test_defaults(self):
        """AlertasResponse defaults to empty lists."""
        from core.schemas import AlertasResponse

        a = _assert_valid(AlertasResponse, {})
        assert a.clientes == []
        assert a.internas == []

    def test_con_datos(self):
        """AlertasResponse with data."""
        from core.schemas import AlertasResponse

        a = _assert_valid(
            AlertasResponse,
            {
                "clientes": [
                    {
                        "titulo": "Vencimiento",
                        "cliente": "Juan",
                        "fecha": "2026-05-10",
                        "mensaje_whatsapp": "Hola",
                    },
                ],
                "internas": [
                    {"titulo": "Vencimiento SOAT", "descripcion": "Vence en 5 días"},
                ],
            },
        )
        assert len(a.clientes) == 1
        assert len(a.internas) == 1


class TestCalendarioItemResponse:
    """CalendarioItemResponse — calendar item."""

    def test_requiere_campos(self):
        """CalendarioItemResponse requires tipo, id, estado."""
        from core.schemas import CalendarioItemResponse

        _assert_validation_error(CalendarioItemResponse, {}, "tipo")

    def test_minimal(self):
        """CalendarioItemResponse with required fields."""
        from core.schemas import CalendarioItemResponse

        c = _assert_valid(
            CalendarioItemResponse,
            {
                "tipo": "renta",
                "id": 1,
                "estado": "Activo",
            },
        )
        assert c.tipo == "renta"


class TestComparendoRegistroResponse:
    """ComparendoRegistroResponse — comparendo registration result."""

    def test_requiere_campos(self):
        """ComparendoRegistroResponse requires id_comparendo."""
        from core.schemas import ComparendoRegistroResponse

        _assert_validation_error(ComparendoRegistroResponse, {}, "id_comparendo")

    def test_minimal(self):
        """ComparendoRegistroResponse with required fields."""
        from core.schemas import ComparendoRegistroResponse

        c = _assert_valid(
            ComparendoRegistroResponse,
            {
                "id_comparendo": 1,
                "vinculado": False,
            },
        )
        assert c.vinculado is False
        assert c.id_renta is None

    def test_vinculado(self):
        """ComparendoRegistroResponse when linked."""
        from core.schemas import ComparendoRegistroResponse

        c = _assert_valid(
            ComparendoRegistroResponse,
            {
                "id_comparendo": 1,
                "vinculado": True,
                "id_renta": 5,
                "id_cliente": 3,
            },
        )
        assert c.vinculado is True
        assert c.id_renta == 5


# ═══════════════════════════════════════════════════════════════════════════════
# Module exports
# ═══════════════════════════════════════════════════════════════════════════════


class TestModuleExports:
    """All schemas are importable from core.schemas."""

    def test_todos_los_schemas_importables(self):
        """Key schemas are importable."""
        from core.schemas import (
            BaseSchema,
            UsuarioBase,
            UsuarioCreate,
            UsuarioUpdate,
            UsuarioResponse,
            AutoBase,
            AutoCreate,
            AutoUpdate,
            AutoResponse,
            ClienteBase,
            ClienteCreate,
            ClienteUpdate,
            ClienteResponse,
            RentaBase,
            RentaCreate,
            RentaCierre,
            RentaUpdate,
            RentaResponse,
            RentaDetalleResponse,
            ReservaBase,
            ReservaCreate,
            ReservaUpdate,
            ReservaResponse,
            MantenimientoBase,
            MantenimientoCreate,
            MantenimientoResponse,
            ComparendoBase,
            ComparendoCreate,
            ComparendoUpdate,
            ComparendoResponse,
            PagoBase,
            PagoCreate,
            PagoResponse,
            GastoBase,
            GastoCreate,
            GastoResponse,
            InspeccionBase,
            InspeccionCreate,
            InspeccionResponse,
            LoginRequest,
            LoginResponse,
            KpiGlobalesResponse,
            ResumenFinancieroResponse,
            RoiVehiculoResponse,
            BalanceMensualItemResponse,
            AlertaClienteResponse,
            AlertaInternaResponse,
            AlertasResponse,
            CalendarioItemResponse,
            ComparendoRegistroResponse,
        )

        # Verify they all have model_config
        schemas = [
            BaseSchema,
            UsuarioBase,
            UsuarioCreate,
            UsuarioUpdate,
            UsuarioResponse,
            AutoBase,
            AutoCreate,
            AutoUpdate,
            AutoResponse,
            ClienteBase,
            ClienteCreate,
            ClienteUpdate,
            ClienteResponse,
            RentaBase,
            RentaCreate,
            RentaCierre,
            RentaUpdate,
            RentaResponse,
            RentaDetalleResponse,
            ReservaBase,
            ReservaCreate,
            ReservaUpdate,
            ReservaResponse,
            MantenimientoBase,
            MantenimientoCreate,
            MantenimientoResponse,
            ComparendoBase,
            ComparendoCreate,
            ComparendoUpdate,
            ComparendoResponse,
            PagoBase,
            PagoCreate,
            PagoResponse,
            GastoBase,
            GastoCreate,
            GastoResponse,
            InspeccionBase,
            InspeccionCreate,
            InspeccionResponse,
            LoginRequest,
            LoginResponse,
            KpiGlobalesResponse,
            ResumenFinancieroResponse,
            RoiVehiculoResponse,
            BalanceMensualItemResponse,
            AlertaClienteResponse,
            AlertaInternaResponse,
            AlertasResponse,
            CalendarioItemResponse,
            ComparendoRegistroResponse,
        ]
        for s in schemas:
            assert hasattr(s, "model_config"), f"{s.__name__} missing model_config"
