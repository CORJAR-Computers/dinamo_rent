from core.models import Auto
from services.auto_service import AutoService
from services.dashboard_service import DashboardService


def test_kpi_globales_estructura(db_session):
    """Validate KPI globales response structure (keys, types)."""
    kpi = DashboardService.kpi_globales()
    assert isinstance(kpi, dict)
    # All expected keys exist
    expected_keys = [
        "rentas_activas",
        "autos_disponibles",
        "autos_rentados",
        "autos_mantenimiento",
        "total_flota",
        "ocupacion_flota",
        "ingresos_mes",
        "pagos_pendientes",
    ]
    for key in expected_keys:
        assert key in kpi, f"Missing key: {key}"
    # All values are numeric and >= 0
    for key in expected_keys:
        assert isinstance(kpi[key], (int, float)), f"{key} should be numeric, got {type(kpi[key])}"
        assert kpi[key] >= 0, f"{key}={kpi[key]} should be >= 0"


def test_kpi_globales_incluye_nuevos_autos(db_session):
    """KPI globales includes newly created autos in its counts."""
    kpi_before = DashboardService.kpi_globales()
    total_before = kpi_before["total_flota"]

    # Add 2 cars
    auto1 = Auto(placa="XYZ123", marca="Toyota", modelo="Corolla", estado="Disponible")
    auto2 = Auto(placa="ABC987", marca="Ford", modelo="Fiesta", estado="Rentado")
    db_session.add(auto1)
    db_session.add(auto2)
    db_session.commit()

    kpi_after = DashboardService.kpi_globales()
    # Total should have increased by at least 2
    assert kpi_after["total_flota"] >= total_before + 2
    # At least 1 Disponible (ours) and 1 Rentado (ours)
    assert kpi_after["autos_disponibles"] >= 1
    assert kpi_after["autos_rentados"] >= 1
    # New autos exist in DB
    assert AutoService.obtener("XYZ123")["placa"] == "XYZ123"
    assert AutoService.obtener("ABC987")["placa"] == "ABC987"
