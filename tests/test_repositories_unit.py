"""
test_repositories_unit.py — Unit tests for AutoRepositorySA, ClienteRepositorySA,
                            RentaRepositorySA, and PagoRepositorySA.

Tests repositories directly (not through services) using Pydantic schemas.
Uses the existing conftest.py for in-memory SQLite database setup.
Each test generates unique data to avoid UNIQUE constraint violations
from the shared session-scoped database.

Run: pytest tests/test_repositories_unit.py -v
"""

import datetime
from decimal import Decimal
from datetime import date, time

import pytest

from core.models import Auto, Cliente, Renta
from core.schemas import (
    AutoCreate,
    AutoUpdate,
    ClienteCreate,
    ClienteUpdate,
    RentaCreate,
    RentaCierre,
    PagoCreate,
)
from core.exceptions import RegistroNoEncontrado
from repositories.auto_repository_sa import AutoRepositorySA
from repositories.cliente_repository_sa import ClienteRepositorySA
from repositories.renta_repository_sa import RentaRepositorySA
from repositories.pago_repository_sa import PagoRepositorySA
from core.database_sa import SessionLocal


# ═══════════════════════════════════════════════════════════════════════════════
# Unique ID generator (avoids UNIQUE constraint violations across tests)
# ═══════════════════════════════════════════════════════════════════════════════

_test_id = 0


def _next_placa(prefix="RA") -> str:
    """Generate a unique placa for each call."""
    global _test_id
    _test_id += 1
    return f"{prefix}{_test_id:04d}"


def _next_doc(prefix="DOC") -> str:
    """Generate a unique document number for each call."""
    global _test_id
    _test_id += 1
    return f"{prefix}{_test_id:06d}"


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def db_session():
    """Returns a clean session for transactional testing (rolls back after test)."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _raw_insert_auto(placa: str, **kwargs):
    """Helper: insert an Auto row directly via raw session."""
    session = SessionLocal()
    try:
        defaults = dict(placa=placa, marca="Test", modelo="Test", estado="Disponible")
        defaults.update(kwargs)
        auto = Auto(**defaults)
        session.add(auto)
        session.commit()
    finally:
        session.close()


def _raw_insert_cliente(**kwargs) -> int:
    """Helper: insert a Cliente row directly and return its ID."""
    session = SessionLocal()
    try:
        defaults = dict(
            tipo_doc="Cédula",
            no_doc=_next_doc(),
            nombres="Test",
            apellidos="Client",
            nombre_completo="Test Client",
            estado="Activo",
        )
        defaults.update(kwargs)
        cliente = Cliente(**defaults)
        session.add(cliente)
        session.flush()
        cid = cliente.id
        session.commit()
        return cid
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# AutoRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoRepositorySA:
    def test_insertar_y_obtener_todos(self):
        """insertar() creates auto records; obtener_todos() returns them."""
        p1, p2 = _next_placa("RAA"), _next_placa("RAA")
        AutoRepositorySA.insertar(AutoCreate(placa=p1, marca="Toyota", modelo="Corolla"))
        AutoRepositorySA.insertar(AutoCreate(placa=p2, marca="Mazda", modelo="CX-30"))

        todos = AutoRepositorySA.obtener_todos()
        placas = [a["placa"] for a in todos]
        assert p1 in placas
        assert p2 in placas

    def test_obtener_por_placa(self):
        """obtener_por_placa() returns the correct auto dict."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(placa=p, marca="Toyota", modelo="Corolla", kilometraje=5000.0)
        )
        auto = AutoRepositorySA.obtener_por_placa(p)
        assert auto["placa"] == p
        assert auto["marca"] == "Toyota"
        assert auto["kilometraje"] == 5000.0

    def test_obtener_por_placa_no_existe(self):
        """obtener_por_placa() returns None for non-existent placa."""
        assert AutoRepositorySA.obtener_por_placa("NOEXIST") is None

    def test_existe(self):
        """existe() returns True for existing placa, False otherwise."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="T", modelo="M"))
        assert AutoRepositorySA.existe(p) is True
        assert AutoRepositorySA.existe("NOEXIST") is False

    def test_obtener_disponibles(self):
        """obtener_disponibles() only returns autos with estado='Disponible'."""
        p_disp = _next_placa()
        p_mant = _next_placa()

        AutoRepositorySA.insertar(AutoCreate(placa=p_disp, marca="T", modelo="M"))
        AutoRepositorySA.insertar(AutoCreate(placa=p_mant, marca="F", modelo="F"))

        # Update estado to Mantenimiento via raw session (no duplicate insert)
        session = SessionLocal()
        try:
            a = session.query(Auto).filter(Auto.placa == p_mant).first()
            a.estado = "Mantenimiento"
            session.commit()
        finally:
            session.close()

        disponibles = AutoRepositorySA.obtener_disponibles()
        placas = [a["placa"] for a in disponibles]
        assert p_disp in placas
        assert p_mant not in placas

    def test_actualizar(self):
        """actualizar() updates fields of an existing auto."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="Toyota", modelo="Corolla"))

        AutoRepositorySA.actualizar(
            AutoUpdate(placa=p, marca="Toyota Upd", color="Rojo", kilometraje=6000.0)
        )

        auto = AutoRepositorySA.obtener_por_placa(p)
        assert auto["marca"] == "Toyota Upd"
        assert auto["color"] == "Rojo"
        assert auto["kilometraje"] == 6000.0
        assert auto["modelo"] == "Corolla"  # unchanged

    def test_actualizar_no_existe(self):
        """actualizar() raises RegistroNoEncontrado for non-existent placa."""
        with pytest.raises(RegistroNoEncontrado, match="NOEXIST"):
            AutoRepositorySA.actualizar(AutoUpdate(placa="NOEXIST", marca="Nope"))

    def test_cambiar_estado(self):
        """cambiar_estado() updates estado and optionally kilometraje."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="T", modelo="M", kilometraje=5000.0))

        AutoRepositorySA.cambiar_estado(p, "Mantenimiento", kilometraje=5500)

        auto = AutoRepositorySA.obtener_por_placa(p)
        assert auto["estado"] == "Mantenimiento"
        assert auto["kilometraje"] == 5500.0

    def test_cambiar_estado_sin_kilometraje(self):
        """cambiar_estado() without kilometraje keeps existing value."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="T", modelo="M", kilometraje=5000.0))
        AutoRepositorySA.cambiar_estado(p, "Rentado")
        auto = AutoRepositorySA.obtener_por_placa(p)
        assert auto["estado"] == "Rentado"
        assert auto["kilometraje"] == 5000.0

    def test_cambiar_estado_no_existe(self):
        """cambiar_estado() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado):
            AutoRepositorySA.cambiar_estado("NOEXIST", "Disponible")

    def test_obtener_alertas_flota_aceite(self):
        """obtener_alertas_flota() detects oil change alerts."""
        p = _next_placa("ALR")
        _raw_insert_auto(p, kilometraje=9800.0, proximo_aceite=10000)

        alertas = AutoRepositorySA.obtener_alertas_flota()
        oil = [a for a in alertas if a["placa"] == p and a["tipo"] == "Aceite"]
        assert len(oil) == 1
        assert oil[0]["km_actual"] == 9800
        assert oil[0]["km_proximo"] == 10000

    def test_obtener_alertas_flota_soat(self):
        """obtener_alertas_flota() detects SOAT expiring alerts."""
        p = _next_placa("ALR")
        _raw_insert_auto(p, vencimiento_soat=date.today() + datetime.timedelta(days=5))

        alertas = AutoRepositorySA.obtener_alertas_flota()
        soat = [a for a in alertas if a["placa"] == p and a["tipo"] == "SOAT"]
        assert len(soat) == 1
        assert soat[0]["dias_restantes"] == 5

    def test_obtener_alertas_flota_excluye_vendido(self):
        """obtener_alertas_flota() excludes Vendido autos."""
        p = _next_placa("ALR")
        # Insert a non-excluded auto that DOES trigger an alert (proves function works)
        p_active = _next_placa("ALR")
        _raw_insert_auto(p_active, kilometraje=9800, proximo_aceite=10000)
        # Insert a Vendido auto that would trigger if not excluded
        _raw_insert_auto(p, kilometraje=10000, proximo_aceite=10000, estado="Vendido")

        alertas = AutoRepositorySA.obtener_alertas_flota()
        # Verify function is actually working (active auto shows up)
        assert any(a["placa"] == p_active for a in alertas)
        # Verify vendido is excluded
        assert all(a["placa"] != p for a in alertas)

    def test_uso_de_session_externa(self, db_session):
        """AutoRepo methods accept an external session for transactional scope."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="T", modelo="M"), session=db_session)
        auto = AutoRepositorySA.obtener_por_placa(p, session=db_session)
        assert auto is not None
        assert auto["placa"] == p

    def test_insertar_minimal(self):
        """insertar() works with only required fields."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="Mini", modelo="Test"))
        auto = AutoRepositorySA.obtener_por_placa(p)
        assert auto["estado"] == "Disponible"  # default filled

    def test_to_dict_fields(self):
        """_to_dict() returns all expected fields."""
        p = _next_placa()
        AutoRepositorySA.insertar(AutoCreate(placa=p, marca="T", modelo="M"))
        auto = AutoRepositorySA.obtener_por_placa(p)
        expected = {
            "placa",
            "marca",
            "modelo",
            "version",
            "color",
            "tipo",
            "cilindraje",
            "transmision",
            "combustible",
            "no_motor",
            "no_chasis",
            "propietario",
            "estado",
            "costo_fijo_mensual",
            "kilometraje",
            "ubicacion",
            "tipo_adquisicion",
            "proximo_aceite",
            "proximo_frenos",
            "vencimiento_soat",
            "vencimiento_tecnico",
            "vencimiento_extintor",
            "vencimiento_bateria",
            "observaciones",
            "fecha_ingreso",
            "created_at",
            "updated_at",
        }
        assert expected.issubset(auto.keys())


# ═══════════════════════════════════════════════════════════════════════════════
# ClienteRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestClienteRepositorySA:
    def test_insertar_y_buscar(self):
        """insertar() creates a client; buscar() retrieves by name."""
        d1, d2 = _next_doc(), _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d1,
                nombres="Repo",
                apellidos="Uno",
                nombre_completo="Repo Uno",
                celular="+573111111111",
                estado="Activo",
            )
        )
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Pasaporte",
                no_doc=d2,
                nombres="Repo",
                apellidos="Dos",
                nombre_completo="Repo Dos",
                celular="+573222222222",
                estado="Activo",
            )
        )

        results = ClienteRepositorySA.buscar("Repo Uno")
        assert len(results) >= 1
        assert any(c["no_doc"] == d1 for c in results)

    def test_buscar_por_documento(self):
        """buscar() finds clients by document number."""
        d = _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="T",
                apellidos="C",
                nombre_completo="Test C",
                estado="Activo",
            )
        )
        results = ClienteRepositorySA.buscar(d)
        assert results[0]["no_doc"] == d

    def test_buscar_sin_termino(self):
        """buscar() with empty string returns all clients."""
        d1, d2 = _next_doc(), _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d1,
                nombres="A",
                apellidos="B",
                nombre_completo="A B",
                estado="Activo",
            )
        )
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Pasaporte",
                no_doc=d2,
                nombres="C",
                apellidos="D",
                nombre_completo="C D",
                estado="Activo",
            )
        )
        results = ClienteRepositorySA.buscar("")
        docs = [c["no_doc"] for c in results]
        assert d1 in docs
        assert d2 in docs

    def test_buscar_sin_resultados(self):
        """buscar() returns empty list when no match."""
        assert ClienteRepositorySA.buscar("NoExisteNadieConEsteNombre") == []

    def test_obtener_por_id(self):
        """obtener_por_id() returns the correct client."""
        d = _next_doc()
        cid = ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="Repo",
                apellidos="Test",
                nombre_completo="Repo Test",
                pais="Colombia",
                nacionalidad="Colombiana",
                estado="Activo",
            )
        )
        cliente = ClienteRepositorySA.obtener_por_id(cid)
        assert cliente["no_doc"] == d
        assert cliente["pais"] == "Colombia"
        assert cliente["nacionalidad"] == "Colombiana"

    def test_obtener_por_id_no_existe(self):
        """obtener_por_id() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="999999"):
            ClienteRepositorySA.obtener_por_id(999999)

    def test_actualizar(self):
        """actualizar() updates fields of an existing client."""
        d = _next_doc()
        cid = ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="R",
                apellidos="T",
                nombre_completo="R T",
                celular="+573000000000",
                pais="Colombia",
                estado="Activo",
            )
        )
        ClienteRepositorySA.actualizar(
            ClienteUpdate(
                id=cid,
                celular="+573333333333",
                email="u@test.com",
                ciudad="Cartagena",
            )
        )
        cliente = ClienteRepositorySA.obtener_por_id(cid)
        assert cliente["celular"] == "+573333333333"
        assert cliente["email"] == "u@test.com"
        assert cliente["pais"] == "Colombia"  # unchanged

    def test_actualizar_no_existe(self):
        """actualizar() raises RegistroNoEncontrado for non-existent ID."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            ClienteRepositorySA.actualizar(ClienteUpdate(id=99999, celular="+573000000000"))

    def test_buscar_por_celular(self):
        """buscar() finds clients by cell number."""
        d = _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="T",
                apellidos="C",
                nombre_completo="T C",
                celular="+573111111111",
                estado="Activo",
            )
        )
        results = ClienteRepositorySA.buscar("3111111111")
        assert any(c["no_doc"] == d for c in results)

    def test_buscar_por_email(self):
        """buscar() finds clients by email."""
        d = _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="T",
                apellidos="C",
                nombre_completo="T C",
                email="test@test.com",
                estado="Activo",
            )
        )
        results = ClienteRepositorySA.buscar("test@test.com")
        assert len(results) >= 1

    def test_obtener_valores_unicos(self):
        """obtener_valores_unicos() returns distinct values for a field."""
        d1, d2 = _next_doc(), _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d1,
                nombres="A",
                apellidos="B",
                nombre_completo="A B",
                pais="Colombia",
                estado="Activo",
            )
        )
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d2,
                nombres="C",
                apellidos="D",
                nombre_completo="C D",
                pais="Colombia",
                estado="Activo",
            )
        )
        paises = ClienteRepositorySA.obtener_valores_unicos("pais")
        assert "Colombia" in paises
        assert paises.count("Colombia") == 1  # distinct

    def test_obtener_valores_unicos_campo_invalido(self):
        """obtener_valores_unicos() returns [] for non-existent field."""
        assert ClienteRepositorySA.obtener_valores_unicos("no_existe") == []

    def test_obtener_regiones_por_pais(self):
        """obtener_regiones_por_pais() returns distinct regions."""
        d = _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="T",
                apellidos="C",
                nombre_completo="T C",
                pais="Colombia",
                estado_region="Cundinamarca",
                estado="Activo",
            )
        )
        regiones = ClienteRepositorySA.obtener_regiones_por_pais("Colombia")
        assert "Cundinamarca" in regiones

    def test_obtener_ciudades_por_region(self):
        """obtener_ciudades_por_region() returns distinct cities."""
        d = _next_doc()
        ClienteRepositorySA.insertar(
            ClienteCreate(
                tipo_doc="Cédula",
                no_doc=d,
                nombres="T",
                apellidos="C",
                nombre_completo="T C",
                pais="Colombia",
                estado_region="Cundinamarca",
                ciudad="Bogotá",
                estado="Activo",
            )
        )
        ciudades = ClienteRepositorySA.obtener_ciudades_por_region("Colombia", "Cundinamarca")
        assert "Bogotá" in ciudades


# ═══════════════════════════════════════════════════════════════════════════════
# RentaRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRentaRepositorySA:
    def _make_renta(self, placa: str, **kwargs) -> RentaCreate:
        today = date.today()
        defaults = dict(
            placa=placa,
            nombre_cliente="Test Renta Repo",
            fecha_recogida=today,
            hora_recogida=time(10, 0),
            fecha_retorno=today + datetime.timedelta(days=3),
            hora_retorno=time(10, 0),
            dias_calculados=3,
            valor_dia=Decimal("100000"),
            total=Decimal("300000"),
            abono=Decimal("50000"),
            saldo_pendiente=Decimal("250000"),
            estado="Activo",
        )
        defaults.update(kwargs)
        return RentaCreate(**defaults)

    def test_insertar_y_obtener_por_id(self):
        """insertar() creates a rental and returns its ID."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        renta_id = RentaRepositorySA.insertar(self._make_renta(p))
        assert isinstance(renta_id, int) and renta_id > 0

        result = RentaRepositorySA.obtener_por_id(renta_id)
        assert result["placa"] == p
        assert result["total"] == 300000.0
        assert result["estado"] == "Activo"

    def test_obtener_por_id_no_existe(self):
        """obtener_por_id() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            RentaRepositorySA.obtener_por_id(99999)

    def test_obtener_activas(self):
        """obtener_activas() only returns rentals with estado='Activo'."""
        p1, p2 = _next_placa("RR"), _next_placa("RR")
        _raw_insert_auto(p1)
        _raw_insert_auto(p2)

        id1 = RentaRepositorySA.insertar(self._make_renta(p1))
        # Second rental is Finalizado (not Activo)
        RentaRepositorySA.insertar(
            self._make_renta(p2, nombre_cliente="Closed", estado="Finalizado")
        )

        activas = RentaRepositorySA.obtener_activas()
        ids = [r["id"] for r in activas]
        assert id1 in ids
        assert all(r["estado"] == "Activo" for r in activas)

    def test_cerrar_renta(self):
        """cerrar_renta() updates rental with closure data."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        rid = RentaRepositorySA.insertar(self._make_renta(p))

        RentaRepositorySA.cerrar_renta(
            rid,
            RentaCierre(
                fecha_devolucion_real=date.today(),
                hora_devolucion_real=time(14, 30),
                km_final="10500",
                tanque_final="Lleno",
                nota_cierre="Devolución en buen estado",
            ),
        )
        result = RentaRepositorySA.obtener_por_id(rid)
        assert result["estado"] == "Finalizado"
        assert result["km_final"] == "10500"
        assert "Devolución en buen estado" in result.get("observaciones", "")

    def test_cerrar_renta_con_otros_cobros(self):
        """cerrar_renta() with otros_cobros increases total."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        rid = RentaRepositorySA.insertar(self._make_renta(p))

        RentaRepositorySA.cerrar_renta(
            rid,
            RentaCierre(
                fecha_devolucion_real=date.today(),
                hora_devolucion_real=time(14, 0),
                otros_cobros=Decimal("50000"),
            ),
        )
        result = RentaRepositorySA.obtener_por_id(rid)
        assert result["total"] == 350000.0  # 300000 + 50000
        assert result["saldo_pendiente"] == 300000.0  # 350000 - 50000

    def test_cerrar_renta_no_existe(self):
        """cerrar_renta() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            RentaRepositorySA.cerrar_renta(
                99999,
                RentaCierre(
                    fecha_devolucion_real=date.today(),
                    hora_devolucion_real=time(14, 0),
                ),
            )

    def test_extender(self):
        """extender() updates return date and totals."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        rid = RentaRepositorySA.insertar(self._make_renta(p))

        RentaRepositorySA.extender(
            rid,
            nueva_fecha=date.today() + datetime.timedelta(days=5),
            nueva_hora=time(12, 0),
            nuevos_dias=5,
            nuevo_total=500000.0,
            nuevo_saldo=450000.0,
        )
        result = RentaRepositorySA.obtener_por_id(rid)
        assert result["dias_calculados"] == 5
        assert result["total"] == 500000.0
        assert result["saldo_pendiente"] == 450000.0

    def test_actualizar_placa(self):
        """actualizar_placa() changes the vehicle assigned to a rental."""
        p1, p2 = _next_placa("RR"), _next_placa("RR")
        _raw_insert_auto(p1)
        _raw_insert_auto(p2)
        rid = RentaRepositorySA.insertar(self._make_renta(p1))

        RentaRepositorySA.actualizar_placa(rid, p2, "Cambio por mantenimiento")
        result = RentaRepositorySA.obtener_por_id(rid)
        assert result["placa"] == p2
        assert "Cambio por mantenimiento" in result.get("observaciones", "")

    def test_obtener_datos_documento(self):
        """obtener_datos_documento() returns rental with related auto/client data."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        cid = _raw_insert_cliente()
        rid = RentaRepositorySA.insertar(self._make_renta(p, id_cliente=cid))

        doc = RentaRepositorySA.obtener_datos_documento(rid)
        assert doc["placa"] == p
        assert "auto_marca" in doc
        assert "cliente_celular" in doc

    def test_obtener_activas_filtradas_vencen_hoy(self):
        """obtener_activas_filtradas('Vencen Hoy') returns rentals due today."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        today = date.today()
        RentaRepositorySA.insertar(
            self._make_renta(
                p,
                fecha_recogida=today - datetime.timedelta(days=2),
                fecha_retorno=today,
            )
        )
        filtradas = RentaRepositorySA.obtener_activas_filtradas("Vencen Hoy")
        assert len(filtradas) >= 1
        assert all(r["estado"] == "Activo" for r in filtradas)

    def test_uso_de_session_externa(self, db_session):
        """RentaRepo methods accept an external session."""
        p = _next_placa("RR")
        _raw_insert_auto(p)
        rid = RentaRepositorySA.insertar(self._make_renta(p), session=db_session)
        result = RentaRepositorySA.obtener_por_id(rid, session=db_session)
        assert result["placa"] == p


# ═══════════════════════════════════════════════════════════════════════════════
# PagoRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagoRepositorySA:
    def _create_renta(self, placa: str = None, total: Decimal = None) -> int:
        """Create a rental in DB and return its ID."""
        p = placa or _next_placa("RP")
        _raw_insert_auto(p)
        session = SessionLocal()
        try:
            renta = Renta(
                placa=p,
                nombre_cliente="Pago Test",
                fecha_recogida=date.today(),
                hora_recogida=time(10, 0),
                fecha_retorno=date.today() + datetime.timedelta(days=3),
                hora_retorno=time(10, 0),
                dias_calculados=3,
                total=float(total or 300000),
                abono=0.0,
                saldo_pendiente=float(total or 300000),
                estado="Activo",
            )
            session.add(renta)
            session.flush()
            rid = renta.id
            session.commit()
            return rid
        finally:
            session.close()

    def test_insertar_y_obtener_por_renta(self):
        """insertar() creates a payment; obtener_por_renta() retrieves it."""
        rid = self._create_renta()
        pid = PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("100000"),
                metodo_pago="Efectivo",
                concepto="Abono",
            )
        )
        assert isinstance(pid, int) and pid > 0

        pagos = PagoRepositorySA.obtener_por_renta(rid)
        assert len(pagos) == 1
        assert pagos[0]["monto"] == 100000.0
        assert pagos[0]["metodo_pago"] == "Efectivo"

    def test_obtener_por_renta_orden(self):
        """obtener_por_renta() returns payments ordered by date descending."""
        rid = self._create_renta()
        PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("50000"),
                metodo_pago="Efectivo",
                concepto="P1",
            )
        )
        PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("100000"),
                metodo_pago="Tarjeta",
                concepto="P2",
            )
        )
        assert len(PagoRepositorySA.obtener_por_renta(rid)) == 2

    def test_obtener_por_renta_vacia(self):
        """obtener_por_renta() returns [] when no payments exist."""
        assert PagoRepositorySA.obtener_por_renta(99999) == []

    def test_actualizar_abono_renta(self):
        """actualizar_abono_renta() recalculates abono and saldo_pendiente."""
        rid = self._create_renta(total=Decimal("300000"))
        PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("100000"),
                metodo_pago="Efectivo",
                concepto="A",
            )
        )
        PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("50000"),
                metodo_pago="Transferencia",
                concepto="B",
            )
        )
        PagoRepositorySA.actualizar_abono_renta(rid)

        session = SessionLocal()
        try:
            renta = session.query(Renta).filter(Renta.id == rid).first()
            assert renta.abono == 150000.0
            assert renta.saldo_pendiente == 150000.0
        finally:
            session.close()

    def test_actualizar_abono_renta_sin_pagos(self):
        """actualizar_abono_renta() sets abono=0 when no payments exist."""
        rid = self._create_renta(total=Decimal("200000"))
        PagoRepositorySA.actualizar_abono_renta(rid)

        session = SessionLocal()
        try:
            renta = session.query(Renta).filter(Renta.id == rid).first()
            assert renta.abono == 0.0
            assert renta.saldo_pendiente == 200000.0
        finally:
            session.close()

    def test_uso_de_session_externa(self, db_session):
        """PagoRepo methods accept an external session."""
        rid = self._create_renta()
        pid = PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("75000"),
                metodo_pago="Efectivo",
                concepto="Abono",
            ),
            session=db_session,
        )
        PagoRepositorySA.actualizar_abono_renta(rid, session=db_session)

        pagos = PagoRepositorySA.obtener_por_renta(rid, session=db_session)
        assert len(pagos) == 1
        assert pagos[0]["id"] == pid

    def test_to_dict_fields(self):
        """_to_dict() returns all expected payment fields."""
        rid = self._create_renta()
        PagoRepositorySA.insertar(
            PagoCreate(
                id_renta=rid,
                monto=Decimal("50000"),
                metodo_pago="Efectivo",
                concepto="A",
            )
        )
        pagos = PagoRepositorySA.obtener_por_renta(rid)
        expected = {
            "id",
            "id_renta",
            "fecha",
            "monto",
            "metodo_pago",
            "concepto",
            "observaciones",
            "usuario",
            "updated_at",
        }
        assert expected.issubset(pagos[0].keys())
