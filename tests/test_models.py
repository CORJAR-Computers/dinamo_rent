"""
test_models.py — Unit tests for core/models.py

Covers all 14 SQLAlchemy models:
  Base, Usuario, Auto, Cliente, Renta, Reserva,
  MantenimientoVehiculo, Configuracion, Auditoria,
  Inspeccion, Comparendo, Pago, Gasto

Strategy:
  - Column/constraint metadata uses an isolated in-memory engine via inspect()
  - CRUD/persistence uses conftest's db_session fixture (global in-memory DB)
  - __repr__ tests verify string format without persisting

Run: pytest tests/test_models.py -v
"""

from decimal import Decimal
from datetime import date, datetime

import pytest
from sqlalchemy import inspect, Integer, String

from core.models import Base


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture(scope="module")
def model_inspector():
    """Create an isolated in-memory engine with all tables, return inspector."""
    from sqlalchemy import create_engine

    engine = create_engine("sqlite://")
    Base.metadata.create_all(bind=engine)
    return inspect(engine)


def _assert_column(
    inspector,
    table,
    name,
    type_class,
    nullable=None,
    primary_key=False,
    unique=False,
    server_default=None,
):
    """Helper: assert a column exists with the expected properties."""
    columns = {c["name"]: c for c in inspector.get_columns(table)}
    assert name in columns, f"Column '{name}' not found in table '{table}'"
    col = columns[name]
    assert isinstance(
        col["type"], type_class
    ), f"Column '{table}.{name}' expected {type_class.__name__}, got {type(col['type']).__name__}"
    if nullable is not None:
        assert (
            col["nullable"] is nullable
        ), f"Column '{table}.{name}' nullable expected {nullable}, got {col['nullable']}"
    if primary_key:
        pk = set(inspector.get_pk_constraint(table)["constrained_columns"])
        assert name in pk, f"Column '{table}.{name}' should be primary key"
    if unique:
        unique_cols = set()
        for uq in inspector.get_unique_constraints(table):
            unique_cols.update(uq["column_names"])
        assert name in unique_cols, f"Column '{table}.{name}' should be unique"


def _assert_index(inspector, table, column_names):
    """Helper: assert an index exists covering the given columns."""
    indexes = inspector.get_indexes(table)
    for idx in indexes:
        if set(idx["column_names"]) == set(column_names):
            return
    raise AssertionError(
        f"No index on {table} covering {column_names}. "
        f"Existing indexes: {[i['column_names'] for i in indexes]}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Base
# ═══════════════════════════════════════════════════════════════════════════════


class TestBase:
    """DeclarativeBase is properly configured."""

    def test_base_es_declarative(self):
        """Base inherits from DeclarativeBase."""
        from sqlalchemy.orm import DeclarativeBase

        assert issubclass(Base, DeclarativeBase)

    def test_metadata_tiene_tablas(self, model_inspector):
        """Base.metadata contains all expected table names."""
        tables = set(model_inspector.get_table_names())
        expected = {
            "usuarios",
            "autos",
            "clientes",
            "rentas",
            "reservas",
            "mantenimiento_vehiculos",
            "configuracion",
            "auditoria",
            "inspecciones",
            "comparendos",
            "pagos",
            "gastos",
        }
        missing = expected - tables
        assert not missing, f"Tables not found: {missing}"


# ═══════════════════════════════════════════════════════════════════════════════
# Usuario
# ═══════════════════════════════════════════════════════════════════════════════


class TestUsuarioModel:
    """Usuario model — users."""

    def test_table_name(self):
        """Usuario maps to 'usuarios'."""
        from core.models import Usuario

        assert Usuario.__tablename__ == "usuarios"

    def test_crear_con_campos_requeridos(self, db_session):
        """Usuario can be created with minimum required fields."""
        from core.models import Usuario

        user = Usuario(username="test_user", password="s3cr3t")
        db_session.add(user)
        db_session.flush()
        assert user.id is not None
        assert isinstance(user.id, int)

    def test_crear_con_todos_los_campos(self, db_session):
        """Usuario can be created with all fields."""
        from core.models import Usuario

        user = Usuario(
            username="full_user",
            password="hashed_pwd",
            nombre="Juan Pérez",
            rol="Administrador",
            email="juan@example.com",
            activo=1,
            intentos_fallidos=0,
            debe_cambiar_password=0,
            ultimo_acceso=datetime(2026, 1, 15, 10, 30, 0),
        )
        db_session.add(user)
        db_session.flush()
        assert user.id is not None

    def test_defaults(self, db_session):
        """Usuario server_default values are set on persist."""
        from core.models import Usuario

        user = Usuario(username="defaults_user", password="x")
        db_session.add(user)
        db_session.flush()
        assert user.activo == 1
        assert user.intentos_fallidos == 0
        assert user.debe_cambiar_password == 0
        assert user.created_at is not None
        assert user.updated_at is not None

    def test_username_unique(self, db_session):
        """Username must be unique."""
        from core.models import Usuario

        db_session.add(Usuario(username="unique_user", password="a"))
        db_session.flush()
        with pytest.raises(Exception):
            db_session.add(Usuario(username="unique_user", password="b"))
            db_session.flush()

    def test_repr(self):
        """__repr__ returns expected format."""
        from core.models import Usuario

        u = Usuario(username="admin", rol="Administrador")
        assert repr(u) == "<Usuario admin (Administrador)>"

    def test_columnas_usuario(self, model_inspector):
        """Usuario columns match model definition."""
        from core.models import Usuario

        _assert_column(model_inspector, "usuarios", "id", Integer, primary_key=True)
        _assert_column(model_inspector, "usuarios", "username", String, nullable=False)
        # SQLite doesn't expose unique=True as a separate constraint
        # when combined with index=True; check via metadata instead
        assert Usuario.__table__.columns["username"].unique, "username should be unique"
        _assert_column(model_inspector, "usuarios", "password", String, nullable=False)
        _assert_column(model_inspector, "usuarios", "nombre", String, nullable=True)
        _assert_column(model_inspector, "usuarios", "rol", String, nullable=True)
        _assert_column(model_inspector, "usuarios", "email", String, nullable=True)

    def test_username_indexed(self, model_inspector):
        """username column has an index."""
        _assert_index(model_inspector, "usuarios", ["username"])


# ═══════════════════════════════════════════════════════════════════════════════
# Auto
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoModel:
    """Auto model — vehicles."""

    def test_table_name(self):
        """Auto maps to 'autos'."""
        from core.models import Auto

        assert Auto.__tablename__ == "autos"

    def test_crear_con_placa(self, db_session):
        """Auto requires placa as primary key."""
        from core.models import Auto

        auto = Auto(placa="ABC123")
        db_session.add(auto)
        db_session.flush()
        assert auto.placa == "ABC123"

    def test_crear_con_todos_los_campos(self, db_session):
        """Auto can be created with all fields."""
        from core.models import Auto

        auto = Auto(
            placa="XYZ999",
            marca="Toyota",
            modelo="Corolla",
            version="XLI",
            color="Blanco",
            tipo="Automóvil",
            cilindraje="1800",
            transmision="Automática",
            combustible="Gasolina",
            no_motor="MOTOR123",
            no_chasis="CHASIS456",
            propietario="Empresa S.A.S.",
            estado="Disponible",
            costo_fijo_mensual=Decimal("500.00"),
            kilometraje=15000.50,
            ubicacion="Bodega Norte",
            tipo_adquisicion="Propio",
            proximo_aceite=5000,
            proximo_frenos=10000,
            observaciones="Vehículo nuevo",
            fecha_ingreso=date(2026, 1, 1),
        )
        db_session.add(auto)
        db_session.flush()

    def test_defaults_auto(self, db_session):
        """Auto server_default values are set on persist."""
        from core.models import Auto

        auto = Auto(placa="DEF456")
        db_session.add(auto)
        db_session.flush()
        assert auto.estado == "Disponible"
        assert auto.kilometraje == 0.0

    def test_repr(self):
        """Auto __repr__ returns expected format."""
        from core.models import Auto

        a = Auto(placa="ABC123", marca="Mazda", modelo="3")
        assert repr(a) == "<Auto ABC123 - Mazda 3>"

    def test_estado_indexed(self, model_inspector):
        """estado column on autos has an index."""
        _assert_index(model_inspector, "autos", ["estado"])

    def test_relaciones_auto(self, db_session):
        """Auto has relationships: rentas, mantenimientos, comparendos, reservas, gastos."""
        from core.models import Auto

        a = Auto(placa="REL01")
        db_session.add(a)
        db_session.flush()
        assert hasattr(a, "rentas")
        assert hasattr(a, "mantenimientos")
        assert hasattr(a, "comparendos")
        assert hasattr(a, "reservas")
        assert hasattr(a, "gastos")


# ═══════════════════════════════════════════════════════════════════════════════
# Cliente
# ═══════════════════════════════════════════════════════════════════════════════


class TestClienteModel:
    """Cliente model — clients."""

    def test_table_name(self):
        """Cliente maps to 'clientes'."""
        from core.models import Cliente

        assert Cliente.__tablename__ == "clientes"

    def test_crear_minimo(self, db_session):
        """Cliente can be created with minimum required fields."""
        from core.models import Cliente

        c = Cliente(nombre_completo="Carlos López")
        db_session.add(c)
        db_session.flush()
        assert c.id is not None

    def test_crear_completo(self, db_session):
        """Cliente can be created with all fields."""
        from core.models import Cliente

        c = Cliente(
            tipo_doc="Cédula",
            no_doc="12345678",
            nombres="Carlos",
            apellidos="López Pérez",
            nombre_completo="Carlos López Pérez",
            celular="3001234567",
            celular2="3017654321",
            email="carlos@email.com",
            ciudad="Medellín",
            estado_region="Antioquia",
            pais="Colombia",
            nacionalidad="Colombiana",
            dir_residencia="Calle 1 #2-3",
            no_licencia="LIC12345",
            tipo_licencia="B1",
            vencimiento_licencia=date(2027, 5, 10),
            estado="Activo",
        )
        db_session.add(c)
        db_session.flush()
        assert c.id is not None

    def test_defaults_cliente(self, db_session):
        """Cliente server_default values are set on persist."""
        from core.models import Cliente

        c = Cliente(nombre_completo="Test Defaults")
        db_session.add(c)
        db_session.flush()
        assert c.estado == "Activo"

    def test_repr(self):
        """Cliente __repr__ returns expected format."""
        from core.models import Cliente

        c = Cliente(nombre_completo="Ana María", no_doc="98765432")
        assert repr(c) == "<Cliente Ana María (98765432)>"

    def test_no_doc_unique(self):
        """no_doc column has a unique constraint (via metadata)."""
        from core.models import Cliente

        col = Cliente.__table__.columns["no_doc"]
        assert col.unique, "no_doc should be unique"

    def test_relaciones_cliente(self, db_session):
        """Cliente has relationships: rentas, reservas, comparendos."""
        from core.models import Cliente

        c = Cliente(nombre_completo="Cliente Relaciones")
        db_session.add(c)
        db_session.flush()
        assert hasattr(c, "rentas")
        assert hasattr(c, "reservas")
        assert hasattr(c, "comparendos")


# ═══════════════════════════════════════════════════════════════════════════════
# Renta
# ═══════════════════════════════════════════════════════════════════════════════


class TestRentaModel:
    """Renta model — rentals."""

    def test_table_name(self):
        """Renta maps to 'rentas'."""
        from core.models import Renta

        assert Renta.__tablename__ == "rentas"

    def test_crear_minimo(self, db_session):
        """Renta can be created with minimum required fields."""
        from core.models import Renta

        r = Renta()
        db_session.add(r)
        db_session.flush()
        assert r.id is not None

    def test_crear_con_valores(self, db_session):
        """Renta can store monetary values as Decimal."""
        from core.models import Renta

        r = Renta(
            valor_dia=Decimal("120000.00"),
            descuento=Decimal("10000.00"),
            subtotal=Decimal("110000.00"),
            impuestos=Decimal("20900.00"),
            total=Decimal("130900.00"),
            abono=Decimal("50000.00"),
            saldo_pendiente=Decimal("80900.00"),
            estado="Activo",
            dias_calculados=3,
            km_salida=5000.0,
        )
        db_session.add(r)
        db_session.flush()

    def test_defaults_renta(self, db_session):
        """Renta server_default values."""
        from core.models import Renta

        r = Renta()
        db_session.add(r)
        db_session.flush()
        assert r.estado == "Activo"
        assert r.subtotal == 0.0
        assert r.total == 0.0
        assert r.dias_calculados == 0
        assert r.km_salida == 0.0
        assert r.tanque_salida == "Lleno"

    def test_repr(self):
        """Renta __repr__ returns expected format."""
        from core.models import Renta

        r = Renta(id=42, placa="ABC123", estado="Activo")
        assert repr(r) == "<Renta 42 - ABC123 (Activo)>"

    def test_foreign_keys(self, model_inspector):
        """Renta has FK to autos (placa) and clientes (id_cliente)."""
        fks = model_inspector.get_foreign_keys("rentas")
        fk_cols = {tuple(sorted(fk["constrained_columns"])) for fk in fks}
        assert ("placa",) in fk_cols, "Missing FK: rentas.placa -> autos.placa"
        assert ("id_cliente",) in fk_cols, "Missing FK: rentas.id_cliente -> clientes.id"

    def test_relaciones_renta(self, db_session):
        """Renta has relationships: auto_rel, cliente_rel, pagos, inspecciones, comparendos."""
        from core.models import Renta

        r = Renta()
        db_session.add(r)
        db_session.flush()
        assert hasattr(r, "auto_rel")
        assert hasattr(r, "cliente_rel")
        assert hasattr(r, "pagos")
        assert hasattr(r, "inspecciones")
        assert hasattr(r, "comparendos")
        assert hasattr(r, "reserva_rel")


# ═══════════════════════════════════════════════════════════════════════════════
# Reserva
# ═══════════════════════════════════════════════════════════════════════════════


class TestReservaModel:
    """Reserva model — reservations."""

    def test_table_name(self):
        """Reserva maps to 'reservas'."""
        from core.models import Reserva

        assert Reserva.__tablename__ == "reservas"

    def test_crear_minimo(self, db_session):
        """Reserva can be created with minimum required fields."""
        from core.models import Reserva

        r = Reserva()
        db_session.add(r)
        db_session.flush()
        assert r.id is not None

    def test_crear_con_valores(self, db_session):
        """Reserva stores financial fields correctly."""
        from core.models import Reserva

        r = Reserva(
            nombre_cliente="Pedro Gómez",
            categoria_vehiculo="Automóvil",
            valor_dia=Decimal("150000.00"),
            abono=Decimal("50000.00"),
            total=Decimal("150000.00"),
            estado="Confirmada",
            dias_calculados=1,
        )
        db_session.add(r)
        db_session.flush()

    def test_defaults_reserva(self, db_session):
        """Reserva server_default values."""
        from core.models import Reserva

        r = Reserva()
        db_session.add(r)
        db_session.flush()
        assert r.estado == "Confirmada"
        assert r.total == 0.0
        assert r.dias_calculados == 0

    def test_repr(self):
        """Reserva __repr__ returns expected format."""
        from core.models import Reserva

        r = Reserva(id=7, nombre_cliente="Luis García")
        assert repr(r) == "<Reserva 7 - Luis García>"

    def test_relaciones_reserva(self, db_session):
        """Reserva has relationships: cliente_rel, auto_rel, rentas."""
        from core.models import Reserva

        r = Reserva()
        db_session.add(r)
        db_session.flush()
        assert hasattr(r, "cliente_rel")
        assert hasattr(r, "auto_rel")
        assert hasattr(r, "rentas")


# ═══════════════════════════════════════════════════════════════════════════════
# MantenimientoVehiculo
# ═══════════════════════════════════════════════════════════════════════════════


class TestMantenimientoVehiculoModel:
    """MantenimientoVehiculo model — vehicle maintenance."""

    def test_table_name(self):
        """MantenimientoVehiculo maps to 'mantenimiento_vehiculos'."""
        from core.models import MantenimientoVehiculo

        assert MantenimientoVehiculo.__tablename__ == "mantenimiento_vehiculos"

    def test_crear_minimo(self, db_session):
        """MantenimientoVehiculo can be created with minimum fields."""
        from core.models import MantenimientoVehiculo

        m = MantenimientoVehiculo()
        db_session.add(m)
        db_session.flush()
        assert m.id is not None

    def test_crear_con_valores(self, db_session):
        """MantenimientoVehiculo stores maintenance data correctly."""
        from core.models import MantenimientoVehiculo

        m = MantenimientoVehiculo(
            pieza_varias_tipo="Cambio Aceite",
            cost_varios=Decimal("150000.00"),
            total_mantenimiento=Decimal("250000.00"),
            km_proximo_cambio_aceite=10000,
        )
        db_session.add(m)
        db_session.flush()

    def test_defaults_mantenimiento(self, db_session):
        """MantenimientoVehiculo server_default values."""
        from core.models import MantenimientoVehiculo

        m = MantenimientoVehiculo()
        db_session.add(m)
        db_session.flush()
        assert m.total_mantenimiento == 0.0
        assert m.cost_varios == 0.0

    def test_repr(self):
        """MantenimientoVehiculo __repr__ returns expected format."""
        from core.models import MantenimientoVehiculo

        m = MantenimientoVehiculo(id=5, placa="ABC123")
        assert repr(m) == "<Mantenimiento 5 - ABC123>"

    def test_relacion_auto(self, db_session):
        """MantenimientoVehiculo has auto_rel relationship."""
        from core.models import MantenimientoVehiculo

        m = MantenimientoVehiculo()
        db_session.add(m)
        db_session.flush()
        assert hasattr(m, "auto_rel")


# ═══════════════════════════════════════════════════════════════════════════════
# Configuracion
# ═══════════════════════════════════════════════════════════════════════════════


class TestConfiguracionModel:
    """Configuracion model — key-value configuration."""

    def test_table_name(self):
        """Configuracion maps to 'configuracion'."""
        from core.models import Configuracion

        assert Configuracion.__tablename__ == "configuracion"

    def test_crear(self, db_session):
        """Configuracion stores key-value pairs."""
        from core.models import Configuracion

        c = Configuracion(clave="IVA", valor="19", tipo="porcentaje")
        db_session.add(c)
        db_session.flush()
        assert c.clave == "IVA"

    def test_clave_primary_key(self):
        """clave is the primary key."""
        from core.models import Configuracion

        assert Configuracion.__mapper__.primary_key[0].name == "clave"

    def test_repr(self):
        """Configuracion __repr__ returns expected format."""
        from core.models import Configuracion

        c = Configuracion(clave="IVA")
        assert repr(c) == "<Configuracion IVA>"


# ═══════════════════════════════════════════════════════════════════════════════
# Auditoria
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditoriaModel:
    """Auditoria model — audit log."""

    def test_table_name(self):
        """Auditoria maps to 'auditoria'."""
        from core.models import Auditoria

        assert Auditoria.__tablename__ == "auditoria"

    def test_crear(self, db_session):
        """Auditoria stores audit entries."""
        from core.models import Auditoria

        a = Auditoria(
            usuario="admin",
            accion="LOGIN",
            mensaje="Usuario admin inició sesión",
            ip="192.168.1.1",
        )
        db_session.add(a)
        db_session.flush()
        assert a.id is not None
        assert a.fecha is not None

    def test_repr(self):
        """Auditoria __repr__ returns expected format."""
        from core.models import Auditoria

        a = Auditoria(id=1, usuario="admin")
        assert repr(a) == "<Auditoria 1 - admin>"

    def test_indices_auditoria(self, model_inspector):
        """Auditoria has indexes on usuario and fecha."""
        _assert_index(model_inspector, "auditoria", ["usuario"])
        _assert_index(model_inspector, "auditoria", ["fecha"])


# ═══════════════════════════════════════════════════════════════════════════════
# Inspeccion
# ═══════════════════════════════════════════════════════════════════════════════


class TestInspeccionModel:
    """Inspeccion model — vehicle inspections."""

    def test_table_name(self):
        """Inspeccion maps to 'inspecciones'."""
        from core.models import Inspeccion

        assert Inspeccion.__tablename__ == "inspecciones"

    def test_crear_con_requeridos(self, db_session):
        """Inspeccion requires id_renta, tipo, fecha, kilometraje, nivel_gasolina."""
        from core.models import Inspeccion, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        insp = Inspeccion(
            id_renta=renta.id,
            tipo="Salida",
            kilometraje=5000.0,
            nivel_gasolina="Lleno",
        )
        db_session.add(insp)
        db_session.flush()
        assert insp.id is not None
        assert insp.fecha is not None

    def test_defaults_inspeccion(self, db_session):
        """Inspeccion server_default values."""
        from core.models import Inspeccion, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        insp = Inspeccion(
            id_renta=renta.id,
            tipo="Salida",
            fecha=datetime.now(),
            kilometraje=1000.0,
            nivel_gasolina="Medio",
        )
        db_session.add(insp)
        db_session.flush()
        assert insp.limpieza == "Limpio"
        assert insp.tiene_repuesto == 1
        assert insp.tiene_gato_cruceta == 1
        assert insp.tiene_kit_carretera == 1
        assert insp.tiene_documentos == 1

    def test_repr(self):
        """Inspeccion __repr__ returns expected format."""
        from core.models import Inspeccion

        i = Inspeccion(id=3, id_renta=10)
        assert repr(i) == "<Inspeccion 3 - Renta 10>"

    def test_relacion_renta(self, db_session):
        """Inspeccion has renta_rel relationship."""
        from core.models import Inspeccion, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        i = Inspeccion(
            id_renta=renta.id,
            tipo="Salida",
            fecha=datetime.now(),
            kilometraje=0.0,
            nivel_gasolina="Lleno",
        )
        db_session.add(i)
        db_session.flush()
        assert hasattr(i, "renta_rel")


# ═══════════════════════════════════════════════════════════════════════════════
# Comparendo
# ═══════════════════════════════════════════════════════════════════════════════


class TestComparendoModel:
    """Comparendo model — traffic tickets."""

    def test_table_name(self):
        """Comparendo maps to 'comparendos'."""
        from core.models import Comparendo

        assert Comparendo.__tablename__ == "comparendos"

    def test_crear_con_requeridos(self, db_session):
        """Comparendo requires placa, fecha_infraccion, hora_infraccion, monto."""
        from datetime import time
        from core.models import Comparendo, Auto

        auto = Auto(placa="CMP001")
        db_session.add(auto)
        db_session.flush()
        c = Comparendo(
            placa="CMP001",
            fecha_infraccion=date(2026, 3, 15),
            hora_infraccion=time(14, 30),
            monto=Decimal("500000.00"),
        )
        db_session.add(c)
        db_session.flush()
        assert c.id is not None

    def test_defaults_comparendo(self, db_session):
        """Comparendo server_default values."""
        from datetime import time
        from core.models import Comparendo, Auto

        auto = Auto(placa="CMP002")
        db_session.add(auto)
        db_session.flush()
        c = Comparendo(
            placa="CMP002",
            fecha_infraccion=date(2026, 3, 15),
            hora_infraccion=time(10, 0),
            monto=Decimal("500000.00"),
        )
        db_session.add(c)
        db_session.flush()
        assert c.monto == Decimal("500000.00")

    def test_repr(self):
        """Comparendo __repr__ returns expected format."""
        from core.models import Comparendo

        c = Comparendo(id=8, placa="XYZ789")
        assert repr(c) == "<Comparendo 8 - XYZ789>"

    def test_relaciones_comparendo(self, db_session):
        """Comparendo has auto_rel, renta_rel, cliente_rel relationships."""
        from datetime import time
        from core.models import Comparendo, Auto, Renta, Cliente

        auto = Auto(placa="CMP003")
        db_session.add(auto)
        cliente = Cliente(nombre_completo="Cmp Cliente")
        db_session.add(cliente)
        db_session.flush()
        renta = Renta(placa="CMP003", id_cliente=cliente.id)
        db_session.add(renta)
        db_session.flush()
        c = Comparendo(
            placa="CMP003",
            fecha_infraccion=date(2026, 3, 15),
            hora_infraccion=time(8, 45),
            monto=Decimal("100000.00"),
            id_renta=renta.id,
            id_cliente=cliente.id,
        )
        db_session.add(c)
        db_session.flush()
        assert c.auto_rel.placa == "CMP003"
        assert c.renta_rel.id == renta.id
        assert c.cliente_rel.nombre_completo == "Cmp Cliente"


# ═══════════════════════════════════════════════════════════════════════════════
# Pago
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagoModel:
    """Pago model — payments."""

    def test_table_name(self):
        """Pago maps to 'pagos'."""
        from core.models import Pago

        assert Pago.__tablename__ == "pagos"

    def test_crear_con_requeridos(self, db_session):
        """Pago requires id_renta, monto, metodo_pago, concepto."""
        from core.models import Pago, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        p = Pago(
            id_renta=renta.id,
            monto=Decimal("200000.00"),
            metodo_pago="Efectivo",
            concepto="Abono renta",
        )
        db_session.add(p)
        db_session.flush()
        assert p.id is not None
        assert p.fecha is not None

    def test_crear_con_todos(self, db_session):
        """Pago can be created with all fields."""
        from core.models import Pago, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        p = Pago(
            id_renta=renta.id,
            monto=Decimal("150000.00"),
            metodo_pago="Transferencia",
            concepto="Pago total",
            observaciones="Pagó en línea",
            usuario="admin",
        )
        db_session.add(p)
        db_session.flush()

    def test_repr(self):
        """Pago __repr__ returns expected format."""
        from core.models import Pago

        p = Pago(id=5, id_renta=3, monto=Decimal("100000.00"))
        assert repr(p) == "<Pago 5 - Renta 3 - $100000.00>"

    def test_relacion_renta(self, db_session):
        """Pago has renta_rel relationship."""
        from core.models import Pago, Renta

        renta = Renta()
        db_session.add(renta)
        db_session.flush()
        p = Pago(
            id_renta=renta.id, monto=Decimal("50000.00"), metodo_pago="Efectivo", concepto="Abono"
        )
        db_session.add(p)
        db_session.flush()
        assert hasattr(p, "renta_rel")


# ═══════════════════════════════════════════════════════════════════════════════
# Gasto
# ═══════════════════════════════════════════════════════════════════════════════


class TestGastoModel:
    """Gasto model — expenses."""

    def test_table_name(self):
        """Gasto maps to 'gastos'."""
        from core.models import Gasto

        assert Gasto.__tablename__ == "gastos"

    def test_crear_con_requeridos(self, db_session):
        """Gasto requires fecha, categoria, descripcion, monto."""
        from core.models import Gasto

        g = Gasto(
            fecha=date(2026, 4, 1),
            categoria="Mantenimiento",
            descripcion="Cambio de aceite",
            monto=Decimal("120000.00"),
        )
        db_session.add(g)
        db_session.flush()
        assert g.id is not None

    def test_crear_con_placa(self, db_session):
        """Gasto can be linked to a vehicle via placa."""
        from core.models import Gasto, Auto

        auto = Auto(placa="GST001")
        db_session.add(auto)
        db_session.flush()
        g = Gasto(
            placa="GST001",
            fecha=date(2026, 4, 1),
            categoria="Combustible",
            descripcion="Tanque lleno",
            monto=Decimal("200000.00"),
            comprobante="FAC-001",
            usuario="admin",
        )
        db_session.add(g)
        db_session.flush()

    def test_defaults_gasto(self, db_session):
        """Gasto server_default values."""
        from core.models import Gasto

        g = Gasto(
            fecha=date(2026, 4, 1),
            categoria="Lavado",
            descripcion="Lavado general",
            monto=Decimal("30000.00"),
        )
        db_session.add(g)
        db_session.flush()
        assert g.usuario == "Sistema"

    def test_repr(self):
        """Gasto __repr__ returns expected format."""
        from core.models import Gasto

        g = Gasto(id=2, categoria="Lavado", monto=Decimal("30000.00"))
        assert repr(g) == "<Gasto 2 - Lavado - $30000.00>"

    def test_relacion_auto(self, db_session):
        """Gasto has auto_rel relationship."""
        from core.models import Gasto

        g = Gasto(
            fecha=date(2026, 4, 1),
            categoria="Peaje",
            descripcion="Peaje Ruta 45",
            monto=Decimal("10000.00"),
        )
        db_session.add(g)
        db_session.flush()
        assert hasattr(g, "auto_rel")


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-model relationships (integration)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCrossModelRelationships:
    """Integration tests across related models."""

    def test_auto_con_renta(self, db_session):
        """Auto -> Renta relationship works bidirectionally."""
        from core.models import Auto, Renta

        auto = Auto(placa="CROSS01", marca="Test", modelo="X")
        db_session.add(auto)
        db_session.flush()

        renta = Renta(placa="CROSS01")
        db_session.add(renta)
        db_session.flush()

        # Auto can access its rentas
        assert len(auto.rentas) == 1
        assert auto.rentas[0].id == renta.id

        # Renta can access its auto_rel
        assert renta.auto_rel.placa == "CROSS01"

    def test_cliente_con_renta(self, db_session):
        """Cliente -> Renta relationship works."""
        from core.models import Cliente, Renta

        cliente = Cliente(nombre_completo="Cliente Test", no_doc="99999999")
        db_session.add(cliente)
        db_session.flush()

        renta = Renta(id_cliente=cliente.id)
        db_session.add(renta)
        db_session.flush()

        assert len(cliente.rentas) == 1
        assert renta.cliente_rel.nombre_completo == "Cliente Test"

    def test_auto_con_mantenimiento(self, db_session):
        """Auto -> MantenimientoVehiculo relationship works."""
        from core.models import Auto, MantenimientoVehiculo

        auto = Auto(placa="CROSS02")
        db_session.add(auto)
        db_session.flush()

        m = MantenimientoVehiculo(placa="CROSS02")
        db_session.add(m)
        db_session.flush()

        assert len(auto.mantenimientos) == 1
        assert m.auto_rel.placa == "CROSS02"

    def test_renta_con_pago(self, db_session):
        """Renta -> Pago relationship works."""
        from core.models import Renta, Pago

        renta = Renta()
        db_session.add(renta)
        db_session.flush()

        pago = Pago(
            id_renta=renta.id, monto=Decimal("100000.00"), metodo_pago="Efectivo", concepto="Abono"
        )
        db_session.add(pago)
        db_session.flush()

        assert len(renta.pagos) == 1
        assert pago.renta_rel.id == renta.id

    def test_renta_con_inspeccion(self, db_session):
        """Renta -> Inspeccion relationship works."""
        from core.models import Renta, Inspeccion
        from datetime import datetime

        renta = Renta()
        db_session.add(renta)
        db_session.flush()

        insp = Inspeccion(
            id_renta=renta.id,
            tipo="Salida",
            fecha=datetime.now(),
            kilometraje=1000.0,
            nivel_gasolina="Lleno",
        )
        db_session.add(insp)
        db_session.flush()

        assert len(renta.inspecciones) == 1
        assert insp.renta_rel.id == renta.id

    def test_renta_con_reserva(self, db_session):
        """Renta -> Reserva relationship works."""
        from core.models import Renta, Reserva

        reserva = Reserva(nombre_cliente="Reserva Test")
        db_session.add(reserva)
        db_session.flush()

        renta = Renta(id_reserva=reserva.id)
        db_session.add(renta)
        db_session.flush()

        assert len(reserva.rentas) == 1
        assert renta.reserva_rel.id == reserva.id

    def test_auto_con_gasto(self, db_session):
        """Auto -> Gasto relationship works."""
        from core.models import Auto, Gasto
        from datetime import date

        auto = Auto(placa="CROSS03")
        db_session.add(auto)
        db_session.flush()

        gasto = Gasto(
            placa="CROSS03",
            fecha=date(2026, 4, 1),
            categoria="Combustible",
            descripcion="Gasolina",
            monto=Decimal("100000.00"),
        )
        db_session.add(gasto)
        db_session.flush()

        assert len(auto.gastos) == 1
        assert gasto.auto_rel.placa == "CROSS03"

    def test_auto_con_comparendo(self, db_session):
        """Auto -> Comparendo relationship works."""
        from datetime import time, date
        from core.models import Auto, Comparendo

        auto = Auto(placa="CROSS04")
        db_session.add(auto)
        db_session.flush()

        cmp = Comparendo(
            placa="CROSS04",
            fecha_infraccion=date(2026, 4, 1),
            hora_infraccion=time(14, 0),
            monto=Decimal("300000.00"),
        )
        db_session.add(cmp)
        db_session.flush()

        assert len(auto.comparendos) == 1
        assert cmp.auto_rel.placa == "CROSS04"

    def test_renta_y_cliente_y_comparendo(self, db_session):
        """Comparendo has relationships with Renta and Cliente."""
        from datetime import time, date
        from core.models import Auto, Cliente, Renta, Comparendo

        auto = Auto(placa="CROSS05")
        db_session.add(auto)
        db_session.flush()

        cliente = Cliente(nombre_completo="Cliente Cmp")
        db_session.add(cliente)
        db_session.flush()

        renta = Renta(placa="CROSS05", id_cliente=cliente.id)
        db_session.add(renta)
        db_session.flush()

        cmp = Comparendo(
            placa="CROSS05",
            fecha_infraccion=date(2026, 4, 1),
            hora_infraccion=time(9, 15),
            monto=Decimal("300000.00"),
            id_renta=renta.id,
            id_cliente=cliente.id,
        )
        db_session.add(cmp)
        db_session.flush()

        assert cmp.auto_rel.placa == "CROSS05"
        assert cmp.renta_rel.id == renta.id
        assert cmp.cliente_rel.nombre_completo == "Cliente Cmp"
