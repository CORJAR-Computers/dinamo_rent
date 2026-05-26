"""
test_services_more.py — Unit tests for PagoService, MantenimientoService,
                         ReservaService, and AlertaService

Requires conftest.py to set up the in-memory SQLite database.
Each test method is self-contained (creates its own data).
Run: pytest tests/test_services_more.py -v
"""

import datetime
from decimal import Decimal

import pytest

from core.exceptions import (
    NegocioError,
    ValidacionError,
)
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.renta_service import RentaService
from services.pago_service import PagoService
from services.mantenimiento_service import MantenimientoService
from services.reserva_service import ReservaService
from services.alerta_service import AlertaService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers (reuse same pattern from test_services_unit.py)
# ═══════════════════════════════════════════════════════════════════════════════


def _crear_auto(placa: str, **kwargs):
    """Create a test auto with defaults."""
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
    """Create a test client with defaults."""
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
    """Create a test rental and return its ID. Auto must be Disponible."""
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


def _make_disponible(placa: str):
    """Force an auto back to Disponible state via service."""
    AutoService.guardar({"placa": placa, "estado": "Disponible"})


def _buscar_cliente_por_doc(no_doc: str):
    """Helper to find a client ID by document number."""
    clientes = ClienteService.buscar(no_doc)
    if clientes:
        return clientes[0]["id"]
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# PagoService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestPagoService:
    def test_registrar_pago(self):
        """registrar() creates a payment record."""
        _crear_auto("PAG001")
        renta_id = _crear_renta("PAG001", nombre_cliente="Pago Test")
        pago_id = PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "50000",
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
            }
        )
        assert isinstance(pago_id, int)
        assert pago_id > 0

    def test_registrar_pago_actualiza_abono(self):
        """registrar() updates the rental's abono and saldo_pendiente atomically."""
        _crear_auto("PAG002")
        renta_id = _crear_renta(
            "PAG002", nombre_cliente="Abono Test", total=Decimal("300000"), abono=Decimal("0")
        )

        # Register first payment of 100000
        PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "100000",
                "metodo_pago": "Transferencia",
            }
        )
        renta = RentaService.obtener(renta_id)
        assert renta["abono"] == 100000.0
        assert renta["saldo_pendiente"] == 200000.0

        # Register second payment of 150000
        PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "150000",
                "metodo_pago": "Efectivo",
            }
        )
        renta = RentaService.obtener(renta_id)
        assert renta["abono"] == 250000.0  # 100000 + 150000
        assert renta["saldo_pendiente"] == 50000.0  # 300000 - 250000

    def test_listar_pagos_por_renta(self):
        """listar_por_renta() returns all payments for a given rental."""
        _crear_auto("PAG003")
        renta_id = _crear_renta("PAG003", nombre_cliente="Listar Pagos")

        PagoService.registrar({"id_renta": renta_id, "monto": "30000", "metodo_pago": "Efectivo"})
        PagoService.registrar({"id_renta": renta_id, "monto": "40000", "metodo_pago": "Tarjeta"})

        pagos = PagoService.listar_por_renta(renta_id)
        assert len(pagos) == 2
        montos = [p["monto"] for p in pagos]
        assert 30000.0 in montos
        assert 40000.0 in montos

    def test_registrar_pago_sin_monto(self):
        """registrar() raises error when monto is missing."""
        _crear_auto("PAG004")
        renta_id = _crear_renta("PAG004")
        with pytest.raises((ValidacionError, NegocioError)):
            PagoService.registrar(
                {
                    "id_renta": renta_id,
                    "metodo_pago": "Efectivo",
                    # No monto
                }
            )

    def test_registrar_pago_monto_cero(self):
        """registrar() raises error when monto <= 0."""
        _crear_auto("PAG005")
        renta_id = _crear_renta("PAG005")
        with pytest.raises(ValidacionError, match="mayor a cero"):
            PagoService.registrar(
                {
                    "id_renta": renta_id,
                    "monto": "0",
                    "metodo_pago": "Efectivo",
                }
            )


# ═══════════════════════════════════════════════════════════════════════════════
# MantenimientoService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestMantenimientoService:
    def test_registrar_cambio_aceite(self):
        """registrar() creates an oil change record and updates auto's proximo_aceite."""
        _crear_auto("MNT001", kilometraje=15000, proximo_aceite=15000)

        MantenimientoService.registrar(
            {
                "placa": "MNT001",
                "tipo": "Cambio Aceite",
                "fecha": str(datetime.date.today()),
                "costo": "250000",
                "prox_km": 20000,
                "km_actual": 15000,
                "accion_estado": "mantener",
            }
        )

        # Check maintenance record exists in history
        historial = MantenimientoService.listar_historial()
        mant_records = [m for m in historial if m["placa"] == "MNT001"]
        assert len(mant_records) >= 1

        # Check auto's proximo_aceite was updated
        auto = AutoService.obtener("MNT001")
        assert auto["proximo_aceite"] == 20000

    def test_registrar_mantenimiento_cambia_estado(self):
        """registrar() changes auto state when accion_estado='mantenimiento'."""
        _crear_auto("MNT002", kilometraje=20000)

        MantenimientoService.registrar(
            {
                "placa": "MNT002",
                "tipo": "Frenos",
                "fecha": str(datetime.date.today()),
                "costo": "120000",
                "km_actual": 20000,
                "accion_estado": "mantenimiento",
            }
        )

        auto = AutoService.obtener("MNT002")
        assert auto["estado"] == "Mantenimiento"

    def test_registrar_mantenimiento_vuelve_disponible(self):
        """registrar() sets auto back to Disponible when accion_estado='disponible'."""
        _crear_auto("MNT003", kilometraje=30000, estado="Mantenimiento")

        MantenimientoService.registrar(
            {
                "placa": "MNT003",
                "tipo": "Lavado General",
                "fecha": str(datetime.date.today()),
                "costo": "50000",
                "km_actual": 30000,
                "accion_estado": "disponible",
            }
        )

        auto = AutoService.obtener("MNT003")
        assert auto["estado"] == "Disponible"

    def test_registrar_tecnomecanica_actualiza_vencimiento(self):
        """registrar() with 'Tecno-Mecánica' updates auto's vencimiento_tecnico."""
        _crear_auto("MNT004", kilometraje=40000)

        MantenimientoService.registrar(
            {
                "placa": "MNT004",
                "tipo": "Tecno-Mecánica",
                "fecha": str(datetime.date.today()),
                "costo": "350000",
                "km_actual": 40000,
                "accion_estado": "mantener",
            }
        )

        auto = AutoService.obtener("MNT004")
        # vencimiento_tecnico should be set to today + 365 days
        expected = datetime.date.today() + datetime.timedelta(days=365)
        assert str(auto["vencimiento_tecnico"]) == str(expected)

    def test_listar_historial(self):
        """listar_historial() returns maintenance records."""
        _crear_auto("MNT005")
        MantenimientoService.registrar(
            {
                "placa": "MNT005",
                "tipo": "Llantas",
                "fecha": str(datetime.date.today()),
                "costo": "800000",
                "km_actual": 10000,
            }
        )
        historial = MantenimientoService.listar_historial()
        assert len(historial) >= 1
        assert any(m["placa"] == "MNT005" for m in historial)

    def test_listar_autos(self):
        """listar_autos() returns autos with km (excludes Vendido/Baja)."""
        _crear_auto("MNT006", kilometraje=5000)
        _crear_auto("MNT007", kilometraje=8000, estado="Vendido")

        autos = MantenimientoService.listar_autos()
        placas = [a["placa"] for a in autos]
        assert "MNT006" in placas
        assert "MNT007" not in placas  # Vendido excluded

    def test_registrar_sin_tipo_lanza_error(self):
        """registrar() raises error when tipo is not provided."""
        _crear_auto("MNT008")
        with pytest.raises(ValidacionError, match="tipo"):
            MantenimientoService.registrar(
                {
                    "placa": "MNT008",
                    "costo": "50000",
                    "km_actual": 10000,
                    # No tipo
                }
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ReservaService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestReservaService:
    def test_crear_reserva(self):
        """crear() creates a reservation and returns its ID."""
        _crear_cliente("7777777777", nombres="Reserva", apellidos="Test")
        cliente_id = _buscar_cliente_por_doc("7777777777")

        hoy = datetime.date.today()
        reserva_id = ReservaService.crear(
            {
                "id_cliente": cliente_id,
                "nombre_cliente": "Reserva Test",
                "categoria_vehiculo": "Automóvil",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(9, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=2),
                "hora_retorno": datetime.time(9, 0),
                "dias_calculados": 2,
                "valor_dia": Decimal("120000"),
                "total": Decimal("240000"),
            }
        )
        assert isinstance(reserva_id, int)
        assert reserva_id > 0

    def test_crear_reserva_con_calculo_automatico(self):
        """crear() auto-calculates total when not provided."""
        _crear_cliente("8888888888", nombres="AutoCalc", apellidos="Reserva")
        cliente_id = _buscar_cliente_por_doc("8888888888")

        hoy = datetime.date.today()
        reserva_id = ReservaService.crear(
            {
                "id_cliente": cliente_id,
                "nombre_cliente": "AutoCalc",
                "categoria_vehiculo": "Van",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(8, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=3),
                "hora_retorno": datetime.time(8, 0),
                "dias_calculados": 3,
                "valor_dia": Decimal("150000"),
                # No total — should auto-calculate to 3 * 150000 = 450000
            }
        )
        reserva = ReservaService.obtener_para_pdf(reserva_id)
        assert reserva["total"] == 450000.0

    def test_listar_reservas(self):
        """listar() returns all reservations."""
        _crear_cliente("9999999999", nombres="Listar", apellidos="Reservas")
        cliente_id = _buscar_cliente_por_doc("9999999999")

        hoy = datetime.date.today()
        ReservaService.crear(
            {
                "id_cliente": cliente_id,
                "nombre_cliente": "List Reserva",
                "categoria_vehiculo": "Automóvil",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": datetime.time(10, 0),
                "total": Decimal("100000"),
            }
        )
        reservas = ReservaService.listar()
        assert len(reservas) >= 1
        assert any(r["nombre_cliente"] == "List Reserva" for r in reservas)

    def test_crear_reserva_sin_cliente(self):
        """crear() raises error when no id_cliente is provided."""
        with pytest.raises(ValidacionError, match="cliente"):
            ReservaService.crear(
                {
                    "nombre_cliente": "No Client",
                    # No id_cliente
                    "categoria_vehiculo": "Automóvil",
                    "fecha_recogida": datetime.date.today(),
                    "hora_recogida": datetime.time(10, 0),
                    "fecha_retorno": datetime.date.today() + datetime.timedelta(days=1),
                    "hora_retorno": datetime.time(10, 0),
                }
            )

    def test_crear_reserva_sin_vehiculo(self):
        """crear() raises error when no categoria_vehiculo or placa_asignada."""
        _crear_cliente("1010101010", nombres="No", apellidos="Vehicle")
        cliente_id = _buscar_cliente_por_doc("1010101010")

        with pytest.raises(ValidacionError, match="vehículo|vehiculo|categoría|categoria"):
            ReservaService.crear(
                {
                    "id_cliente": cliente_id,
                    "nombre_cliente": "No Vehicle",
                    # No categoria_vehiculo or placa_asignada
                    "fecha_recogida": datetime.date.today(),
                    "hora_recogida": datetime.time(10, 0),
                    "fecha_retorno": datetime.date.today() + datetime.timedelta(days=1),
                    "hora_retorno": datetime.time(10, 0),
                }
            )

    def test_cancelar_reserva(self):
        """cancelar() changes reservation status to 'Cancelada'."""
        _crear_cliente("1212121212", nombres="Cancel", apellidos="Reserva")
        cliente_id = _buscar_cliente_por_doc("1212121212")

        hoy = datetime.date.today()
        reserva_id = ReservaService.crear(
            {
                "id_cliente": cliente_id,
                "nombre_cliente": "Cancel Test",
                "categoria_vehiculo": "Lujo",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": datetime.time(10, 0),
                "total": Decimal("200000"),
            }
        )

        ReservaService.cancelar(reserva_id)
        reserva = ReservaService.obtener_para_pdf(reserva_id)
        assert reserva["estado"] == "Cancelada"

    def test_obtener_contacto(self):
        """obtener_contacto() returns client name and nationality from reservation."""
        _crear_cliente(
            "1313131313", nombres="Contacto", apellidos="Test", nacionalidad="Colombiana"
        )
        cliente_id = _buscar_cliente_por_doc("1313131313")

        hoy = datetime.date.today()
        reserva_id = ReservaService.crear(
            {
                "id_cliente": cliente_id,
                "nombre_cliente": "Contacto Test",
                "nacionalidad": "Colombiana",
                "categoria_vehiculo": "Automóvil",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": datetime.time(10, 0),
                "total": Decimal("100000"),
            }
        )

        contacto = ReservaService.obtener_contacto(reserva_id)
        assert contacto["nombre_cliente"] == "Contacto Test"
        assert contacto["nacionalidad"] == "Colombiana"


# ═══════════════════════════════════════════════════════════════════════════════
# AlertaService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAlertaService:
    def test_obtener_alertas_estructura(self):
        """obtener_todas_las_alertas() returns dict with expected keys."""
        alertas = AlertaService.obtener_todas_las_alertas()
        assert isinstance(alertas, dict)
        assert "clientes" in alertas
        assert "internas" in alertas
        # Note: lists may contain data from other tests sharing the same DB

    def test_alertas_rentas_por_vencer(self):
        """Detects rentals ending within the next 3 days."""
        _crear_cliente("1414141414", nombres="Alerta", apellidos="Cliente")
        cliente_id = _buscar_cliente_por_doc("1414141414")

        _crear_auto("ALR001")
        hoy = datetime.date.today()
        manana = hoy + datetime.timedelta(days=1)

        _crear_renta(
            "ALR001",
            nombre_cliente="Alerta Cliente",
            id_cliente=cliente_id,
            fecha_recogida=hoy,
            fecha_retorno=manana,
        )

        alertas = AlertaService.obtener_todas_las_alertas()
        client_alerts = [a for a in alertas["clientes"] if "ALR001" in a["titulo"]]
        assert len(client_alerts) >= 1
        assert "ALR001" in client_alerts[0]["titulo"]

    def test_alertas_documentos_por_vencer(self):
        """Detects autos with SOAT expiring within 15 days."""
        hoy = datetime.date.today()
        _crear_auto("ALR002", vencimiento_soat=str(hoy + datetime.timedelta(days=3)))

        alertas = AlertaService.obtener_todas_las_alertas()
        doc_alerts = [a for a in alertas["internas"] if "ALR002" in a["titulo"]]
        assert len(doc_alerts) >= 1
        assert "SOAT" in doc_alerts[0]["descripcion"] or "Documentos" in doc_alerts[0]["titulo"]

    def test_alertas_mantenimiento_proximo(self):
        """Detects autos needing oil change soon."""
        _crear_auto("ALR003", kilometraje=9500, proximo_aceite=10000)

        alertas = AlertaService.obtener_todas_las_alertas()
        # Use equality check instead of substring to avoid matching placas like ALR0031
        oil_alerts = [a for a in alertas["internas"] if a["titulo"].endswith(" - ALR003")]
        assert len(oil_alerts) >= 1
        assert any("Aceite" in a["titulo"] for a in oil_alerts)
