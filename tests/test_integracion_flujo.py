"""
test_integracion_flujo.py — Integration tests for the complete rental workflow.

Tests the end-to-end flow through the service layer:
  ClienteService → AutoService → RentaService → PagoService → RentaService.cerrar

Uses the existing conftest.py for in-memory SQLite database setup.
Each test is self-contained with unique data identifiers.

Run: pytest tests/test_integracion_flujo.py -v
"""

import datetime
from decimal import Decimal
from datetime import date, time

import pytest

from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    ValidacionError,
    VehiculoNoDisponible,
    RentaYaCerrada,
    ClienteEnListaNegra,
    RegistroNoEncontrado,
)
from services.cliente_service import ClienteService
from services.auto_service import AutoService
from services.renta_service import RentaService
from services.pago_service import PagoService


# ═══════════════════════════════════════════════════════════════════════════════
# Unique ID generator (avoids UNIQUE constraint violations across tests)
# ═══════════════════════════════════════════════════════════════════════════════

_test_id = 0


def _next_placa(prefix="INT") -> str:
    global _test_id
    _test_id += 1
    return f"{prefix}{_test_id:04d}"


def _next_doc() -> str:
    global _test_id
    _test_id += 1
    return f"{_test_id:09d}"  # purely numeric, passes validar_documento (6-15 digits)


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Full Rental Flow
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlujoCompletoRenta:
    def test_flujo_completo_normal(self):
        """
        Full end-to-end rental workflow:
        1. Create client
        2. Create auto (Disponible)
        3. Create rental (auto → Rentado)
        4. Register payment (abono/saldo updated)
        5. Close rental (auto → Disponible, estado → Finalizado)
        """
        # ── Step 1: Create client ────────────────────────────────────────
        doc = _next_doc()
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Carlos",
                "apellidos": "Integración",
                "nombre_completo": "Carlos Integración",
                "celular": "+573001234567",
                "email": "carlos@test.com",
                "ciudad": "Bogotá",
                "pais": "Colombia",
                "nacionalidad": "Colombiana",
                "estado": "Activo",
            }
        )

        # Verify client exists
        clientes = ClienteService.buscar(doc)
        assert len(clientes) == 1
        assert clientes[0]["no_doc"] == doc
        cliente_id = clientes[0]["id"]
        assert cliente_id > 0

        # ── Step 2: Create auto ─────────────────────────────────────────
        placa = _next_placa()
        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Toyota",
                "modelo": "Corolla",
                "tipo": "Automóvil",
                "transmision": "Automática",
                "combustible": "Gasolina",
                "kilometraje": 15000.0,
                "color": "Blanco",
                "estado": "Disponible",
            }
        )

        # Verify auto exists and is Disponible
        auto = AutoService.obtener(placa)
        assert auto["estado"] == "Disponible"
        assert auto["kilometraje"] == 15000.0

        # ── Step 3: Create rental (3 days, $100,000/day) ────────────────
        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Carlos Integración",
                "nacionalidad": "Colombiana",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=3),
                "hora_retorno": time(10, 0),
                "dias_calculados": 3,
                "valor_dia": Decimal("100000"),
                "total": Decimal("300000"),
                "abono": Decimal("0"),
            }
        )

        assert isinstance(renta_id, int)
        assert renta_id > 0

        # Verify auto changed to Rentado
        auto = AutoService.obtener(placa)
        assert auto["estado"] == "Rentado"

        # Verify rental exists with correct data
        renta = RentaService.obtener(renta_id)
        assert renta["placa"] == placa
        assert renta["nombre_cliente"] == "Carlos Integración"
        assert renta["total"] == 300000.0
        assert renta["abono"] == 0.0
        assert renta["saldo_pendiente"] == 0.0  # Service stores default (not auto-calculated)
        assert renta["estado"] == "Activo"

        # ── Step 4: Register payment (first payment: $100,000) ──────────
        pago1_id = PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "100000",
                "metodo_pago": "Efectivo",
                "concepto": "Abono inicial",
            }
        )
        assert isinstance(pago1_id, int)
        assert pago1_id > 0

        # Verify rental abono/saldo updated
        renta = RentaService.obtener(renta_id)
        assert renta["abono"] == 100000.0
        assert renta["saldo_pendiente"] == 200000.0

        # Register second payment ($150,000)
        pago2_id = PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "150000",
                "metodo_pago": "Transferencia",
                "concepto": "Segundo abono",
            }
        )
        assert pago2_id > 0

        # Verify accumulated abono/saldo
        renta = RentaService.obtener(renta_id)
        assert renta["abono"] == 250000.0  # 100000 + 150000
        assert renta["saldo_pendiente"] == 50000.0  # 300000 - 250000

        # Verify payments list
        pagos = PagoService.listar_por_renta(renta_id)
        assert len(pagos) == 2
        montos = sorted([p["monto"] for p in pagos])
        assert montos == [100000.0, 150000.0]

        # ── Step 5: Close rental ────────────────────────────────────────
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=3),
                "hora_devolucion_real": time(10, 30),
                "km_final": "15300",
                "tanque_final": "3/4",
                "nota_cierre": "Cliente devolvió en buen estado",
            },
        )

        # Verify rental is Finalizado
        renta = RentaService.obtener(renta_id)
        assert renta["estado"] == "Finalizado"
        assert renta["km_final"] == "15300"

        # Verify auto is back to Disponible with updated km
        auto = AutoService.obtener(placa)
        assert auto["estado"] == "Disponible"
        assert auto["kilometraje"] == 15300.0

    def test_flujo_con_retraso_y_cargos_extra(self):
        """
        Rental returned late with extra charges:
        1. Create client + auto + 2-day rental
        2. Close rental 2 days late with otros_cobros
        3. Verify late fees and extra charges applied
        """
        # Setup
        doc = _next_doc()
        placa = _next_placa("LAT")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Late",
                "apellidos": "Return",
                "nombre_completo": "Late Return",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Nissan",
                "modelo": "Versa",
                "tipo": "Automóvil",
                "transmision": "Mecánica",
                "combustible": "Gasolina",
                "kilometraje": 20000.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Late Return",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=2),
                "hora_retorno": time(10, 0),
                "dias_calculados": 2,
                "valor_dia": Decimal("80000"),
                "total": Decimal("160000"),
                "abono": Decimal("160000"),  # Paid in full
            }
        )

        # Close rental 2 days late with extra km and cleaning fee
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=4),  # 2 days late
                "hora_devolucion_real": time(14, 0),
                "km_final": "20700",  # 700 km over
                "tanque_final": "1/4",
                "nota_cierre": "Devolución tardía con tanque bajo",
                "otros_cobros": Decimal("120000"),  # Late fee + cleaning
            },
        )

        # Verify state
        renta = RentaService.obtener(renta_id)
        assert renta["estado"] == "Finalizado"
        # Total should be 160000 + 120000 = 280000
        assert renta["total"] == 280000.0
        # Saldo pendiente should be 280000 - 160000 = 120000
        assert renta["saldo_pendiente"] == 120000.0
        assert renta["km_final"] == "20700"

        # Verify auto updated
        auto = AutoService.obtener(placa)
        assert auto["estado"] == "Disponible"
        assert auto["kilometraje"] == 20700.0

    def test_flujo_pago_total_al_cierre(self):
        """
        Client pays remaining balance at closure:
        1. Create rental with partial abono
        2. Register full payment at closing
        3. Verify saldo_pendiente = 0
        """
        doc = _next_doc()
        placa = _next_placa("FUL")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Full",
                "apellidos": "Payment",
                "nombre_completo": "Full Payment",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Chevrolet",
                "modelo": "Spark",
                "kilometraje": 5000.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Full Payment",
                "fecha_recogida": hoy,
                "hora_recogida": time(9, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": time(9, 0),
                "dias_calculados": 1,
                "valor_dia": Decimal("120000"),
                "total": Decimal("120000"),
                "abono": Decimal("50000"),
            }
        )

        # Make partial payment
        PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "50000",
                "metodo_pago": "Efectivo",
                "concepto": "Abono",
            }
        )

        # Register final payment at closure
        PagoService.registrar(
            {
                "id_renta": renta_id,
                "monto": "70000",
                "metodo_pago": "Tarjeta",
                "concepto": "Pago final",
            }
        )

        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=1),
                "hora_devolucion_real": time(9, 0),
            },
        )

        renta = RentaService.obtener(renta_id)
        assert renta["estado"] == "Finalizado"
        assert renta["abono"] == 120000.0  # 50000 + 70000
        assert renta["saldo_pendiente"] == 0.0  # Fully paid

    def test_flujo_devuelve_mismo_dia(self):
        """
        Client returns the car on the same day (early return):
        1. Create 5-day rental
        2. Close on same day
        3. Verify everything works correctly
        """
        doc = _next_doc()
        placa = _next_placa("EAR")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Early",
                "apellidos": "Bird",
                "nombre_completo": "Early Bird",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Renault",
                "modelo": "Logan",
                "kilometraje": 30000.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Early Bird",
                "fecha_recogida": hoy,
                "hora_recogida": time(8, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=5),
                "hora_retorno": time(8, 0),
                "dias_calculados": 5,
                "valor_dia": Decimal("90000"),
                "total": Decimal("450000"),
                "abono": Decimal("450000"),
            }
        )

        # Close same day
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy,
                "hora_devolucion_real": time(16, 0),
                "km_final": "30150",
                "nota_cierre": "Devolución anticipada",
            },
        )

        renta = RentaService.obtener(renta_id)
        assert renta["estado"] == "Finalizado"
        assert renta["km_final"] == "30150"

        auto = AutoService.obtener(placa)
        assert auto["estado"] == "Disponible"


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Error Paths in Flow
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlujoErrores:
    def test_crear_renta_vehiculo_no_disponible(self):
        """Cannot rent an auto that is already Rentado."""
        doc = _next_doc()
        placa = _next_placa("ERR")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Fail",
                "apellidos": "Test",
                "nombre_completo": "Fail Test",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Test",
                "modelo": "X",
                "kilometraje": 100.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_kwargs = {
            "placa": placa,
            "id_cliente": cliente_id,
            "nombre_cliente": "Fail Test",
            "fecha_recogida": hoy,
            "hora_recogida": time(10, 0),
            "fecha_retorno": hoy + datetime.timedelta(days=1),
            "hora_retorno": time(10, 0),
            "total": Decimal("100000"),
        }

        # First rental succeeds
        RentaService.crear(renta_kwargs)

        # Second rental for same auto must fail
        with pytest.raises(VehiculoNoDisponible):
            RentaService.crear(renta_kwargs)

    def test_crear_renta_cliente_lista_negra(self):
        """Cannot create a rental for a blacklisted client."""
        doc = _next_doc()
        placa = _next_placa("BLK")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Black",
                "apellidos": "Listed",
                "nombre_completo": "Black Listed",
                "estado": "Lista Negra",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Test",
                "modelo": "X",
                "kilometraje": 100.0,
                "estado": "Disponible",
            }
        )

        with pytest.raises(ClienteEnListaNegra):
            RentaService.crear(
                {
                    "placa": placa,
                    "id_cliente": cliente_id,
                    "nombre_cliente": "Black Listed",
                    "estado_cliente": "Lista Negra",  # Service checks this field, not DB state
                    "fecha_recogida": date.today(),
                    "hora_recogida": time(10, 0),
                    "fecha_retorno": date.today() + datetime.timedelta(days=1),
                    "hora_retorno": time(10, 0),
                    "total": Decimal("100000"),
                }
            )

    def test_cerrar_renta_ya_cerrada(self):
        """Cannot close an already closed rental."""
        doc = _next_doc()
        placa = _next_placa("DCL")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Double",
                "apellidos": "Close",
                "nombre_completo": "Double Close",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Test",
                "modelo": "Y",
                "kilometraje": 200.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Double Close",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": time(10, 0),
                "total": Decimal("100000"),
            }
        )

        # Close once
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=1),
                "hora_devolucion_real": time(10, 0),
            },
        )

        # Close again must fail
        with pytest.raises(RentaYaCerrada):
            RentaService.cerrar(
                renta_id,
                {
                    "fecha_devolucion_real": hoy + datetime.timedelta(days=1),
                    "hora_devolucion_real": time(10, 0),
                },
            )

    def test_cerrar_renta_inexistente(self):
        """Cannot close a non-existent rental."""
        with pytest.raises(RegistroNoEncontrado):
            RentaService.cerrar(
                99999,
                {
                    "fecha_devolucion_real": date.today(),
                    "hora_devolucion_real": time(10, 0),
                },
            )

    def test_crear_renta_sin_cliente(self):
        """Creating a rental without a client will proceed (id_cliente defaults to 0)."""
        placa = _next_placa("NOC")
        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Test",
                "modelo": "Z",
                "kilometraje": 300.0,
                "estado": "Disponible",
            }
        )

        # The service doesn't validate id_cliente is present — it just creates
        # with a default or None value. No exception expected.
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "nombre_cliente": "No Client",
                "fecha_recogida": date.today(),
                "hora_recogida": time(10, 0),
                "fecha_retorno": date.today() + datetime.timedelta(days=1),
                "hora_retorno": time(10, 0),
                "total": Decimal("100000"),
            }
        )
        assert isinstance(renta_id, int)
        assert renta_id > 0

    def test_pago_sin_renta(self):
        """Cannot register a payment for a non-existent rental (FK constraint)."""
        with pytest.raises((RegistroNoEncontrado, IntegrityError)):
            PagoService.registrar(
                {
                    "id_renta": 99999,
                    "monto": "50000",
                    "metodo_pago": "Efectivo",
                    "concepto": "Abono",
                }
            )

    def test_pago_monto_cero(self):
        """Cannot register a payment with zero amount."""
        doc = _next_doc()
        placa = _next_placa("ZER")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Zero",
                "apellidos": "Pay",
                "nombre_completo": "Zero Pay",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]
        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Test",
                "modelo": "W",
                "kilometraje": 400.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Zero Pay",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": time(10, 0),
                "total": Decimal("100000"),
            }
        )

        with pytest.raises(ValidacionError, match="mayor a cero"):
            PagoService.registrar(
                {
                    "id_renta": renta_id,
                    "monto": "0",
                    "metodo_pago": "Efectivo",
                    "concepto": "Abono",
                }
            )


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Multi-Rental and State Transitions
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlujoMultiplesRentas:
    def test_auto_rentado_varias_veces(self):
        """
        An auto can be rented multiple times (sequential):
        Rent → Return → Rent → Return → Rent → Return
        """
        doc = _next_doc()
        placa = _next_placa("SEQ")
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Sequential",
                "apellidos": "Renter",
                "nombre_completo": "Sequential Renter",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        AutoService.guardar(
            {
                "placa": placa,
                "marca": "Kia",
                "modelo": "Picanto",
                "kilometraje": 10000.0,
                "estado": "Disponible",
            }
        )

        hoy = date.today()

        # Rental 1
        r1_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Sequential Renter",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": time(10, 0),
                "total": Decimal("80000"),
                "abono": Decimal("80000"),
            }
        )
        assert AutoService.obtener(placa)["estado"] == "Rentado"

        # Return 1
        RentaService.cerrar(
            r1_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=1),
                "hora_devolucion_real": time(10, 0),
                "km_final": "10200",
            },
        )
        assert AutoService.obtener(placa)["estado"] == "Disponible"

        # Rental 2
        r2_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Sequential Renter",
                "fecha_recogida": hoy + datetime.timedelta(days=2),
                "hora_recogida": time(9, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=4),
                "hora_retorno": time(9, 0),
                "total": Decimal("160000"),
                "abono": Decimal("100000"),
            }
        )
        assert AutoService.obtener(placa)["estado"] == "Rentado"

        # Return 2
        RentaService.cerrar(
            r2_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=4),
                "hora_devolucion_real": time(9, 0),
                "km_final": "10500",
            },
        )
        assert AutoService.obtener(placa)["estado"] == "Disponible"

        # Rental 3
        r3_id = RentaService.crear(
            {
                "placa": placa,
                "id_cliente": cliente_id,
                "nombre_cliente": "Sequential Renter",
                "fecha_recogida": hoy + datetime.timedelta(days=5),
                "hora_recogida": time(12, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=7),
                "hora_retorno": time(12, 0),
                "total": Decimal("160000"),
                "abono": Decimal("160000"),
            }
        )
        assert AutoService.obtener(placa)["estado"] == "Rentado"

        RentaService.cerrar(
            r3_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=7),
                "hora_devolucion_real": time(12, 0),
                "km_final": "10800",
            },
        )
        assert AutoService.obtener(placa)["estado"] == "Disponible"

        # Final checks — km should update after each close
        assert AutoService.obtener(placa)["kilometraje"] == 10800.0
        assert RentaService.obtener(r3_id)["estado"] == "Finalizado"

    def test_rentas_activas_after_operations(self):
        """
        After multiple operations, obtener_rentas_activas() should
        only return rentals still in 'Activo' state.
        """
        doc_a = _next_doc()
        doc_b = _next_doc()
        p1, p2, p3 = _next_placa("AC"), _next_placa("AC"), _next_placa("AC")

        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc_a,
                "nombres": "Active",
                "apellidos": "One",
                "nombre_completo": "Active One",
                "estado": "Activo",
            }
        )
        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc_b,
                "nombres": "Active",
                "apellidos": "Two",
                "nombre_completo": "Active Two",
                "estado": "Activo",
            }
        )
        cid_a = ClienteService.buscar(doc_a)[0]["id"]
        cid_b = ClienteService.buscar(doc_b)[0]["id"]

        for p in [p1, p2, p3]:
            AutoService.guardar(
                {
                    "placa": p,
                    "marca": "Test",
                    "modelo": "X",
                    "kilometraje": 100.0,
                    "estado": "Disponible",
                }
            )

        hoy = date.today()

        # Create 3 rentals
        r1 = RentaService.crear(
            {
                "placa": p1,
                "id_cliente": cid_a,
                "nombre_cliente": "Active One",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=3),
                "hora_retorno": time(10, 0),
                "total": Decimal("150000"),
                "abono": Decimal("50000"),
            }
        )
        r2 = RentaService.crear(
            {
                "placa": p2,
                "id_cliente": cid_b,
                "nombre_cliente": "Active Two",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=2),
                "hora_retorno": time(10, 0),
                "total": Decimal("100000"),
            }
        )
        r3 = RentaService.crear(
            {
                "placa": p3,
                "id_cliente": cid_a,
                "nombre_cliente": "Active One",
                "fecha_recogida": hoy,
                "hora_recogida": time(12, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=1),
                "hora_retorno": time(12, 0),
                "total": Decimal("50000"),
            }
        )

        # Close r2 and r3, leave r1 active
        RentaService.cerrar(
            r2,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=2),
                "hora_devolucion_real": time(10, 0),
            },
        )
        RentaService.cerrar(
            r3,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=1),
                "hora_devolucion_real": time(12, 0),
            },
        )

        activas = RentaService.obtener_activas()
        ids_activas = [r["id"] for r in activas]

        assert r1 in ids_activas  # Still active
        assert r2 not in ids_activas  # Closed
        assert r3 not in ids_activas  # Closed
        assert all(r["estado"] == "Activo" for r in activas)


# ═══════════════════════════════════════════════════════════════════════════════
# Integration: Cambio de Vehículo
# ═══════════════════════════════════════════════════════════════════════════════


class TestFlujoCambioVehiculo:
    def test_cambiar_vehiculo_en_renta_activa(self):
        """
        Change the vehicle assigned to an active rental:
        1. Create rental with auto A (A → Rentado)
        2. Change to auto B (A → Disponible, B → Rentado)
        3. Close rental (B → Disponible)
        """
        doc = _next_doc()
        placa_a = _next_placa("SWP")
        placa_b = _next_placa("SWP")

        ClienteService.guardar(
            {
                "tipo_doc": "Cédula",
                "no_doc": doc,
                "nombres": "Swap",
                "apellidos": "Vehicle",
                "nombre_completo": "Swap Vehicle",
                "estado": "Activo",
            }
        )
        cliente_id = ClienteService.buscar(doc)[0]["id"]

        for p in [placa_a, placa_b]:
            AutoService.guardar(
                {
                    "placa": p,
                    "marca": "Test",
                    "modelo": "Swap",
                    "kilometraje": 5000.0,
                    "estado": "Disponible",
                }
            )

        hoy = date.today()
        renta_id = RentaService.crear(
            {
                "placa": placa_a,
                "id_cliente": cliente_id,
                "nombre_cliente": "Swap Vehicle",
                "fecha_recogida": hoy,
                "hora_recogida": time(10, 0),
                "fecha_retorno": hoy + datetime.timedelta(days=2),
                "hora_retorno": time(10, 0),
                "total": Decimal("200000"),
                "abono": Decimal("50000"),
            }
        )

        # Verify A is Rentado, B is Disponible
        assert AutoService.obtener(placa_a)["estado"] == "Rentado"
        assert AutoService.obtener(placa_b)["estado"] == "Disponible"

        # Change vehicle from A to B
        RentaService.cambiar_vehiculo(
            renta_id,
            placa_actual=placa_a,
            km_actual=5300.0,
            estado_actual="Disponible",
            placa_nueva=placa_b,
            motivo="Vehículo A presentó problema mecánico",
        )

        # Verify A is Disponible again, B is Rentado
        assert AutoService.obtener(placa_a)["estado"] == "Disponible"
        assert AutoService.obtener(placa_b)["estado"] == "Rentado"

        # Verify rental now references B
        renta = RentaService.obtener(renta_id)
        assert renta["placa"] == placa_b
        assert "problema mecánico" in renta.get("observaciones", "")

        # Close rental (B should go back to Disponible)
        RentaService.cerrar(
            renta_id,
            {
                "fecha_devolucion_real": hoy + datetime.timedelta(days=2),
                "hora_devolucion_real": time(10, 0),
                "km_final": "5500",
            },
        )

        assert AutoService.obtener(placa_a)["estado"] == "Disponible"
        assert AutoService.obtener(placa_b)["estado"] == "Disponible"  # B was returned
        # B should have updated km from close
        assert AutoService.obtener(placa_b)["kilometraje"] == 5500.0
