"""
services/__init__.py — Importación centralizada de todos los servicios

F1B: Punto de entrada único para importar servicios.
Los archivos individuales se pueden importar directamente o desde aquí.

Usage:
    from services import AutoService, RentaService, FinancialService
"""
from services.auto_service import AutoService
from services.cliente_service import ClienteService
from services.renta_service import RentaService
from services.auth_service import AuthService
from services.backup_service import BackupService
from services.reserva_service import ReservaService
from services.mantenimiento_service import MantenimientoService
from services.usuario_service import UsuarioService
from services.inspeccion_service import InspeccionService
from services.comparendo_service import ComparendoService
from services.pago_service import PagoService
from services.gasto_service import GastoService
from services.alerta_service import AlertaService
from services.informe_service import InformeService
from services.financial_service import FinancialService
from services.dashboard_service import DashboardService

__all__ = [
    "AutoService",
    "ClienteService",
    "RentaService",
    "AuthService",
    "BackupService",
    "ReservaService",
    "MantenimientoService",
    "UsuarioService",
    "InspeccionService",
    "ComparendoService",
    "PagoService",
    "GastoService",
    "AlertaService",
    "InformeService",
    "FinancialService",
    "DashboardService",
]
