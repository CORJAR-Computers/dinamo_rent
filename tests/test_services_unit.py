"""
test_services_unit.py — Unit tests for AutoService, ClienteService, and RentaService

Requires conftest.py to set up the in-memory SQLite database.
Each test method is self-contained (creates its own data).
Run: pytest tests/test_services_unit.py -v
"""

import datetime
from decimal import Decimal

import pytest

from core.exceptions import (
    NegocioError,
    ValidacionError,
    VehiculoNoDisponible,
    RentaYaCerrada,
    ClienteEnListaNegra,
    RegistroNoEncontrado,
)
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.renta_service import RentaService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
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


# ═══════════════════════════════════════════════════════════════════════════════
# AutoService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAutoService:
    def test_listar_autos_estructura(self):
        """listar() returns a list with expected keys in each auto dict."""
        autos = AutoService.listar()
        assert isinstance(autos, list)
        if autos:
            auto = autos[0]
            expected_keys = {
                "placa",
                "marca",
                "modelo",
                "estado",
                "kilometraje",
                "tipo",
                "transmision",
                "combustible",
            }
            assert expected_keys.issubset(
                auto.keys()
            ), f"Missing keys in auto dict: {expected_keys - auto.keys()}"

    def test_guardar_y_listar_auto(self):
        """guardar() creates an auto, then listar() returns it."""
        _crear_auto("ABC001")
        autos = AutoService.listar()
        assert any(a["placa"] == "ABC001" for a in autos)

    def test_listar_disponibles(self):
        """listar_disponibles() only returns autos with estado='Disponible'."""
        _crear_auto("DSP001")
        _crear_auto("DSP002", estado="Mantenimiento")
        disponibles = AutoService.listar_disponibles()
        placas = [a["placa"] for a in disponibles]
        assert "DSP001" in placas
        assert "DSP002" not in placas

    def test_obtener_auto_por_placa(self):
        """obtener() returns the correct auto dict by placa."""
        _crear_auto("GET001", marca="Honda", modelo="Civic")
        auto = AutoService.obtener("GET001")
        assert auto["placa"] == "GET001"
        assert auto["marca"] == "Honda"
        assert auto["modelo"] == "Civic"

    def test_obtener_auto_no_encontrado(self):
        """obtener() raises NegocioError for a non-existent placa."""
        with pytest.raises(NegocioError, match="no encontrado"):
            AutoService.obtener("ZZZ999")

    def test_actualizar_auto(self):
        """guardar() with an existing placa updates the auto."""
        _crear_auto("UPD001", modelo="Base", color="Blanco")
        AutoService.guardar(
            {
                "placa": "UPD001",
                "marca": "Test",
                "modelo": "Premium",
                "color": "Rojo",
                "kilometraje": 20000,
            }
        )
        auto = AutoService.obtener("UPD001")
        assert auto["modelo"] == "Premium"
        assert auto["color"] == "Rojo"
        assert auto["kilometraje"] == 20000

    def test_guardar_placa_invalida_lanza_error(self):
        """guardar() raises ValidacionError for an invalid placa format."""
        with pytest.raises((ValidacionError, NegocioError)):
            AutoService.guardar(
                {
                    "placa": "INVALIDA12345",  # exceeds regex ^[A-Z0-9]{3,8}$
                    "marca": "Test",
                }
            )

    def test_alertas_aceite(self):
        """obtener_alertas() detects oil change alerts when km nears threshold."""
        _crear_auto("OIL001", kilometraje=9500, proximo_aceite=10000)
        alertas = AutoService.obtener_alertas()
        aceite_alerts = [a for a in alertas if a["tipo"] == "Aceite" and a["placa"] == "OIL001"]
        assert len(aceite_alerts) >= 1
        # Format: "9,500/10,000 km" — check it contains relevant numbers
        detalle = aceite_alerts[0]["detalle"]
        assert "/10,000 km" in detalle
        assert "9,500" in detalle or "9500" in detalle

    def test_alertas_soat(self):
        """obtener_alertas() detects SOAT expiration alerts."""
        _crear_auto("SOAT01", vencimiento_soat=str(datetime.date.today()))
        alertas = AutoService.obtener_alertas()
        soat_alerts = [a for a in alertas if a["tipo"] == "SOAT" and a["placa"] == "SOAT01"]
        assert len(soat_alerts) >= 1

    def test_alertas_tecnomecanica(self):
        """obtener_alertas() detects tecno-mecánica expiration alerts."""
        _crear_auto("TEC001", vencimiento_tecnico=str(datetime.date.today()))
        alertas = AutoService.obtener_alertas()
        # The service transforms 'Tecno-mecánica' to 'Tecno'
        tecno_alerts = [a for a in alertas if a["tipo"] == "Tecno" and a["placa"] == "TEC001"]
        assert len(tecno_alerts) >= 1


# ═══════════════════════════════════════════════════════════════════════════════
# ClienteService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestClienteService:
    def test_guardar_y_buscar_cliente(self):
        """guardar() creates a client, then buscar() finds it by name."""
        _crear_cliente("1111111111", nombres="Carlos", apellidos="Méndez")
        clientes = ClienteService.buscar("Carlos")
        assert any("Carlos Méndez" in c["nombre_completo"] for c in clientes)

    def test_buscar_por_documento(self):
        """buscar() finds clients by document number."""
        _crear_cliente("2222222222", nombres="Ana", apellidos="López")
        clientes = ClienteService.buscar("2222222222")
        assert len(clientes) >= 1

    def test_buscar_sin_termino_retorna_todos(self):
        """buscar() without a term returns all clients."""
        _crear_cliente("3333333333", nombres="Pedro", apellidos="Ramírez")
        result = ClienteService.buscar("")
        assert len(result) >= 1
        assert any(c["no_doc"] == "3333333333" for c in result)

    def test_obtener_cliente_por_id(self):
        """obtener() returns a client by ID."""
        _crear_cliente("4444444444", nombres="Laura", apellidos="Torres")
        clientes = ClienteService.buscar("4444444444")
        assert len(clientes) >= 1
        cliente_id = clientes[0]["id"]
        cliente = ClienteService.obtener(cliente_id)
        assert cliente["id"] == cliente_id
        assert cliente["no_doc"] == "4444444444"

    def test_obtener_cliente_no_encontrado(self):
        """obtener() raises RegistroNoEncontrado for non-existent ID."""
        with pytest.raises((RegistroNoEncontrado, NegocioError)):
            ClienteService.obtener(99999)

    def test_actualizar_cliente(self):
        """guardar() with an existing ID updates the client."""
        _crear_cliente("5555555555", nombres="Original", apellidos="Name")
        clientes = ClienteService.buscar("5555555555")
        cliente_id = clientes[0]["id"]

        ClienteService.guardar(
            {
                "id": cliente_id,
                "nombres": "Updated",
                "apellidos": "Name",
                "celular": "+573009999999",
            }
        )
        cliente = ClienteService.obtener(cliente_id)
        assert cliente["nombres"] == "Updated"
        assert cliente["celular"] == "+573009999999"

    def test_guardar_sin_nombres_lanza_error(self):
        """guardar() without 'nombres' raises ValidacionError."""
        with pytest.raises((ValidacionError, NegocioError)):
            ClienteService.guardar(
                {
                    "tipo_doc": "Cédula",
                    "no_doc": "6666666666",
                    "nombres": "",
                    "apellidos": "",
                }
            )


# ═══════════════════════════════════════════════════════════════════════════════
# RentaService Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestRentaService:
    def test_crear_renta(self):
        """crear() creates a rental and marks the vehicle as Rentado."""
        _crear_auto("RTA001")
        renta_id = _crear_renta("RTA001")
        assert isinstance(renta_id, int)
        assert renta_id > 0
        # Auto should now be Rentado
        auto = AutoService.obtener("RTA001")
        assert auto["estado"] == "Rentado"

    def test_crear_renta_con_calculo_automatico(self):
        """crear() auto-calculates total via FinancialService if not provided."""
        _crear_auto("RTA002")
        hoy = datetime.date.today()
        renta_id = RentaService.crear(
            {
                "placa": "RTA002",
                "nombre_cliente": "AutoCalc Test",
                "fecha_recogida": hoy,
                "hora_recogida": datetime.time(8, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=2),
                "hora_retorno": datetime.time(8, 0),
                "dias_calculados": 2,
                "valor_dia": Decimal("150000"),
                # No total — should auto-calculate to 300000
            }
        )
        renta = RentaService.obtener(renta_id)
        # Total should be 2 * 150000 = 300000 (no extras)
        assert renta["total"] == 300000.0

    def test_crear_renta_vehiculo_no_disponible(self):
        """crear() raises VehiculoNoDisponible if auto is already rented."""
        _crear_auto("RTA003")
        _crear_renta("RTA003")  # First rental makes it Rentado
        with pytest.raises(VehiculoNoDisponible):
            _crear_renta("RTA003")  # Second attempt should fail

    def test_crear_renta_cliente_lista_negra(self):
        """crear() raises ClienteEnListaNegra if estado_cliente is 'Lista Negra'."""
        _crear_auto("RTA004")
        with pytest.raises(ClienteEnListaNegra):
            RentaService.crear(
                {
                    "placa": "RTA004",
                    "nombre_cliente": "Blacklisted Client",
                    "estado_cliente": "Lista Negra",
                    "fecha_recogida": datetime.date.today(),
                    "hora_recogida": datetime.time(10, 0),
                    "fecha_retorno": datetime.date.today() + datetime.timedelta(days=1),
                    "hora_retorno": datetime.time(10, 0),
                    "total": Decimal("50000"),
                }
            )

    def test_obtener_renta_por_id(self):
        """obtener() returns rental details by ID."""
        _crear_auto("RTA005")
        renta_id = _crear_renta("RTA005", nombre_cliente="GetTest")
        renta = RentaService.obtener(renta_id)
        assert renta["id"] == renta_id
        assert renta["placa"] == "RTA005"
        assert renta["estado"] == "Activo"

    def test_obtener_rentas_activas(self):
        """obtener_activas() returns currently active rentals."""
        _crear_auto("RTA006")
        _crear_renta("RTA006", nombre_cliente="ActiveTest")
        activas = RentaService.obtener_activas()
        assert len(activas) >= 1
        assert any(r["placa"] == "RTA006" for r in activas)

    def test_cerrar_renta(self):
        """cerrar() closes a rental, marks auto Disponible, calculates total."""
        _crear_auto("RTA007")
        renta_id = _crear_renta(
            "RTA007",
            nombre_cliente="CloseTest",
            valor_dia=Decimal("120000"),
            total=Decimal("360000"),
        )

        hoy = datetime.date.today()
        total = RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy,
                "hora_devolucion_real": datetime.time(14, 30),
                "km_final": "20500",
                "tanque_final": "Lleno",
                "nota_cierre": "Devuelto en buen estado",
                "otros_cobros": Decimal("0"),
            },
        )
        assert total == 360000.0  # No retraso, no otros cobros

        # Auto should be Disponible again
        auto = AutoService.obtener("RTA007")
        assert auto["estado"] == "Disponible"

        # Renta should be Finalizado
        renta = RentaService.obtener(renta_id)
        assert renta["estado"] == "Finalizado"

    def test_cerrar_renta_con_retraso(self):
        """cerrar() includes delay charges when returned late."""
        _crear_auto("RTA008")
        hoy = datetime.date.today()
        renta_id = _crear_renta(
            "RTA008",
            nombre_cliente="LateTest",
            fecha_recogida=hoy - datetime.timedelta(days=5),
            fecha_retorno=hoy - datetime.timedelta(days=2),
            dias_calculados=3,
            valor_dia=Decimal("100000"),
            total=Decimal("300000"),
        )

        # Return 2 days late
        late_total = RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy,
                "hora_devolucion_real": datetime.time(14, 0),
                "km_final": "25000",
                "tanque_final": "Medio",
                "nota_cierre": "Llegó tarde",
                "otros_cobros": Decimal("0"),
            },
        )
        # 2 days late * 100000 + original 300000 = 500000
        assert late_total == 500000.0

    def test_cerrar_renta_ya_cerrada(self):
        """cerrar() raises RentaYaCerrada if the rental is already finalized."""
        _crear_auto("RTA009")
        renta_id = _crear_renta("RTA009", nombre_cliente="DoubleClose")
        hoy = datetime.date.today()
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy,
                "hora_devolucion_real": datetime.time(12, 0),
                "otros_cobros": Decimal("0"),
            },
        )
        # Second close should fail
        with pytest.raises(RentaYaCerrada):
            RentaService.cerrar(
                renta_id,
                {
                    "fecha_devolucion_real": hoy,
                    "hora_devolucion_real": datetime.time(12, 0),
                    "otros_cobros": Decimal("0"),
                },
            )

    def test_cambiar_vehiculo(self):
        """cambiar_vehiculo() swaps vehicle on an active rental atomically."""
        # Create two autos
        _crear_auto("RTA010")  # Will be swapped FROM
        _crear_auto("RTA011")  # Will be swapped TO (starts Disponible)

        # Create a rental on RTA010
        renta_id = _crear_renta("RTA010", nombre_cliente="SwapTest")

        # Swap to RTA011
        RentaService.cambiar_vehiculo(
            id_renta=renta_id,
            placa_actual="RTA010",
            km_actual=15000,
            estado_actual="Disponible",
            placa_nueva="RTA011",
            motivo="Cliente solicitó cambio",
        )

        # Old auto should be Disponible
        assert AutoService.obtener("RTA010")["estado"] == "Disponible"
        # New auto should be Rentado
        assert AutoService.obtener("RTA011")["estado"] == "Rentado"
        # Rental should reference new plate
        renta = RentaService.obtener(renta_id)
        assert renta["placa"] == "RTA011"
        # Observation should mention the swap
        assert renta["observaciones"] is not None
        assert "RTA010" in renta["observaciones"]
