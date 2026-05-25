"""Lazy-loading service imports.

Services are imported lazily when accessed, to avoid loading all
service modules at startup (saves ~200ms on import time).
"""

import importlib

_SERVICE_MODULE_MAP = {
    "AlertaService": "services.alerta_service",
    "AuthService": "services.auth_service",
    "AutoService": "services.auto_service",
    "BackupService": "services.backup_service",
    "ClienteService": "services.cliente_service",
    "ComparendoService": "services.comparendo_service",
    "DashboardService": "services.dashboard_service",
    "FinancialService": "services.financial_service",
    "GastoService": "services.gasto_service",
    "InformeService": "services.informe_service",
    "InspeccionService": "services.inspeccion_service",
    "MantenimientoService": "services.mantenimiento_service",
    "PagoService": "services.pago_service",
    "RentaService": "services.renta_service",
    "ReservaService": "services.reserva_service",
    "UsuarioService": "services.usuario_service",
}

__all__ = sorted(_SERVICE_MODULE_MAP.keys())


def __getattr__(name):
    if name in _SERVICE_MODULE_MAP:
        module = importlib.import_module(_SERVICE_MODULE_MAP[name])
        return getattr(module, name)
    raise AttributeError(f"module 'services' has no attribute '{name}'")


def __dir__():
    return __all__
