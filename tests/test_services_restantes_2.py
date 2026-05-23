"""
test_services_restantes_2.py — Unit tests for ComparendoService, GastoService,
                               and InspeccionService

Requires conftest.py to set up the in-memory SQLite database.
Each test method is self-contained (creates its own data).
Run: pytest tests/test_services_restantes_2.py -v
"""

import datetime
from decimal import Decimal

import pytest

from core.exceptions import (
    NegocioError, ValidacionError, RegistroNoEncontrado, PlacaInvalida,
)
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.renta_service import RentaService
from services.comparendo_service import ComparendoService
from services.gasto_service import GastoService
from services.inspeccion_service import InspeccionService


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers (same pattern from test_services_more.py)
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


# ═══════════════════════════════════════════════════════════════════════════════
# ComparendoService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestComparendoService:

    def test_listar_vacio(self):
        """listar() returns an empty list when no comparendos exist."""
        comparendos = ComparendoService.listar()
        assert isinstance(comparendos, list)

    def test_registrar_comparendo_basico(self):
        """registrar() creates a comparendo and returns the response."""
        _crear_auto("CMP001")
        result = ComparendoService.registrar({
            "placa": "CMP001",
            "fecha": str(datetime.date.today()),
            "hora": "14:30",
            "monto": "150000",
            "observaciones": "Exceso de velocidad",
        })
        assert isinstance(result, dict)
        assert result["id_comparendo"] > 0
        assert result["vinculado"] is False  # No rental for this date range
        assert result["id_renta"] is None
        assert result["id_cliente"] is None

    def test_registrar_comparendo_listar_incluye(self):
        """After registering, listar() includes the comparendo."""
        _crear_auto("CMP002")
        ComparendoService.registrar({
            "placa": "CMP002",
            "fecha": str(datetime.date.today()),
            "hora": "10:00",
            "monto": "200000",
        })
        comparendos = ComparendoService.listar()
        assert any(c["placa"] == "CMP002" for c in comparendos)

    def test_registrar_comparendo_sin_placa(self):
        """registrar() raises error when placa is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="Placa"):
            ComparendoService.registrar({
                "fecha": str(datetime.date.today()),
                "hora": "10:00",
                "monto": "50000",
            })

    def test_registrar_comparendo_fecha_invalida(self):
        """registrar() raises error when fecha/hora format is invalid."""
        _crear_auto("CMP003")
        with pytest.raises(ValidacionError, match="fecha|hora|inválida"):
            ComparendoService.registrar({
                "placa": "CMP003",
                "fecha": "not-a-date",
                "hora": "10:00",
                "monto": "50000",
            })

    def test_registrar_comparendo_vincula_renta_activa(self):
        """registrar() auto-links comparendo to an active rental in the same date range."""
        _crear_auto("CMP004")

        hoy = datetime.date.today()
        renta_id = _crear_renta(
            "CMP004",
            nombre_cliente="Comparendo Vinculado",
            fecha_recogida=hoy - datetime.timedelta(days=1),
            hora_recogida=datetime.time(8, 0),
            fecha_retorno=hoy + datetime.timedelta(days=5),
            hora_retorno=datetime.time(18, 0),
        )

        result = ComparendoService.registrar({
            "placa": "CMP004",
            "fecha": str(hoy),
            "hora": "12:00",
            "monto": "300000",
        })
        assert result["id_renta"] == renta_id
        assert result["vinculado"] is False  # No id_cliente on rental
        assert result["id_cliente"] is None

    def test_cambiar_estado_comparendo(self):
        """cambiar_estado() updates the comparendo status."""
        _crear_auto("CMP005")
        result = ComparendoService.registrar({
            "placa": "CMP005",
            "fecha": str(datetime.date.today()),
            "hora": "09:00",
            "monto": "100000",
            "estado": "Pendiente",
        })
        cid = result["id_comparendo"]

        ComparendoService.cambiar_estado(cid, "Pagado")
        comparendos = ComparendoService.listar()
        updated = [c for c in comparendos if c["id"] == cid]
        assert len(updated) == 1
        assert updated[0]["estado"] == "Pagado"

    def test_cambiar_estado_comparendo_inexistente(self):
        """cambiar_estado() raises RegistroNoEncontrado for non-existent comparendo."""
        with pytest.raises(RegistroNoEncontrado, match="Comparendo"):
            ComparendoService.cambiar_estado(99999, "Pagado")

    def test_listar_comparendos_estructura(self):
        """listar() returns comparendos with expected keys."""
        _crear_auto("CMP006")
        ComparendoService.registrar({
            "placa": "CMP006",
            "fecha": str(datetime.date.today()),
            "hora": "11:00",
            "monto": "75000",
        })
        comparendos = ComparendoService.listar()
        cmp = next((c for c in comparendos if c["placa"] == "CMP006"), None)
        assert cmp is not None
        assert "id" in cmp
        assert "placa" in cmp
        assert "monto" in cmp
        assert "estado" in cmp
        assert "fecha_infraccion" in cmp
        assert "hora_infraccion" in cmp


# ═══════════════════════════════════════════════════════════════════════════════
# GastoService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestGastoService:

    def test_listar_recientes_vacio(self):
        """listar_recientes() returns an empty list when no gastos exist."""
        gastos = GastoService.listar_recientes()
        assert isinstance(gastos, list)

    def test_registrar_gasto_basico(self):
        """registrar() creates a gasto and returns its ID."""
        gasto_id = GastoService.registrar({
            "fecha": str(datetime.date.today()),
            "categoria": "Lavado",
            "descripcion": "Lavado general",
            "monto": "25000",
        })
        assert isinstance(gasto_id, int)
        assert gasto_id > 0

    def test_registrar_gasto_listar_incluye(self):
        """After registering, listar_recientes() includes the gasto."""
        GastoService.registrar({
            "fecha": str(datetime.date.today()),
            "categoria": "Combustible",
            "descripcion": "Gasolina extra",
            "monto": "120000",
        })
        gastos = GastoService.listar_recientes()
        assert any(g["descripcion"] == "Gasolina extra" for g in gastos)

    def test_registrar_gasto_con_placa(self):
        """registrar() with a valid placa links the gasto to a vehicle."""
        _crear_auto("GST001")
        GastoService.registrar({
            "placa": "GST001",
            "fecha": str(datetime.date.today()),
            "categoria": "Llantas",
            "descripcion": "Cambio llanta delantera",
            "monto": "180000",
        })
        gastos = GastoService.listar_por_placa("GST001")
        assert len(gastos) >= 1
        assert any(g["descripcion"] == "Cambio llanta delantera" for g in gastos)

    def test_registrar_gasto_sin_fecha(self):
        """registrar() raises error when fecha is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="Fecha"):
            GastoService.registrar({
                "categoria": "Lavado",
                "descripcion": "Test",
                "monto": "10000",
            })

    def test_registrar_gasto_monto_cero(self):
        """registrar() raises error when monto <= 0."""
        with pytest.raises(ValidacionError, match="mayor a cero"):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "categoria": "Lavado",
                "descripcion": "Test",
                "monto": "0",
            })

    def test_registrar_gasto_monto_negativo(self):
        """registrar() raises error when monto is negative."""
        with pytest.raises(ValidacionError, match="mayor a cero"):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "categoria": "Lavado",
                "descripcion": "Test",
                "monto": "-5000",
            })

    def test_listar_por_placa_sin_gastos(self):
        """listar_por_placa() returns empty list for a placa with no gastos."""
        _crear_auto("GST002")
        gastos = GastoService.listar_por_placa("GST002")
        assert isinstance(gastos, list)
        assert len(gastos) == 0

    def test_listar_por_placa_placa_invalida(self):
        """listar_por_placa() raises error for invalid placa format."""
        with pytest.raises((ValidacionError, PlacaInvalida)):
            GastoService.listar_por_placa("X")

    def test_gasto_estructura_respuesta(self):
        """listar_recientes() returns gastos with expected keys."""
        GastoService.registrar({
            "fecha": str(datetime.date.today()),
            "categoria": "Papelería",
            "descripcion": "Resmas de papel",
            "monto": "35000",
            "usuario": "Admin",
        })
        gastos = GastoService.listar_recientes()
        gasto = next((g for g in gastos if g["descripcion"] == "Resmas de papel"), None)
        assert gasto is not None
        assert "id" in gasto
        assert "fecha" in gasto
        assert "categoria" in gasto
        assert "descripcion" in gasto
        assert "monto" in gasto
        assert "usuario" in gasto

    def test_gasto_sin_categoria(self):
        """registrar() raises error when categoria is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="Categoría"):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "descripcion": "Test",
                "monto": "10000",
            })

    def test_gasto_sin_descripcion(self):
        """registrar() raises error when descripcion is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="Descripción"):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "categoria": "Lavado",
                "monto": "10000",
            })

    def test_gasto_sin_monto(self):
        """registrar() raises error when monto is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="Monto"):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "categoria": "Lavado",
                "descripcion": "Test",
            })

    def test_gasto_con_placa_invalida(self):
        """registrar() raises error when placa format is invalid."""
        with pytest.raises((ValidacionError, PlacaInvalida), match="placa|Placa"):
            GastoService.registrar({
                "placa": "X",
                "fecha": str(datetime.date.today()),
                "categoria": "Lavado",
                "descripcion": "Test",
                "monto": "10000",
            })

    def test_listar_recientes_limite(self):
        """listar_recientes() returns at most 200 recent gastos."""
        for i in range(5):
            GastoService.registrar({
                "fecha": str(datetime.date.today()),
                "categoria": "Varios",
                "descripcion": f"Gasto test {i}",
                "monto": f"{1000 * (i + 1)}",
            })
        gastos = GastoService.listar_recientes()
        assert len(gastos) >= 5


# ═══════════════════════════════════════════════════════════════════════════════
# InspeccionService Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestInspeccionService:

    def _setup_renta(self, placa: str) -> int:
        """Helper: create an auto + rental and return rental ID."""
        _crear_auto(placa)
        return _crear_renta(placa, nombre_cliente="Inspección Test")

    def test_listar_por_renta_vacio(self):
        """listar_por_renta() returns empty list when no inspections exist."""
        renta_id = self._setup_renta("INP001")
        inspecciones = InspeccionService.listar_por_renta(renta_id)
        assert isinstance(inspecciones, list)
        assert len(inspecciones) == 0

    def test_registrar_inspeccion_basica(self):
        """registrar() creates an inspection and returns its ID."""
        renta_id = self._setup_renta("INP002")
        inspeccion_id = InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Salida",
            "kilometraje": 10000,
            "nivel_gasolina": "Lleno",
        })
        assert isinstance(inspeccion_id, int)
        assert inspeccion_id > 0

    def test_registrar_inspeccion_listar_incluye(self):
        """After registering, listar_por_renta() includes the inspection."""
        renta_id = self._setup_renta("INP003")
        InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Salida",
            "kilometraje": 15000,
            "nivel_gasolina": "Lleno",
        })
        inspecciones = InspeccionService.listar_por_renta(renta_id)
        assert len(inspecciones) == 1
        assert inspecciones[0]["tipo"] == "Salida"

    def test_registrar_inspeccion_con_todos_los_campos(self):
        """registrar() works with all optional fields provided."""
        renta_id = self._setup_renta("INP004")
        inspeccion_id = InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Retorno",
            "kilometraje": 15300,
            "nivel_gasolina": "3/4",
            "limpieza": "Limpio",
            "tiene_repuesto": True,
            "tiene_gato_cruceta": False,
            "tiene_kit_carretera": True,
            "tiene_documentos": True,
            "danos_carroceria": "Rayón puerta derecha",
            "observaciones": "Todo en orden",
        })
        assert inspeccion_id > 0
        inspecciones = InspeccionService.listar_por_renta(renta_id)
        inspeccion = next((i for i in inspecciones if i["id"] == inspeccion_id), None)
        assert inspeccion is not None
        assert inspeccion["danos_carroceria"] == "Rayón puerta derecha"
        assert inspeccion["tipo"] == "Retorno"

    def test_registrar_inspeccion_sin_id_renta(self):
        """registrar() raises error when id_renta is missing."""
        with pytest.raises((ValidacionError, NegocioError), match="renta|Renta|ID"):
            InspeccionService.registrar({
                "tipo": "Salida",
                "kilometraje": 10000,
                "nivel_gasolina": "Lleno",
            })

    def test_registrar_inspeccion_sin_tipo(self):
        """registrar() raises error when tipo is missing."""
        renta_id = self._setup_renta("INP005")
        with pytest.raises((ValidacionError, NegocioError), match="tipo|Tipo|Inspección"):
            InspeccionService.registrar({
                "id_renta": renta_id,
                "kilometraje": 10000,
                "nivel_gasolina": "Lleno",
            })

    def test_registrar_inspeccion_sin_kilometraje(self):
        """registrar() raises error when kilometraje is missing."""
        renta_id = self._setup_renta("INP006")
        with pytest.raises((ValidacionError, NegocioError), match="kilometraje|Kilometraje"):
            InspeccionService.registrar({
                "id_renta": renta_id,
                "tipo": "Salida",
                "nivel_gasolina": "Lleno",
            })

    def test_registrar_inspeccion_sin_nivel_gasolina(self):
        """registrar() raises error when nivel_gasolina is missing (required in schema)."""
        renta_id = self._setup_renta("INP007")
        with pytest.raises((ValidacionError, NegocioError), match="nivel_gasolina|gasolina|Gasolina"):
            InspeccionService.registrar({
                "id_renta": renta_id,
                "tipo": "Salida",
                "kilometraje": 10000,
            })

    def test_registrar_varias_inspecciones_misma_renta(self):
        """registrar() can add multiple inspections for the same rental."""
        renta_id = self._setup_renta("INP008")
        InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Salida",
            "kilometraje": 20000,
            "nivel_gasolina": "Lleno",
        })
        InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Retorno",
            "kilometraje": 20350,
            "nivel_gasolina": "1/2",
            "danos_carroceria": "Ninguno",
        })
        inspecciones = InspeccionService.listar_por_renta(renta_id)
        assert len(inspecciones) == 2

    def test_listar_por_renta_inexistente(self):
        """listar_por_renta() returns empty list for non-existent rental ID."""
        inspecciones = InspeccionService.listar_por_renta(99999)
        assert isinstance(inspecciones, list)
        assert len(inspecciones) == 0

    def test_inspeccion_estructura_respuesta(self):
        """listar_por_renta() returns inspections with expected keys."""
        renta_id = self._setup_renta("INP009")
        InspeccionService.registrar({
            "id_renta": renta_id,
            "tipo": "Salida",
            "kilometraje": 5000,
            "nivel_gasolina": "Lleno",
        })
        inspecciones = InspeccionService.listar_por_renta(renta_id)
        inspeccion = inspecciones[0]
        assert "id" in inspeccion
        assert "id_renta" in inspeccion
        assert "tipo" in inspeccion
        assert "kilometraje" in inspeccion
        assert "nivel_gasolina" in inspeccion
        assert "limpieza" in inspeccion
        assert "tiene_repuesto" in inspeccion
        assert "tiene_gato_cruceta" in inspeccion
        assert "tiene_kit_carretera" in inspeccion
        assert "tiene_documentos" in inspeccion
        assert "danos_carroceria" in inspeccion
        assert "observaciones" in inspeccion
