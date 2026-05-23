"""
test_repositories_restantes.py — Unit tests for remaining 6 repositories:
  ComparendoRepositorySA, GastoRepositorySA, InspeccionRepositorySA,
  MantenimientoRepositorySA, ReservaRepositorySA, AlertaRepositorySA

Tests repositories directly (not through services) using Pydantic schemas.
Uses the existing conftest.py for shared in-memory SQLite database setup.
Each test generates unique data to avoid UNIQUE constraint violations.

Run: pytest tests/test_repositories_restantes.py -v
"""

import datetime
from decimal import Decimal
from datetime import date, time, timedelta

import pytest

from core.models import Auto, Renta, Cliente
from core.schemas import (
    ComparendoCreate, GastoCreate, InspeccionCreate,
    MantenimientoCreate, ReservaCreate,
)
from core.exceptions import RegistroNoEncontrado
from repositories.comparendo_repository_sa import ComparendoRepositorySA
from repositories.gasto_repository_sa import GastoRepositorySA
from repositories.inspeccion_repository_sa import InspeccionRepositorySA
from repositories.mantenimiento_repository_sa import MantenimientoRepositorySA
from repositories.reserva_repository_sa import ReservaRepositorySA
from repositories.alerta_repository_sa import AlertaRepositorySA
from core.database_sa import SessionLocal


# ═══════════════════════════════════════════════════════════════════════════════
# Unique ID generator (avoids UNIQUE constraint violations across tests)
# ═══════════════════════════════════════════════════════════════════════════════

_test_id = 0


def _next_placa(prefix="RX") -> str:
    """Generate a unique placa for each call."""
    global _test_id
    _test_id += 1
    return f"{prefix}{_test_id:04d}"


def _next_doc(prefix="RXDOC") -> str:
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


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers — raw DB inserts (bypass repos to create prerequisite data)
# ═══════════════════════════════════════════════════════════════════════════════

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


def _raw_insert_renta(placa: str, **kwargs) -> int:
    """Helper: insert a Renta row directly and return its ID."""
    session = SessionLocal()
    try:
        today = date.today()
        defaults = dict(
            placa=placa,
            nombre_cliente="Test Renta",
            fecha_recogida=today,
            hora_recogida=time(10, 0),
            fecha_retorno=today + timedelta(days=3),
            hora_retorno=time(10, 0),
            dias_calculados=3,
            total=300000.0,
            abono=0.0,
            saldo_pendiente=300000.0,
            estado="Activo",
        )
        defaults.update(kwargs)
        renta = Renta(**defaults)
        session.add(renta)
        session.flush()
        rid = renta.id
        session.commit()
        return rid
    finally:
        session.close()


# ═══════════════════════════════════════════════════════════════════════════════
# ComparendoRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestComparendoRepositorySA:

    def test_insertar_y_obtener_todos(self):
        """insertar() creates comparendo; obtener_todos() returns it."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        today = date.today()

        cid = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=today, hora_infraccion=time(14, 0),
            monto=Decimal("150000"),
        ))
        assert isinstance(cid, int) and cid > 0

        todos = ComparendoRepositorySA.obtener_todos()
        ids = [c["id"] for c in todos]
        assert cid in ids
        match = [c for c in todos if c["id"] == cid]
        assert len(match) == 1
        assert match[0]["monto"] == 150000.0
        assert match[0]["placa"] == p.upper()

    def test_obtener_todos_vacio(self):
        """obtener_todos() returns [] when no comparendos exist."""
        # We can't rely on the DB being empty, but we can check we get a list
        todos = ComparendoRepositorySA.obtener_todos()
        assert isinstance(todos, list)

    def test_insertar_con_relaciones(self):
        """insertar() works with id_renta and id_cliente."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        cid_cliente = _raw_insert_cliente()
        rid = _raw_insert_renta(p)
        today = date.today()

        cid = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=today, hora_infraccion=time(10, 0),
            monto=Decimal("50000"), id_renta=rid, id_cliente=cid_cliente,
            estado="Pagado",
        ))

        todos = ComparendoRepositorySA.obtener_todos()
        match = [c for c in todos if c["id"] == cid]
        assert len(match) == 1
        assert match[0]["id_renta"] == rid
        assert match[0]["id_cliente"] == cid_cliente
        assert match[0]["estado"] == "Pagado"

    def test_actualizar_estado(self):
        """actualizar_estado() changes the comparendo estado."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        today = date.today()

        cid = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=today, hora_infraccion=time(12, 0),
            monto=Decimal("80000"),
        ))
        ComparendoRepositorySA.actualizar_estado(cid, "Pagado")

        todos = ComparendoRepositorySA.obtener_todos()
        match = [c for c in todos if c["id"] == cid]
        assert match[0]["estado"] == "Pagado"

    def test_actualizar_estado_no_existe(self):
        """actualizar_estado() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            ComparendoRepositorySA.actualizar_estado(99999, "Pagado")

    def test_buscar_historial_rentas_placa(self):
        """buscar_historial_rentas_placa() returns rentals for a placa."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        rid = _raw_insert_renta(p)

        historial = ComparendoRepositorySA.buscar_historial_rentas_placa(p)
        assert len(historial) >= 1
        ids = [h["id"] for h in historial]
        assert rid in ids

    def test_buscar_historial_sin_resultados(self):
        """buscar_historial_rentas_placa() returns [] when no rentals exist for placa."""
        historial = ComparendoRepositorySA.buscar_historial_rentas_placa("NOEXIST")
        assert historial == []

    def test_obtener_todos_orden_desc(self):
        """obtener_todos() returns comparendos ordered by fecha_infraccion desc."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        today = date.today()
        yesterday = today - timedelta(days=1)

        # Insert in reverse order: today, then yesterday
        cid_today = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=today, hora_infraccion=time(10, 0),
            monto=Decimal("100000"),
        ))
        cid_yesterday = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=yesterday, hora_infraccion=time(10, 0),
            monto=Decimal("50000"),
        ))

        todos = ComparendoRepositorySA.obtener_todos()
        # With desc order, today should appear before yesterday
        today_pos = None
        yesterday_pos = None
        for i, c in enumerate(todos):
            if c["id"] == cid_today:
                today_pos = i
            if c["id"] == cid_yesterday:
                yesterday_pos = i
        assert today_pos is not None and yesterday_pos is not None
        assert today_pos < yesterday_pos, "Today should appear before yesterday (desc order)"

    def test_to_dict_fields(self):
        """_to_dict() returns all expected comparendo fields."""
        p = _next_placa("CMP")
        _raw_insert_auto(p)
        today = date.today()

        cid = ComparendoRepositorySA.insertar(ComparendoCreate(
            placa=p, fecha_infraccion=today, hora_infraccion=time(10, 0),
            monto=Decimal("75000"), observaciones="Test obs",
        ))
        todos = ComparendoRepositorySA.obtener_todos()
        match = [c for c in todos if c["id"] == cid]
        assert len(match) == 1
        expected = {"id", "placa", "fecha_infraccion", "hora_infraccion", "monto",
                    "id_renta", "id_cliente", "estado", "observaciones",
                    "created_at", "updated_at"}
        assert expected.issubset(match[0].keys())


# ═══════════════════════════════════════════════════════════════════════════════
# GastoRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGastoRepositorySA:

    def test_insertar_y_obtener_todos(self):
        """insertar() creates a gasto; obtener_todos() returns it."""
        today = date.today()
        gid = GastoRepositorySA.insertar(GastoCreate(
            fecha=today, categoria="Lavado", descripcion="Lavado general",
            monto=Decimal("25000"),
        ))
        assert isinstance(gid, int) and gid > 0

        todos = GastoRepositorySA.obtener_todos()
        ids = [g["id"] for g in todos]
        assert gid in ids
        match = [g for g in todos if g["id"] == gid]
        assert match[0]["monto"] == 25000.0
        assert match[0]["categoria"] == "Lavado"

    def test_obtener_todos_limite(self):
        """obtener_todos(limite=5) returns at most 5 items."""
        today = date.today()
        for i in range(10):
            GastoRepositorySA.insertar(GastoCreate(
                fecha=today, categoria="Test", descripcion=f"Gasto {i}",
                monto=Decimal("10000"),
            ))
        limitados = GastoRepositorySA.obtener_todos(limite=5)
        assert len(limitados) <= 5

    def test_obtener_por_placa(self):
        """obtener_por_placa() filters by placa."""
        p = _next_placa("GTO")
        _raw_insert_auto(p)
        today = date.today()

        # Insert gasto with placa
        gid = GastoRepositorySA.insertar(GastoCreate(
            placa=p, fecha=today, categoria="Combustible",
            descripcion="Tanque lleno", monto=Decimal("120000"),
        ))
        # Insert gasto without placa
        GastoRepositorySA.insertar(GastoCreate(
            fecha=today, categoria="Lavado", descripcion="Lavado",
            monto=Decimal("20000"),
        ))

        por_placa = GastoRepositorySA.obtener_por_placa(p)
        assert len(por_placa) >= 1
        assert gid in [g["id"] for g in por_placa]
        assert all(g["placa"] == p.upper() for g in por_placa)

    def test_obtener_por_placa_vacio(self):
        """obtener_por_placa() returns [] when no gastos exist for placa."""
        assert GastoRepositorySA.obtener_por_placa("NOEXIST") == []

    def test_insertar_sin_placa(self):
        """insertar() works without a placa (nullable)."""
        today = date.today()
        gid = GastoRepositorySA.insertar(GastoCreate(
            fecha=today, categoria="Papelería", descripcion="Resma de papel",
            monto=Decimal("15000"),
        ))
        todos = GastoRepositorySA.obtener_todos()
        match = [g for g in todos if g["id"] == gid]
        assert match[0]["placa"] is None

    def test_insertar_con_placa(self):
        """insertar() works with a placa."""
        p = _next_placa("GTO")
        _raw_insert_auto(p)
        today = date.today()

        gid = GastoRepositorySA.insertar(GastoCreate(
            placa=p, fecha=today, categoria="Mantenimiento",
            descripcion="Cambio de aceite", monto=Decimal("80000"),
        ))
        por_placa = GastoRepositorySA.obtener_por_placa(p)
        assert gid in [g["id"] for g in por_placa]

    def test_insertar_con_usuario_personalizado(self):
        """insertar() accepts a custom usuario."""
        today = date.today()
        gid = GastoRepositorySA.insertar(GastoCreate(
            fecha=today, categoria="Otros", descripcion="Compra varias",
            monto=Decimal("35000"), usuario="Admin",
        ))
        todos = GastoRepositorySA.obtener_todos()
        match = [g for g in todos if g["id"] == gid]
        assert match[0]["usuario"] == "Admin"

    def test_to_dict_fields(self):
        """_to_dict() returns all expected gasto fields."""
        today = date.today()
        gid = GastoRepositorySA.insertar(GastoCreate(
            fecha=today, categoria="Lavado", descripcion="Lavado completo",
            monto=Decimal("30000"), comprobante="FAC-001",
        ))
        todos = GastoRepositorySA.obtener_todos()
        match = [g for g in todos if g["id"] == gid]
        expected = {"id", "placa", "fecha", "categoria", "descripcion",
                    "monto", "comprobante", "usuario", "created_at", "updated_at"}
        assert expected.issubset(match[0].keys())


# ═══════════════════════════════════════════════════════════════════════════════
# InspeccionRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestInspeccionRepositorySA:

    def _create_renta(self, placa: str = None, **kwargs) -> int:
        """Helper: create a rental and return its ID."""
        p = placa or _next_placa("INSP")
        _raw_insert_auto(p)
        return _raw_insert_renta(p, **kwargs)

    def test_insertar_y_obtener_por_renta(self):
        """insertar() creates an inspection; obtener_por_renta() returns it."""
        rid = self._create_renta()
        iid = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Salida", kilometraje=5000.0,
            nivel_gasolina="Lleno",
        ))
        assert isinstance(iid, int) and iid > 0

        insps = InspeccionRepositorySA.obtener_por_renta(rid)
        ids = [i["id"] for i in insps]
        assert iid in ids

    def test_obtener_por_renta_vacio(self):
        """obtener_por_renta() returns [] when id_renta doesn't match."""
        insps = InspeccionRepositorySA.obtener_por_renta(99999)
        assert insps == []

    def test_insertar_con_todos_los_campos(self):
        """insertar() works with all optional fields."""
        rid = self._create_renta()
        iid = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Entrada", kilometraje=5200.0,
            nivel_gasolina="3/4", limpieza="Limpio",
            tiene_repuesto=True, tiene_gato_cruceta=False,
            tiene_kit_carretera=True, tiene_documentos=True,
            danos_carroceria="Rayón en puerta izquierda",
            observaciones="Inspección de entrada completa",
        ))
        insps = InspeccionRepositorySA.obtener_por_renta(rid)
        match = [i for i in insps if i["id"] == iid]
        assert len(match) == 1
        assert match[0]["tipo"] == "Entrada"
        assert match[0]["kilometraje"] == 5200.0
        assert match[0]["nivel_gasolina"] == "3/4"
        assert match[0]["tiene_gato_cruceta"] is False
        assert match[0]["danos_carroceria"] == "Rayón en puerta izquierda"

    def test_insertar_varias_inspecciones(self):
        """obtener_por_renta() returns all inspections for a rental."""
        rid = self._create_renta()
        iid1 = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Salida", kilometraje=5000.0,
            nivel_gasolina="Lleno",
        ))
        iid2 = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Entrada", kilometraje=5300.0,
            nivel_gasolina="1/2",
        ))
        insps = InspeccionRepositorySA.obtener_por_renta(rid)
        ids = [i["id"] for i in insps]
        assert iid1 in ids
        assert iid2 in ids
        assert len(ids) >= 2

    def test_obtener_por_renta_ajena(self):
        """obtener_por_renta() does not return inspections from different rentals."""
        rid1 = self._create_renta()
        rid2 = self._create_renta()
        iid = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid1, tipo="Salida", kilometraje=5000.0,
            nivel_gasolina="Lleno",
        ))
        insps_rid2 = InspeccionRepositorySA.obtener_por_renta(rid2)
        assert iid not in [i["id"] for i in insps_rid2]

    def test_to_dict_fields(self):
        """_to_dict() returns all expected inspection fields."""
        rid = self._create_renta()
        iid = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Salida", kilometraje=5000.0,
            nivel_gasolina="Lleno", observaciones="OK",
        ))
        insps = InspeccionRepositorySA.obtener_por_renta(rid)
        match = [i for i in insps if i["id"] == iid]
        expected = {"id", "id_renta", "tipo", "fecha", "kilometraje",
                    "nivel_gasolina", "limpieza", "tiene_repuesto",
                    "tiene_gato_cruceta", "tiene_kit_carretera",
                    "tiene_documentos", "danos_carroceria", "observaciones"}
        assert expected.issubset(match[0].keys())

    def test_insertar_verifica_id_retornado(self):
        """insertar() returns a valid positive ID."""
        rid = self._create_renta()
        iid = InspeccionRepositorySA.insertar(InspeccionCreate(
            id_renta=rid, tipo="Salida", kilometraje=5000.0,
            nivel_gasolina="Lleno",
        ))
        insps = InspeccionRepositorySA.obtener_por_renta(rid)
        assert iid in [i["id"] for i in insps]


# ═══════════════════════════════════════════════════════════════════════════════
# MantenimientoRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestMantenimientoRepositorySA:

    def test_insertar_y_obtener_historial(self):
        """insertar() creates a maintenance record; obtener_historial() returns it."""
        p = _next_placa("MTO")
        _raw_insert_auto(p)

        mid = MantenimientoRepositorySA.insertar(MantenimientoCreate(
            placa=p, pieza_varias_tipo="Cambio Aceite",
            total_mantenimiento=Decimal("120000"),
        ))
        assert isinstance(mid, int) and mid > 0

        historial = MantenimientoRepositorySA.obtener_historial()
        ids = [m["id"] for m in historial]
        assert mid in ids

    def test_obtener_historial_limite(self):
        """obtener_historial(limite=3) returns at most 3 items."""
        p = _next_placa("MTO")
        _raw_insert_auto(p)
        for i in range(10):
            MantenimientoRepositorySA.insertar(MantenimientoCreate(
                placa=p, pieza_varias_tipo=f"Tipo {i}",
                total_mantenimiento=Decimal("50000"),
            ))
        limitados = MantenimientoRepositorySA.obtener_historial(limite=3)
        assert len(limitados) <= 3

    def test_insertar_con_todos_los_campos(self):
        """insertar() works with all optional fields."""
        p = _next_placa("MTO")
        _raw_insert_auto(p)
        today = date.today()

        mid = MantenimientoRepositorySA.insertar(MantenimientoCreate(
            placa=p, pieza_varias_tipo="Frenos",
            pieza_varias_fecha=today,
            pieza_varias_desc="Cambio pastillas de freno delanteras",
            pieza_varias_obs="Pastillas marca Bosch",
            cost_varios=Decimal("80000"),
            km_proximo_cambio_aceite=15000,
            total_mantenimiento=Decimal("200000"),
        ))
        historial = MantenimientoRepositorySA.obtener_historial()
        match = [m for m in historial if m["id"] == mid]
        assert len(match) == 1
        assert match[0]["pieza_varias_tipo"] == "Frenos"
        assert match[0]["total_mantenimiento"] == 200000.0
        assert match[0]["cost_varios"] == 80000.0
        assert match[0]["km_proximo_cambio_aceite"] == 15000

    def test_obtener_autos_con_km(self):
        """obtener_autos_con_km() returns active autos with km data."""
        p = _next_placa("MTO")
        _raw_insert_auto(p, kilometraje=10000.0, marca="Toyota", modelo="Corolla")

        autos = MantenimientoRepositorySA.obtener_autos_con_km()
        placas = [a["placa"] for a in autos]
        assert p in placas
        match = [a for a in autos if a["placa"] == p]
        assert match[0]["kilometraje"] == 10000.0
        assert match[0]["marca"] == "Toyota"

    def test_obtener_autos_con_km_excluye_excluidos(self):
        """obtener_autos_con_km() excludes Vendido and Baja autos."""
        p_active = _next_placa("MTO")
        p_vendido = _next_placa("MTO")
        _raw_insert_auto(p_active, kilometraje=5000.0)
        _raw_insert_auto(p_vendido, kilometraje=5000.0, estado="Vendido")

        autos = MantenimientoRepositorySA.obtener_autos_con_km()
        placas = [a["placa"] for a in autos]
        assert p_active in placas
        assert p_vendido not in placas

    def test_actualizar_auto(self):
        """actualizar_auto() updates campos on the Auto record."""
        p = _next_placa("MTO")
        _raw_insert_auto(p, kilometraje=8000.0, proximo_aceite=10000)

        MantenimientoRepositorySA.actualizar_auto(p, {
            "kilometraje": 8500.0,
            "proximo_aceite": 15000,
        })

        # Verify via fresh session
        session = SessionLocal()
        try:
            auto = session.query(Auto).filter(Auto.placa == p).first()
            assert auto.kilometraje == 8500.0
            assert auto.proximo_aceite == 15000
        finally:
            session.close()

    def test_actualizar_auto_no_existe(self):
        """actualizar_auto() raises RegistroNoEncontrado for non-existent placa."""
        with pytest.raises(RegistroNoEncontrado, match="NOEXIST"):
            MantenimientoRepositorySA.actualizar_auto("NOEXIST", {"kilometraje": 5000.0})

    def test_uso_de_session_externa(self, db_session):
        """MantenimientoRepo methods accept an external session."""
        p = _next_placa("MTO")
        _raw_insert_auto(p)

        mid = MantenimientoRepositorySA.insertar(MantenimientoCreate(
            placa=p, pieza_varias_tipo="Revisión",
            total_mantenimiento=Decimal("50000"),
        ), session=db_session)

        MantenimientoRepositorySA.actualizar_auto(p, {"kilometraje": 9999.0}, session=db_session)

        historial = MantenimientoRepositorySA.obtener_historial(session=db_session)
        ids = [m["id"] for m in historial]
        assert mid in ids

    def test_to_dict_fields(self):
        """_to_dict() returns all expected maintenance fields."""
        p = _next_placa("MTO")
        _raw_insert_auto(p)

        mid = MantenimientoRepositorySA.insertar(MantenimientoCreate(
            placa=p, pieza_varias_tipo="Llantas",
            total_mantenimiento=Decimal("300000"),
        ))
        historial = MantenimientoRepositorySA.obtener_historial()
        match = [m for m in historial if m["id"] == mid]
        expected = {"id", "placa", "pieza_varias_tipo", "pieza_varias_fecha",
                    "pieza_varias_desc", "pieza_varias_obs", "cost_varios",
                    "km_proximo_cambio_aceite", "total_mantenimiento",
                    "created_at", "updated_at"}
        assert expected.issubset(match[0].keys())


# ═══════════════════════════════════════════════════════════════════════════════
# ReservaRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestReservaRepositorySA:

    def _make_create(self, placa: str = None, **kwargs) -> ReservaCreate:
        """Helper: build a ReservaCreate with defaults."""
        today = date.today()
        defaults = dict(
            nombre_cliente="Reserva Test",
            fecha_recogida=today,
            hora_recogida=time(10, 0),
            fecha_retorno=today + timedelta(days=2),
            hora_retorno=time(10, 0),
            dias_calculados=2,
            valor_dia=Decimal("150000"),
            total=Decimal("300000"),
            estado="Confirmada",
        )
        if placa:
            defaults["placa_asignada"] = placa
        defaults.update(kwargs)
        return ReservaCreate(**defaults)

    def test_insertar_y_obtener_todas(self):
        """insertar() creates a reserva; obtener_todas() returns it."""
        rid = ReservaRepositorySA.insertar(self._make_create())
        assert isinstance(rid, int) and rid > 0

        todas = ReservaRepositorySA.obtener_todas()
        ids = [r["id"] for r in todas]
        assert rid in ids

    def test_obtener_todas_vacio(self):
        """obtener_todas() returns a list (may have data from other tests)."""
        todas = ReservaRepositorySA.obtener_todas()
        assert isinstance(todas, list)

    def test_obtener_por_id(self):
        """obtener_por_id() returns the correct reserva."""
        rid = ReservaRepositorySA.insertar(self._make_create(
            nombre_cliente="Obtener Test",
            nacionalidad="Colombiana",
        ))
        reserva = ReservaRepositorySA.obtener_por_id(rid)
        assert reserva["nombre_cliente"] == "Obtener Test"
        assert reserva["nacionalidad"] == "Colombiana"
        assert reserva["id"] == rid

    def test_obtener_por_id_no_existe(self):
        """obtener_por_id() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            ReservaRepositorySA.obtener_por_id(99999)

    def test_obtener_por_id_con_placa_asignada(self):
        """obtener_por_id() returns placa_asignada correctly."""
        p = _next_placa("RSV")
        _raw_insert_auto(p)
        rid = ReservaRepositorySA.insertar(self._make_create(placa=p))
        reserva = ReservaRepositorySA.obtener_por_id(rid)
        assert reserva["placa_asignada"] == p.upper()

    def test_cancelar(self):
        """cancelar() changes estado to 'Cancelada'."""
        rid = ReservaRepositorySA.insertar(self._make_create())
        ReservaRepositorySA.cancelar(rid)

        reserva = ReservaRepositorySA.obtener_por_id(rid)
        assert reserva["estado"] == "Cancelada"

    def test_cancelar_no_existe(self):
        """cancelar() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            ReservaRepositorySA.cancelar(99999)

    def test_obtener_contacto_cliente(self):
        """obtener_contacto_cliente() returns contact info."""
        rid = ReservaRepositorySA.insertar(self._make_create(
            nombre_cliente="Contacto Test",
            nacionalidad="Mexicana",
        ))
        contacto = ReservaRepositorySA.obtener_contacto_cliente(rid)
        assert contacto["nombre_cliente"] == "Contacto Test"
        assert contacto["nacionalidad"] == "Mexicana"

    def test_obtener_contacto_no_existe(self):
        """obtener_contacto_cliente() raises RegistroNoEncontrado."""
        with pytest.raises(RegistroNoEncontrado, match="99999"):
            ReservaRepositorySA.obtener_contacto_cliente(99999)

    def test_to_dict_fields(self):
        """_to_dict() returns all expected reserva fields."""
        rid = ReservaRepositorySA.insertar(self._make_create(
            nombre_cliente="Full Fields Test",
            categoria_vehiculo="Automóvil",
            ubicacion_recogida="Aeropuerto",
            ubicacion_retorno="Oficina",
            horas_extras=2,
            valor_hora_adic=Decimal("20000"),
            abono=Decimal("50000"),
            observaciones="Test observaciones",
        ))
        todas = ReservaRepositorySA.obtener_todas()
        match = [r for r in todas if r["id"] == rid]
        expected = {"id", "id_cliente", "nombre_cliente", "nacionalidad",
                    "categoria_vehiculo", "placa_asignada",
                    "fecha_recogida", "hora_recogida", "ubicacion_recogida",
                    "fecha_retorno", "hora_retorno", "ubicacion_retorno",
                    "dias_calculados", "horas_extras", "valor_dia",
                    "valor_hora_adic", "abono", "total", "observaciones",
                    "estado", "created_at", "updated_at"}
        assert expected.issubset(match[0].keys())


# ═══════════════════════════════════════════════════════════════════════════════
# AlertaRepositorySA Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAlertaRepositorySA:

    def test_obtener_rentas_por_vencer_vacio(self):
        """obtener_rentas_por_vencer() returns a list (resilient to shared DB)."""
        alertas = AlertaRepositorySA.obtener_rentas_por_vencer()
        assert isinstance(alertas, list)

    def test_obtener_rentas_por_vencer_con_datos(self):
        """obtener_rentas_por_vencer() returns rentas within next 3 days."""
        p = _next_placa("ALR")
        _raw_insert_auto(p)
        cid = _raw_insert_cliente()

        # Create a rental ending today (within the 3-day window)
        rid = _raw_insert_renta(p, fecha_retorno=date.today(), id_cliente=cid)

        alertas = AlertaRepositorySA.obtener_rentas_por_vencer()
        match = [a for a in alertas if a["id"] == rid]
        assert len(match) >= 1
        # Verify expected structure
        assert "nombre_completo" in match[0]
        assert "celular" in match[0]
        assert "fecha_retorno" in match[0]

    def test_obtener_rentas_por_vencer_excluye_no_activas(self):
        """obtener_rentas_por_vencer() only includes Activo rentals."""
        p = _next_placa("ALR")
        _raw_insert_auto(p)
        cid = _raw_insert_cliente()

        # Create a Finalizado rental ending today (with cliente for inner join)
        rid = _raw_insert_renta(p, fecha_retorno=date.today(), estado="Finalizado",
                                id_cliente=cid)

        alertas = AlertaRepositorySA.obtener_rentas_por_vencer()
        # This rental should NOT appear (estado is Finalizado, not Activo)
        assert all(a["id"] != rid for a in alertas)

    def test_obtener_rentas_por_vencer_excluye_fecha_lejana(self):
        """obtener_rentas_por_vencer() excludes rentals ending more than 3 days out."""
        p = _next_placa("ALR")
        _raw_insert_auto(p)
        cid = _raw_insert_cliente()

        # Create a rental ending 10 days from now (outside the 3-day window)
        # With cliente for the inner join
        lejano = date.today() + timedelta(days=10)
        rid = _raw_insert_renta(p, fecha_retorno=lejano, estado="Activo",
                                id_cliente=cid)

        alertas = AlertaRepositorySA.obtener_rentas_por_vencer()
        assert all(a["id"] != rid for a in alertas)

    def test_obtener_documentos_por_vencer_vacio(self):
        """obtener_documentos_por_vencer() returns a list."""
        alertas = AlertaRepositorySA.obtener_documentos_por_vencer()
        assert isinstance(alertas, list)

    def test_obtener_documentos_por_vencer_con_datos(self):
        """obtener_documentos_por_vencer() returns autos with SOAT expiring within 15 days."""
        p = _next_placa("ALR")
        # SOAT expiring in 5 days
        _raw_insert_auto(p, vencimiento_soat=date.today() + timedelta(days=5))

        alertas = AlertaRepositorySA.obtener_documentos_por_vencer()
        placas = [a["placa"] for a in alertas]
        assert p in placas

    def test_obtener_documentos_por_vencer_excluye_vendido(self):
        """obtener_documentos_por_vencer() excludes Vendido autos."""
        p_active = _next_placa("ALR")
        p_vendido = _next_placa("ALR")

        target_date = date.today() + timedelta(days=5)
        _raw_insert_auto(p_active, vencimiento_soat=target_date)
        _raw_insert_auto(p_vendido, vencimiento_soat=target_date, estado="Vendido")

        alertas = AlertaRepositorySA.obtener_documentos_por_vencer()
        placas = [a["placa"] for a in alertas]
        assert p_active in placas
        assert p_vendido not in placas

    def test_obtener_mantenimientos_proximos_con_datos(self):
        """obtener_mantenimientos_proximos() returns autos near oil change."""
        p = _next_placa("ALR")
        # km=9800, proximo_aceite=10000 → km >= (10000 - 500=9500) → True
        _raw_insert_auto(p, kilometraje=9800.0, proximo_aceite=10000)

        alertas = AlertaRepositorySA.obtener_mantenimientos_proximos()
        placas = [a["placa"] for a in alertas]
        assert p in placas
        match = [a for a in alertas if a["placa"] == p]
        assert match[0]["kilometraje"] == 9800
        assert match[0]["proximo_aceite"] == 10000

    def test_obtener_mantenimientos_proximos_excluye_lejanos(self):
        """obtener_mantenimientos_proximos() excludes autos far from oil change."""
        p = _next_placa("ALR")
        # km=5000, proximo_aceite=10000 → km >= (10000 - 500=9500) → False → excluded
        _raw_insert_auto(p, kilometraje=5000.0, proximo_aceite=10000)

        alertas = AlertaRepositorySA.obtener_mantenimientos_proximos()
        assert all(a["placa"] != p for a in alertas)

    def test_obtener_mantenimientos_proximos_sin_proximo_aceite(self):
        """obtener_mantenimientos_proximos() excludes autos with NULL proximo_aceite."""
        p = _next_placa("ALR")
        _raw_insert_auto(p, kilometraje=100000.0)

        # Explicitly set proximo_aceite to NULL via raw session
        # (bypasses server_default='0' which would set it to 0 on INSERT)
        session = SessionLocal()
        try:
            auto = session.query(Auto).filter(Auto.placa == p).first()
            auto.proximo_aceite = None
            session.commit()
        finally:
            session.close()

        alertas = AlertaRepositorySA.obtener_mantenimientos_proximos()
        assert all(a["placa"] != p for a in alertas)
