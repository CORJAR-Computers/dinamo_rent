"""
test_financial_service.py — Unit tests for FinancialService

Covers:
  - calcular_total_renta (pure calculation: días × valor_día, extras, descuento, impuestos)
  - calcular_total_cierre (retraso, otros_cobros, límites)
  - roi_flota (ROI con datos reales en BD, exclusión de Vendido/Baja)

Requires conftest.py to set up the in-memory SQLite database.
Each test method is self-contained (creates its own data).
Run: pytest tests/test_financial_service.py -v
"""

import datetime
from decimal import Decimal

import pytest

from services.financial_service import FinancialService
from repositories.repositories_sa import (
    AutoRepositorySA,
    RentaRepositorySA,
)
from repositories.mantenimiento_repository_sa import MantenimientoRepositorySA
from repositories.gasto_repository_sa import GastoRepositorySA
from core.schemas import (
    AutoCreate,
    RentaCreate,
    MantenimientoCreate,
    GastoCreate,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level counter for unique IDs (shared DB across tests)
# ═══════════════════════════════════════════════════════════════════════════════

_test_counter = 0


def _next_placa(prefix: str = "FIN") -> str:
    global _test_counter
    _test_counter += 1
    return f"{prefix}{_test_counter:04d}"


# ═══════════════════════════════════════════════════════════════════════════════
# calcular_total_renta Tests  (pure calculation — no DB needed)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalcularTotalRenta:
    def test_basico_dias_por_valor_dia(self):
        """3 días × $100.000 = $300.000 — sin extras ni descuentos."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": 3,
                "valor_dia": 100000,
            }
        )
        assert total == 300000.0

    def test_con_horas_extras(self):
        """3 días × $100.000 + 2 horas extra × $20.000 = $340.000."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": 3,
                "valor_dia": 100000,
                "horas_extras": 2,
                "valor_hora_extra": 20000,
            }
        )
        assert total == 340000.0

    def test_con_todos_los_extras(self):
        """Incluye todos los costos extra adicionales."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": 2,
                "valor_dia": 80000,
                "costo_lavado": 30000,
                "costo_silla": 15000,
                "costo_retorno": 50000,
                "costo_domicilio": 20000,
                "costo_cables": 10000,
                "costo_inversor": 25000,
            }
        )
        # 2 × 80000 + 30000 + 15000 + 50000 + 20000 + 10000 + 25000
        # = 160000 + 150000 = 310000
        assert total == 310000.0

    def test_con_descuento(self):
        """Subtotal con descuento aplicado."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": 5,
                "valor_dia": 100000,
                "descuento": 50000,
            }
        )
        # 5 × 100000 - 50000 = 450000
        assert total == 450000.0

    def test_con_descuento_e_impuestos(self):
        """Subtotal - descuento + impuestos."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": 3,
                "valor_dia": 100000,
                "descuento": 30000,
                "impuestos": 57000,
            }
        )
        # (3 × 100000) - 30000 + 57000 = 300000 - 30000 + 57000 = 327000
        assert total == 327000.0

    def test_valores_cero_retorna_cero(self):
        """Todos los valores en cero devuelven 0.0."""
        total = FinancialService.calcular_total_renta({})
        assert total == 0.0

    def test_solo_extras_sin_dias(self):
        """Extras sin días ni valor_día se suman correctamente."""
        total = FinancialService.calcular_total_renta(
            {
                "costo_lavado": 40000,
                "costo_silla": 20000,
            }
        )
        assert total == 60000.0

    def test_valores_como_strings(self):
        """Valores pasados como strings se convierten a float."""
        total = FinancialService.calcular_total_renta(
            {
                "dias_calculados": "3",
                "valor_dia": "100000",
                "horas_extras": "2",
                "valor_hora_extra": "25000",
                "costo_lavado": "15000",
                "descuento": "10000",
            }
        )
        # 3 × 100000 + 2 × 25000 + 15000 - 10000 = 300000 + 50000 + 15000 - 10000 = 355000
        assert total == 355000.0

    def test_impuestos_sin_subtotal(self):
        """Solo impuestos sin días ni valor_día."""
        total = FinancialService.calcular_total_renta(
            {
                "impuestos": 19000,
            }
        )
        assert total == 19000.0


# ═══════════════════════════════════════════════════════════════════════════════
# calcular_total_cierre Tests  (pure calculation — no DB needed)
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalcularTotalCierre:
    def test_devolucion_a_tiempo_sin_cargos(self):
        """Misma fecha pactada y real = solo el total original."""
        total = FinancialService.calcular_total_cierre(
            {"total": 300000, "valor_dia": 100000, "fecha_retorno": "2026-05-20"},
            {"fecha_devolucion_real": "2026-05-20"},
        )
        assert total == 300000.0

    def test_devolucion_con_retraso(self):
        """2 días de retraso: 300000 + 2 × 100000 = 500000."""
        total = FinancialService.calcular_total_cierre(
            {"total": 300000, "valor_dia": 100000, "fecha_retorno": "2026-05-18"},
            {"fecha_devolucion_real": "2026-05-20"},
        )
        assert total == 500000.0

    def test_devolucion_con_retraso_y_otros_cobros(self):
        """2 días retraso + $50.000 otros cobros."""
        total = FinancialService.calcular_total_cierre(
            {"total": 300000, "valor_dia": 100000, "fecha_retorno": "2026-05-18"},
            {"fecha_devolucion_real": "2026-05-20", "otros_cobros": 50000},
        )
        assert total == 550000.0

    def test_devolucion_antes_de_tiempo_sin_penalizacion(self):
        """Devolver antes no descuenta — días_retraso = max(0, ...) = 0."""
        total = FinancialService.calcular_total_cierre(
            {"total": 300000, "valor_dia": 100000, "fecha_retorno": "2026-05-25"},
            {"fecha_devolucion_real": "2026-05-20"},
        )
        assert total == 300000.0

    def test_fechas_invalidas_retraso_cero(self):
        """Si no se pueden parsear las fechas, dias_retraso = 0."""
        total = FinancialService.calcular_total_cierre(
            {"total": 200000, "valor_dia": 50000, "fecha_retorno": ""},
            {"fecha_devolucion_real": "mal-formato"},
        )
        assert total == 200000.0

    def test_fechas_ausentes_retraso_cero(self):
        """Si faltan fechas completamente, dias_retraso = 0."""
        total = FinancialService.calcular_total_cierre(
            {"total": 150000, "valor_dia": 75000},
            {},
        )
        assert total == 150000.0

    def test_solo_otros_cobros_sin_retraso(self):
        """A tiempo pero con otros cobros adicionales."""
        total = FinancialService.calcular_total_cierre(
            {"total": 500000, "valor_dia": 200000, "fecha_retorno": "2026-06-01"},
            {"fecha_devolucion_real": "2026-06-01", "otros_cobros": 120000},
        )
        assert total == 620000.0

    def test_siete_dias_de_retraso(self):
        """7 días de retraso con valor_dia alto."""
        total = FinancialService.calcular_total_cierre(
            {"total": 700000, "valor_dia": 100000, "fecha_retorno": "2026-05-01"},
            {"fecha_devolucion_real": "2026-05-08"},
        )
        assert total == 1400000.0  # 700000 + 7 × 100000

    def test_calculo_con_valores_decimales(self):
        """Valor_dia con decimales en el cálculo de retraso."""
        total = FinancialService.calcular_total_cierre(
            {"total": 150000, "valor_dia": 75000.50, "fecha_retorno": "2026-05-10"},
            {"fecha_devolucion_real": "2026-05-12"},
        )
        # 150000 + 2 × 75000.50 = 150000 + 150001 = 300001
        assert total == pytest.approx(300001.0, rel=1e-9)


# ═══════════════════════════════════════════════════════════════════════════════
# roi_flota Tests  (requires DB with autos, rentas, mantenimiento, gastos)
# ═══════════════════════════════════════════════════════════════════════════════


class TestRoiFlota:
    def test_roi_retorna_lista_con_estructura_correcta(self):
        """roi_flota() retorna lista de dicts con las claves esperadas."""
        reporte = FinancialService.roi_flota()
        assert isinstance(reporte, list)
        if reporte:
            item = reporte[0]
            expected_keys = {
                "placa",
                "vehiculo",
                "ingresos",
                "mantenimiento",
                "gastos",
                "costos_fijos",
                "utilidad",
                "roi_pct",
                "equilibrio_dias",
            }
            assert expected_keys.issubset(item.keys())
            # Tipos correctos
            assert isinstance(item["placa"], str)
            assert isinstance(item["ingresos"], float)
            assert isinstance(item["roi_pct"], float)

    def test_auto_sin_ingresos_ni_gastos(self):
        """Auto sin rentas, mantenimiento ni gastos → utilidad negativa (solo costos fijos)."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Zero",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("500000"),
                kilometraje=0,
                fecha_ingreso=datetime.date.today(),
            )
        )

        reporte = FinancialService.roi_flota()
        item = next(r for r in reporte if r["placa"] == p)

        assert item["ingresos"] == 0.0
        assert item["mantenimiento"] == 0.0
        assert item["gastos"] == 0.0
        assert item["costos_fijos"] >= 500000.0  # mínimo 1 mes
        assert item["utilidad"] < 0  # pérdida porque solo hay costos fijos
        assert item["roi_pct"] < 0

    def test_auto_con_ingresos_por_rentas(self):
        """Auto con renta finalizada genera ingresos en el ROI."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Income",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("300000"),
                kilometraje=0,
                fecha_ingreso=datetime.date.today(),
            )
        )
        # Crear una renta y cerrarla para que genere ingresos
        hoy = datetime.date.today()
        _renta_id = RentaRepositorySA.insertar(
            RentaCreate(
                placa=p,
                nombre_cliente="ROI Test",
                fecha_recogida=hoy - datetime.timedelta(days=5),
                hora_recogida=datetime.time(10, 0),
                fecha_retorno=hoy - datetime.timedelta(days=2),
                hora_retorno=datetime.time(10, 0),
                dias_calculados=3,
                valor_dia=Decimal("100000"),
                total=Decimal("300000"),
                abono=Decimal("300000"),
                saldo_pendiente=Decimal("0"),
                estado="Finalizado",  # ya finalizada
            )
        )

        reporte = FinancialService.roi_flota()
        item = next(r for r in reporte if r["placa"] == p)

        assert item["ingresos"] >= 300000.0
        # Utilidad = ingresos - costos_fijos (sin mantenimiento ni gastos)
        assert item["utilidad"] == pytest.approx(300000.0 - item["costos_fijos"], rel=1e-6)

    def test_auto_vendido_excluido(self):
        """Auto con estado 'Vendido' no aparece en el reporte."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Sold",
                tipo="Automóvil",
                estado="Vendido",
                fecha_ingreso=datetime.date.today(),
            )
        )

        reporte = FinancialService.roi_flota()
        placas = [r["placa"] for r in reporte]
        assert p not in placas

    def test_auto_baja_excluido(self):
        """Auto con estado 'Baja' no aparece en el reporte."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Retired",
                tipo="Automóvil",
                estado="Baja",
                fecha_ingreso=datetime.date.today(),
            )
        )

        reporte = FinancialService.roi_flota()
        placas = [r["placa"] for r in reporte]
        assert p not in placas

    def test_auto_con_gastos_e_ingresos(self):
        """Auto con ingresos, mantenimiento y gastos calcula ROI correctamente."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Full ROI",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("200000"),
                kilometraje=0,
                fecha_ingreso=datetime.date.today(),
            )
        )

        hoy = datetime.date.today()

        # Crear renta finalizada: $500,000 de ingresos
        RentaRepositorySA.insertar(
            RentaCreate(
                placa=p,
                nombre_cliente="ROI Full",
                fecha_recogida=hoy - datetime.timedelta(days=10),
                hora_recogida=datetime.time(10, 0),
                fecha_retorno=hoy - datetime.timedelta(days=6),
                hora_retorno=datetime.time(10, 0),
                dias_calculados=4,
                valor_dia=Decimal("125000"),
                total=Decimal("500000"),
                abono=Decimal("500000"),
                saldo_pendiente=Decimal("0"),
                estado="Finalizado",
            )
        )

        # Agregar mantenimiento: $80,000
        MantenimientoRepositorySA.insertar(
            MantenimientoCreate(
                placa=p,
                pieza_varias_tipo="Cambio Aceite",
                pieza_varias_fecha=hoy,
                cost_varios=Decimal("80000"),
                total_mantenimiento=Decimal("80000"),
            )
        )

        # Agregar gasto: $20,000
        GastoRepositorySA.insertar(
            GastoCreate(
                placa=p,
                fecha=hoy,
                categoria="Lavado",
                descripcion="Lavado general",
                monto=Decimal("20000"),
            )
        )

        reporte = FinancialService.roi_flota()
        item = next(r for r in reporte if r["placa"] == p)

        assert item["ingresos"] == 500000.0
        assert item["mantenimiento"] == 80000.0
        assert item["gastos"] == 20000.0

        # Utilidad = ingresos - mantenimiento - gastos - costos_fijos
        expected_utilidad = 500000.0 - 80000.0 - 20000.0 - item["costos_fijos"]
        assert item["utilidad"] == pytest.approx(expected_utilidad, rel=1e-6)

        # ROI % = (utilidad / costos_fijos) * 100
        if item["costos_fijos"] > 0:
            expected_roi = (expected_utilidad / item["costos_fijos"]) * 100
            assert item["roi_pct"] == pytest.approx(expected_roi, rel=1e-5)

    def test_multiples_autos_con_roi_variado(self):
        """Varios autos: uno rentable, otro en pérdida, uno excluido."""
        p1 = _next_placa()
        p2 = _next_placa()
        p3 = _next_placa()

        hoy = datetime.date.today()

        # Auto 1: rentable ($600,000 ingresos, $250,000 costo fijo)
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p1,
                marca="Test",
                modelo="Profit",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("250000"),
                fecha_ingreso=hoy,
            )
        )
        RentaRepositorySA.insertar(
            RentaCreate(
                placa=p1,
                nombre_cliente="Profit",
                fecha_recogida=hoy - datetime.timedelta(days=5),
                hora_recogida=datetime.time(10, 0),
                fecha_retorno=hoy - datetime.timedelta(days=1),
                hora_retorno=datetime.time(10, 0),
                dias_calculados=4,
                valor_dia=Decimal("150000"),
                total=Decimal("600000"),
                abono=Decimal("600000"),
                saldo_pendiente=Decimal("0"),
                estado="Finalizado",
            )
        )

        # Auto 2: pérdida (solo costo fijo, sin ingresos)
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p2,
                marca="Test",
                modelo="Loss",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("400000"),
                fecha_ingreso=hoy,
            )
        )

        # Auto 3: Vendido (excluido)
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p3,
                marca="Test",
                modelo="Sold",
                tipo="Automóvil",
                estado="Vendido",
                fecha_ingreso=hoy,
            )
        )

        reporte = FinancialService.roi_flota()
        placas = [r["placa"] for r in reporte]

        assert p1 in placas  # rentable
        assert p2 in placas  # pérdida
        assert p3 not in placas  # excluido

        # Verificar que p1 tiene ROI positivo y p2 negativo
        item1 = next(r for r in reporte if r["placa"] == p1)
        item2 = next(r for r in reporte if r["placa"] == p2)

        assert item1["ingresos"] > 0
        assert item2["ingresos"] == 0.0
        assert item2["utilidad"] < 0  # pérdida

    def test_roi_con_meses_calculados(self):
        """Múltiples meses desde fecha_ingreso incrementan costos_fijos."""
        p = _next_placa()
        hace_3_meses = datetime.date.today() - datetime.timedelta(days=90)

        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="Old Timer",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("100000"),
                kilometraje=0,
                fecha_ingreso=hace_3_meses,
            )
        )

        reporte = FinancialService.roi_flota()
        item = next(r for r in reporte if r["placa"] == p)

        # 3 meses × $100,000 = $300,000 en costos fijos (o más si el mes actual cuenta)
        assert item["costos_fijos"] >= 300000.0
        # Sin ingresos → utilidad negativa
        assert item["utilidad"] == pytest.approx(-item["costos_fijos"], rel=1e-6)

    def test_roi_equilibrio_dias(self):
        """equilibrio_dias se calcula correctamente cuando hay ingresos."""
        p = _next_placa()
        AutoRepositorySA.insertar(
            AutoCreate(
                placa=p,
                marca="Test",
                modelo="BreakEven",
                tipo="Automóvil",
                estado="Disponible",
                costo_fijo_mensual=Decimal("300000"),
                fecha_ingreso=datetime.date.today(),
            )
        )

        # Ingresos altos para probar el cálculo de días de equilibrio
        # Si mes = 1, ingresos = 600000, promedio_dia = 600000 / 30 = 20000
        # equilibrio_dias = 300000 / 20000 = 15
        RentaRepositorySA.insertar(
            RentaCreate(
                placa=p,
                nombre_cliente="BreakEven",
                fecha_recogida=datetime.date.today() - datetime.timedelta(days=10),
                hora_recogida=datetime.time(10, 0),
                fecha_retorno=datetime.date.today() - datetime.timedelta(days=5),
                hora_retorno=datetime.time(10, 0),
                dias_calculados=5,
                valor_dia=Decimal("120000"),
                total=Decimal("600000"),
                abono=Decimal("600000"),
                saldo_pendiente=Decimal("0"),
                estado="Finalizado",
            )
        )

        reporte = FinancialService.roi_flota()
        item = next(r for r in reporte if r["placa"] == p)

        # Si mes ≈ 1, promedio_dia = 600000/30 = 20000, equilibrio = 300000/20000 = 15
        if item["costos_fijos"] > 0 and item["ingresos"] > 0:
            assert item.get("equilibrio_dias", 0) > 0
            # Debería ser aproximadamente 15 días
            assert 10 <= item["equilibrio_dias"] <= 20
